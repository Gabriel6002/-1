# 桌面物体检测 · 数据集制作工具集

一套把「拍照 → 自动标注 → 人工复核 → 划分数据集」全流程串起来的脚本，
面向 **YOLOv8 目标检测**。用 COCO 预训练模型做自动预标注，人工只需修正少量错误，
比纯手工画框快 5~10 倍。

> 本工具集源自一个实机项目：3 类桌面物体（鼠标 / 键盘 / 杯子），
> 手机采集 → 本工具标注 → RTX 4090 训练，测试集 **mAP50 = 0.94**，
> 最终部署到 Jetson Orin NX 上实时检测。

## 特性

- **自动预标注**：`auto_label.py` 用 YOLOv8x 检测桌面物体，直接输出 YOLO 格式标注
- **一键采集**：`capture_images.py` 摄像头连拍采集
- **标注质检**：`check_labels.py` 查坐标越界、类别错误、样本不均衡
- **数据集划分**：`split_dataset.py` 按比例分 train/val/test 并生成 `data.yaml`
- **设备自适应**：脚本自动选择 CUDA / Apple MPS / CPU，同一份代码跨平台

## 环境要求

- Python 3.9+
- 见 `requirements.txt`

```bash
git clone <你的仓库地址>
cd desk-object-labeling
pip install -r requirements.txt
```

> 首次运行 `auto_label.py` 会自动下载预训练权重 `yolov8x.pt`（约 130MB）到当前目录，
> 需要联网。国内网络慢可提前手动下载放到项目根目录（见文末）。

## 快速开始（4 步）

假设你的照片已按下面结构放好（也可以全部混在一个目录，自动标注不要求预先分类）：

```
raw/
├── mouse/
├── keyboard/
└── cup/
```

```bash
# 1. （可选）用摄像头采集照片
python tools/capture_images.py --class mouse --limit 100 --out raw

# 2. 自动预标注：机器画框，生成 YOLO 标注
python tools/auto_label.py --images raw --out labeled \
    --classes mouse keyboard cup --model yolov8x.pt --conf 0.25

# 3. 人工复核（用 labelImg 修正少量错误，见 docs/02）
pip install labelImg
labelImg labeled/images

# 4. 划分数据集 + 质检
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
│   ├── 01-采集拍摄指南.md    拍多少张、什么角度、怎么拍
│   └── 02-标注与数据集制作.md 自动标注 + labelImg 复核详解
├── requirements.txt
└── README.md
```

## 换成你自己的类别

把命令里的 `--classes mouse keyboard cup` 换成你的类别即可。
**注意**：类别必须是 COCO 80 类里已有的，自动标注才有效
（如 `bottle` `cell phone` `book` `scissors` `laptop` `banana` 等）。
支持的别名映射见 `tools/auto_label.py` 顶部的 `COCO_ALIASES`。
COCO 里没有的类别，`auto_label.py` 会跳过，需要全程手动标注。

`--classes` 的顺序决定类别编号（第一个是 0），**一经确定不要更改**。

## 常见问题

- **`auto_label.py` 下载权重失败**：手动下载
  [yolov8x.pt](https://github.com/ultralytics/assets/releases) 放到项目根目录。
- **自动标注漏检 / 框歪**：这是预标注的正常现象，用 labelImg 修正即可（第 3 步）。
  详见 `docs/02`。
- **Mac 报 SSL 证书错**：`export SSL_CERT_FILE=/etc/ssl/cert.pem` 后重试。

## License

MIT
