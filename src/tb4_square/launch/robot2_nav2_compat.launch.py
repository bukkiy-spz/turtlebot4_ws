"""robot2 向けの Nav2 起動 workaround launch。

`turtlebot4_navigation/nav2.launch.py` で `smoother_server` が
初期化待ちのまま進まない環境向けに、`smoother_server` を起動対象から
外した最小構成の Nav2 bringup を行う。
"""

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node, PushRosNamespace, SetRemap
from launch_ros.descriptions import ParameterFile

from nav2_common.launch import RewrittenYaml


def launch_setup(context, *args, **kwargs):
    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    params_file = LaunchConfiguration("params_file")
    use_respawn = LaunchConfiguration("use_respawn")
    log_level = LaunchConfiguration("log_level")
    pkg_tb4_square = get_package_share_directory("tb4_square")

    lifecycle_nodes = [
        "controller_server",
        "planner_server",
        "bt_navigator",
        "waypoint_follower",
        "velocity_smoother",
    ]

    remappings = [
        ("/tf", "tf_nav"),
        ("/tf_static", "tf_static"),
    ]

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites={
                "use_sim_time": use_sim_time,
                "autostart": autostart,
                "default_nav_to_pose_bt_xml": PathJoinSubstitution(
                    [pkg_tb4_square, "behavior_trees", "navigate_to_pose_no_recovery.xml"]
                ),
                "default_nav_through_poses_bt_xml": PathJoinSubstitution(
                    [
                        pkg_tb4_square,
                        "behavior_trees",
                        "navigate_through_poses_no_recovery.xml",
                    ]
                ),
            },
            convert_types=True,
        ),
        allow_substs=True,
    )

    namespace_str = namespace.perform(context)
    if namespace_str and not namespace_str.startswith("/"):
        namespace_str = "/" + namespace_str

    nav_nodes = GroupAction(
        actions=[
            PushRosNamespace(namespace),
            SetRemap(namespace_str + "/global_costmap/scan", namespace_str + "/scan"),
            SetRemap(namespace_str + "/local_costmap/scan", namespace_str + "/scan"),
            Node(
                package="tb4_square",
                executable="odom_tf_publisher",
                name="odom_tf_publisher",
                output="screen",
                parameters=[
                    {"use_sim_time": use_sim_time},
                    {
                        "odom_topic": namespace_str + "/odom",
                        "parent_frame": "odom",
                        "child_frame": "base_link",
                        "publish_rate": 20.0,
                        "stale_after_sec": 1.0,
                        "use_msg_stamp": True,
                    },
                ],
                remappings=[("/tf", namespace_str + "/tf_nav")],
            ),
            Node(
                package="nav2_controller",
                executable="controller_server",
                output="screen",
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
                remappings=remappings + [("cmd_vel", "cmd_vel_nav")],
            ),
            Node(
                package="nav2_planner",
                executable="planner_server",
                name="planner_server",
                output="screen",
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
                remappings=remappings,
            ),
            Node(
                package="nav2_bt_navigator",
                executable="bt_navigator",
                name="bt_navigator",
                output="screen",
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
                remappings=remappings,
            ),
            Node(
                package="nav2_waypoint_follower",
                executable="waypoint_follower",
                name="waypoint_follower",
                output="screen",
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
                remappings=remappings,
            ),
            Node(
                package="nav2_velocity_smoother",
                executable="velocity_smoother",
                name="velocity_smoother",
                output="screen",
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
                remappings=remappings + [
                    ("cmd_vel", "cmd_vel_nav"),
                    ("cmd_vel_smoothed", "cmd_vel"),
                ],
            ),
            Node(
                package="tb4_square",
                executable="lifecycle_bringup_retry",
                name="lifecycle_bringup_retry_navigation",
                output="screen",
                arguments=["--ros-args", "--log-level", log_level],
                parameters=[
                    {"use_sim_time": use_sim_time},
                    {"node_names": lifecycle_nodes},
                    {"target_namespace": namespace},
                    {"retry_count": 30},
                    {"service_wait_sec": 2.0},
                    {"retry_delay_sec": 1.0},
                    {"startup_delay_sec": 5.0},
                ],
            ),
        ]
    )

    return [nav_nodes]


def generate_launch_description():
    pkg_turtlebot4_navigation = get_package_share_directory("turtlebot4_navigation")

    ld = LaunchDescription()
    ld.add_action(SetEnvironmentVariable("RCUTILS_LOGGING_BUFFERED_STREAM", "1"))
    ld.add_action(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock if true",
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            "params_file",
            default_value=PathJoinSubstitution(
                [pkg_turtlebot4_navigation, "config", "nav2.yaml"]
            ),
            description="Full path to the Nav2 parameters file",
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            "namespace",
            default_value="robot2",
            description="Robot namespace",
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            "autostart",
            default_value="true",
            description="Automatically startup the nav2 stack",
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            "use_respawn",
            default_value="false",
            description="Whether to respawn if a node crashes",
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            "log_level",
            default_value="info",
            description="log level",
        )
    )
    ld.add_action(OpaqueFunction(function=launch_setup))
    return ld
