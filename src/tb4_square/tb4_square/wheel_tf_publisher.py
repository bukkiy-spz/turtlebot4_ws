"""JointState から車輪まわりの TF を再構成して配信するノード。"""

import math
from typing import Dict

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster


def quaternion_from_rpy(roll: float, pitch: float, yaw: float):
    """roll, pitch, yaw を quaternion に変換する補助関数。"""

    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)

    return {
        "x": sr * cp * cy - cr * sp * sy,
        "y": cr * sp * cy + sr * cp * sy,
        "z": cr * cp * sy - sr * sp * cy,
        "w": cr * cp * cy + sr * sp * sy,
    }


class WheelTfPublisher(Node):
    """最新 JointState をもとに左右車輪の TF 木を作り直す。"""

    def __init__(self) -> None:
        super().__init__("wheel_tf_publisher")
        # joint_states_topic を変えると参照する関節角の入力先が変わる。
        # base_frame を変えると、生成される車輪 TF の親フレームが変わる。
        # publish_rate を上げると見た目は細かくなるが、TF 配信量は増える。
        self.declare_parameter("joint_states_topic", "/robot2/joint_states")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("publish_rate", 20.0)
        self.declare_parameter("warn_if_joint_states_missing_sec", 5.0)

        self.joint_states_topic = str(self.get_parameter("joint_states_topic").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        publish_rate = float(self.get_parameter("publish_rate").value)
        self.warn_if_joint_states_missing_sec = float(
            self.get_parameter("warn_if_joint_states_missing_sec").value
        )
        if publish_rate <= 0:
            raise ValueError("publish_rate must be > 0")
        if self.warn_if_joint_states_missing_sec < 0:
            raise ValueError("warn_if_joint_states_missing_sec must be >= 0")

        self.joint_positions: Dict[str, float] = {}
        self.latest_joint_state_time = None
        self._missing_joint_state_warned = False
        self.broadcaster = TransformBroadcaster(self)
        qos_profile = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.subscription = self.create_subscription(
            JointState,
            self.joint_states_topic,
            self.joint_state_callback,
            qos_profile,
        )
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_transforms)

        self.get_logger().info(
            f"Publishing TurtleBot4 wheel TFs from '{self.joint_states_topic}'"
        )

    def joint_state_callback(self, msg: JointState) -> None:
        # 関節名ごとの現在角度を辞書へ入れておく。
        # どの joint 名を使うかは、下の make_*_transform 呼び出し側で決まる。
        self.latest_joint_state_time = self.get_clock().now()
        self._missing_joint_state_warned = False
        for name, position in zip(msg.name, msg.position):
            self.joint_positions[name] = position

    def publish_transforms(self) -> None:
        stamp = self.get_clock().now().to_msg()
        self.maybe_warn_about_missing_joint_states()
        # 左右の wheel_drop と wheel を base_link 配下の小さな TF 木として publish する。
        # ここにフレームを足せば、追加関節の可視化も同じ流れで拡張できる。
        transforms = [
            self.make_wheel_drop_transform(
                stamp,
                child_frame="wheel_drop_left",
                y=0.1165,
                drop_joint="wheel_drop_left_joint",
            ),
            self.make_wheel_transform(
                stamp,
                parent_frame="wheel_drop_left",
                child_frame="left_wheel",
                wheel_joint="left_wheel_joint",
            ),
            self.make_wheel_drop_transform(
                stamp,
                child_frame="wheel_drop_right",
                y=-0.1165,
                drop_joint="wheel_drop_right_joint",
            ),
            self.make_wheel_transform(
                stamp,
                parent_frame="wheel_drop_right",
                child_frame="right_wheel",
                wheel_joint="right_wheel_joint",
            ),
        ]
        self.broadcaster.sendTransform(transforms)

    def maybe_warn_about_missing_joint_states(self) -> None:
        # 起動直後や入力停止時の警告を 1 回だけ出す。
        # warn_if_joint_states_missing_sec を短くすると、異常検知は早くなる。
        if self.warn_if_joint_states_missing_sec == 0:
            return

        if self.latest_joint_state_time is None:
            if not self._missing_joint_state_warned:
                self.get_logger().warn(
                    "No JointState received yet; publishing fallback wheel TFs with zero angles."
                )
                self._missing_joint_state_warned = True
            return

        age = self.get_clock().now() - self.latest_joint_state_time
        if age > Duration(seconds=self.warn_if_joint_states_missing_sec):
            if not self._missing_joint_state_warned:
                self.get_logger().warn(
                    "JointState updates look stale; continuing to publish wheel TFs "
                    "from the last known positions."
                )
                self._missing_joint_state_warned = True

    def make_wheel_drop_transform(
        self, stamp, child_frame: str, y: float, drop_joint: str
    ) -> TransformStamped:
        # wheel_drop_* は、車輪本体より手前の「上下位置を持つ中間フレーム」。
        # y や z の計算を変えると、RViz 上で見える車輪位置が変わる。
        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = self.base_frame
        transform.child_frame_id = child_frame
        transform.transform.translation.x = 0.0
        transform.transform.translation.y = y
        transform.transform.translation.z = 0.0402 - self.joint_positions.get(
            drop_joint, 0.0
        )
        rotation = quaternion_from_rpy(-math.pi / 2.0, 0.0, 0.0)
        transform.transform.rotation.x = rotation["x"]
        transform.transform.rotation.y = rotation["y"]
        transform.transform.rotation.z = rotation["z"]
        transform.transform.rotation.w = rotation["w"]
        return transform

    def make_wheel_transform(
        self, stamp, parent_frame: str, child_frame: str, wheel_joint: str
    ) -> TransformStamped:
        # left_wheel / right_wheel は簡略モデルとして yaw 回転だけを反映している。
        # もし実機モデルに合わせて回転軸を変えたいなら、この quaternion 計算が編集点。
        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = parent_frame
        transform.child_frame_id = child_frame
        transform.transform.translation.x = 0.0
        transform.transform.translation.y = 0.0
        transform.transform.translation.z = 0.0
        rotation = quaternion_from_rpy(0.0, 0.0, self.joint_positions.get(wheel_joint, 0.0))
        transform.transform.rotation.x = rotation["x"]
        transform.transform.rotation.y = rotation["y"]
        transform.transform.rotation.z = rotation["z"]
        transform.transform.rotation.w = rotation["w"]
        return transform


def main(args=None) -> None:
    rclpy.init(args=args)
    node = WheelTfPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
