# 桌面物体检测 · 数据集制作工具集

一套把「**拍照 → 自动标注 → 人工复核 → 划分数据集**」全流程串起来的脚本，
面向 **YOLOv8 目标检测**。用 COCO 预训练模型做自动预标注，人工只需修正少量错误，
比纯手工画框快 **5~10 倍**。

> 本工具集源自一个真实项目：3 类桌面物体（鼠标 / 键盘 / 杯子），
> 手机采集 589 张 → 本工具标注 → RTX 4090 训练，
> 测试集 **mAP50 = 0.94**，最终部署到 Jetson Orin NX 上实时检测。

## 整体流程

```
拍照采集          自动预标注           人工复核            划分 + 质检          训练
  │                 │                   │                   │                 │
capture_images → auto_label →      labelImg 修正 →    split_dataset →      YOLOv8
  .py            .py (机器画框)      (删错框/补漏检)    check_labels.py     训练
```

## 功能

- **自动预标注** — `auto_label.py` 用 YOLOv8x 检测桌面物体，直接输出 YOLO 格式标注 txt
- **摄像头采集** — `capture_images.py` 连拍采集，支持撤销、自动连拍
- **标注质检** — `check_labels.py` 查坐标越界、类别错误、空标注、样本不均衡
- **数据集划分** — `split_dataset.py` 按比例分 train/val/test 并自动生成 `data.yaml`
- **设备自适应** — 脚本自动选择 CUDA / Apple 芯片 MPS / CPU，同一份代码跨平台可跑

## 环境要求

- Python 3.9 及以上

```bash
git clone https://github.com/hanlinji4002/desk-object-labeling.git
cd desk-object-labeling
pip install -r requirements.txt
```

> 首次运行 `auto_label.py` 会自动下载预训练权重 `yolov8x.pt`（约 130MB）到当前目录，
> 需要联网。国内网络慢的话可提前手动下载放到项目根目录（见下方「常见问题」）。

## 快速开始（四步）

假设照片已按类别放好（也可以全部混在一个目录，自动标注不要求预先分类）：

```
raw/
├── mouse/
├── keyboard/
└── cup/
```

**第 1 步 · 采集照片**（可选，也可以用手机拍好直接放进 `raw/`）

```bash
python tools/capture_images.py --class mouse --limit 100 --out raw
```

**第 2 步 · 自动预标注**（机器画框，秒级完成）

```bash
python tools/auto_label.py --images raw --out labeled \
    --classes mouse keyboard cup --model yolov8x.pt --conf 0.25
```

**第 3 步 · 人工复核**（用 labelImg 修正少量漏检/框歪，决定数据质量）

```bash
pip install labelImg
labelImg labeled/images
```

复核方法详见 [docs/02-标注与数据集制作](docs/02-标注与数据集制作.md)。

**第 4 步 · 划分数据集 + 质检**

```bash
python tools/split_dataset.py --input labeled/images --output dataset \
    --classes mouse keyboard cup --ratio 0.7 0.2 0.1
python tools/check_labels.py --data dataset/data.yaml --show 20
```

得到的 `dataset/`（含 `data.yaml`）即可直接用于 YOLOv8 训练：

```bash
yolo detect train data=dataset/data.yaml model=yolov8n.pt epochs=100 imgsz=640
```

## 目录结构

```
.
├── tools/
│   ├── auto_label.py       自动预标注（核心）
│   ├── capture_images.py   摄像头采集
│   ├── common.py           公共函数（设备自适应等，勿删）
│   ├── split_dataset.py    划分 train/val/test + 生成 data.yaml
│   └── check_labels.py     标注质检
├── docs/
│   ├── 01-采集拍摄指南.md      拍多少张、什么角度、怎么拍
│   └── 02-标注与数据集制作.md   自动标注 + labelImg 复核详解
├── requirements.txt
├── LICENSE
└── README.md
```

## 换成你自己的类别

把命令里的 `--classes mouse keyboard cup` 换成你的类别即可。

**注意**：类别必须是 COCO 80 类里已有的，自动标注才有效
（例如 `bottle` `cell phone` `book` `scissors` `laptop` `banana` `apple` 等）。
支持的别名映射见 `tools/auto_label.py` 顶部的 `COCO_ALIASES`。
COCO 里没有的类别，`auto_label.py` 会自动跳过，需要全程手动标注。

> ⚠️ `--classes` 的顺序决定类别编号（第一个是 0），**一经确定就不要再改**，
> 否则已标注的数据类别会全部错乱。

## 常见问题

- **`auto_label.py` 下载权重失败** — 手动下载
  [yolov8x.pt](https://github.com/ultralytics/assets/releases) 放到项目根目录再运行。
- **自动标注有漏检 / 框歪** — 这是预标注的正常现象，用 labelImg 修正即可（第 3 步）。
  自动标注负责画好大部分框，人工只做少量修正，详见 [docs/02](docs/02-标注与数据集制作.md)。
- **macOS 报 SSL 证书错误** — 执行 `export SSL_CERT_FILE=/etc/ssl/cert.pem` 后重试。

## 开源协议

本项目采用 [MIT 协议](LICENSE)，可自由使用、修改、分发。
