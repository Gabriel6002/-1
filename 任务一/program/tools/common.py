#!/usr/bin/env python3
"""各脚本共用的小工具。"""

import os


def pick_device(requested='auto'):
    """把 --device 参数解析成 ultralytics 认识的设备字符串。

    'auto' 时按 CUDA > MPS > CPU 的顺序挑，这样同一份代码在
    Mac(M系列)、有 N 卡的台式机、Jetson 上都不用改参数。
    """
    if requested and requested != 'auto':
        return requested

    try:
        import torch
    except ImportError:
        return 'cpu'

    if torch.cuda.is_available():
        return '0'
    if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available():
        # 部分算子还没有 MPS 实现，允许回落到 CPU，否则训练会中途报错
        os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
        return 'mps'
    return 'cpu'


def describe_device(device):
    try:
        import torch
    except ImportError:
        return device
    if device == 'mps':
        return 'mps (Apple 芯片 GPU)'
    if device == 'cpu':
        return 'cpu（会很慢，确认这不是你想要的）'
    try:
        return f'cuda:{device} ({torch.cuda.get_device_name(int(device))})'
    except (ValueError, RuntimeError, AssertionError):
        return device


def precision_kwargs(half=True, int8=False):
    """兼容新旧 ultralytics 的精度参数。

    8.4 起 half / int8 被统一的 quantize 取代，旧写法会刷一屏废弃警告；
    而 Jetson 上装到的版本不一定同步，所以按运行时的实际 API 选。
    """
    try:
        from ultralytics.cfg import DEFAULT_CFG_DICT
        new_api = 'quantize' in DEFAULT_CFG_DICT
    except ImportError:
        new_api = False

    if new_api:
        if int8:
            return {'quantize': 8}
        return {'quantize': 16} if half else {}

    out = {}
    if half:
        out['half'] = True
    if int8:
        out['int8'] = True
    return out
