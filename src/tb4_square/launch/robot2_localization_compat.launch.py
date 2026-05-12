"""robot2 向けの localization 起動 workaround launch。"""

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node, PushRosNamespace
from launch_ros.descriptions import ParameterFile

from nav2_common.launch import RewrittenYaml


def launch_setup(context, *args, **kwargs):
    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params")
    map_yaml = LaunchConfiguration("map")

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites={"use_sim_time": use_sim_time, "yaml_filename": map_yaml},
            convert_types=True,
        ),
        allow_substs=True,
    )

    namespace_str = namespace.perform(context)
    if namespace_str and not namespace_str.startswith("/"):
        namespace_str = "/" + namespace_str

    remappings = [
        ("/tf", "tf_nav"),
        ("/tf_static", "tf_static"),
    ]

    localization_nodes = GroupAction(
        actions=[
            PushRosNamespace(namespace),
            Node(
                package="tb4_square",
                executable="tf_filter_republisher",
                name="tf_filter_republisher",
                output="screen",
                parameters=[
                    {"use_sim_time": use_sim_time},
                    {"drop_parent_frame": "odom"},
                    {"drop_child_frame": "base_link"},
                ],
                remappings=[
                    ("tf_in", namespace_str + "/tf"),
                    ("tf_out", namespace_str + "/tf_nav"),
                ],
            ),
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
                package="nav2_map_server",
                executable="map_server",
                name="map_server",
                output="screen",
                parameters=[configured_params],
                remappings=remappings,
            ),
            Node(
                package="nav2_amcl",
                executable="amcl",
                name="amcl",
                output="screen",
                parameters=[configured_params],
                remappings=remappings,
            ),
            Node(
                package="tb4_square",
                executable="lifecycle_bringup_retry",
                name="lifecycle_bringup_retry_localization",
                output="screen",
                parameters=[
                    {"use_sim_time": use_sim_time},
                    {"node_names": ["map_server", "amcl"]},
                    {"target_namespace": namespace},
                    {"retry_count": 30},
                    {"service_wait_sec": 2.0},
                    {"retry_delay_sec": 1.0},
                    {"startup_delay_sec": 5.0},
                ],
            ),
        ]
    )

    return [localization_nodes]


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
            "namespace",
            default_value="robot2",
            description="Robot namespace",
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            "params",
            default_value=PathJoinSubstitution(
                [pkg_turtlebot4_navigation, "config", "localization.yaml"]
            ),
            description="Localization parameters",
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            "map",
            default_value=PathJoinSubstitution(
                [pkg_turtlebot4_navigation, "maps", "warehouse.yaml"]
            ),
            description="Full path to map yaml file to load",
        )
    )
    ld.add_action(OpaqueFunction(function=launch_setup))
    return ld
