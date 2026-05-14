"""Keep a selected TF transform available on another TF topic."""

from copy import deepcopy

import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from tf2_msgs.msg import TFMessage


class TfStableRepublisher(Node):
    """Cache one transform and republish it periodically."""

    def __init__(self) -> None:
        super().__init__("tf_stable_republisher")

        self.declare_parameter("input_topic", "/robot2/tf")
        self.declare_parameter("output_topic", "/tf")
        self.declare_parameter("parent_frame", "map")
        self.declare_parameter("child_frame", "odom")
        self.declare_parameter("publish_rate", 10.0)
        self.declare_parameter("refresh_stamp", True)

        self.input_topic = str(self.get_parameter("input_topic").value)
        self.output_topic = str(self.get_parameter("output_topic").value)
        self.parent_frame = str(self.get_parameter("parent_frame").value)
        self.child_frame = str(self.get_parameter("child_frame").value)
        self.refresh_stamp = bool(self.get_parameter("refresh_stamp").value)
        publish_rate = float(self.get_parameter("publish_rate").value)

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.cached_transform = None
        self.last_rx_time = None
        self.last_wait_log = self.get_clock().now()

        self.subscription = self.create_subscription(
            TFMessage, self.input_topic, self.tf_callback, qos
        )
        self.publisher = self.create_publisher(TFMessage, self.output_topic, qos)
        self.timer = self.create_timer(1.0 / max(publish_rate, 0.1), self.publish_tf)

        self.get_logger().info(
            "Republishing latest TF "
            f"{self.parent_frame} -> {self.child_frame} from "
            f"'{self.input_topic}' to '{self.output_topic}' at {publish_rate:.1f} Hz"
        )

    def tf_callback(self, msg: TFMessage) -> None:
        for transform in msg.transforms:
            if (
                transform.header.frame_id == self.parent_frame
                and transform.child_frame_id == self.child_frame
            ):
                self.cached_transform = deepcopy(transform)
                self.last_rx_time = self.get_clock().now()

    def publish_tf(self) -> None:
        if self.cached_transform is None:
            now = self.get_clock().now()
            if now - self.last_wait_log > Duration(seconds=5.0):
                self.get_logger().warn(
                    "Still waiting for TF "
                    f"{self.parent_frame} -> {self.child_frame} on '{self.input_topic}'"
                )
                self.last_wait_log = now
            return

        transform = deepcopy(self.cached_transform)
        if self.refresh_stamp:
            transform.header.stamp = self.get_clock().now().to_msg()

        msg = TFMessage()
        msg.transforms = [transform]
        self.publisher.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TfStableRepublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
