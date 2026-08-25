"""TurtleBot4 2台シミュレーション: Robot2 + Robot5."""

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    UnsetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():

    pkg_tb4_square = get_package_share_directory("tb4_square")

    ignition_launch = PathJoinSubstitution([
        pkg_tb4_square,
        "launch",
        "turtlebot4_sim_ignition_multi.launch.py",
    ])

    spawn_launch = PathJoinSubstitution([
        pkg_tb4_square,
        "launch",
        "turtlebot4_sim_spawn.launch.py",
    ])

    spawn_multi_launch = PathJoinSubstitution([
        pkg_tb4_square,
        "launch",
        "turtlebot4_sim_spawn_multi.launch.py",
    ])

    # 既に作成済みのmulti-robot対応launchを使う
    localization_launch = PathJoinSubstitution([
        pkg_tb4_square,
        "launch",
        "robot2_localization_compat.launch.py",
    ])

    nav2_launch = PathJoinSubstitution([
        pkg_tb4_square,
        "launch",
        "robot2_nav2_compat.launch.py",
    ])

    rviz_launch = PathJoinSubstitution([
        pkg_tb4_square,
        "launch",
        "multi_robot_rviz.launch.py",
    ])

    world = LaunchConfiguration("world")
    model = LaunchConfiguration("model")
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_file = LaunchConfiguration("map")

    # =========================================================
    # Gazebo
    # =========================================================

    ignition = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ignition_launch]),
        launch_arguments={
            "world": world,
            "model": model,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    # =========================================================
    # Robot2
    # =========================================================

    robot2_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([spawn_launch]),
        launch_arguments={
            "namespace": "robot2",
            "world": world,
            "model": model,
            "use_sim_time": use_sim_time,

            # 後で正しいcharger位置へ変更
            "x": "4.07285",
            "y": "-2.56021",
            "z": "0.0",
            "yaw": "0.0",
        }.items(),
    )

    # =========================================================
    # Robot5
    # =========================================================

    robot5_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([spawn_multi_launch]),
        launch_arguments={
            "namespace": "robot5",
            "world": world,
            "model": model,
            "use_sim_time": use_sim_time,

            # 後で正しいcharger位置へ変更
            "x": "2.242856",
            "y": "-0.661110",
            "z": "0.0",
            "yaw": "1.9414",
        }.items(),
    )

    # 最初はspawnだけ確認するため、
    # localization/Nav2/RVizは後段で追加する

    return LaunchDescription([
        DeclareLaunchArgument(
            "world",
            default_value="tb4_20260612",
        ),
        DeclareLaunchArgument(
            "model",
            default_value="standard",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
        ),
        DeclareLaunchArgument(
            "map",
            default_value="",
        ),

        UnsetEnvironmentVariable("ROS_DISCOVERY_SERVER"),
        UnsetEnvironmentVariable("ROS_STATIC_PEERS"),

        ignition,

        # Gazebo起動直後に2台同時spawnさせるより少しずらす
        TimerAction(
            period=3.0,
            actions=[robot2_spawn],
        ),

        TimerAction(
            period=6.0,
            actions=[robot5_spawn],
        ),
    ])
