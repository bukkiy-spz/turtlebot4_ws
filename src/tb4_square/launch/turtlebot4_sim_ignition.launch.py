import os

from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


ARGUMENTS = [
    DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        choices=["true", "false"],
        description="Use simulation clock",
    ),
    DeclareLaunchArgument(
        "world",
        default_value="warehouse",
        description="Ignition world name",
    ),
    DeclareLaunchArgument(
        "model",
        default_value="standard",
        choices=["standard", "lite"],
        description="TurtleBot4 model",
    ),
]


def generate_launch_description():
    pkg_turtlebot4_ignition_bringup = get_package_share_directory(
        "turtlebot4_ignition_bringup"
    )
    pkg_turtlebot4_description = get_package_share_directory("turtlebot4_description")
    pkg_irobot_create_description = get_package_share_directory("irobot_create_description")
    pkg_irobot_create_ignition_bringup = get_package_share_directory(
        "irobot_create_ignition_bringup"
    )
    pkg_irobot_create_ignition_plugins = get_package_share_directory(
        "irobot_create_ignition_plugins"
    )
    pkg_turtlebot4_ignition_gui_plugins = get_package_share_directory(
        "turtlebot4_ignition_gui_plugins"
    )
    pkg_ros_ign_gazebo = get_package_share_directory("ros_ign_gazebo")
    pkg_tb4_square = get_package_share_directory("tb4_square")

    ign_resource_path = SetEnvironmentVariable(
        name="IGN_GAZEBO_RESOURCE_PATH",
        value=[
            os.path.join(pkg_turtlebot4_ignition_bringup, "worlds"),
            ":",
            os.path.join(pkg_irobot_create_ignition_bringup, "worlds"),
            ":",
            str(Path(pkg_turtlebot4_description).parent.resolve()),
            ":",
            str(Path(pkg_irobot_create_description).parent.resolve()),
        ],
    )

    ign_gui_plugin_path = SetEnvironmentVariable(
        name="IGN_GUI_PLUGIN_PATH",
        value=[
            os.path.join(pkg_turtlebot4_ignition_gui_plugins, "lib"),
            ":",
            os.path.join(pkg_irobot_create_ignition_plugins, "lib"),
        ],
    )

    ign_gazebo_launch = PathJoinSubstitution(
        [pkg_ros_ign_gazebo, "launch", "ign_gazebo.launch.py"]
    )
    gui_config = PathJoinSubstitution([pkg_tb4_square, "gui", "turtlebot4_sim.gui.config"])
    ignition_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ign_gazebo_launch]),
        launch_arguments=[
            (
                "ign_args",
                [
                    LaunchConfiguration("world"),
                    ".sdf -r -v 4 --render-engine-gui ogre --render-engine-server ogre --gui-config ",
                    gui_config,
                ],
            )
        ],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="clock_bridge",
        output="screen",
        arguments=["/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock"],
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(ign_resource_path)
    ld.add_action(ign_gui_plugin_path)
    ld.add_action(ignition_gazebo)
    ld.add_action(clock_bridge)
    return ld
