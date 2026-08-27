"""TurtleBot4 3台シミュレーション: Robot2 + Robot5 + Robot6.

Robot2/Robot5の2台版を変更せず、Robot6をmulti-description spawnとして
追加するための専用launchである。
"""

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

    ignition_launch = PathJoinSubstitution(
        [pkg_tb4_square, "launch", "turtlebot4_sim_ignition_multi.launch.py"]
    )
    spawn_launch = PathJoinSubstitution(
        [pkg_tb4_square, "launch", "turtlebot4_sim_spawn.launch.py"]
    )
    spawn_multi_launch = PathJoinSubstitution(
        [pkg_tb4_square, "launch", "turtlebot4_sim_spawn_multi.launch.py"]
    )

    world = LaunchConfiguration("world")
    model = LaunchConfiguration("model")
    use_sim_time = LaunchConfiguration("use_sim_time")

    ignition = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ignition_launch]),
        launch_arguments={
            "world": world,
            "model": model,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    # Robot2は2台版と同じ通常description（model Sensors plugin ON）を使う。
    robot2_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([spawn_launch]),
        launch_arguments={
            "namespace": "robot2",
            "world": world,
            "model": model,
            "use_sim_time": use_sim_time,
            "x": "4.07285",
            "y": "-2.56021",
            "z": "0.0",
            "yaw": "0.0",
        }.items(),
    )

    # Robot5/Robot6はmulti description（model Sensors plugin OFF）を共有する。
    robot5_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([spawn_multi_launch]),
        launch_arguments={
            "namespace": "robot5",
            "world": world,
            "model": model,
            "use_sim_time": use_sim_time,
            "x": "2.242856",
            "y": "-0.661110",
            "z": "0.0",
            "yaw": "1.9414",
        }.items(),
    )

    # robot6_charger=(1.1972718,-1.1213489)からrobot6_predockへは
    # backward lane。dock側を向くrobot yaw=2.70656 radを使用する。
    robot6_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([spawn_multi_launch]),
        launch_arguments={
            "namespace": "robot6",
            "world": world,
            "model": model,
            "use_sim_time": use_sim_time,
            "x": "1.197272",
            "y": "-1.121349",
            "z": "0.0",
            "yaw": "2.70656",
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("world", default_value="tb4_20260612"),
        DeclareLaunchArgument("model", default_value="standard"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        UnsetEnvironmentVariable("ROS_DISCOVERY_SERVER"),
        UnsetEnvironmentVariable("ROS_STATIC_PEERS"),
        ignition,
        TimerAction(period=3.0, actions=[robot2_spawn]),
        # 2台版で検証済みのRobot5 delayは変更しない。
        TimerAction(period=30.0, actions=[robot5_spawn]),
        # controller/spawner namespace raceを避け、Robot6はさらに後に開始する。
        TimerAction(period=60.0, actions=[robot6_spawn]),
    ])
