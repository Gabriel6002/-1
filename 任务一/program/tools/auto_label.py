#!/usr/bin/env python3
"""自动预标注：用 COCO 预训练 YOLO 检测桌面物体，输出 YOLO 格式标注，供人工复核。

思路：你们要的 mouse/keyboard/cup 都是 COCO 类别，预训练模型直接认识。
先让它把框画好，人工只做"检查 + 修正"，比从零画框快 5~10 倍。

用法：
  python3 auto_label.py --images ../dataset/raw --out ../dataset/labeled \
      --classes mouse keyboard cup --model yolov8x.pt --conf 0.25

产出（可直接用 labelImg 打开复核）：
  <out>/images/*.jpg      复制过来的图片
  <out>/labels/*.txt      自动生成的 YOLO 标注
  <out>/classes.txt       类别表（labelImg 需要）
  <out>/_preview/*.jpg    画好框的预览图，先扫一遍看质量
  <out>/_review.csv       每张图的框数/最低置信度，按可疑程度排序，优先复核
"""

import argparse
import csv
import os
import shutil
import sys

# 保证无论从哪个目录调用，都能找到同目录的 common.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2

# 你们的类别名 → COCO 里的类别名（预训练模型认识的名字）
# 左边是自定义类别，右边必须是 COCO 标准名
COCO_ALIASES = {
    'mouse': 'mouse', 'keyboard': 'keyboard', 'cup': 'cup',
    'bottle': 'bottle', 'cell phone': 'cell phone', 'phone': 'cell phone',
    'book': 'book', 'scissors': 'scissors', 'remote': 'remote',
    'laptop': 'laptop', 'banana': 'banana', 'apple': 'apple', 'orange': 'orange',
}
IMG_EXT = {'.jpg', '.jpeg', '.png', '.bmp'}
PALETTE = [(56, 56, 255), (49, 210, 207), (134, 219, 61),
           (255, 194, 0), (168, 153, 44), (23, 204, 146)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', required=True, help='待标注图片目录（可含子文件夹）')
    ap.add_argument('--out', required=True, help='输出目录')
    ap.add_argument('--classes', nargs='+', required=True,
                    help='你们的类别，顺序 = 最终类别编号，务必与 classes.txt 一致')
    ap.add_argument('--model', default='yolov8x.pt',
                    help='预训练权重，x 最准（首次会自动下载约 130MB）')
    ap.add_argument('--conf', type=float, default=0.25,
                    help='置信度阈值，低一点宁可多框，人工删比补快')
    ap.add_argument('--imgsz', type=int, default=960,
                    help='预标注用大输入更准，反正不实时')
    ap.add_argument('--device', default='auto')
    args = ap.parse_args()

    from common import pick_device, describe_device
    device = pick_device(args.device)
    print(f'预标注设备: {describe_device(device)}')

    # 建立 “COCO 类别id → 我们的类别id” 的映射
    from ultralytics import YOLO
    model = YOLO(args.model)
    coco_name_to_id = {v: k for k, v in model.names.items()}

    want = {}          # coco_id -> our_id
    for our_id, cname in enumerate(args.classes):
        coco_name = COCO_ALIASES.get(cname, cname)
        if coco_name not in coco_name_to_id:
            print(f'⚠ 类别 "{cname}" 不在 COCO 里，这类没法自动标，需要手动画：'
                  f'可选 COCO 名见 {sorted(COCO_ALIASES.values())}')
            continue
        want[coco_name_to_id[coco_name]] = our_id
        print(f'  {cname}(我们的#{our_id}) ← COCO "{coco_name}"(#{coco_name_to_id[coco_name]})')

    if not want:
        raise SystemExit('没有任何类别能自动标注，检查 --classes 是否为 COCO 类别')

    img_out = os.path.join(args.out, 'images')
    lbl_out = os.path.join(args.out, 'labels')
    prev_out = os.path.join(args.out, '_preview')
    for d in (img_out, lbl_out, prev_out):
        os.makedirs(d, exist_ok=True)
    with open(os.path.join(args.out, 'classes.txt'), 'w') as f:
        f.write('\n'.join(args.classes) + '\n')

    files = []
    for root, _, names in os.walk(args.images):
        if os.path.abspath(root).startswith(os.path.abspath(args.out)):
            continue                       # 别把输出目录自己也扫进去
        for n in names:
            if os.path.splitext(n)[1].lower() in IMG_EXT:
                files.append(os.path.join(root, n))
    files.sort()
    if not files:
        raise SystemExit(f'{args.images} 下没有图片')
    print(f'\n共 {len(files)} 张待标注\n')

    review, n_boxes, n_empty = [], 0, 0
    for i, path in enumerate(files, 1):
        img = cv2.imread(path)
        if img is None:
            continue
        h, w = img.shape[:2]
        r = model.predict(source=img, imgsz=args.imgsz, conf=args.conf,
                          device=device, verbose=False)[0]

        stem = f'{i:05d}_{os.path.splitext(os.path.basename(path))[0]}'
        # 图片统一复制到输出目录，保证 image/label 同名配对，labelImg 才认
        dst_img = os.path.join(img_out, stem + '.jpg')
        cv2.imwrite(dst_img, img)

        lines, confs, prev = [], [], img.copy()
        if r.boxes is not None:
            for (x1, y1, x2, y2), cf, ci in zip(
                    r.boxes.xyxy.cpu().numpy(),
                    r.boxes.conf.cpu().numpy(),
                    r.boxes.cls.cpu().numpy().astype(int)):
                if int(ci) not in want:
                    continue               # 不是我们要的类别，丢弃
                our_id = want[int(ci)]
                cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
                bw, bh = (x2 - x1) / w, (y2 - y1) / h
                lines.append(f'{our_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}')
                confs.append(float(cf))
                c = PALETTE[our_id % len(PALETTE)]
                p1, p2 = (int(x1), int(y1)), (int(x2), int(y2))
                cv2.rectangle(prev, p1, p2, c, 2)
                lb = f'{args.classes[our_id]} {cf:.2f}'
                cv2.putText(prev, lb, (p1[0], max(p1[1] - 6, 14)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, c, 2)

        with open(os.path.join(lbl_out, stem + '.txt'), 'w') as f:
            f.write('\n'.join(lines))
        cv2.imwrite(os.path.join(prev_out, stem + '.jpg'), prev)

        n_boxes += len(lines)
        if not lines:
            n_empty += 1
        review.append({
            'image': stem + '.jpg', 'n_boxes': len(lines),
            'min_conf': round(min(confs), 3) if confs else 0.0,
            'source': os.path.relpath(path),
        })
        if i % 50 == 0:
            print(f'  {i}/{len(files)}')

    # 按 “框数少 + 置信度低” 排序，最可疑的排最前，人工优先看这些
    review.sort(key=lambda r: (r['n_boxes'], r['min_conf']))
    with open(os.path.join(args.out, '_review.csv'), 'w', newline='',
              encoding='utf-8-sig') as f:
        w_ = csv.DictWriter(f, fieldnames=['image', 'n_boxes', 'min_conf', 'source'])
        w_.writeheader()
        w_.writerows(review)

    print('\n' + '=' * 54)
    print(f'  已预标注 {len(files)} 张，共 {n_boxes} 个框')
    print(f'  其中 {n_empty} 张没检测到任何目标（需重点人工检查）')
    print('=' * 54)
    print(f'输出目录 : {os.path.abspath(args.out)}')
    print('复核步骤 :')
    print(f'  1) 先翻 _preview/ 里的图，整体扫一遍质量')
    print(f'  2) 打开 _review.csv，n_boxes=0 或 min_conf 低的优先改')
    print(f'  3) labelImg {img_out}  逐张修正（删错框/补漏框/改类别）')
    print(f'     labelImg 里 Open Dir 选 images/，Change Save Dir 选 labels/')


if __name__ == '__main__':
    main()
