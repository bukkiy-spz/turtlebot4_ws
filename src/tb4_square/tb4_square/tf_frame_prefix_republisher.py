"""TFMessage の frame 名に接頭辞を付けて別トピックへ中継する。"""

from typing import Iterable

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from tf2_msgs.msg import TFMessage


class TfFramePrefixRepublisher(Node):
    """複数ロボット表示用に TF frame 名を衝突しない形へ変換する。"""

    def __init__(self) -> None:
        super().__init__("tf_frame_prefix_republisher")
        self.declare_parameter("input_topic", "/robot2/tf")
        self.declare_parameter("output_topic", "/viz/tf")
        self.declare_parameter("frame_prefix", "robot2")
        self.declare_parameter("preserve_frames", ["map"])
        self.declare_parameter("reliable", False)
        self.declare_parameter("transient_local", False)

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        raw_prefix = str(self.get_parameter("frame_prefix").value).strip("/")
        self.frame_prefix = raw_prefix
        self.preserve_frames = set(self._iter_preserve_frames())
        reliable = bool(self.get_parameter("reliable").value)
        transient_local = bool(self.get_parameter("transient_local").value)

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=(
                ReliabilityPolicy.RELIABLE
                if reliable
                else ReliabilityPolicy.BEST_EFFORT
            ),
            durability=(
                DurabilityPolicy.TRANSIENT_LOCAL
                if transient_local
                else DurabilityPolicy.VOLATILE
            ),
        )

        self.subscription = self.create_subscription(
            TFMessage, input_topic, self.tf_callback, qos
        )
        self.publisher = self.create_publisher(TFMessage, output_topic, qos)

        self.get_logger().info(
            f"Republishing TF from '{input_topic}' to '{output_topic}' "
            f"with prefix '{self.frame_prefix}/'"
        )

    def _iter_preserve_frames(self) -> Iterable[str]:
        value = self.get_parameter("preserve_frames").value
        if isinstance(value, (list, tuple)):
            for item in value:
                text = str(item).strip()
                if text:
                    yield text
            return
        text = str(value).strip()
        if text:
            yield text

    def _prefix_frame(self, frame_id: str) -> str:
        clean = frame_id.lstrip("/")
        if not clean:
            return frame_id
        if clean in self.preserve_frames:
            return clean
        prefix = f"{self.frame_prefix}/"
        if clean.startswith(prefix):
            return clean
        return prefix + clean

    def tf_callback(self, msg: TFMessage) -> None:
        relay = TFMessage()
        for transform in msg.transforms:
            copied = transform
            copied.header.frame_id = self._prefix_frame(transform.header.frame_id)
            copied.child_frame_id = self._prefix_frame(transform.child_frame_id)
            relay.transforms.append(copied)
        if relay.transforms:
            self.publisher.publish(relay)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TfFramePrefixRepublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
