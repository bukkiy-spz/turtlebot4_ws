"""TF を中継しつつ、不要な親子フレームだけを除外するノード。"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from tf2_msgs.msg import TFMessage


class TfFilterRepublisher(Node):
    """特定の transform を落として別トピックへ流す。"""

    def __init__(self) -> None:
        super().__init__("tf_filter_republisher")
        self.declare_parameter("drop_parent_frame", "odom")
        self.declare_parameter("drop_child_frame", "base_link")

        self.drop_parent_frame = str(self.get_parameter("drop_parent_frame").value)
        self.drop_child_frame = str(self.get_parameter("drop_child_frame").value)
        self.warned_drop = False

        sub_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        pub_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.subscription = self.create_subscription(
            TFMessage, "tf_in", self.tf_callback, sub_qos
        )
        self.publisher = self.create_publisher(TFMessage, "tf_out", pub_qos)

        self.get_logger().info(
            "Republishing TF while dropping "
            f"{self.drop_parent_frame} -> {self.drop_child_frame}"
        )

    def tf_callback(self, msg: TFMessage) -> None:
        filtered = []
        for transform in msg.transforms:
            if (
                transform.header.frame_id == self.drop_parent_frame
                and transform.child_frame_id == self.drop_child_frame
            ):
                if not self.warned_drop:
                    self.get_logger().warn(
                        "Dropping source TF for "
                        f"{self.drop_parent_frame} -> {self.drop_child_frame}"
                    )
                    self.warned_drop = True
                continue
            filtered.append(transform)

        if not filtered:
            return

        relay = TFMessage()
        relay.transforms = filtered
        self.publisher.publish(relay)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TfFilterRepublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
