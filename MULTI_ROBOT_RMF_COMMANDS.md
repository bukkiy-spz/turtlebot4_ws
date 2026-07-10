# Multi Robot RMF Commands

ホスト側でサーバを立ち上げる
```bash
cd ~/turtlebot4_ws
./scripts/start_shared_discovery_server.sh 192.168.11.104 11811
```

このファイルは、`robot2` `robot5` `robot6` を

- 1つの地図
- 1つの RMF
- 1つの rmf-web

で扱うときの、実運用向けコマンド集です。

対象の現行構成:

- map: `~/rmf_main_ws/maps/tb4_rebuild_20260612`
- adapter config: `~/fleet_adapter_template_tb4_ws/src/tb4_fleet_adapter/config_tb4_20260612_multi.yaml`
- adapter wrapper: `~/fleet_adapter_template_tb4_ws/scripts/run_direct_adapter_tb4_20260612.sh`

## 1. 先に前提確認

### 1-0. multi-robot adapter 用の共通 env

1本の adapter process で `robot2/5/6` を同時に扱うときは、個別の
`robot2_env.bash` ではなく、3台分の onboard discovery server に同時接続する
共通 env を使います。

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/shared_multi_robot_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot[256]/'
```

ここで `robot2`, `robot5`, `robot6` の topic が同じシェルから見えることが重要です。

### 1-1. 3台とも host から見えるか

`robot2`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 topic list | grep '^/robot2/'
ros2 action list | grep '/robot2/'
```

`robot5`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 topic list | grep '^/robot5/'
ros2 action list | grep '/robot5/'
```

`robot6`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 topic list | grep '^/robot6/'
ros2 action list | grep '/robot6/'
```

最低限見たいもの:

- `/robotX/amcl_pose`
- `/robotX/navigate_to_pose`
- `/robotX/dock`
- `/robotX/undock`
- `/robotX/battery_state`

注意:

- 現在の `robot2_env.bash`, `robot5_env.bash`, `robot6_env.bash` は robot ごとに個別 discovery 接続です
- 1本の multi-robot adapter を本番運用する前に、adapter を起動するホスト側 graph から `robot2/5/6` 全部が見えることを必ず確認してください
- もし 1つの adapter 起動シェルから `robot2` しか見えない場合は、discovery 構成の再確認が必要です

## 2. robot2 を localization + Nav2 で起動

### 2-1. localization

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_localization_compat.launch.py \
  namespace:=robot2 \
  map:=/home/masu_ubu/maps/robot2_map.yaml \
  use_sim_time:=false
```

### 2-2. RViz で初期姿勢

```bash
cd ~/turtlebot4_ws
./scripts/robot2_localization_rviz.sh
```

#### 2-2-2. Nav Graph Markers

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/shared_multi_robot_env.bash
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash
source ~/fleet_adapter_template_tb4_ws/install/setup.bash

python3 ~/fleet_adapter_template_tb4_ws/scripts/publish_nav_graph_markers.py \
  --nav-graph ~/rmf_main_ws/maps/tb4_rebuild_20260612/nav_graphs/0.yaml \
  --config ~/fleet_adapter_template_tb4_ws/src/tb4_fleet_adapter/config_tb4_20260612_multi.yaml \
  --level L1 \
  --frame-id map \
  --topic /tb4/nav_graph_markers \
  --use-robot-frame
```

### 2-3. Nav2

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py \
  namespace:=robot2 \
  params_file:=/home/masu_ubu/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml \
  use_sim_time:=false
```

### 2-4. 確認

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 lifecycle get /robot2/amcl
ros2 lifecycle get /robot2/map_server
ros2 lifecycle get /robot2/controller_server
ros2 lifecycle get /robot2/planner_server
ros2 action list | grep '/robot2/navigate_to_pose'
```

## 3. robot5 を localization + Nav2 で起動

### 3-1. localization

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 launch tb4_square robot2_localization_compat.launch.py \
  namespace:=robot5 \
  map:=/home/masu_ubu/maps/robot2_map.yaml \
  use_sim_time:=false
