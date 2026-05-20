"""robot2 向けの SLAM Toolbox 起動 launch。"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    namespace = LaunchConfiguration("namespace")

    namespace_str = namespace.perform(context)
    if namespace_str and not namespace_str.startswith("/"):
        namespace_str = "/" + namespace_str

    slam_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        namespace=namespace,
        name="slam_toolbox",
        output="screen",
        parameters=[
            LaunchConfiguration("params_file"),
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
        remappings=[
            ("/tf", namespace_str + "/tf"),
            ("/tf_static", namespace_str + "/tf_static"),
            ("/scan", namespace_str + "/scan"),
            ("/map", namespace_str + "/map"),
            ("/map_metadata", namespace_str + "/map_metadata"),
            ("/map_updates", namespace_str + "/map_updates"),
        ],
    )

    return [slam_node]


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory("tb4_square")
    default_params = os.path.join(package_share, "config", "robot2_slam.yaml")
    default_rviz_config = os.path.join(package_share, "rviz", "robot2_slam.rviz")
    robot2_rviz_launch = os.path.join(package_share, "launch", "robot2_rviz.launch.py")

    return LaunchDescription(
        [
            DeclareLaunchArgument("namespace", default_value="robot2"),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument("params_file", default_value=default_params),
            DeclareLaunchArgument("rviz_config", default_value=default_rviz_config),
            OpaqueFunction(function=launch_setup),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([robot2_rviz_launch]),
                launch_arguments={
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "rviz_config": LaunchConfiguration("rviz_config"),
                }.items(),
                condition=IfCondition(LaunchConfiguration("rviz")),
            ),
        ]
    )
