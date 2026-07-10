"""Ignition 上に TurtleBot4 を出現させ、ROS 側の関連ノード群も起動する。"""

from ament_index_python.packages import get_package_share_directory

from irobot_create_common_bringup.namespace import GetNamespacedName
from irobot_create_common_bringup.offset import OffsetParser, RotationalOffsetX, RotationalOffsetY

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node, PushRosNamespace


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
    # ロボット記述、bridge、Create 3 関連ノードの launch を参照するためのパス群。
    # 既存 launch を別のものへ差し替えたい場合は、ここが変更点になる。
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

    # 起動引数をいったん LaunchConfiguration として束ねる。
    # x / y / z / yaw を変えると初期出現位置と向きが変わる。
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

    # dock はロボットの近くに出したいので、robot 側の姿勢から相対計算している。
    # 数値を変えると dock と robot の初期距離や向きの関係が変わる。
    dock_offset_x = RotationalOffsetX(0.157, yaw)
    dock_offset_y = RotationalOffsetY(0.157, yaw)
    x_dock = OffsetParser(x, dock_offset_x)
    y_dock = OffsetParser(y, dock_offset_y)
    z_robot = OffsetParser(z, -0.0025)
    yaw_dock = OffsetParser(yaw, 3.1416)

    spawn_robot_group_action = GroupAction(
        [
            PushRosNamespace(namespace),
            # robot_description と基本 TF を出す。
            # model を変えると標準機体と lite 機体が切り替わる。
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([robot_description_launch]),
                launch_arguments=[
                    ("model", LaunchConfiguration("model")),
                    ("use_sim_time", use_sim_time),
                ],
            ),
            # dock の URDF 側 description を用意する。
            # 別タイプの dock を使う場合はこの include 先や引数を見直す。
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([dock_description_launch]),
                launch_arguments={"gazebo": "ignition"}.items(),
            ),
            # robot_state_publisher が配信する robot_description topic を使って spawn する。
            # -x/-y/-z/-Y を変えると、シミュレータ上の出現位置が変わる。
            Node(
                package="ros_ign_gazebo",
                executable="create",
                arguments=[
                    "-name", robot_name,
                    "-x", x,
                    "-y", y,
                    "-z", z_robot,
                    "-Y", yaw,
                    "-topic", "robot_description",
                ],
                output="screen",
            ),
            # dock_state_publisher 側の standard_dock_description topic から dock を spawn する。
            # x_dock / y_dock / yaw_dock の計算を変えると dock の相対配置が変わる。
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
                    "-topic", "standard_dock_description",
                ],
                output="screen",
            ),
            # LiDAR や camera など、シミュレータの topic を ROS 2 topic へ橋渡しする。
            # センサ topic 名を変えたいときは、この include 先の bridge launch が主な編集点。
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
            # TurtleBot4 / Create 3 の ROS ノード群を起動する。
            # param_file を差し替えると TurtleBot4 本体ノードの細かな設定を変えられる。
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
            # RViz や一部センサ処理が期待する静的 TF を追加する。
            # 親子フレーム名を変えると、LaserScan や PointCloud の見え方に直接影響する。
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
            # camera の optical frame を明示的に補う。
            # 回転値を変えると、画像や点群の向きが RViz 上でずれて見える。
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

    # 起動引数と実際の action 群をまとめて返す。
    # 新しい spawn 処理や補助ノードを足すなら、この GroupAction か add_action が追加先。
    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(param_file_cmd)
    ld.add_action(spawn_robot_group_action)
    return ld