```

### 3-2. RViz で初期姿勢

```bash
cd ~/turtlebot4_ws
./scripts/robot5_localization_rviz.sh
```

### 3-3. Nav2

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py \
  namespace:=robot5 \
  params_file:=/home/masu_ubu/turtlebot4_ws/src/tb4_square/config/robot5_nav2.yaml \
  use_sim_time:=false
```

### 3-4. 確認

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 lifecycle get /robot5/amcl
ros2 lifecycle get /robot5/map_server
ros2 lifecycle get /robot5/controller_server
ros2 lifecycle get /robot5/planner_server
ros2 action list | grep '/robot5/navigate_to_pose'
```

## 4. robot6 を localization + Nav2 で起動

### 4-1. localization

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 launch tb4_square robot2_localization_compat.launch.py \
  namespace:=robot6 \
  map:=/home/masu_ubu/maps/robot2_map.yaml \
  use_sim_time:=false
```

### 4-2. RViz で初期姿勢

```bash
cd ~/turtlebot4_ws
./scripts/robot6_localization_rviz.sh
```

### 4-3. Nav2

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py \
  namespace:=robot6 \
  params_file:=/home/masu_ubu/turtlebot4_ws/src/tb4_square/config/robot6_nav2.yaml \
  use_sim_time:=false
```

### 4-4. 確認

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 lifecycle get /robot6/amcl
ros2 lifecycle get /robot6/map_server
ros2 lifecycle get /robot6/controller_server
ros2 lifecycle get /robot6/planner_server
ros2 action list | grep '/robot6/navigate_to_pose'
```

## 5. RMF schedule / adapter / dispatch

### 5-1. schedule 起動

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_schedule.sh
```

### 5-2. adapter 起動

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_adapter_tb4_20260612.sh
```

注意:

- この adapter は `config_tb4_20260612_multi.yaml` を使います
- この wrapper は既定で `~/turtlebot4_ws/scripts/shared_multi_robot_env.bash` を source します
- `reference_coordinates.rmf` と `reference_coordinates.robot` が埋まっていないと起動を止めます

### 5-3. dispatch 例

`robot2 -> LP1`:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh LP2 robot2
```

`robot5 -> LP2`:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh LP1 robot5
```

`robot6 -> LP4`:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh LP4 robot6
```

### 5-4. dispatch できる place 例

- `LP1`
- `LP2`
- `LP3`
- `LP4`
- `robot2_charger`
- `robot5_charger`
- `robot6_charger`
- `robot2_predock`
- `robot5_predock`
- `robot6_predock`

`L1` は階名なので dispatch の place 引数には使いません。

## 6. ドッキング確認

今回の構成では、最後のドッキング動作は `Create3` の native `Dock` action を使います。  
つまり、以前と同じく **Create3 と充電ドックの赤外線通信を利用したドッキング** を前提にしています。

さらに現在の multi-robot config では、

- `use_native_dock_action: true`
- `require_recent_ir_opcode_for_dock: true`
- `ir_opcode_min_count: 2`

にしてあるため、adapter 側も「最近 IR を見ていること」を条件に使います。

## 6-1. まずは native dock action が見えるか

`robot2`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 action list | grep '/robot2/dock'
ros2 action list | grep '/robot2/undock'
```

`robot5`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 action list | grep '/robot5/dock'
ros2 action list | grep '/robot5/undock'
```

`robot6`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 action list | grep '/robot6/dock'
ros2 action list | grep '/robot6/undock'
```

## 6-2. 直接 dock action を試す

`robot2`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 action send_goal /robot2/dock irobot_create_msgs/action/Dock "{}"
```

`robot5`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 action send_goal /robot5/dock irobot_create_msgs/action/Dock "{}"
```

`robot6`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 action send_goal /robot6/dock irobot_create_msgs/action/Dock "{}"
```

undock の例:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 action send_goal /robot5/undock irobot_create_msgs/action/Undock "{}"
```

## 6-2b. IR opcode が見えているか確認

`robot2`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 topic list | grep '/robot2/ir_opcode'
ros2 topic echo /robot2/ir_opcode
```

`robot5`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 topic list | grep '/robot5/ir_opcode'
ros2 topic echo /robot5/ir_opcode
```

