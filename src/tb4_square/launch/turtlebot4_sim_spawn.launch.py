import os

from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from irobot_create_common_bringup.namespace import GetNamespacedName
from irobot_create_common_bringup.offset import OffsetParser, RotationalOffsetX, RotationalOffsetY

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node, PushRosNamespace

import tempfile
import os


ARGUMENTS = [
    DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        choices=["true", "false"],
        description="Use simulation clock",
    ),
    DeclareLaunchArgument(
        "model",
        default_value="standard",
        choices=["standard", "lite"],
        description="TurtleBot4 model",
    ),
    DeclareLaunchArgument(
        "namespace",
        default_value="",
        description="Robot namespace",
    ),
    DeclareLaunchArgument(
        "world",
        default_value="warehouse",
        description="Ignition world name",
    ),
]

for pose_element in ["x", "y", "z", "yaw"]:
    ARGUMENTS.append(
        DeclareLaunchArgument(
            pose_element,
            default_value="0.0",
            description=f"{pose_element} component of the robot pose",
        )
    )


def generate_launch_description():
    pkg_turtlebot4_ignition_bringup = get_package_share_directory(
        "turtlebot4_ignition_bringup"
    )
    pkg_turtlebot4_description = get_package_share_directory("turtlebot4_description")
    pkg_irobot_create_common_bringup = get_package_share_directory(
        "irobot_create_common_bringup"
    )
    pkg_irobot_create_ignition_bringup = get_package_share_directory(
        "irobot_create_ignition_bringup"
    )
    pkg_irobot_create_description = get_package_share_directory(
        "irobot_create_description"
    )

    turtlebot4_ros_ign_bridge_launch = PathJoinSubstitution(
        [pkg_turtlebot4_ignition_bringup, "launch", "ros_ign_bridge.launch.py"]
    )
    turtlebot4_node_launch = PathJoinSubstitution(
        [pkg_turtlebot4_ignition_bringup, "launch", "turtlebot4_nodes.launch.py"]
    )
    create3_nodes_launch = PathJoinSubstitution(
        [pkg_irobot_create_common_bringup, "launch", "create3_nodes.launch.py"]
    )
    create3_ignition_nodes_launch = PathJoinSubstitution(
        [pkg_irobot_create_ignition_bringup, "launch", "create3_ignition_nodes.launch.py"]
    )
    robot_description_launch = PathJoinSubstitution(
        [pkg_turtlebot4_description, "launch", "robot_description.launch.py"]
    )
    dock_description_launch = PathJoinSubstitution(
        [pkg_irobot_create_common_bringup, "launch", "dock_description.launch.py"]
    )

    param_file_cmd = DeclareLaunchArgument(
        "param_file",
        default_value=PathJoinSubstitution(
            [pkg_turtlebot4_ignition_bringup, "config", "turtlebot4_node.yaml"]
        ),
        description="TurtleBot4 node parameter file",
    )

    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    world = LaunchConfiguration("world")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    yaw = LaunchConfiguration("yaw")
    turtlebot4_node_yaml_file = LaunchConfiguration("param_file")

    robot_name = GetNamespacedName(namespace, "turtlebot4")
    dock_name = GetNamespacedName(namespace, "standard_dock")

    dock_offset_x = RotationalOffsetX(0.157, yaw)
    dock_offset_y = RotationalOffsetY(0.157, yaw)
    x_dock = OffsetParser(x, dock_offset_x)
    y_dock = OffsetParser(y, dock_offset_y)
    z_robot = OffsetParser(z, -0.0025)
    yaw_dock = OffsetParser(yaw, 3.1416)

    spawn_robot_group_action = GroupAction(
        [
            PushRosNamespace(namespace),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([robot_description_launch]),
                launch_arguments=[
                    ("model", LaunchConfiguration("model")),
                    ("use_sim_time", use_sim_time),
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([dock_description_launch]),
                launch_arguments={"gazebo": "ignition"}.items(),
            ),
            Node(
                package="ros_ign_gazebo",
                executable="create",
                arguments=[
                    "-name", robot_name,
                    "-x", x,
                    "-y", y,
                    "-z", z_robot,
                    "-Y", yaw,
                    "-param", "robot_description",
                ],
                parameters=[
                    {
                        "robot_description": Command(
                            [
                                "xacro ",
                                PathJoinSubstitution(
                                    [
                                        pkg_turtlebot4_description,
                                        "urdf",
                                        LaunchConfiguration("model"),
                                        "turtlebot4.urdf.xacro",
                                    ]
                                ),
                                " gazebo:=ignition namespace:=",
                                robot_name,
                            ]
                        )
                    }
                ],
                output="screen",
            ),
            Node(
                package="ros_ign_gazebo",
                executable="create",
                arguments=[
                    "-name",
                    dock_name,
                    "-x",
                    x_dock,
                    "-y",
                    y_dock,
                    "-z",
                    z,
                    "-Y",
                    yaw_dock,
                    "-param", "standard_dock_description",
                ],
                parameters=[
                    {
                        "standard_dock_description": Command(
                            [
                                "xacro ",
                                PathJoinSubstitution(
                                    [
                                        pkg_irobot_create_description,
                                        "urdf",
                                        "dock",
                                        "standard_dock.urdf.xacro",
                                    ]
                                ),
                                " gazebo:=ignition",
                            ]
                        )
                    }
                ],
                output="screen",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([turtlebot4_ros_ign_bridge_launch]),
                launch_arguments=[
                    ("model", LaunchConfiguration("model")),
                    ("robot_name", robot_name),
                    ("dock_name", dock_name),
                    ("namespace", namespace),
                    ("world", world),
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([turtlebot4_node_launch]),
                launch_arguments=[
                    ("model", LaunchConfiguration("model")),
                    ("param_file", turtlebot4_node_yaml_file),
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([create3_nodes_launch]),
                launch_arguments=[("namespace", namespace)],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([create3_ignition_nodes_launch]),
                launch_arguments=[
                    ("robot_name", robot_name),
                    ("dock_name", dock_name),
                ],
            ),
            Node(
                name="rplidar_stf",
                package="tf2_ros",
                executable="static_transform_publisher",
                output="screen",
                arguments=[
                    "0",
                    "0",
                    "0",
                    "0",
                    "0",
                    "0.0",
                    "rplidar_link",
                    [robot_name, "/rplidar_link/rplidar"],
                ],
                remappings=[
                    ("/tf", "tf"),
                    ("/tf_static", "tf_static"),
                ],
            ),
            Node(
                name="camera_stf",
                package="tf2_ros",
                executable="static_transform_publisher",
                output="screen",
                arguments=[
                    "0",
                    "0",
                    "0",
                    "1.5707",
                    "-1.5707",
                    "0",
                    "oakd_rgb_camera_optical_frame",
                    [robot_name, "/oakd_rgb_camera_frame/rgbd_camera"],
                ],
                remappings=[
                    ("/tf", "tf"),
                    ("/tf_static", "tf_static"),
                ],
            ),
        ]
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(param_file_cmd)
    ld.add_action(spawn_robot_group_action)
    return ld
