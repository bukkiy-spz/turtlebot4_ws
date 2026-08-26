"""Navigation-critical Gazebo bridges for the second TurtleBot4.

The upstream full bridge starts camera, cliff, IR and HMI bridges as separate
processes.  They are not inputs to localization/Nav2, but their DDS endpoints
prevented the second Nav2 lifecycle graph from being discovered reliably in
the two-robot simulation.  Keep the bridges that provide velocity, odometry,
ground truth, bumper safety and LiDAR data.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


ARGUMENTS = [
    DeclareLaunchArgument("use_sim_time", default_value="true", choices=["true", "false"]),
    DeclareLaunchArgument("robot_name", default_value="turtlebot4"),
    DeclareLaunchArgument("dock_name", default_value="standard_dock"),
    DeclareLaunchArgument("namespace", default_value=""),
    DeclareLaunchArgument("world", default_value="warehouse"),
]


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    robot_name = LaunchConfiguration("robot_name")
    dock_name = LaunchConfiguration("dock_name")
    namespace = LaunchConfiguration("namespace")
    world = LaunchConfiguration("world")
    parameters = [{"use_sim_time": use_sim_time}]

    cmd_vel = Node(
        package="ros_gz_bridge", executable="parameter_bridge", name="cmd_vel_bridge",
        output="screen", parameters=parameters,
        arguments=[
            [namespace, "/cmd_vel@geometry_msgs/msg/Twist[ignition.msgs.Twist"],
            ["/model/", robot_name, "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist"],
        ],
        remappings=[
            ([namespace, "/cmd_vel"], "cmd_vel"),
            (["/model/", robot_name, "/cmd_vel"], "diffdrive_controller/cmd_vel_unstamped"),
        ],
    )
    pose = Node(
        package="ros_gz_bridge", executable="parameter_bridge", name="pose_bridge",
        output="screen", parameters=parameters,
        arguments=[
            ["/model/", robot_name, "/pose@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V"],
            ["/model/", dock_name, "/pose@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V"],
        ],
        remappings=[
            (["/model/", robot_name, "/pose"], "_internal/sim_ground_truth_pose"),
            (["/model/", dock_name, "/pose"], "_internal/sim_ground_truth_dock_pose"),
        ],
    )
    odom_tf = Node(
        package="ros_gz_bridge", executable="parameter_bridge", name="odom_base_tf_bridge",
        output="screen", parameters=parameters,
        arguments=[["/model/", robot_name, "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V"]],
        remappings=[(["/model/", robot_name, "/tf"], "tf")],
    )
    bumper = Node(
        package="ros_gz_bridge", executable="parameter_bridge", name="bumper_contact_bridge",
        output="screen", parameters=parameters,
        arguments=[[namespace, "/bumper_contact@ros_gz_interfaces/msg/Contacts[ignition.msgs.Contacts"]],
        remappings=[([namespace, "/bumper_contact"], "bumper_contact")],
    )
    lidar = Node(
        package="ros_gz_bridge", executable="parameter_bridge", name="lidar_bridge",
        output="screen", parameters=parameters,
        arguments=[
            ["/world/", world, "/model/", robot_name,
             "/link/rplidar_link/sensor/rplidar/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan"],
        ],
        remappings=[
            (["/world/", world, "/model/", robot_name, "/link/rplidar_link/sensor/rplidar/scan"], "scan"),
        ],
    )

    return LaunchDescription(ARGUMENTS + [cmd_vel, pose, odom_tf, bumper, lidar])
