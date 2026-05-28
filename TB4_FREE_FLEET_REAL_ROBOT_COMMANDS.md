# TB4 Real Robot Commands

このファイルは、`turtlebot4_ws` から `robot2` 実機を `SLAM -> localization -> Nav2 -> RMF接続 -> dispatch確認` まで通すための本線手順です。  
現在の実マップは `tb4_20260521`、RMF 側の nav graph は `~/rmf_main_ws/maps/tb4_rebuild_20260521/nav_graphs/0.yaml` を使います。
※turtlebot4_wsのCOMMANDS.mdの#10までやってから以下を進めること(以下に#10までを載せています)

# TurtleBot4 コマンドメモ

このファイルは、`TurtleBot4` 実機や `Gazebo / Ignition` シミュレーションを動かすときのメモです。  
「どちらの端末で打つか」が分かるように、`PC側` と `実機側` を分けてあります。

## 0. まず確認すること

- `VSCode Remote-SSH` で開いたターミナル:
  基本的に `実機側`
- 普通の端末アプリで開いたローカル端末:
  `PC側`
- 今後のおすすめ運用:
  `Humble` 用と `Jazzy` 用で `VSCode` のウィンドウ自体を分ける
- 迷ったら次で確認

```bash
hostname
whoami
pwd
```

`VSCode` を分ける例:

- `Humble` 用ウィンドウ:
  `~/turtlebot4_ws` を開く
- `Jazzy/free_fleet` 用ウィンドウ:
  Docker コンテナに接続して `~/jazzy_ff_ws` を開く

このやり方だと、どちらの `ROS` を使っているか視覚的に分かりやすく、`source /opt/ros/humble/setup.bash` と `source /opt/ros/jazzy/setup.bash` を混ぜにくいです。

## 1. PC側: 実機に SSH 接続する

```bash
ssh ubuntu@192.168.11.22
```

## 2. PC側: 実機に届くか確認する

```bash
ping 192.168.11.22
```

## 3. 実機側: IP アドレスを確認する

```bash
hostname -I
ip addr
```

## 4. 実機側: TurtleBot4 の ROS 環境を読み込む

```bash
turtlebot4-source
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION
echo $ROS_DISCOVERY_SERVER
```

## 5. 実機側: ROS デーモンを更新する

```bash
turtlebot4-source
turtlebot4-daemon-restart
```

## 6. 実機側: 実機の主要トピックを確認する

```bash
ros2 topic list | head
ros2 topic list | grep robot2
ros2 topic list | grep cmd_vel
ros2 topic list | grep tf
```

## `cmd_vel` がなければ再起動

```bash
sudo reboot
```

## 7. PC側: ROS 通信設定を入れる

毎回新しい PC 側ターミナルを開いたら、まずこれを実行します。
実機側で `ROS_DISCOVERY_SERVER=127.0.0.1:11811;` と出る場合でも、PC側では `127.0.0.1` ではなく実機のIPアドレスを指定します。

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 daemon stop
ros2 daemon start
```

設定が入っているか確認するには次を使います。

```bash
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION
echo $ROS_DISCOVERY_SERVER
```

## 8. PC側: 実機のトピックが見えているか確認する

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic list | grep robot2
ros2 topic list | grep cmd_vel
ros2 topic list | grep tf
```

## 9. PC側: ワークスペースの基本セットアップ

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## 10. PC側: パッケージをビルドし直す

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select tb4_square
source install/setup.bash
```


## 1. Host 側 robot2 環境

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
source ~/turtlebot4_ws/scripts/robot2_env.bash
```

注意:

- `source ~/turtlebot4_ws/scripts/robot2_env.bash` は最後に `~/turtlebot4_ws` へ `cd` する
- その後に他ワークスペースの `scripts/*.py` を使うときは、絶対パスで実行するか、実行前に `cd` し直す

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

現在の既定 `params_file` は  
`~/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml`。

このファイルでは、衝突回避の安全距離を少し小さくするために
`local_costmap/global_costmap` の `inflation_radius` を
`0.45 -> 0.30` へ変更してある。

よく触る場所:

- `inflation_radius`
  障害物まわりに取る安全マージン
- `cost_scaling_factor`
  障害物に近づいたときの嫌い方
- `xy_goal_tolerance`, `yaw_goal_tolerance`
  ゴール到達とみなす許容誤差
- `progress_checker.*`
  動いていない判定のしきい値

編集するとき:

```bash
sed -n '1,260p' ~/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml
```

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py
```

別の Nav2 設定ファイルを使いたいとき:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py \
  params_file:=/home/masu_ubu/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml
```

まずは既定ファイルを直接調整して、変更後に launch を再起動して挙動を見るのが一番追いやすい。
Lifecycle bringup completed.とログの最後に出ていれば起動OK．

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
"{pose: {header: {frame_id: map}, pose: {position: {x: -0.42, y: -0.25, z: 0.0}, orientation: {z: 0.989, w: 0.147}}}}"
```

`reference_coordinates.robot` の実測値:

- `robot2_charger`: `[-0.290396, -0.098816]`
- `pre_dock`: `[-0.418503, -0.247466]`
- `LP1`: `[-1.571370, -0.764647]`
- `LP2`: `[-2.408269, 0.591567]`
- `LP3`: `[-1.234636, 1.099470]`

## 10. RMF 側へ保存 map を同期する

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/sync_robot_map_to_rmf.py --also-latest
```

## 11. nav graph / map の重なりを確認する

画像で確認:

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/plot_tb4_map_navgraph.py \
  --use-robot-frame \
  --topic /robot2/amcl_pose \
  --save ~/obs_recording/tb4_20260521_overlay_robot_frame_latest.pngcd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_schedule.sh
```

RViz で waypoint / charger / lane を表示:

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/publish_nav_graph_markers.py \
  --use-robot-frame
```

RViz 側:

- `Fixed Frame` を `map`
- `MarkerArray` display を追加
- topic を `/tb4/nav_graph_markers`

## 12. RMF 用パッケージを build する

```bash
cd ~/rmf_main_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select rmf_demos_tasks

cd ~/fleet_adapter_template_tb4_ws
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash
colcon build --packages-select tb4_fleet_adapter
```

## 13. RMF へ渡す

別端末 1:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_schedule.sh
```

別端末 2:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_adapter.sh
```

別端末 3:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh LP1
```

有効な waypoint 名:

- `LP1`
- `LP2`
- `LP3`
- `pre_dock`
- `robot2_charger`

## 14. RMF 接続の確認

```bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash
source ~/fleet_adapter_template_tb4_ws/install/setup.bash
source ~/turtlebot4_ws/scripts/robot2_env.bash

ros2 topic list | grep /fleet_states
ros2 node list | grep tb4_fleet
timeout 5 ros2 topic echo /fleet_states --once
```

## 15. 反復の動作確認

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_tb4_rebuild_20260521_checks.sh
```

## 16. 現在の既知制約

- `config.yaml` の `finishing_request` は `park`
- nav graph の charger 進入は `pre_dock -> robot2_charger` の dock lane
- ただし `dock()` / `start_process()` は実機の本物の docking を未実装
- そのため、RMF タスク後に `pre_dock` / charger 系へ戻ろうとする挙動が見えることがある

## 17. 最低限の生存確認

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic list | rg '^/robot2/(amcl_pose|map|tf_nav|battery_state)$'
ros2 action list | grep /robot2/navigate_to_pose
timeout 5 ros2 topic echo /robot2/amcl_pose --once
```
