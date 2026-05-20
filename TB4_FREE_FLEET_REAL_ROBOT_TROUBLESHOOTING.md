# TB4 Real Robot Troubleshooting

このファイルは、`turtlebot4_ws` から `robot2` 実機を直接扱うときの詰まりどころをまとめたものです。

## 1. RViz に `No map received` が出る

まず `SLAM` 自体が起動しているかを見る。

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic list | grep /robot2/map
timeout 5 ros2 topic echo /robot2/map --once
```

対処:

- `./scripts/robot2_slam.sh` を使う
- `Map` display の topic を `/robot2/map` にする
- `Fixed Frame` を `map` にする

## 2. `Message Filter dropping message ... queue is full`

意味:

- `RViz` が `scan` や `odom` を `map` へ変換したい
- でも `map -> odom` がまだ無い、または TF topic が違う

確認:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 5 ros2 topic echo /robot2/map --once
timeout 5 ros2 run tf2_ros tf2_echo map odom \
  --ros-args -r /tf:=/robot2/tf_nav -r /tf_static:=/robot2/tf_static
```

対処:

- `SLAM` 中は数秒だけ出るのは珍しくない
- `localization` / `Nav2` では RViz を `tf_topic:=/robot2/tf_nav` で開く
- `initial pose` を入れて `map -> odom` を作る

## 3. RViz の Robot Model が `No transform from ...`

典型原因:

- `localization` / `Nav2` 段階で `/robot2/tf` を見ている
- 本当は `/robot2/tf_nav` を見るべき

正しい起動:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_rviz.launch.py \
  rviz_config:=$(ros2 pkg prefix tb4_square --share)/rviz/robot2_slam.rviz \
  use_sim_time:=false \
  tf_topic:=/robot2/tf_nav
```

## 4. `map_server/get_state timed out`

これは `map_server` 自体ではなく、lifecycle bringup 側の待ち方で起きていた。

現状:

- `tb4_square/lifecycle_bringup_retry.py` 側を修正済み
- `robot2_localization_compat.launch.py` を使えばよい

再起動:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_localization_compat.launch.py \
  map:=$HOME/maps/robot2_map.yaml
```

## 5. Nav2 起動時に `"spin" action server not available`

原因:

- 既定 BT が recovery 用 `spin` action server を要求していた

現状:

- `robot2_nav2_compat.launch.py` で repo 内の `no_recovery` BT を明示指定済み

使うコマンド:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py
```

## 6. `initial pose` が入らない

確認:

- `RViz` の `Fixed Frame` が `map`
- `2D Pose Estimate` の topic が `/robot2/initialpose`
- `localization` が起動済み

CLI での代替:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 3 ros2 topic pub /robot2/initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
"{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}, covariance: [0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.068]}}" \
--rate 5 \
--qos-reliability best_effort
```

## 7. direct Nav2 goal は通るが RMF へ進めない

まず `robot2` 単体の最低条件を再確認する。

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 5 ros2 topic echo /robot2/amcl_pose --once
ros2 action list | grep /robot2/navigate_to_pose
```

これが通らない間は `fleet adapter` 側を見ても詰まりやすい。

## 8. `SLAM` と `AMCL` を同時に動かしてしまった

対処:

1. `teleop` を止める
2. `SLAM` を止める
3. `localization` を起動し直す
4. `initial pose` を入れ直す
5. `Nav2` を起動する

`SLAM` 中に保存した map を使う段階では、`SLAM` と `AMCL` は分ける。
