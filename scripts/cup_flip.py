#!/usr/bin/env python3
"""Make training-only horizontal flips for images containing a verified Cup box."""

import argparse
from pathlib import Path

import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('images', type=Path)
    ap.add_argument('labels', type=Path)
    ap.add_argument('--cup-id', type=int, default=2)
    ap.add_argument('--prefix', default='augcup_flip_')
    args = ap.parse_args()

    made = 0
    for label in sorted(args.labels.glob('*.txt')):
        if label.name.startswith(args.prefix):
            continue
        rows = [line.split() for line in label.read_text().splitlines() if line.strip()]
        if not any(int(row[0]) == args.cup_id for row in rows):
            continue
        image = next((args.images / f'{label.stem}{ext}' for ext in ('.JPG', '.jpg', '.png')
                      if (args.images / f'{label.stem}{ext}').exists()), None)
        if image is None:
            continue
        frame = cv2.imread(str(image))
        if frame is None:
            continue
        frame = cv2.convertScaleAbs(cv2.flip(frame, 1), alpha=1.04, beta=3)
        out_image = args.images / f'{args.prefix}{image.name}'
        out_label = args.labels / f'{args.prefix}{label.name}'
        if out_image.exists() and out_label.exists():
            continue
        cv2.imwrite(str(out_image), frame)
        transformed = []
        for cls_id, x, y, w, h in rows:
            transformed.append(f'{cls_id} {1.0-float(x):.6f} {float(y):.6f} '
                               f'{float(w):.6f} {float(h):.6f}')
        out_label.write_text('\n'.join(transformed) + '\n')
        made += 1
    print(f'Created {made} Cup-focused training pairs.')


if __name__ == '__main__':
    main()
