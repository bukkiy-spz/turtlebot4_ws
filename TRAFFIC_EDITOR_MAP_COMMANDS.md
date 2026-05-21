# Traffic Editor Map Workflow (TB4 + RMF)

このメモは、最新の SLAM マップを使って `traffic-editor` で LP/チャージャー/壁を設定し、RMF 用の地図データを作るための実行手順です。

## 0. 前提

- 実機で SLAM 済みで、保存済み地図がある
- このワークスペースの `robot2` 運用手順を使う
- RMF 側は `traffic-editor` (legacy) を利用する

## 1. まず実機側の地図座標を固定する

`traffic-editor` に入る前に、保存地図で localization と Nav2 の単体確認を通す。

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
source ~/turtlebot4_ws/scripts/robot2_env.bash

# 保存地図で localization
ros2 launch tb4_square robot2_localization_compat.launch.py \
  map:=$HOME/maps/robot2_map.yaml
```

別端末:

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
source ~/turtlebot4_ws/scripts/robot2_env.bash

# Nav2
ros2 launch tb4_square robot2_nav2_compat.launch.py
```

補足:

- `robot2_nav2_compat.launch.py` の既定 `params_file` は `~/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml`
- まずは `inflation_radius` を小さくして安全距離を調整し、`robot_radius` は最後に触る方が安全

確認:

```bash
source ~/turtlebot4_ws/scripts/robot2_env.bash
timeout 5 ros2 topic echo /robot2/amcl_pose --once
ros2 action list | rg /robot2/navigate_to_pose
```

## 2. traffic-editor の起動準備

まず `traffic-editor` が使えるか確認:

```bash
source /opt/ros/humble/setup.bash
command -v traffic-editor
```

見つからない場合は、`rmf_traffic_editor` を Humble ブランチでビルドする。

```bash
mkdir -p ~/rmf_main_ws/src
cd ~/rmf_main_ws/src
git clone -b humble https://github.com/open-rmf/rmf_traffic_editor.git

cd ~/rmf_main_ws
source /opt/ros/humble/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
sudo apt install -y python3-shapely python3-yaml python3-requests
colcon build --symlink-install
```

起動:

```bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash
traffic-editor
```

## 3. traffic-editor での編集手順

1. `Building -> New...` で `*.building.yaml` を作成（Reference-image coordinatesを選択）
2. `levels` で floorplan 画像を読み込む
3. `measurements` を必ず入れて縮尺を合わせる
4. 必要なら `layers` で SLAM 画像オーバレイを重ねる
5. `vertices/lanes` で LP/動線を作る
6. チャージャー頂点に `is_charger=true` を付ける
7. カスタムドックなら `dock_name` も設定する
8. `walls` は固定設備のみ引く

## 4. LP/チャージャー/壁の注意点

- SLAM 更新後は origin や向きが少しでも変わると LP/チャージャー位置がずれる。再アライン前提で作業する。
- `SLAM` 実行中と `localization/Nav2` を同時起動しない。
- 実機初期位置は charger 接触点そのものより、`pre-dock` の手前 LP から入る方が再現性が高い。
- チャージャーへ入る最後の lane は向きを固定する (forward/backward を明示)。
- LP は壁際/狭隘部/ドア可動域の直近を避ける。
- 壁は「常設障害物」のみ。可動棚などは壁化しない。

## 5. 生成コマンド (RMF 用)

`traffic-editor` で保存した `*.building.yaml` から nav graph を生成:

```bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash

mkdir -p ~/rmf_main_ws/maps/tb4_rebuild_20260521/nav_graphs
ros2 run rmf_building_map_tools building_map_generator nav \
  ~/rmf_main_ws/maps/tb4_rebuild_20260521/tb4_20260521.building.yaml \
  ~/rmf_main_ws/maps/tb4_rebuild_20260521/nav_graphs
```

シミュレーション world 生成 (`building_map_generator -h` で `ignition` が無い環境):

```bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash

mkdir -p ~/rmf_main_ws/maps/tb4_rebuild_20260521/world ~/rmf_main_ws/maps/tb4_rebuild_20260521/models
ros2 run rmf_building_map_tools building_map_generator gazebo \
  ~/rmf_main_ws/maps/tb4_rebuild_20260521/tb4_20260521.building.yaml \
  ~/rmf_main_ws/maps/tb4_rebuild_20260521/world/tb4_20260521.world \
  ~/rmf_main_ws/maps/tb4_rebuild_20260521/models
```

補足:

- `building_map_generator -h` の候補が `{gazebo, nav, navgraph_visualization}` の場合は、`ignition` は使えない。
- この場合は `gazebo` サブコマンドで生成した world を使う。
- もし `ignition` を使いたい場合は、`ignition` サブコマンドを含む版の `rmf_traffic_editor/rmf_building_map_tools` をソースビルドする。

参照モデルをダウンロード:

```bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash

ros2 run rmf_building_map_tools building_map_model_downloader \
  ~/rmf_main_ws/maps/tb4_rebuild_20260521/tb4_20260521.building.yaml -f -e ~/.gazebo/models
```

## 6. 最終チェック (RMF に渡す前)

- `initial pose` を `map` フレームで入れる
- LP への `navigate_to_pose` が安定して通る
- `pre-dock -> charger` の順で実機が毎回同じ向きで入れる
- `reference_coordinates` は `robot2_charger / pre_dock / LP1 / LP2 / LP3` の 5 点で取り直す

実行確認コマンド:

```bash
source ~/turtlebot4_ws/scripts/robot2_env.bash
timeout 5 ros2 topic echo /robot2/amcl_pose --once
timeout 5 ros2 topic echo /robot2/map --once
ros2 action list | rg /robot2/navigate_to_pose
```

新マップ (`tb4_20260521`) で RMF dispatch 試験を回すコマンド:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_tb4_rebuild_20260521_checks.sh
```

重なり確認:

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/plot_tb4_map_navgraph.py \
  --use-robot-frame \
  --topic /robot2/amcl_pose \
  --save ~/obs_recording/tb4_20260521_overlay_robot_frame_latest.png
```

RViz 上で waypoint / charger / lane を見る:

```bash
python3 ~/fleet_adapter_template_tb4_ws/scripts/publish_nav_graph_markers.py \
  --use-robot-frame
```

個別に投げる場合:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh LP1
./scripts/run_direct_dispatch_go_to_place.sh LP2
./scripts/run_direct_dispatch_go_to_place.sh LP3
./scripts/run_direct_dispatch_go_to_place.sh pre_dock
./scripts/run_direct_dispatch_go_to_place.sh robot2_charger
```

補足:

- `dispatch_go_to_place` に `L1` は使えない。`L1` は階名で、使うのは waypoint 名。
- 現状の `finishing_request` は `park`。
- charger lane は `pre_dock -> robot2_charger` だが、adapter 側の実機 docking は未実装。
- そのため、タスク後に `pre_dock` / charger 系へ戻ろうとする挙動が見えることがある。

## 7. 参照

- https://osrf.github.io/ros2multirobotbook/traffic-editor.html
- https://osrf.github.io/ros2multirobotbook/integration_nav-maps-strategies.html
- https://github.com/open-rmf/rmf_traffic_editor
- /home/masu_ubu/turtlebot4_ws/TB4_FREE_FLEET_REAL_ROBOT_COMMANDS.md
- /home/masu_ubu/turtlebot4_ws/COMMANDS.md
