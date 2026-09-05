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
│   └── jetson_detect_ros2.py Jetson 实时检测与 ROS2 发布脚本
├── data/                       YOLO 配置与 train/val/test 标签
├── models/best.pt              最优训练权重
├── results/training/           曲线、混淆矩阵、验证预测与训练日志
├── report/                     英文 PDF、LaTeX 源文件与文字版说明
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

训练模型：

```bash
yolo detect train data=data/data.yaml model=yolov8n.pt epochs=100 imgsz=640
```

Jetson 运行：

```bash
cd /home/nvidia/HYJJJ
source /opt/ros/humble/setup.bash
python3 scripts/jetson_detect_ros2.py --model models/best.pt --device 0
```

查看 ROS2 结果：

```bash
ros2 topic echo /desk_object_detections
```

## 提交材料

仓库包含数据集配置与标签、模型、程序、训练结果、运行说明以及 LaTeX/PDF 实验报告。最终整合数据集约有 650 张图像，其中已逐项审计的核心子集为 225 张图像和 687 个正样本目标框；负样本计入图像总数，但不产生正样本框。完整原始图片及结果视频不批量上传 GitHub，在课程提交材料中单独保存。
