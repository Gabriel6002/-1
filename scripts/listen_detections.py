#!/usr/bin/env python3
"""Readable ROS2 console subscriber for the detector JSON topic."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DetectionConsole(Node):
    def __init__(self):
        super().__init__('desk_detection_console')
        self.create_subscription(String, '/desk_object_detections', self.show, 10)

    def show(self, message):
        packet = json.loads(message.data)
        for item in packet.get('detections', []):
            self.get_logger().info(
                f"object:{item['class_name']} | confidence:{item['confidence']:.2f} | "
                f"box:{item['xyxy']} | center:{item['center']} | size:{item['size']}"
            )


def main():
    rclpy.init()
    node = DetectionConsole()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
