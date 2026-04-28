"""四角形走行デモ用ノードを起動する launch ファイル。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            # ここで default_value を変えると、起動時の既定挙動が変わる。
            # たとえば side_length を大きくすると走る正方形が大きくなり、
            # linear_speed / angular_speed を変えると直進や旋回の速さが変わる。
            DeclareLaunchArgument("namespace", default_value=""),
            DeclareLaunchArgument("cmd_vel_topic", default_value="cmd_vel"),
            DeclareLaunchArgument("use_stamped", default_value="false"),
            DeclareLaunchArgument("side_length", default_value="0.4"),
            DeclareLaunchArgument("linear_speed", default_value="0.10"),
            DeclareLaunchArgument("angular_speed", default_value="0.6"),
            DeclareLaunchArgument("pause_time", default_value="0.5"),
            DeclareLaunchArgument("wait_for_subscriber_sec", default_value="8.0"),
            DeclareLaunchArgument("require_subscriber", default_value="true"),
            DeclareLaunchArgument("reliability", default_value="reliable"),
            # 実際に cmd_vel を出すノード本体。
            # launch 引数をここへ流し込むことで、コマンドを出す相手の topic や
            # 速度プロファイルを外から切り替えられるようにしている。
            Node(
                package="tb4_square",
                executable="square_driver",
                name="square_driver",
                namespace=LaunchConfiguration("namespace"),
                output="screen",
                parameters=[
                    {
                        "cmd_vel_topic": LaunchConfiguration("cmd_vel_topic"),
                        "use_stamped": LaunchConfiguration("use_stamped"),
                        "side_length": LaunchConfiguration("side_length"),
                        "linear_speed": LaunchConfiguration("linear_speed"),
                        "angular_speed": LaunchConfiguration("angular_speed"),
                        "pause_time": LaunchConfiguration("pause_time"),
                        "wait_for_subscriber_sec": LaunchConfiguration("wait_for_subscriber_sec"),
                        "require_subscriber": LaunchConfiguration("require_subscriber"),
                        "reliability": LaunchConfiguration("reliability"),
                    }
                ],
            ),
        ]
    )
