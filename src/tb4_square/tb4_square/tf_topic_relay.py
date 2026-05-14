"""任意の TF トピックを別名でそのまま中継するノード。"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from tf2_msgs.msg import TFMessage


class TfTopicRelay(Node):
    """TFMessage を入力トピックから出力トピックへそのまま流す。"""

    def __init__(self) -> None:
        super().__init__("tf_topic_relay")
        self.declare_parameter("input_topic", "/robot2/tf")
        self.declare_parameter("output_topic", "/tf")

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.subscription = self.create_subscription(
            TFMessage, input_topic, self.tf_callback, qos
        )
        self.publisher = self.create_publisher(TFMessage, output_topic, qos)

        self.get_logger().info(f"Relaying TF from '{input_topic}' to '{output_topic}'")

    def tf_callback(self, msg: TFMessage) -> None:
        self.publisher.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TfTopicRelay()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
