#!/usr/bin/env python3
"""Readable ROS2 console subscriber for the detector JSON topic."""

import json
import argparse

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DetectionConsole(Node):
    def __init__(self, topic):
        super().__init__('desk_detection_console')
        self.create_subscription(String, topic, self.show, 10)

    def show(self, message):
        packet = json.loads(message.data)
        for item in packet.get('detections', []):
            self.get_logger().info(
                f"object:{item['class_name']} | confidence:{item['confidence']:.2f} | "
                f"box:{item['xyxy']} | center:{item['center']} | size:{item['size']}"
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', default='/desk_object_detections')
    args = ap.parse_args()
    rclpy.init()
    node = DetectionConsole(args.topic)
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
