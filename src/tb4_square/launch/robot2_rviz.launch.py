"""/robot2 用の RViz と可視化補助ノードを起動する launch ファイル。"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory("tb4_square")
    default_rviz_config = os.path.join(package_share, "rviz", "robot2.rviz")
    pkg_turtlebot4_description = get_package_share_directory("turtlebot4_description")
    turtlebot4_xacro = PathJoinSubstitution(
        [
            pkg_turtlebot4_description,
            "urdf",
            LaunchConfiguration("model"),
            "turtlebot4.urdf.xacro",
        ]
    )

    return LaunchDescription(
        [
            # rviz_config を差し替えると、表示するトピックや見た目の初期設定を切り替えられる。
            DeclareLaunchArgument("rviz_config", default_value=default_rviz_config),
            DeclareLaunchArgument("model", default_value="standard"),
            DeclareLaunchArgument("tf_topic", default_value="/robot2/tf"),
            DeclareLaunchArgument("tf_static_topic", default_value="/robot2/tf_static"),
            # simulation を見るときは true のまま使う。
            # false にすると /clock ではなく PC の時計で動くため、TF や LaserScan が
            # 古いデータ扱いになることがある。
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            # 実機側で odom -> base_link が既に配信されているなら false のままにする。
            # true にすると、/robot2/odom 不在時の補助 TF をローカル生成する。
            DeclareLaunchArgument("enable_odom_tf_helper", default_value="false"),
            # 実機側 robot_state_publisher が wheel TF を出している場合は
            # false のままにして、二重配信による TF_OLD_DATA を防ぐ。
            # wheel TF が欠ける環境だけ true で補助ノードを有効化する。
            DeclareLaunchArgument("enable_wheel_tf_helper", default_value="false"),
            # RViz 側でもローカルに robot_description / tf_static を持っておくと、
            # 実機側 discovery が少し不安定でもモデルを表示しやすい。
            # ただし JointState まで購読させると、wheel_tf_publisher と同じ
            # wheel 系フレームを二重配信して TF_OLD_DATA を起こしやすい。
            # ここでは local の robot_state_publisher から動的 TF を切り離し、
            # fixed joint の tf_static だけを担当させる。
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                namespace="robot2",
                name="robot_state_publisher_local",
                output="screen",
                parameters=[
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                    {
                        "robot_description": Command(
                            [
                                "xacro",
                                " ",
                                turtlebot4_xacro,
                                " ",
                                "gazebo:=ignition",
                                " ",
                                "namespace:=robot2",
                            ]
                        )
                    },
                ],
                remappings=[
                    ("joint_states", "robot_state_publisher_local/joint_states_unused"),
                    ("/tf", "tf"),
                    ("/tf_static", "tf_static"),
                ],
            ),
            # オドメトリから Path を作る補助ノード。
            # odom_topic を変えると参照する移動情報が変わり、
            # path_topic を変えると RViz 側で購読すべき topic 名も変わる。
            # max_poses を大きくすると軌跡が長く残るが、表示負荷は少し上がる。
            Node(
                package="tb4_square",
                executable="odom_path_publisher",
                name="odom_path_publisher",
                output="screen",
                parameters=[
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                    {
                        "odom_topic": "/robot2/odom",
                        "path_topic": "/robot2/path",
                        "max_poses": 1000,
                    }
                ],
            ),
            # /robot2/tf に odom -> base_link の TF を流す補助ノード。
            # parent_frame / child_frame を変えると RViz が組み立てる座標木の形が変わる。
            # publish_rate を上げると表示はなめらかになりやすいが、配信量は増える。
            # stale_after_sec は「オドメトリが止まった」と警告するまでの猶予時間。
            Node(
                package="tb4_square",
                executable="odom_tf_publisher",
                name="robot2_odom_tf_publisher",
                output="screen",
                condition=IfCondition(LaunchConfiguration("enable_odom_tf_helper")),
                parameters=[
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                    {
                        "odom_topic": "/robot2/odom",
                        "parent_frame": "odom",
                        "child_frame": "base_link",
                        "publish_rate": 20.0,
                        "stale_after_sec": 1.0,
                    }
                ],
                remappings=[
                    ("/tf", "/robot2/tf"),
                ],
            ),
            # JointState から左右車輪まわりの TF を再構成する補助ノード。
            # joint_states_topic を変えると参照元が変わり、
            # base_frame を変えると車輪 TF をぶら下げる親フレームが変わる。
            Node(
                package="tb4_square",
                executable="wheel_tf_publisher",
                name="robot2_wheel_tf_publisher",
                output="screen",
                condition=IfCondition(LaunchConfiguration("enable_wheel_tf_helper")),
                parameters=[
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                    {
                        "joint_states_topic": "/robot2/joint_states",
                        "base_frame": "base_link",
                        "publish_rate": 20.0,
                    }
                ],
                remappings=[
                    ("/tf", "/robot2/tf"),
                ],
            ),
            # RViz 本体。/robot2/tf と /robot2/tf_static を見るようにしている。
            # ここを通常の /tf に戻すと、別ロボットの TF と混ざる可能性がある。
            Node(
                package="rviz2",
                executable="rviz2",
                name="robot2_rviz",
                output="screen",
                arguments=["-d", LaunchConfiguration("rviz_config")],
                parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
                remappings=[
                    ("/tf", LaunchConfiguration("tf_topic")),
                    ("/tf_static", LaunchConfiguration("tf_static_topic")),
                ],
            ),
        ]
    )
