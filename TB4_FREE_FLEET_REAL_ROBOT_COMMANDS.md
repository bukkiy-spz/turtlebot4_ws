# TB4 free_fleet Real Robot Commands

このファイルは `turtlebot4_ws` 視点の Host/Robot 補助コマンド集です。

## 1. Host 側 robot2 環境

```bash
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
source ~/turtlebot4_ws/scripts/robot2_env.bash
```

## 2. Robot へ SSH

```bash
ssh ubuntu@192.168.11.22
```

## 3. Robot 生存確認

```bash
date
chronyc tracking
curl -I http://192.168.186.2
```

## 4. Robot 側生 topic 確認

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

date +%s
timeout 5 ros2 topic echo /robot2/scan --once
timeout 5 ros2 topic echo /robot2/tf --once
timeout 5 ros2 topic echo /robot2/odom --once
```

## 5. Robot 側 localization

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

ros2 launch turtlebot4_navigation localization.launch.py \
  namespace:=robot2 \
  use_sim_time:=false \
  map:=/home/ubuntu/maps/tb4/tb4_map.yaml
```

## 6. Robot 側 initial pose

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

timeout 3 ros2 topic pub /robot2/initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
"{header: {frame_id: map}, pose: {pose: {position: {x: -1.0, y: -0.5, z: 0.0}, orientation: {w: 1.0}}, covariance: [0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.068]}}" \
--rate 5 \
--qos-reliability best_effort
```

## 7. localization 確認

```bash
timeout 5 ros2 topic echo /robot2/amcl_pose --once
timeout 10 ros2 run tf2_ros tf2_echo map odom --ros-args -r /tf:=/robot2/tf -r /tf_static:=/robot2/tf_static
```

## 8. Robot 側 Nav2

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

ros2 launch turtlebot4_navigation nav2.launch.py \
  namespace:=robot2 \
  use_sim_time:=false
```

## 9. Robot 側 `/robot2/tf -> /tf` relay

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

python3 - <<'PY'
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from tf2_msgs.msg import TFMessage

class Relay(Node):
    def __init__(self):
        super().__init__('robot2_tf_to_tf_relay')
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.pub = self.create_publisher(TFMessage, '/tf', qos)
        self.sub = self.create_subscription(TFMessage, '/robot2/tf', self.cb, qos)
        self.get_logger().info("Relaying /robot2/tf -> /tf on robot side")

    def cb(self, msg):
        self.pub.publish(msg)

rclpy.init()
node = Relay()
try:
    rclpy.spin(node)
except KeyboardInterrupt:
    pass
finally:
    node.destroy_node()
    rclpy.shutdown()
PY
```

## 10. Robot 側 `map -> odom` が `/tf` に乗っているか確認

```bash
timeout 5 ros2 topic echo /tf --once
```

## 11. Robot 側 bridge

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

/home/ubuntu/zenoh_bridge/zenoh-bridge-ros2dds \
  -c /home/ubuntu/zenoh_bridge/robot2_zenoh_bridge_ros2dds_client_config.json5
```

## 12. Robot 側 direct Nav2 goal

free_fleet を経由せず Robot 単体で試すとき:

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

ros2 action send_goal /robot2/navigate_to_pose nav2_msgs/action/NavigateToPose \
"{pose: {header: {frame_id: map}, pose: {position: {x: -1.25, y: -0.55, z: 0.0}, orientation: {w: 1.0}}}}"
```

## 13. Host 側 status helper

```bash
~/turtlebot4_ws/scripts/robot2_status.sh
```

## 14. Robot 側 map 保存（`/robot2/map`）

`map_saver_cli` が `/map` 前提だと失敗することがあるので、
この環境では `/robot2/map` を明示して保存する。

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

mkdir -p /home/ubuntu/maps/tb4
ros2 run nav2_map_server map_saver_cli \
  -f /home/ubuntu/maps/tb4/tb4_map_20260518 \
  --ros-args -r map:=/robot2/map
```

## 15. Robot 側 Nav2 単体切り分け

RMF を挟む前に、実機単体で Nav2 が通るか確認する。

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

ros2 action send_goal /robot2/navigate_to_pose nav2_msgs/action/NavigateToPose \
"{pose: {header: {frame_id: map}, pose: {position: {x: -1.90, y: -0.50, z: 0.0}, orientation: {w: 1.0}}}}"
```

## 16. Host 側 dispatch（`rmf_main_ws`）

`rmf_demos_tasks` を build 済みなら、Host 側から waypoint 指定で投げられる。

```bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash
source ~/fleet_adapter_template_tb4_ws/install/setup.bash

ros2 run rmf_demos_tasks dispatch_go_to_place -F tb4_fleet -R robot2 -p LP1
```
