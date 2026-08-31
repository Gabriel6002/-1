# 桌面物体目标检测实验

本项目用于“实验一：目标检测与识别”。实验对象为桌面常见物体，数据由本人采集并手动标注，随后使用 YOLOv8 训练目标检测模型，并部署到 Jetson 平台进行实时识别和 ROS2 结果发布。

## 实验类别

本次训练包含 3 类目标：

```text
mouse
keyboard
cup
```

## 项目流程

```text
图像采集 -> 手动标注 -> 数据集划分 -> 标注检查 -> 模型训练 -> Jetson 部署 -> ROS2 发布
```

## 目录说明

```text
.
├── 任务一/                 实验一提交材料
├── tools/
│   ├── capture_images.py   摄像头采集脚本
│   ├── split_dataset.py    数据集划分脚本
│   ├── check_labels.py     标注检查脚本
│   ├── common.py           公共工具函数
│   └── jetson_detect_ros2.py Jetson 实时检测与 ROS2 发布脚本
├── docs/
│   ├── 01-采集拍摄指南.md
│   └── 02-标注与数据集制作.md
├── requirements.txt
└── LICENSE
```

## 快速使用

采集图片：

```bash
python tools/capture_images.py --class mouse --limit 100 --out raw
```

手动标注：

```bash
labelImg raw
```

划分数据集：

```bash
python tools/split_dataset.py --input labeled --output yolo_dataset \
    --classes mouse keyboard cup --ratio 0.7 0.2 0.1
```

检查标注：

```bash
python tools/check_labels.py --data yolo_dataset/data.yaml --show 20
```

训练模型：

```bash
yolo detect train data=yolo_dataset/data.yaml model=yolov8n.pt epochs=100 imgsz=640
```

Jetson 运行：

```bash
cd /home/nvidia/HYJJJ
source /opt/ros/humble/setup.bash
python3 jetson_detect_ros2.py --model best.pt --device 0
```

查看 ROS2 结果：

```bash
ros2 topic echo /desk_object_detections
```

## 提交材料

实验一材料整理在 `任务一/` 目录中，包含数据集标注、模型、程序、训练结果、运行说明和实验报告。
