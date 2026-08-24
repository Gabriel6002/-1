#!/usr/bin/env python3
"""把标注好的图片按比例划分为 train/val/test，并生成 data.yaml。

输入目录要求（labelImg / X-AnyLabeling 导出 YOLO 格式后的样子）：
  <input>/images/*.jpg      图片
  <input>/labels/*.txt      同名标注文件
或者图片和 txt 混在同一个目录里也行，脚本会自动配对。

用法：
  python3 split_dataset.py --input ../dataset/labeled \
      --output ../dataset/desk_objects --classes mouse cup keyboard \
      --ratio 0.7 0.2 0.1
"""

import argparse
import os
import random
import shutil
from collections import Counter

IMG_EXT = {'.jpg', '.jpeg', '.png', '.bmp'}


def collect_pairs(input_dir):
    """找出所有 (图片, 标注) 对；没有 txt 的图片视为背景负样本，也允许保留。"""
    img_dir = os.path.join(input_dir, 'images')
    lbl_dir = os.path.join(input_dir, 'labels')
    if not os.path.isdir(img_dir):
        img_dir = lbl_dir = input_dir

    pairs, orphan_labels, no_label = [], [], []
    imgs = [f for f in os.listdir(img_dir)
            if os.path.splitext(f)[1].lower() in IMG_EXT]
    for f in sorted(imgs):
        stem = os.path.splitext(f)[0]
        lbl = os.path.join(lbl_dir, stem + '.txt')
        if os.path.exists(lbl):
            pairs.append((os.path.join(img_dir, f), lbl))
        else:
            no_label.append(f)
            pairs.append((os.path.join(img_dir, f), None))

    if os.path.isdir(lbl_dir):
        stems = {os.path.splitext(f)[0] for f in imgs}
        for f in os.listdir(lbl_dir):
            if f.endswith('.txt') and f != 'classes.txt' \
                    and os.path.splitext(f)[0] not in stems:
                orphan_labels.append(f)

    return pairs, no_label, orphan_labels


def class_histogram(pairs):
    hist = Counter()
    for _, lbl in pairs:
        if not lbl:
            continue
        with open(lbl, encoding='utf-8') as f:
            for line in f:
                parts = line.split()
                if parts:
                    hist[int(parts[0])] += 1
    return hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='已标注数据目录')
    ap.add_argument('--output', required=True, help='输出数据集根目录')
    ap.add_argument('--classes', nargs='+', required=True, help='类别名，顺序必须与标注时一致')
    ap.add_argument('--ratio', nargs=3, type=float, default=[0.7, 0.2, 0.1],
                    metavar=('TRAIN', 'VAL', 'TEST'))
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--move', action='store_true', help='移动而不是复制文件')
    args = ap.parse_args()

    if abs(sum(args.ratio) - 1.0) > 1e-6:
        raise SystemExit(f'划分比例之和必须为 1，当前为 {sum(args.ratio)}')

    pairs, no_label, orphan = collect_pairs(args.input)
    if not pairs:
        raise SystemExit(f'在 {args.input} 下没找到图片')

    print(f'共找到 {len(pairs)} 张图片')
    if no_label:
        print(f'⚠ {len(no_label)} 张图片没有对应的 .txt 标注（会被当作背景负样本）:')
        for f in no_label[:5]:
            print(f'    {f}')
        if len(no_label) > 5:
            print(f'    ... 还有 {len(no_label) - 5} 张')
    if orphan:
        print(f'⚠ {len(orphan)} 个标注文件找不到对应图片，已忽略')

    hist = class_histogram(pairs)
    print('\n标注框统计：')
    for cid in sorted(hist):
        name = args.classes[cid] if cid < len(args.classes) else f'<越界id={cid}>'
        print(f'    [{cid}] {name:<16} {hist[cid]} 个框')
    bad = [c for c in hist if c >= len(args.classes)]
    if bad:
        raise SystemExit(f'标注中出现越界类别 id {bad}，请检查 --classes 顺序或标注文件')

    random.seed(args.seed)
    random.shuffle(pairs)
    n = len(pairs)
    n_train = int(n * args.ratio[0])
    n_val = int(n * args.ratio[1])
    splits = {
        'train': pairs[:n_train],
        'val': pairs[n_train:n_train + n_val],
        'test': pairs[n_train + n_val:],
    }

    op = shutil.move if args.move else shutil.copy2
    for split, items in splits.items():
        img_out = os.path.join(args.output, 'images', split)
        lbl_out = os.path.join(args.output, 'labels', split)
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)
        for img, lbl in items:
            op(img, os.path.join(img_out, os.path.basename(img)))
            if lbl:
                op(lbl, os.path.join(lbl_out, os.path.basename(lbl)))
        print(f'{split:<6}: {len(items)} 张')

    yaml_path = os.path.join(args.output, 'data.yaml')
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write('# 由 split_dataset.py 自动生成\n')
        f.write(f'path: {os.path.abspath(args.output)}\n')
        f.write('train: images/train\n')
        f.write('val: images/val\n')
        f.write('test: images/test\n\n')
        f.write(f'nc: {len(args.classes)}\n')
        f.write('names:\n')
        for i, c in enumerate(args.classes):
            f.write(f'  {i}: {c}\n')
    print(f'\n已生成 {yaml_path}')


if __name__ == '__main__':
    main()
