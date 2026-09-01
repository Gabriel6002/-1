# 实验一：目标检测与识别

本目录为实验一提交材料整理版，包含数据集、训练模型、Jetson 运行程序、训练结果、运行说明和实验报告。

## 目录结构

```text
任务一/
├── dataset/              YOLO 格式数据集配置与标注，图片因体积较大未上传
├── model/best.pt         本次训练得到的最优模型
├── program/              标注检查、数据集划分、Jetson 实时检测代码
├── training_results/     训练曲线、混淆矩阵、验证预测图和结果日志
├── results_video/        Jetson 实测结果视频保存位置
├── error_cases/          典型错误案例保存位置
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
- ROS2：Humble
- Jetson 摄像头：`/dev/video0`、`/dev/video1`
- 实测速度：30 帧推理耗时 3.716 秒，平均约 8.07 FPS

## 数据集图片说明

本次实验图片使用手机拍摄后传到电脑整理。本地完整图片数据集位于原训练目录的 `yolo_dataset/images/`。由于图片体积较大，GitHub 仓库中只保留 `data.yaml` 和 `labels/` 标注文件；如需复现实验，将图片按 `data.yaml` 的 train/val/test 结构放回 `dataset/images/` 即可。

## 待补材料

结果视频和典型错误案例需要在 Jetson 上实际运行检测程序后保存，再放入：

```text
任务一/results_video/
任务一/error_cases/
```

20 个物体测试正确率需要现场测试后填写到 `docs/20_object_test_template.csv`。
