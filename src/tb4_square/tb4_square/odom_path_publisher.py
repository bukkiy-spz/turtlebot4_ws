from collections import deque

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path
from rclpy.node import Node


class OdomPathPublisher(Node):
    def __init__(self) -> None:
        super().__init__("odom_path_publisher")
        self.declare_parameter("odom_topic", "/robot2/odom")
        self.declare_parameter("path_topic", "/robot2/path")
        self.declare_parameter("max_poses", 1000)

        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.path_topic = str(self.get_parameter("path_topic").value)
        self.max_poses = int(self.get_parameter("max_poses").value)

        if self.max_poses <= 0:
            raise ValueError("max_poses must be > 0")

        self.poses = deque(maxlen=self.max_poses)
        self.path_publisher = self.create_publisher(Path, self.path_topic, 10)
        self.odom_subscription = self.create_subscription(
            Odometry, self.odom_topic, self.odom_callback, 10
        )

        self.get_logger().info(
            f"Publishing path from '{self.odom_topic}' to '{self.path_topic}' "
            f"with max_poses={self.max_poses}"
        )

    def odom_callback(self, msg: Odometry) -> None:
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose.pose
        self.poses.append(pose)

        path = Path()
        path.header = msg.header
        path.poses = list(self.poses)
        self.path_publisher.publish(path)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = OdomPathPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