`robot6`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 topic list | grep '/robot6/ir_opcode'
ros2 topic echo /robot6/ir_opcode
```

見たいこと:

- dock 正面付近で `ir_opcode` が流れる
- その状態で direct `Dock` action が成功する

## 6-3. RMF 経由で charger へ戻す

`robot2` を `robot2_charger` へ:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh robot2_charger robot2
```

`robot5` を `robot5_charger` へ:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh robot5_charger robot5
```

`robot6` を `robot6_charger` へ:

```bash
cd ~/fleet_adapter_template_tb4_ws
./scripts/run_direct_dispatch_go_to_place.sh robot6_charger robot6
```

期待する流れ:

1. RMF が charger waypoint 近傍までナビゲーション
2. adapter が `/robotX/dock` を呼ぶ
3. `dock_status` と charging 状態が揃えば dock 完了扱い

確認:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 topic echo /robot5/dock_status
```

## 7. rmf-web 起動

## 7-1. 未導入なら install

```bash
cd ~/rmf_main_ws
./scripts/install_rmf_web_humble.sh
```

## 7-2. まとめて起動

```bash
cd ~/rmf_main_ws
./scripts/rmf_web_stack_up.sh
```

このスクリプトは現在:

- `schedule`
- `dispatcher`
- `adapter`
- `api`
- `dashboard`

をまとめて起動します。  
`adapter` は既定で `run_direct_adapter_tb4_20260612.sh` を使うようにしてあります。

## 7-3. 状態確認

```bash
cd ~/rmf_main_ws
./scripts/rmf_web_stack_status.sh
```

## 7-4. 停止

```bash
cd ~/rmf_main_ws
./scripts/rmf_web_stack_down.sh
```

## 7-5. 直接 API / Dashboard を個別起動

API:

```bash
cd ~/rmf_main_ws
./scripts/run_rmf_web_api.sh
```

Dashboard:

```bash
cd ~/rmf_main_ws
./scripts/run_rmf_web_dashboard.sh
```

URL:

- Dashboard: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

## 8. rmf-web から dispatch

起動順:

1. `robot2/5/6` の localization
2. `robot2/5/6` の Nav2
3. `schedule`
4. `adapter`
5. `api`
6. `dashboard`

その後:

1. `http://localhost:3000` を開く
2. fleet で `tb4_fleet` を選ぶ
3. robot で `robot2` `robot5` `robot6` を選ぶ
4. place で `LP1`, `LP2`, `LP4`, `robotX_charger` などを選ぶ
5. dispatch する

## 9. よく使う確認コマンド

`robot2`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot2_env.bash
ros2 topic echo /robot2/amcl_pose --once
ros2 topic echo /robot2/battery_state --once
ros2 topic echo /robot2/dock_status --once
```

`robot5`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot5_env.bash
ros2 topic echo /robot5/amcl_pose --once
ros2 topic echo /robot5/battery_state --once
ros2 topic echo /robot5/dock_status --once
```

`robot6`:

```bash
cd ~/turtlebot4_ws
source install/setup.bash
source scripts/robot6_env.bash
ros2 topic echo /robot6/amcl_pose --once
ros2 topic echo /robot6/battery_state --once
ros2 topic echo /robot6/dock_status --once
```

rmf-web logs:

```bash
tail -n 120 ~/rmf_main_ws/log/rmf_web_stack/schedule.log
tail -n 120 ~/rmf_main_ws/log/rmf_web_stack/adapter.log
tail -n 120 ~/rmf_main_ws/log/rmf_web_stack/api.log
tail -n 120 ~/rmf_main_ws/log/rmf_web_stack/dashboard.log
```

## 10. 今回の実運用上のポイント

- `robot2` の SLAM map を 3台共通 map として使う方針でよいです
- `traffic-editor` で作った charger waypoint 名と adapter config の charger waypoint 名は一致させてください
- `robot2_charger`, `robot5_charger`, `robot6_charger` は各 robot 専用にしてあります
- 直接 `Dock` action が成功することを先に確認してから RMF docking を試すと切り分けがかなり楽です
- 1本の adapter で 3台を同時に扱うには、adapter 起動シェルから `robot2/5/6` 全部が見えていることが絶対条件です
