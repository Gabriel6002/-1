#!/usr/bin/env python3
"""The training settings used for the Apple Silicon experiment."""

import argparse

from ultralytics import YOLO

from common import describe_device, pick_device


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data/data.yaml')
    ap.add_argument('--model', default='yolov8n.pt')
    ap.add_argument('--epochs', type=int, default=100)
    ap.add_argument('--batch', type=int, default=8)
    ap.add_argument('--imgsz', type=int, default=640)
    ap.add_argument('--device', default='auto')
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    device = pick_device(args.device)
    print(f'Training device: {describe_device(device)}')
    YOLO(args.model).train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
        seed=args.seed,
        project='results',
        name='desk_y8n',
    )


if __name__ == '__main__':
    main()
