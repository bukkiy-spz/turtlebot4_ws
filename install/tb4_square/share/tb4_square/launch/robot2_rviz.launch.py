import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory("tb4_square")
    default_rviz_config = os.path.join(package_share, "rviz", "robot2.rviz")

    return LaunchDescription(
        [
            DeclareLaunchArgument("rviz_config", default_value=default_rviz_config),
            Node(
                package="tb4_square",
                executable="odom_path_publisher",
                name="odom_path_publisher",
                output="screen",
                parameters=[
                    {
                        "odom_topic": "/robot2/odom",
                        "path_topic": "/robot2/path",
                        "max_poses": 1000,
                    }
                ],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="robot2_rviz",
                output="screen",
                arguments=["-d", LaunchConfiguration("rviz_config")],
                remappings=[
                    ("/tf", "/robot2/tf"),
                    ("/tf_static", "/robot2/tf_static"),
                ],
            ),
        ]
    )
