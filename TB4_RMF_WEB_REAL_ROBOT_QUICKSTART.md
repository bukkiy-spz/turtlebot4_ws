# TB4 RMF-Web Real Robot Quickstart

この手順は、`turtlebot4_ws` + `fleet_adapter_template_tb4_ws` + `rmf_main_ws` を使って、
`rmf-web` から `robot2` 実機へ移動タスクを投入するための最短手順です。

対象:
- 実機: `robot2` (`tb4_fleet`)
- place 名: `LP1`, `LP2`, `LP3`, `pre_dock`, `robot2_charger`

注意:
- `L1` は階名なので dispatch 先には使えません。
- `source ~/turtlebot4_ws/scripts/robot2_env.bash` を実行すると CWD が `~/turtlebot4_ws` に変わります。

## 1. 端末の役割

Terminal A (実機 SSH):
- 実機の ROS 基盤確認用 (`turtlebot4-source`、topic 確認など)

Terminal B (PC):
- `localization` と `Nav2` を起動したまま保持

Terminal C (PC):
- `schedule` / `dispatcher` / `adapter` / `rmf-web api` / `rmf-web dashboard` を起動

Terminal D (PC, 任意):
- 疎通確認・トラブル切り分け用

Browser:
- `http://localhost:3000` で task 作成

## 2. 事前条件チェック

### 2-1. 実機 SSH 側 (Terminal A)

最低条件:
- `turtlebot4-source` 済み
- 実機 topic が生きている

### 2-2. PC 側で localization / Nav2 を起動 (Terminal B)

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_localization_compat.launch.py \
  map:=$HOME/maps/robot2_map.yaml
```

別ターミナルで:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py
```

必要なら RViz で `2D Pose Estimate` を入れて `amcl_pose` を安定させる。

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_rviz.launch.py \
  rviz_config:=$(ros2 pkg prefix tb4_square --share)/rviz/robot2_slam.rviz \
  use_sim_time:=false \
  tf_topic:=/robot2/tf_nav
```

### 2-3. PC 側の疎通確認 (Terminal D など)

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
timeout 5 ros2 topic echo /robot2/amcl_pose --once
ros2 action list | grep /robot2/navigate_to_pose
timeout 5 ros2 topic echo /robot2/battery_state --once
```

3つとも通れば、RMF 側へ進めます。

## 3. 初回だけのセットアップ

### 3-1. build

```bash
cd ~/rmf_main_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select rmf_demos_tasks

cd ~/fleet_adapter_template_tb4_ws
source /opt/ros/humble/setup.bash
source ~/rmf_main_ws/install/setup.bash
colcon build --packages-select tb4_fleet_adapter
```

### 3-2. 地図を更新した場合だけ同期

```bash
cd ~/fleet_adapter_template_tb4_ws
python3 scripts/sync_robot_map_to_rmf.py --also-latest
```

### 3-3. rmf-web 未導入なら install

```bash
cd ~/rmf_main_ws
./scripts/install_rmf_web_humble.sh
```

## 4. 本番起動 (毎回)

Terminal C:

```bash
cd ~/rmf_main_ws
./scripts/rmf_web_stack_up.sh
./scripts/rmf_web_stack_status.sh
```

この 5 プロセスが `running` なら OK:
- schedule
- dispatcher
- adapter
- api
- dashboard

URL:
- Dashboard: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

起動確認 (推奨):

```bash
curl -sS http://localhost:8000/fleets
curl -sS http://localhost:8000/building_map
curl -sS "http://localhost:8000/tasks?limit=10"
```

## 5. rmf-web から移動タスクを投げる

Browser (`http://localhost:3000`):

1. `Tasks` タブを開く
2. `New Task` を押す
3. Dispatch の移動タスク (Go to place 系) を選ぶ
4. `fleet: tb4_fleet`
5. `robot: robot2`
6. `place: LP1` (または `LP2`, `LP3`, `pre_dock`, `robot2_charger`)
7. Submit

実機が動けば成功です。

補足:

- バッテリーが 20% 未満のときは `Charge Battery` が優先され、移動タスクは進みにくい
- 現在の安定運用値: `recharge_threshold=0.15`, `recharge_soc=0.2`

## 6. 停止

Terminal C:

```bash
cd ~/rmf_main_ws
./scripts/rmf_web_stack_down.sh
```

## 7. よくある詰まりどころ

`Dashboard は開くが Network Error`:

```bash
curl -sSf http://localhost:8000/docs >/dev/null && echo "api ok"
```

`adapter が schedule 待ちで進まない`:
- `schedule` を先に起動する
- 一括起動なら `rmf_web_stack_up.sh` を使う

`System Overview にロボット/マップが出ない`:
- `curl /fleets` と `curl /building_map` で API 応答を確認
- `rmf_web_stack_down.sh -> up.sh` で再起動
- ブラウザを再読み込み

`Failed to create task: 500`:
- `dispatcher` / `adapter` / `api` の稼働を `rmf_web_stack_status.sh` で確認
- 必要なら stack を再起動

`dispatch は通るが実機が動かない`:
- `/robot2/amcl_pose`
- `/robot2/navigate_to_pose`
- `/robot2/battery_state`
を再確認する

`Charge Battery` が `standby` で止まる:
- `curl -sS http://localhost:8000/fleets` で `battery` を確認
- `battery < 0.2` なら仕様動作 (20% 到達まで充電優先)

`L1` を投げて失敗する:
- `LP1` など waypoint 名を使う

## 8. 参照コマンド集

- `~/turtlebot4_ws/TB4_FREE_FLEET_REAL_ROBOT_COMMANDS.md`
- `~/fleet_adapter_template_tb4_ws/TB4_FLEET_ADAPTER_COMMANDS.md`
- `~/rmf_main_ws/RMF_MAIN_WS_COMMANDS.md`
