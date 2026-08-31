#!/usr/bin/env python3
"""数据采集：从摄像头抓图存到 dataset/raw/<类别名>/。

用法：
  python3 capture_images.py --class mouse                 # 空格拍一张
  python3 capture_images.py --class cup --auto --interval 0.5   # 自动连拍

按键：
  空格  拍一张        a  切换自动连拍       u  撤销上一张
  q/ESC 退出
"""

import argparse
import os
import time
from datetime import datetime

import cv2


def build_capture(args):
    if args.csi:
        pipeline = (
            f'nvarguscamerasrc sensor-id={args.device} ! '
            f'video/x-raw(memory:NVMM), width=(int){args.width}, '
            f'height=(int){args.height}, framerate=(fraction)30/1 ! '
            f'nvvidconv flip-method={args.flip} ! video/x-raw, format=(string)BGRx ! '
            f'videoconvert ! video/x-raw, format=(string)BGR ! appsink drop=true max-buffers=1'
        )
        return cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    cap = cv2.VideoCapture(args.device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    return cap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--class', dest='cls', required=True, help='类别名，用英文小写')
    ap.add_argument('--out', default='../dataset/raw', help='输出根目录')
    ap.add_argument('--device', type=int, default=0)
    ap.add_argument('--csi', action='store_true', help='使用 Jetson CSI 摄像头')
    ap.add_argument('--flip', type=int, default=0)
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720)
    ap.add_argument('--auto', action='store_true', help='启动即自动连拍')
    ap.add_argument('--interval', type=float, default=0.5, help='自动连拍间隔（秒）')
    ap.add_argument('--limit', type=int, default=0, help='拍够多少张自动退出，0=不限')
    args = ap.parse_args()

    out_dir = os.path.join(args.out, args.cls)
    os.makedirs(out_dir, exist_ok=True)

    cap = build_capture(args)
    if not cap.isOpened():
        raise SystemExit('无法打开摄像头')

    auto = args.auto
    last_save = 0.0
    saved = []
    print(f'输出目录: {os.path.abspath(out_dir)}')
    print('空格=拍照  a=自动连拍开关  u=撤销  q=退出')

    while True:
        ok, frame = cap.read()
        if not ok:
            print('读取失败')
            break

        now = time.time()
        do_save = False
        if auto and now - last_save >= args.interval:
            do_save = True

        preview = frame.copy()
        hud = f'{args.cls} | saved {len(saved)} | auto {"ON" if auto else "OFF"}'
        cv2.rectangle(preview, (0, 0), (preview.shape[1], 30), (0, 0, 0), -1)
        cv2.putText(preview, hud, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0), 2)
        cv2.imshow('capture', preview)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        if key == ord(' '):
            do_save = True
        if key == ord('a'):
            auto = not auto
        if key == ord('u') and saved:
            os.remove(saved.pop())
            print(f'已撤销，剩余 {len(saved)} 张')

        if do_save:
            # 文件名带类别+毫秒时间戳，多人分头采集合并时不会重名
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            path = os.path.join(out_dir, f'{args.cls}_{stamp}.jpg')
            cv2.imwrite(path, frame)
            saved.append(path)
            last_save = now
            print(f'[{len(saved)}] {path}')
            if args.limit and len(saved) >= args.limit:
                print('已达到目标张数')
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f'本次共采集 {len(saved)} 张，保存在 {os.path.abspath(out_dir)}')


if __name__ == '__main__':
    main()
