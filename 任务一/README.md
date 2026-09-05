# 实验一：目标检测与识别

本目录为实验一提交材料整理版，重点保存可复现代码、数据配置、轻量标签、训练模型、训练结果、运行说明和 LaTeX 实验报告。完整原始图像和结果视频因体积较大保存在本地，不重复上传到 GitHub。

## 目录结构

```text
任务一/
├── dataset/              YOLO 格式数据集配置与标注，图片因体积较大未上传
├── model/best.pt         本次训练得到的最优模型
├── program/              标注检查、数据集划分、Jetson 实时检测代码
├── training_results/     训练曲线、混淆矩阵、验证预测图和结果日志
├── report/               最终 PDF、LaTeX 源文件和完整 Overleaf 工程包
├── README.md             本说明
└── 实验报告.md
```

## Jetson 运行命令

模型和运行脚本已部署到 Jetson：

```bash
cd /home/nvidia/HYJJJ
source /opt/ros/humble/setup.bash
python3 jetson_detect_ros2.py --model best.pt --device 0
```

如果摄像头 0 不显示，改用：

```bash
python3 jetson_detect_ros2.py --model best.pt --device 1
```

查看 ROS2 发布结果：

```bash
ros2 topic echo /desk_object_detections
```

## 程序功能

- 实时读取 Jetson 摄像头画面
- 使用 YOLOv8 模型检测桌面物体
- 实时显示目标类别、检测框、置信度和 FPS
- 通过 ROS2 发布 JSON 格式检测结果
- 自动保存检测视频 `result.mp4`
- 自动保存检测日志 `detections.csv`
- 运行时按 `e` 保存典型错误案例截图
- 运行时按 `q` 退出程序

## 当前实测

- 检测类别：`mouse`、`keyboard`、`cup`
- Jetson 设备：Orin
- ROS2：已完成 `rclpy` 发布程序；实际话题回显需在 Jetson 的 Humble 环境验证
- Jetson 摄像头：`/dev/video0`、`/dev/video1`
- 最终结果视频：1280×720、300 帧、20 秒，画面稳定显示 15 FPS

## 数据集图片说明

自采图片使用手机拍摄后传到电脑整理。最终整合数据集约有 650 张图像，包括自采正样本、网络补充样本和空桌面、线缆、显示器边框等负样本。其中已逐项审计的核心子集为 225 张图像、687 个正样本目标框。负样本计入图像总数，但不计入目标框数量。

本地完整图像保存在 `yolo_dataset/images/`。GitHub 仓库只保留 `data.yaml` 和 `labels/` 等轻量、可审查内容；原始图像和网络样本不批量上传，以避免仓库过大及重复分发第三方图片。如需复现实验，将图像按 `data.yaml` 的 train/val/test 结构放回 `dataset/images/` 即可。

## GitHub 提交范围

仓库用于展示开发过程和保证程序可复现，提交代码、配置、标签、模型、训练结果和实验报告。完整数据集及结果视频作为课程平台提交材料单独保存，不批量放入 GitHub。20 个物体的现场验收结果应在实际测试后填写到 `docs/20_object_test_template.csv`，未填写前不在报告中声称已经达到对应正确率。
