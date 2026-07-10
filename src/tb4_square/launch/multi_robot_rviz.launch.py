"""3台の TurtleBot4 を 1つの RViz へ重ねて表示する launch。"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory("tb4_square")
    default_rviz_config = os.path.join(package_share, "rviz", "multi_robot_full.rviz")
    pkg_turtlebot4_description = get_package_share_directory("turtlebot4_description")
    model = LaunchConfiguration("model")
    use_sim_time = LaunchConfiguration("use_sim_time")
    rviz_config = LaunchConfiguration("rviz_config")

    def robot_description(namespace: str):
        xacro_path = PathJoinSubstitution(
            [pkg_turtlebot4_description, "urdf", model, "turtlebot4.urdf.xacro"]
        )
        return Command(
            [
                "xacro",
                " ",
                xacro_path,
                " ",
                "gazebo:=ignition",
                " ",
                "namespace:=",
                namespace,
            ]
        )

    def description_node(namespace: str) -> Node:
        return Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            namespace=namespace,
            name="robot_state_publisher_viz",
            output="screen",
            parameters=[
                {"use_sim_time": use_sim_time},
                {"robot_description": robot_description(namespace)},
            ],
            remappings=[
                ("joint_states", "robot_state_publisher_viz/joint_states_unused"),
                ("/tf", f"/viz/{namespace}/tf_unused"),
                ("/tf_static", f"/viz/{namespace}/tf_static_unused"),
            ],
        )

    def tf_relay_node(namespace: str, static: bool) -> Node:
        input_topic = f"/{namespace}/tf_static" if static else f"/{namespace}/tf"
        output_topic = "/viz/tf_static" if static else "/viz/tf"
        return Node(
            package="tb4_square",
            executable="tf_frame_prefix_republisher",
            name=f"{namespace}_{'tf_static' if static else 'tf'}_prefix_republisher",
            output="screen",
            parameters=[
                {"input_topic": input_topic},
                {"output_topic": output_topic},
                {"frame_prefix": namespace},
                {"preserve_frames": ["map"]},
                {"reliable": static},
                {"transient_local": static},
            ],
        )

    def scan_relay_node(namespace: str) -> Node:
        return Node(
            package="tb4_square",
            executable="laser_scan_frame_prefix_republisher",
            name=f"{namespace}_scan_prefix_republisher",
            output="screen",
            parameters=[
                {"input_topic": f"/{namespace}/scan"},
                {"output_topic": f"/viz/{namespace}/scan"},
                {"frame_prefix": namespace},
            ],
        )

    nodes = [
        DeclareLaunchArgument("rviz_config", default_value=default_rviz_config),
        DeclareLaunchArgument("model", default_value="standard"),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
    ]

    for namespace in ("robot2", "robot5", "robot6"):
        nodes.extend(
            [
                description_node(namespace),
                tf_relay_node(namespace, static=False),
                tf_relay_node(namespace, static=True),
                scan_relay_node(namespace),
            ]
        )

    nodes.append(
        Node(
            package="rviz2",
            executable="rviz2",
            name="multi_robot_rviz",
            output="screen",
            arguments=["-d", rviz_config],
            parameters=[{"use_sim_time": use_sim_time}],
            remappings=[
                ("/tf", "/viz/tf"),
                ("/tf_static", "/viz/tf_static"),
            ],
        )
    )

    return LaunchDescription(nodes)
