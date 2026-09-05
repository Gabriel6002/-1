import argparse
import os
from collections import Counter

import cv2

IMG_EXT = ['.jpg', '.jpeg', '.png', '.bmp']
PALETTE = [(56, 56, 255), (31, 112, 255), (49, 210, 207), (10, 249, 72),
           (134, 219, 61), (255, 194, 0), (168, 153, 44), (23, 204, 146)]


def load_yaml(path):
    root, names = os.path.dirname(os.path.abspath(path)), {}
    splits, in_names = {}, False
    with open(path, encoding='utf-8') as f:
        for line in f:
            raw = line.rstrip('\n')
            if not raw.strip() or raw.strip().startswith('#'):
                continue
            if raw.startswith('names:'):
                in_names = True
                continue
            if in_names and (raw.startswith(' ') or raw.startswith('\t')):
                k, _, v = raw.strip().partition(':')
                names[int(k)] = v.strip()
                continue
            in_names = False
            k, _, v = raw.partition(':')
            k, v = k.strip(), v.strip()
            if k == 'path':
                root = v
            elif k in ('train', 'val', 'test'):
                splits[k] = v
    return root, splits, names


def find_image(img_dir, stem):
    for ext in IMG_EXT:
        p = os.path.join(img_dir, stem + ext)
        if os.path.exists(p):
            return p
    return None


def check_split(root, rel, names, problems, hist, samples):
    img_dir = os.path.join(root, rel)
    lbl_dir = img_dir.replace(os.sep + 'images', os.sep + 'labels')
    if not os.path.isdir(img_dir):
        return 0

    count = 0
    for fn in sorted(os.listdir(img_dir)):
        if os.path.splitext(fn)[1].lower() not in IMG_EXT:
            continue
        count += 1
        stem = os.path.splitext(fn)[0]
        lbl = os.path.join(lbl_dir, stem + '.txt')
        if not os.path.exists(lbl):
            problems.append(f'[缺标注] {rel}/{fn}')
            continue

        boxes, seen = [], set()
        with open(lbl, encoding='utf-8') as f:
            for ln, line in enumerate(f, 1):
                parts = line.split()
                if not parts:
                    continue
                if len(parts) != 5:
                    problems.append(f'[格式错] {stem}.txt:{ln} 应为 5 个字段，实际 {len(parts)}')
                    continue
                try:
                    cid = int(parts[0])
                    x, y, w, h = map(float, parts[1:])
                except ValueError:
                    problems.append(f'[非数值] {stem}.txt:{ln} → {line.strip()}')
                    continue
                if cid not in names:
                    problems.append(f'[类别越界] {stem}.txt:{ln} class_id={cid}')
                if not all(0.0 <= v <= 1.0 for v in (x, y, w, h)):
                    problems.append(f'[坐标越界] {stem}.txt:{ln} → {x:.3f} {y:.3f} {w:.3f} {h:.3f}')
                if w <= 0.002 or h <= 0.002:
                    problems.append(f'[框过小] {stem}.txt:{ln} w={w:.4f} h={h:.4f}')
                key = (cid, round(x, 4), round(y, 4), round(w, 4), round(h, 4))
                if key in seen:
                    problems.append(f'[重复框] {stem}.txt:{ln}')
                seen.add(key)
                hist[cid] += 1
                boxes.append((cid, x, y, w, h))

        if not boxes:
            problems.append(f'[空标注] {stem}.txt 没有任何框')
        img_path = find_image(img_dir, stem)
        if img_path:
            samples.append((img_path, boxes))
    return count


def visualize(samples, names, n):
    import random
    random.shuffle(samples)
    print(f'\n抽样可视化 {min(n, len(samples))} 张，按任意键下一张，q 退出')
    for img_path, boxes in samples[:n]:
        img = cv2.imread(img_path)
        if img is None:
            continue
        H, W = img.shape[:2]
        for cid, x, y, w, h in boxes:
            x1, y1 = int((x - w / 2) * W), int((y - h / 2) * H)
            x2, y2 = int((x + w / 2) * W), int((y + h / 2) * H)
            color = PALETTE[cid % len(PALETTE)]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, names.get(cid, str(cid)), (x1, max(y1 - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.imshow('label check', img)
        if (cv2.waitKey(0) & 0xFF) == ord('q'):
            break
    cv2.destroyAllWindows()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True, help='data.yaml 路径')
    ap.add_argument('--show', type=int, default=0, help='抽样可视化张数，0=不显示')
    args = ap.parse_args()

    root, splits, names = load_yaml(args.data)
    print(f'数据集根目录: {root}')
    print(f'类别: {names}\n')

    problems, hist, samples = [], Counter(), []
    total = 0
    for split, rel in splits.items():
        n = check_split(root, rel, names, problems, hist, samples)
        print(f'{split:<6}: {n} 张图片')
        total += n

    print(f'\n合计 {total} 张，标注框统计：')
    for cid in sorted(names):
        n = hist.get(cid, 0)
        flag = '  ⚠ 样本偏少' if n < 100 else ''
        print(f'    [{cid}] {names[cid]:<16} {n} 个框{flag}')

    if hist:
        mx, mn = max(hist.values()), min(hist.values())
        if mn and mx / mn > 3:
            print(f'\n⚠ 类别不均衡：最多/最少 = {mx / mn:.1f}x，建议补采少数类的数据')

    if problems:
        print(f'\n发现 {len(problems)} 个问题：')
        for p in problems[:40]:
            print('   ', p)
        if len(problems) > 40:
            print(f'    ... 还有 {len(problems) - 40} 个')
    else:
        print('\n✓ 未发现标注问题')

    if args.show:
        visualize(samples, names, args.show)


if __name__ == '__main__':
    main()
