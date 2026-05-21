# TB4 Real Robot Troubleshooting

このファイルは、`turtlebot4_ws` から `robot2` 実機を `localization -> Nav2 -> RMF` まで通すときの詰まりどころをまとめたものです。

## 1. RViz に `No map received` が出る

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic list | grep /robot2/map
timeout 5 ros2 topic echo /robot2/map --once
```

対処:

- `./scripts/robot2_slam.sh` で map が出ているか確認する
- `Map` display の topic を `/robot2/map` にする
- `Fixed Frame` を `map` にする

## 2. `Message Filter dropping message ... queue is full`

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

## 3. `initial pose` が入らない

確認:

- `RViz` の `Fixed Frame` が `map`
- `2D Pose Estimate` の topic が `/robot2/initialpose`
- `localization` が起動済み

CLI 代替:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 3 ros2 topic pub /robot2/initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
"{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}, covariance: [0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.068]}}" \
--rate 5 \
--qos-reliability best_effort
```

## 4. `worldToMap failed` / `goal is off the global costmap`

意味:

- RMF / adapter から送られたゴールが、実機 `map` 座標系でコストマップ外にある

典型原因:

- `reference_coordinates` が古い
- nav graph を `RMF` 座標のまま見ている
- waypoint 実測値の再取得前に adapter を使っている

確認:

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/plot_tb4_map_navgraph.py \
  --use-robot-frame \
  --topic /robot2/amcl_pose \
  --save ~/obs_recording/tb4_20260521_overlay_robot_frame_latest.png
```

## 5. RViz の MarkerArray が見えない

確認:

```bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash
source ~/turtlebot4_ws/scripts/robot2_env.bash
ros2 topic info /tb4/nav_graph_markers -v
ros2 topic echo /tb4/nav_graph_markers --once
```

対処:

- publisher は `python3 ~/fleet_adapter_template_tb4_ws/scripts/publish_nav_graph_markers.py --use-robot-frame`
- `robot2_env.bash` を source すると `~/turtlebot4_ws` に `cd` されるので、helper script は絶対パスで呼ぶ
- RViz の `Fixed Frame` は `map`
- `MarkerArray` display の topic は `/tb4/nav_graph_markers`

## 6. `record_reference_pose.py` や `plot_tb4_map_navgraph.py` が見つからない

原因:

- `source ~/turtlebot4_ws/scripts/robot2_env.bash` の後で CWD が `~/turtlebot4_ws` へ変わっている

対処:

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/record_reference_pose.py --label LP1
python3 ~/fleet_adapter_template_tb4_ws/scripts/plot_tb4_map_navgraph.py --use-robot-frame
```

## 7. `SLAM` と `AMCL` を同時に動かしてしまった

対処:

1. `teleop` を止める
2. `SLAM` を止める
3. `localization` を起動し直す
4. `initial pose` を入れ直す
5. `Nav2` を起動する

## 8. direct Nav2 goal は通るが RMF 経由だと変な動きをする

今の既知制約:

- `finishing_request: park` により、タスク完了後に駐機系の要求が出る
- charger lane は `pre_dock -> robot2_charger`
- ただし `dock()` / `start_process()` は実機 docking 未実装

そのため、見かけ上:

- いったん charger 系へ戻ろうとする
- 目標到達後に `pre_dock` へ戻る

これは `Nav2` の単体故障ではなく、現状の RMF 設定と adapter 実装の組み合わせによるもの。

## 9. `L1` を dispatch して失敗する

原因:

- `L1` は階名であって waypoint 名ではない

現在有効な place 名:

- `LP1`
- `LP2`
- `LP3`
- `pre_dock`
- `robot2_charger`

## 10. RMF に進む前の最低条件

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 5 ros2 topic echo /robot2/amcl_pose --once
ros2 action list | grep /robot2/navigate_to_pose
timeout 5 ros2 topic echo /robot2/battery_state --once
```

## 11. Nav2 の安全距離を見直したい

現在の `robot2` 用 Nav2 設定ファイル:

- `~/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml`

まず触る候補:

- `local_costmap.local_costmap.ros__parameters.inflation_layer.inflation_radius`
- `global_costmap.global_costmap.ros__parameters.inflation_layer.inflation_radius`

今は `0.45 -> 0.30` にしてある。  
物理サイズを直接小さく見せる `robot_radius` は、接触リスクが上がるので後回し推奨。

よく使う値の見方:

- `inflation_radius`
  障害物の周囲にどれだけ安全マージンを広げるか。狭い通路を通りにくいときはまずここを見る。
- `cost_scaling_factor`
  障害物に近づいたとき、どれだけ急に「危険」と判定するか。大きいほど壁際を強く嫌う。
- `robot_radius`
  ロボット本体を Nav2 が何 m の円として扱うか。ここを小さくしすぎると実機接触に直結しやすい。

症状ごとの当たり先:

- 狭い通路の手前で止まりやすい
  `inflation_radius` を少し下げる
- 通れるが壁から離れすぎて大回りする
  `cost_scaling_factor` を少し下げる
- 壁や棚に実機が近づきすぎる
  `inflation_radius` を戻すか、`cost_scaling_factor` を上げる
- ゴール近傍で細かく行ったり来たりする
  `xy_goal_tolerance` / `yaw_goal_tolerance` や `RotateToGoal.*` を見る
- 進路は合っているのに「動いていない」と扱われて abort する
  `progress_checker.required_movement_radius` と `movement_time_allowance` を見る
- 局所的に避け切れずに苦しそう
  `local_costmap.width` / `height`、`BaseObstacle.scale`、`sim_time` も候補

編集後の起動:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py
```

この launch は既定で `~/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml` を読む。

## 12. `robot2_env.bash` の後に helper script が動かない

原因:

- `source ~/turtlebot4_ws/scripts/robot2_env.bash` が最後に `cd ~/turtlebot4_ws` を行う

そのため:

- `~/fleet_adapter_template_tb4_ws` で使うつもりだった相対パス script が見つからなくなる

対処:

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/record_reference_pose.py --label LP1
python3 ~/fleet_adapter_template_tb4_ws/scripts/publish_nav_graph_markers.py --use-robot-frame
python3 ~/fleet_adapter_template_tb4_ws/scripts/plot_tb4_map_navgraph.py --use-robot-frame
```

## 13. RMF の place に `L1` を送って失敗する

原因:

- `L1` は階名で、place 名ではない

現在使う名前:

- `LP1`
- `LP2`
- `LP3`
- `pre_dock`
- `robot2_charger`

## 14. goal 後に charger / pre_dock へ戻ろうとする

主因:

- `tb4_fleet_adapter/config.yaml` の `finishing_request: park`
- nav graph 上で charger 系が `pre_dock -> robot2_charger` の dock lane
- adapter 側の実機 docking 処理が未実装

そのため現状では:

- 目標値へ行った後に駐機系要求が追加される
- 見かけ上 `pre_dock` 側へ戻ろうとする
- 次タスク開始時も charger 系を意識した経路に見えることがある

これは Nav2 単体の故障ではなく、RMF 設定と adapter 実装の組み合わせによる既知挙動。
