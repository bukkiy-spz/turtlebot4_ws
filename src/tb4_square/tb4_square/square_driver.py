import math
import time

import rclpy
from geometry_msgs.msg import Twist
from geometry_msgs.msg import TwistStamped
from rclpy.topic_endpoint_info import TopicEndpointInfo
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy


class SquareDriver(Node):
    def __init__(self) -> None:
        super().__init__("square_driver")
        self.declare_parameter("cmd_vel_topic", "cmd_vel")
        self.declare_parameter("use_stamped", False)
        self.declare_parameter("side_length", 0.4)
        self.declare_parameter("linear_speed", 0.10)
        self.declare_parameter("angular_speed", 0.6)
        self.declare_parameter("pause_time", 0.5)
        self.declare_parameter("wait_for_subscriber_sec", 3.0)
        self.declare_parameter("require_subscriber", True)
        self.declare_parameter("reliability", "reliable")

        self.cmd_vel_topic = str(self.get_parameter("cmd_vel_topic").value)
        self.use_stamped = bool(self.get_parameter("use_stamped").value)
        self.side_length = float(self.get_parameter("side_length").value)
        self.linear_speed = float(self.get_parameter("linear_speed").value)
        self.angular_speed = float(self.get_parameter("angular_speed").value)
        self.pause_time = float(self.get_parameter("pause_time").value)
        self.wait_for_subscriber_sec = float(self.get_parameter("wait_for_subscriber_sec").value)
        self.require_subscriber = bool(self.get_parameter("require_subscriber").value)
        self.reliability = str(self.get_parameter("reliability").value).lower()

        self._validate_parameters()
        msg_type = TwistStamped if self.use_stamped else Twist
        qos_profile = self._make_qos_profile()
        self.publisher = self.create_publisher(msg_type, self.cmd_vel_topic, qos_profile)
        self.forward_time = self.side_length / self.linear_speed
        self.turn_time = (math.pi / 2.0) / self.angular_speed

    def _make_qos_profile(self) -> QoSProfile:
        if self.reliability == "best_effort":
            reliability = ReliabilityPolicy.BEST_EFFORT
        elif self.reliability == "reliable":
            reliability = ReliabilityPolicy.RELIABLE
        else:
            raise ValueError("reliability must be 'best_effort' or 'reliable'")

        return QoSProfile(depth=10, reliability=reliability)

    def _validate_parameters(self) -> None:
        if self.side_length <= 0.0:
            raise ValueError("side_length must be > 0.0")
        if self.linear_speed <= 0.0:
            raise ValueError("linear_speed must be > 0.0")
        if self.angular_speed <= 0.0:
            raise ValueError("angular_speed must be > 0.0")
        if self.pause_time < 0.0:
            raise ValueError("pause_time must be >= 0.0")
        if self.wait_for_subscriber_sec < 0.0:
            raise ValueError("wait_for_subscriber_sec must be >= 0.0")

    def _make_command(self, linear_x: float, angular_z: float):
        if self.use_stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.twist.linear.x = linear_x
            msg.twist.angular.z = angular_z
            return msg

        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        return msg

    def get_graph_subscribers(self) -> list[TopicEndpointInfo]:
        return list(self.get_subscriptions_info_by_topic(self.cmd_vel_topic))

    @staticmethod
    def format_endpoint_name(endpoint: TopicEndpointInfo) -> str:
        node_name = endpoint.node_name or "_NODE_NAME_UNKNOWN_"
        node_namespace = endpoint.node_namespace or "_NODE_NAMESPACE_UNKNOWN_"
        return f"{node_namespace}/{node_name}".replace("//", "/")

    def wait_for_subscriber(self) -> bool:
        if self.wait_for_subscriber_sec == 0.0:
            return True

        deadline = time.monotonic() + self.wait_for_subscriber_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            matched_subscribers = self.publisher.get_subscription_count()
            graph_subscribers = self.get_graph_subscribers()
            if matched_subscribers > 0:
                self.get_logger().info(
                    f"Detected {matched_subscribers} matched subscriber(s) on "
                    f"'{self.cmd_vel_topic}'"
                )
                return True
            if graph_subscribers:
                subscriber_names = ", ".join(
                    sorted(self.format_endpoint_name(endpoint) for endpoint in graph_subscribers)
                )
                self.get_logger().info(
                    f"Detected subscriber(s) on '{self.cmd_vel_topic}' via graph introspection: "
                    f"{subscriber_names}. Proceeding even though DDS matched count is 0."
                )
                return True

        self.get_logger().warn(
            f"No subscribers detected on '{self.cmd_vel_topic}' after "
            f"{self.wait_for_subscriber_sec:.1f} seconds"
        )
        return False

    def publish_for_duration(self, linear_x: float, angular_z: float, duration: float) -> None:
        end_time = time.monotonic() + duration
        while rclpy.ok() and time.monotonic() < end_time:
            msg = self._make_command(linear_x, angular_z)
            self.publisher.publish(msg)
            time.sleep(0.1)

        self.stop_robot()

    def stop_robot(self) -> None:
        self.publisher.publish(self._make_command(0.0, 0.0))
        time.sleep(self.pause_time)

    def run(self) -> None:
        self.get_logger().info(
            f"Starting square motion on '{self.cmd_vel_topic}': "
            f"use_stamped={self.use_stamped}, "
            f"side_length={self.side_length:.2f} m, "
            f"linear_speed={self.linear_speed:.2f} m/s, "
            f"angular_speed={self.angular_speed:.2f} rad/s, "
            f"reliability={self.reliability}"
        )
        if not self.wait_for_subscriber() and self.require_subscriber:
            raise RuntimeError(
                f"Aborting: no subscriber detected on '{self.cmd_vel_topic}'. "
                "Check ROS_DOMAIN_ID, ROS_DISCOVERY_SERVER, ros2 topic info -v, "
                "and the robot bringup."
            )

        for corner in range(4):
            self.get_logger().info(f"Side {corner + 1}/4: moving forward")
            self.publish_for_duration(self.linear_speed, 0.0, self.forward_time)
            self.get_logger().info(f"Corner {corner + 1}/4: turning left 90 degrees")
            self.publish_for_duration(0.0, self.angular_speed, self.turn_time)

        self.stop_robot()
        self.get_logger().info("Finished square motion")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SquareDriver()
    try:
        node.run()
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()
