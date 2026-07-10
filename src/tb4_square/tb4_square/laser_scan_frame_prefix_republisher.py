"""LaserScan の frame_id に接頭辞を付けて別トピックへ中継する。"""

import copy

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from sensor_msgs.msg import LaserScan


class LaserScanFramePrefixRepublisher(Node):
    """表示専用に LaserScan の frame_id を robot ごとに分離する。"""

    def __init__(self) -> None:
        super().__init__("laser_scan_frame_prefix_republisher")
        self.declare_parameter("input_topic", "/robot2/scan")
        self.declare_parameter("output_topic", "/viz/robot2/scan")
        self.declare_parameter("frame_prefix", "robot2")

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        self.frame_prefix = str(self.get_parameter("frame_prefix").value).strip("/")

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=20,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.subscription = self.create_subscription(
            LaserScan, input_topic, self.scan_callback, qos
        )
        self.publisher = self.create_publisher(LaserScan, output_topic, qos)

        self.get_logger().info(
            f"Republishing LaserScan from '{input_topic}' to '{output_topic}' "
            f"with frame prefix '{self.frame_prefix}/'"
        )

    def scan_callback(self, msg: LaserScan) -> None:
        relay = copy.copy(msg)
        frame_id = msg.header.frame_id.lstrip("/")
        prefix = f"{self.frame_prefix}/"
        if frame_id and not frame_id.startswith(prefix):
            relay.header.frame_id = prefix + frame_id
        else:
            relay.header.frame_id = frame_id
        self.publisher.publish(relay)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LaserScanFramePrefixRepublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
