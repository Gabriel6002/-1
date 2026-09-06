# 桌面物体目标检测实验

本项目用于“实验一：目标检测与识别”。实验对象为桌面常见物体，数据由自采图像、网络补充样本和背景负样本组成，采用自动预标注与人工复核结合的方式制作 YOLO 标签，随后使用 YOLOv8 训练模型并部署到 Jetson 平台进行实时识别。项目同时提供 ROS2 结果发布程序。

## 实验类别

本次训练包含 3 类目标：

```text
mouse
keyboard
cup
```

## 项目流程

```text
图像采集与整理 -> 自动预标注 -> 人工复核 -> 数据集划分 -> 质量检查 -> 模型训练 -> Jetson 部署 -> ROS2 接口
```

## 目录说明

```text
.
├── scripts/                    数据处理、标签检查与 Jetson/ROS2 程序
│   ├── dataset.py            数据集划分脚本
│   ├── labels.py             标注检查脚本
│   ├── common.py             设备与精度参数工具
│   ├── jetson_detect_ros2.py Jetson 实时检测与 ROS2 发布脚本
│   ├── make_seed_labels.py   生成待人工复核的预标注
│   ├── cup_flip.py           Cup 训练集定向增强与坐标同步变换
│   ├── train_on_mac.py       Apple Silicon/MPS 训练入口
│   └── listen_detections.py  ROS2 终端订阅与可读结果输出
├── data/                       YOLO 配置与 train/val/test 标签
├── models/best.pt              最优训练权重
├── results/training/           曲线、混淆矩阵、验证预测与训练日志
├── report/                     英文 PDF、LaTeX 源文件与必要图表素材
├── docs/
│   ├── 01-采集拍摄指南.md
│   ├── 02-标注与数据集制作.md
│   └── 20_object_test_template.csv
├── requirements.txt
└── LICENSE
```

每类材料只保留一个位置，不再使用空目录或重复程序副本。完整数据集图片、结果视频及现场错误案例保存在课程提交材料中，不在 GitHub 重复上传。

## 快速使用

采集图片：使用手机拍摄桌面物体图片，然后传到电脑整理。

手动标注：

```bash
labelImg raw
```

划分数据集：

```bash
python scripts/dataset.py --input labeled --output yolo_dataset \
    --classes mouse keyboard cup --ratio 0.7 0.2 0.1
```

检查标注：

```bash
python scripts/labels.py --data data/data.yaml --show 20
```

自动预标注（输出只是候选标签，必须人工复核）：

```bash
python scripts/make_seed_labels.py raw review_labels --model yolov8x.pt
```

Cup 训练集增强：

```bash
python scripts/cup_flip.py yolo_dataset/images/train yolo_dataset/labels/train
```

训练模型：

```bash
python scripts/train_on_mac.py --data data/data.yaml
```

Jetson 运行：

```bash
cd /home/nvidia/HYJJJ
source /opt/ros/humble/setup.bash
python3 scripts/jetson_detect_ros2.py --model models/best.pt \
    --device 0 --width 1280 --height 720 --fps 15
```

查看 ROS2 结果：

```bash
ros2 topic echo /desk_object_detections
```

也可以使用仓库中的可读订阅端，它会输出类别、置信度、边界框、中心点和宽高：

```bash
python3 scripts/listen_detections.py
```

运行画面左上角会显示与最终视频一致的 `FPS`、`objs`、采集耗时、推理耗时、
过曝/欠曝像素比例 `clip` 和拉普拉斯清晰度 `sharp`。程序同时保存 MP4、逐框 CSV
以及按 `e` 键保留的典型错误帧。

## 数据放置说明

GitHub 只保存轻量标签，不保存原始图片。复现实验时，请把对应图片放到：

```text
data/images/train/
data/images/val/
data/images/test/
```

文件名必须与 `data/labels/` 中的 txt 主文件名一致。负样本可以没有 txt，或使用空 txt。
`dataset.py` 默认按连续 10 个编号组成拍摄组再划分，避免相邻帧同时进入训练集与测试集；
可通过 `--group-span` 调整分组跨度。

## 提交材料

仓库包含数据集配置与标签、模型、程序、训练结果、运行说明以及 LaTeX/PDF 实验报告。最终整合约有 650 张原始图像，其中逐项审计的核心子集为 225 张原始图像和 687 个正样本框；负样本计入图像总数，但不产生正样本框。为改善 Cup 长尾问题，另外对 45 张真实含 Cup 的训练图片进行了水平翻转和轻度亮度/对比度增强，并同步变换 YOLO 坐标。增强后的训练表示为 270 张图像、935 个框，其中 Mouse 370 个、Keyboard 449 个、Cup 116 个。增强样本只进入训练集，不进入验证集和测试集。完整原始图片、增强图片及结果视频不上传 GitHub，在课程提交材料中单独保存。
