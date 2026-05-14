"""Relay ROS TFMessage samples directly to a Zenoh key."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from rclpy.serialization import serialize_message
from tf2_msgs.msg import TFMessage
import zenoh


class RosTfToZenoh(Node):
    """Forward TFMessage samples to Zenoh using ROS 2 CDR serialization."""

    def __init__(self) -> None:
        super().__init__("ros_tf_to_zenoh")

        self.declare_parameter("input_topic", "/robot2/tf")
        self.declare_parameter("zenoh_key", "robot2/tf")
        self.declare_parameter(
            "zenoh_config", "/home/masu_ubu/jazzy_ff_ws/config/zenoh/zenoh_client_config.json5"
        )
        self.declare_parameter("only_parent_frame", "")
        self.declare_parameter("only_child_frame", "")

        self.input_topic = str(self.get_parameter("input_topic").value)
        self.zenoh_key = str(self.get_parameter("zenoh_key").value)
        zenoh_config = str(self.get_parameter("zenoh_config").value)
        self.only_parent_frame = str(self.get_parameter("only_parent_frame").value)
        self.only_child_frame = str(self.get_parameter("only_child_frame").value)

        config = zenoh.Config.from_file(zenoh_config)
        self.session = zenoh.open(config)

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.subscription = self.create_subscription(
            TFMessage, self.input_topic, self.tf_callback, qos
        )
        self.sample_count = 0

        self.get_logger().info(
            f"Relaying '{self.input_topic}' to Zenoh key '{self.zenoh_key}'"
        )

    def tf_callback(self, msg: TFMessage) -> None:
        if self.only_parent_frame or self.only_child_frame:
            msg = self.filter_message(msg)
            if not msg.transforms:
                return

        self.session.put(self.zenoh_key, serialize_message(msg))
        self.sample_count += 1
        if self.sample_count <= 5 or self.sample_count % 100 == 0:
            frames = ", ".join(
                f"{t.header.frame_id}->{t.child_frame_id}" for t in msg.transforms
            )
            self.get_logger().info(
                f"Published TF sample #{self.sample_count} to '{self.zenoh_key}': {frames}"
            )

    def filter_message(self, msg: TFMessage) -> TFMessage:
        filtered = TFMessage()
        for transform in msg.transforms:
            if self.only_parent_frame and transform.header.frame_id != self.only_parent_frame:
                continue
            if self.only_child_frame and transform.child_frame_id != self.only_child_frame:
                continue
            filtered.transforms.append(transform)
        return filtered

    def destroy_node(self) -> bool:
        try:
            self.session.close()
        finally:
            return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RosTfToZenoh()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
