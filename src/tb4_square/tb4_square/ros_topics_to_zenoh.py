"""Relay selected ROS 2 topics directly to Zenoh using ROS 2 CDR serialization."""

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from rclpy.serialization import serialize_message
from sensor_msgs.msg import BatteryState
import zenoh


class RosTopicsToZenoh(Node):
    def __init__(self) -> None:
        super().__init__("ros_topics_to_zenoh")

        self.declare_parameter(
            "zenoh_config", "/home/masu_ubu/jazzy_ff_ws/config/zenoh/zenoh_client_config.json5"
        )
        self.declare_parameter("amcl_topic", "/robot2/amcl_pose")
        self.declare_parameter("amcl_key", "robot2/amcl_pose")
        self.declare_parameter("battery_topic", "/robot2/battery_state")
        self.declare_parameter("battery_key", "robot2/battery_state")

        zenoh_config = str(self.get_parameter("zenoh_config").value)
        self.amcl_key = str(self.get_parameter("amcl_key").value)
        self.battery_key = str(self.get_parameter("battery_key").value)

        self.session = zenoh.open(zenoh.Config.from_file(zenoh_config))

        amcl_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        battery_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.create_subscription(
            PoseWithCovarianceStamped,
            str(self.get_parameter("amcl_topic").value),
            self._amcl_cb,
            amcl_qos,
        )
        self.create_subscription(
            BatteryState,
            str(self.get_parameter("battery_topic").value),
            self._battery_cb,
            battery_qos,
        )

        self._amcl_count = 0
        self._battery_count = 0
        self.get_logger().info(
            f"Relaying AMCL to '{self.amcl_key}' and battery to '{self.battery_key}'"
        )

    def _amcl_cb(self, msg: PoseWithCovarianceStamped) -> None:
        self.session.put(self.amcl_key, serialize_message(msg))
        self._amcl_count += 1
        if self._amcl_count <= 5 or self._amcl_count % 50 == 0:
            pose = msg.pose.pose
            self.get_logger().info(
                f"Published AMCL sample #{self._amcl_count}: "
                f"x={pose.position.x:.3f}, y={pose.position.y:.3f}"
            )

    def _battery_cb(self, msg: BatteryState) -> None:
        self.session.put(self.battery_key, serialize_message(msg))
        self._battery_count += 1
        if self._battery_count <= 5 or self._battery_count % 20 == 0:
            self.get_logger().info(
                f"Published battery sample #{self._battery_count}: "
                f"percentage={msg.percentage:.3f}"
            )

    def destroy_node(self) -> bool:
        try:
            self.session.close()
        finally:
            return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RosTopicsToZenoh()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
