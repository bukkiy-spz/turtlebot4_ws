# TB4 Real Robot Commands

このファイルは、`turtlebot4_ws` から `robot2` 実機を直接扱うときの最短コマンド集です。  
現在の本線は、`Host PC` 側で `SLAM`、`localization`、`Nav2` を起動し、そこから `RMF` へ渡す流れです。

## 1. Host 側 robot2 環境

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
source ~/turtlebot4_ws/scripts/robot2_env.bash
```

## 2. 新しい地図を作る

```bash
cd ~/turtlebot4_ws
./scripts/robot2_slam.sh
```

別端末で teleop:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/robot2/cmd_vel
```

## 3. 地図を保存する

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli \
  -f ~/maps/robot2_map \
  --ros-args -r map:=/robot2/map
```

## 4. 保存した地図で localization

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_localization_compat.launch.py \
  map:=$HOME/maps/robot2_map.yaml
```

## 5. localization / Nav2 用 RViz

`localization` と `Nav2` 段階では `tf_topic:=/robot2/tf_nav` を使う。

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_rviz.launch.py \
  rviz_config:=$(ros2 pkg prefix tb4_square --share)/rviz/robot2_slam.rviz \
  use_sim_time:=false \
  tf_topic:=/robot2/tf_nav
```

## 6. initial pose

基本は `RViz` の `2D Pose Estimate` を使う。

- `Fixed Frame` を `map` にする
- 地図上の実機位置をクリックする
- ドラッグで実機の向きを合わせる

CLI の例:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 3 ros2 topic pub /robot2/initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
"{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}, covariance: [0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.068]}}" \
--rate 5 \
--qos-reliability best_effort
```

## 7. localization の確認

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 5 ros2 topic echo /robot2/amcl_pose --once
timeout 5 ros2 run tf2_ros tf2_echo map odom \
  --ros-args -r /tf:=/robot2/tf_nav -r /tf_static:=/robot2/tf_static
```

## 8. Nav2 を起動する

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py
```

確認:

```bash
source ~/turtlebot4_ws/scripts/robot2_env.bash
ros2 action list | grep /robot2/navigate_to_pose
```

## 9. direct goal で単体確認

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 action send_goal /robot2/navigate_to_pose nav2_msgs/action/NavigateToPose \
"{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.5, z: 0.0}, orientation: {w: 1.0}}}}"
```

## 10. RMF へ渡す

`Nav2` の direct goal まで通ったら、次を別端末で使う。

```bash
~/fleet_adapter_template_tb4_ws/scripts/run_direct_schedule.sh
~/fleet_adapter_template_tb4_ws/scripts/run_direct_adapter.sh
~/fleet_adapter_template_tb4_ws/scripts/run_direct_dispatch_go_to_place.sh LP1
```

## 11. 最低限の生存確認

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic list | rg '^/robot2/(amcl_pose|map|tf_nav|battery_state)$'
ros2 action list | grep /robot2/navigate_to_pose
timeout 5 ros2 topic echo /robot2/amcl_pose --once
```
