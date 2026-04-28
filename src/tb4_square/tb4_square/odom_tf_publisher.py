"""Odometry から補助的な odom -> base_link TF を作るノード。"""

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from tf2_ros import TransformBroadcaster


class OdomTfPublisher(Node):
    """RViz がフレーム木を解決できるよう、オドメトリ姿勢を TF に写す。"""

    def __init__(self) -> None:
        super().__init__("odom_tf_publisher")
        # parent_frame / child_frame を変えると生成する TF の親子関係が変わる。
        # publish_rate を上げると更新は細かくなるが、TF 配信頻度も上がる。
        # stale_after_sec は「入力が止まった」と見なして警告するまでの時間。
        self.declare_parameter("odom_topic", "/robot2/odom")
        self.declare_parameter("parent_frame", "odom")
        self.declare_parameter("child_frame", "base_link")
        self.declare_parameter("publish_rate", 20.0)
        self.declare_parameter("stale_after_sec", 1.0)

        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.parent_frame = str(self.get_parameter("parent_frame").value)
        self.child_frame = str(self.get_parameter("child_frame").value)
        publish_rate = float(self.get_parameter("publish_rate").value)
        self.stale_after_sec = float(self.get_parameter("stale_after_sec").value)
        if publish_rate <= 0.0:
            raise ValueError("publish_rate must be > 0")
        if self.stale_after_sec < 0.0:
            raise ValueError("stale_after_sec must be >= 0")

        self.latest_pose = None
        self.latest_odom_time = None
        self.warned_missing = False
        self.warned_stale = False

        self.broadcaster = TransformBroadcaster(self)
        qos_profile = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.subscription = self.create_subscription(
            Odometry, self.odom_topic, self.odom_callback, qos_profile
        )
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_transform)

        self.get_logger().info(
            f"Publishing fallback odom TF from '{self.odom_topic}' as "
            f"{self.parent_frame} -> {self.child_frame}"
        )

    def odom_callback(self, msg: Odometry) -> None:
        # TF では最新姿勢が重要なので、ここでは直近 1 件だけを保持する。
        self.latest_pose = msg.pose.pose
        self.latest_odom_time = self.get_clock().now()
        self.warned_missing = False
        self.warned_stale = False

    def publish_transform(self) -> None:
        # TF の時刻にはノードの clock を使う。
        # use_sim_time=true なら /clock と同期し、RViz でも同じ時間軸で見える。
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self.parent_frame
        transform.child_frame_id = self.child_frame

        pose = self.latest_pose
        if pose is None:
            if not self.warned_missing:
                self.get_logger().warn(
                    "No odometry received yet; publishing identity odom TF for RViz stability."
                )
                self.warned_missing = True
            # オドメトリ未到着のあいだは単位変換を出して、TF 木の全崩れを防ぐ。
            # ここをやめると、起動直後の RViz で fixed frame 解決に失敗しやすくなる。
            transform.transform.rotation.w = 1.0
            self.broadcaster.sendTransform(transform)
            return

        if self.latest_odom_time is not None and self.stale_after_sec > 0.0:
            age = (self.get_clock().now() - self.latest_odom_time).nanoseconds / 1e9
            if age > self.stale_after_sec and not self.warned_stale:
                self.get_logger().warn(
                    "Odometry looks stale; continuing to publish the last known odom pose."
                )
                self.warned_stale = True

        # 受け取った pose をそのまま TF の平行移動・回転へ写す。
        # もし補正を入れたいなら、この代入部分にオフセット計算を足す。
        transform.transform.translation.x = pose.position.x
        transform.transform.translation.y = pose.position.y
        transform.transform.translation.z = pose.position.z
        transform.transform.rotation = pose.orientation
        self.broadcaster.sendTransform(transform)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = OdomTfPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
