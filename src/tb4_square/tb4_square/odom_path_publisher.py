"""オドメトリを RViz 用の Path へ変換するノード。"""

from collections import deque

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path
from rclpy.node import Node


class OdomPathPublisher(Node):
    """Odometry を購読し、最新の軌跡を Path として保持・配信する。"""

    def __init__(self) -> None:
        super().__init__("odom_path_publisher")
        # odom_topic を変えると参照する移動情報が変わる。
        # path_topic を変えると出力先 topic が変わる。
        # max_poses を増やすと長い軌跡を残せるが、保持データ量も増える。
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
        # 受け取った 1 件のオドメトリを、Path に入れる PoseStamped 1 点へ変換する。
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose.pose
        self.poses.append(pose)

        # 新しい点が来るたびに、保持している全軌跡をまとめて再 publish する。
        # 「過去何点まで残すか」は self.poses の maxlen、つまり max_poses で決まる。
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
