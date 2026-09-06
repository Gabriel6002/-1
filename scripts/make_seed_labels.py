#!/usr/bin/env python3
"""Create reviewable YOLO seed labels from a pretrained detector."""

import argparse
from pathlib import Path

from ultralytics import YOLO

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('images', type=Path)
    ap.add_argument('labels', type=Path)
    ap.add_argument('--model', default='yolov8x.pt')
    ap.add_argument('--conf', type=float, default=0.20)
    ap.add_argument('--classes', nargs='+', default=['mouse', 'keyboard', 'cup'])
    args = ap.parse_args()

    wanted = {name.lower(): idx for idx, name in enumerate(args.classes)}
    args.labels.mkdir(parents=True, exist_ok=True)
    model = YOLO(args.model)
    images = [p for p in sorted(args.images.iterdir()) if p.suffix.lower() in IMAGE_EXTENSIONS]
    for image in images:
        result = model.predict(str(image), conf=args.conf, verbose=False)[0]
        lines = []
        for box in result.boxes:
            source_name = result.names[int(box.cls[0])].lower()
            if source_name not in wanted:
                continue
            x, y, w, h = box.xywhn[0].tolist()
            lines.append(f'{wanted[source_name]} {x:.6f} {y:.6f} {w:.6f} {h:.6f}')
        (args.labels / f'{image.stem}.txt').write_text('\n'.join(lines) + ('\n' if lines else ''))
    print(f'Wrote {len(images)} seed-label files to {args.labels}; manual review is required.')


if __name__ == '__main__':
    main()
