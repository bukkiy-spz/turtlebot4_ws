from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


ARGUMENTS = [
    DeclareLaunchArgument(
        "namespace",
        default_value="",
        description="Robot namespace",
    ),
    DeclareLaunchArgument(
        "rviz",
        default_value="true",
        choices=["true", "false"],
        description="Start RViz",
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
    DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        choices=["true", "false"],
        description="Use simulation clock",
    ),
    DeclareLaunchArgument(
        "localization",
        default_value="false",
        choices=["true", "false"],
        description="Launch localization",
    ),
    DeclareLaunchArgument(
        "slam",
        default_value="false",
        choices=["true", "false"],
        description="Launch SLAM",
    ),
    DeclareLaunchArgument(
        "nav2",
        default_value="false",
        choices=["true", "false"],
        description="Launch Nav2",
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
    pkg_turtlebot4_navigation = get_package_share_directory("turtlebot4_navigation")
    pkg_turtlebot4_viz = get_package_share_directory("turtlebot4_viz")

    pkg_tb4_square = get_package_share_directory("tb4_square")

    ignition_launch = PathJoinSubstitution(
        [pkg_tb4_square, "launch", "turtlebot4_sim_ignition.launch.py"]
    )
    spawn_launch = PathJoinSubstitution(
        [pkg_tb4_square, "launch", "turtlebot4_sim_spawn.launch.py"]
    )
    localization_launch = PathJoinSubstitution(
        [pkg_turtlebot4_navigation, "launch", "localization.launch.py"]
    )
    slam_launch = PathJoinSubstitution(
        [pkg_turtlebot4_navigation, "launch", "slam.launch.py"]
    )
    nav2_launch = PathJoinSubstitution(
        [pkg_turtlebot4_navigation, "launch", "nav2.launch.py"]
    )
    rviz_config = PathJoinSubstitution([pkg_tb4_square, "rviz", "turtlebot4_sim.rviz"])

    default_map = PathJoinSubstitution(
        [pkg_turtlebot4_navigation, "maps", "warehouse.yaml"]
    )
    default_localization_params = PathJoinSubstitution(
        [pkg_turtlebot4_navigation, "config", "localization.yaml"]
    )
    default_nav2_params = PathJoinSubstitution(
        [pkg_turtlebot4_navigation, "config", "nav2.yaml"]
    )
    default_slam_params = PathJoinSubstitution(
        [pkg_turtlebot4_navigation, "config", "slam.yaml"]
    )

    extra_arguments = [
        DeclareLaunchArgument(
            "map",
            default_value=default_map,
            description="Full path to the map yaml file",
        ),
        DeclareLaunchArgument(
            "localization_params",
            default_value=default_localization_params,
            description="Localization parameter file",
        ),
        DeclareLaunchArgument(
            "nav2_params",
            default_value=default_nav2_params,
            description="Nav2 parameter file",
        ),
        DeclareLaunchArgument(
            "slam_params",
            default_value=default_slam_params,
            description="SLAM parameter file",
        ),
    ]

    ignition = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ignition_launch]),
        launch_arguments=[
            ("world", LaunchConfiguration("world")),
            ("model", LaunchConfiguration("model")),
            ("use_sim_time", LaunchConfiguration("use_sim_time")),
        ],
    )

    spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([spawn_launch]),
        launch_arguments=[
            ("namespace", LaunchConfiguration("namespace")),
            ("world", LaunchConfiguration("world")),
            ("model", LaunchConfiguration("model")),
            ("use_sim_time", LaunchConfiguration("use_sim_time")),
            ("x", LaunchConfiguration("x")),
            ("y", LaunchConfiguration("y")),
            ("z", LaunchConfiguration("z")),
            ("yaw", LaunchConfiguration("yaw")),
        ],
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([localization_launch]),
        launch_arguments=[
            ("namespace", LaunchConfiguration("namespace")),
            ("use_sim_time", LaunchConfiguration("use_sim_time")),
            ("map", LaunchConfiguration("map")),
            ("params", LaunchConfiguration("localization_params")),
        ],
        condition=IfCondition(LaunchConfiguration("localization")),
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([slam_launch]),
        launch_arguments=[
            ("namespace", LaunchConfiguration("namespace")),
            ("use_sim_time", LaunchConfiguration("use_sim_time")),
            ("params", LaunchConfiguration("slam_params")),
        ],
        condition=IfCondition(LaunchConfiguration("slam")),
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([nav2_launch]),
        launch_arguments=[
            ("namespace", LaunchConfiguration("namespace")),
            ("use_sim_time", LaunchConfiguration("use_sim_time")),
            ("params_file", LaunchConfiguration("nav2_params")),
        ],
        condition=IfCondition(LaunchConfiguration("nav2")),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        remappings=[
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        ],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    ld = LaunchDescription(ARGUMENTS)
    for argument in extra_arguments:
        ld.add_action(argument)
    ld.add_action(ignition)
    ld.add_action(spawn)
    ld.add_action(localization)
    ld.add_action(slam)
    ld.add_action(nav2)
    ld.add_action(rviz)
    return ld
