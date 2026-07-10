# TurtleBot4 追加2台 Q&A

## 2026-06-12 重要修正

- 直近の切り分けで、`robot2/5/6` が再起動後に `/parameter_events` と `/rosout` しか見えない状態になりました
- この症状は host 側ではなく、各 TurtleBot4 の Raspberry Pi 上で `turtlebot4.service` の bringup が正常に上がっていないときの見え方です
- そのため、`ROS_DISCOVERY_SERVER=192.168.11.104:11811` を robot 側で直接 `export` して offboard-only にする方針はいったん撤回します
- まずは各 robot を公式の `turtlebot4-setup` ベース設定に戻して、robot 単体で `/robotX/*` topic が復活することを最優先にしてください

### まずやること

各 robot で、端末の一時 `export` ではなく `turtlebot4-setup` から Discovery 設定をやり直してください。

注意:

- `turtlebot4-daemon-restart` は ROS 2 CLI daemon の再起動です
- robot 本体の bringup をやり直すには `sudo systemctl restart turtlebot4.service` の確認が必要です

推奨の暫定復旧設定:

- `ROS_DOMAIN_ID=0`
- `ROBOT_NAMESPACE=robot2 / robot5 / robot6`
- Discovery Server `Enabled=True`
- Onboard Server Port `11811`
- Onboard Server ID は robot ごとに一意
- Offboard Server IP はひとまず空欄

Onboard Server ID のおすすめ:

- `robot2 -> 2`
- `robot5 -> 5`
- `robot6 -> 6`

これで各 robot 単体 bringup が復旧した後に、あらためて 1つの RMF / 1つの RViz 向けの統合方式を決めるのが安全です。

### 復旧判定の目安

- `robot6` のように `/robotX/cmd_vel`, `/robotX/odom`, `/robotX/tf`, `/robotX/tf_static` が見えている状態を、ひとまずの復旧基準にします
- `robot2` のように `/robotX/scan` だけ見えて `cmd_vel / odom / tf` がない場合は、Create3 側の topic 群が十分に republish されていません
- `robot5` のように node は上がっているのに topic が `/robotX/scan` しか出ない場合は、`create3_repub` や Create3 側接続の異常を疑います

### 2026-06-12 時点の実測メモ

- `robot6`: ほぼ復旧
- `robot2`: `journalctl` と追加 grep では `/robot2/battery_state`, `/robot2/cmd_vel`, `/robot2/imu`, `/robot2/odom`, `/robot2/tf`, `/robot2/tf_static` まで確認できた
- `robot5`: `journalctl` と追加 grep では `/robot5/battery_state`, `/robot5/cmd_vel`, `/robot5/imu`, `/robot5/odom`, `/robot5/tf`, `/robot5/tf_static` まで確認できた
- つまり `robot2/5/6` とも bringup 自体はほぼ戻っており、起動直後の `ros2 topic list` は discovery 収束前で一部 topic が見えないことがある

### 追加で分かったこと

- `ros2 topic list` は 1回目より 2回目以降のほうが完全に見えることがある
- `grep -nE ... /etc/turtlebot4/setup.bash` では `ROS_DISCOVERY_SERVER` が `;;127.0.0.1:11811;` や `;;;;;127.0.0.1:11811;` のように余分な `;` を含んでいた
- 直ちに bringup が壊れている証拠ではないが、設定が汚れているので `turtlebot4-setup` で Discovery Server 設定を保存し直して `127.0.0.1:11811;` に正規化したほうがよい
- `robot5` では過去 boot に `turtlebot4.service` stop timeout が残っているが、今回の active 実行自体は立ち上がっている
- host 側で robot の onboard discovery server に接続する場合、`ROS_DISCOVERY_SERVER` だけでは不十分で、Fast DDS の `SUPER_CLIENT` XML が必要
- `scripts/robot_env_common.bash` は 2026-06-12 時点で、公式 Create3 ドキュメント相当の `SUPER_CLIENT` XML を自動生成するよう修正済み
- そのため host 側では `FASTRTPS_DEFAULT_PROFILES_FILE` と `FASTDDS_DEFAULT_PROFILES_FILE` の両方が同じ生成 XML を指す状態になる
- さらに `SUPER_CLIENT` XML の `RemoteServer prefix` は robot 側 onboard discovery server の Server ID と一致している必要がある
- 2026-06-12 時点で `robot2=2`, `robot5=5`, `robot6=6` を env script 側にも反映済み
- この修正後、host PC から `robot2` の `/robot2/*` topic と node 一式が見えることを実機確認済み

### この状態で次に見るもの

`robot2` と `robot5` で次を確認してください。

```bash
sudo systemctl status turtlebot4.service --no-pager
sudo journalctl -u turtlebot4.service -n 100 --no-pager
ros2 topic list | grep -E '^/robot(2|5)/(cmd_vel|odom|tf|tf_static|imu|battery_state)'
ros2 node list
```

## 今回こちらで追加したもの

- `~/turtlebot4_ws/scripts/robot5_env.bash`
- `~/turtlebot4_ws/scripts/robot6_env.bash`
- `~/turtlebot4_ws/scripts/robot5_{slam,rviz,status,square}.sh`
- `~/turtlebot4_ws/scripts/robot6_{slam,rviz,status,square}.sh`
- `~/turtlebot4_ws/scripts/robot_{slam,rviz,status,square}_generic.sh`
- `~/turtlebot4_ws/scripts/robot_env_common.bash`
- `robot2` 用 launch / RViz / SLAM / Nav2 設定を namespace 再利用しやすい形へ調整

## まず何ができるようになったか

- `robot5` 用と `robot6` 用に、PC 側から source する Discovery Server 環境を分離できる
- `robot2` と同じ系統の `SLAM / RViz / status / square demo` を `robot5` / `robot6` にも使える
- `robot2_nav2.yaml` と `robot2_slam.yaml` を namespace 再利用できるようにしたので、`robot5` / `robot6` でも同じ launch を `namespace:=robot5` などで流用できる
- `fleet_adapter_template_tb4_ws` 側の adapter 起動スクリプトは、robot ごとに `env script / config / dispatch gate` を差し替えられるようにした

## 使い始めの最短手順

### シェルの使い回しに関する注意

- 以前 `source scripts/shared_fleet_env.bash` したシェルでは、`TB4_DISCOVERY_SERVER` が残って robot 個別 env を上書きすることがありました
- 現在の `scripts/robot2_env.bash`, `scripts/robot5_env.bash`, `scripts/robot6_env.bash` は各 robot の IP を強制するよう修正済みです
- それでも切り分け時は「robot ごとに新しいターミナル」を使うのが安全です

## robot2 の SLAM を基準に traffic-editor へつなぐ一連の流れ

### 全体像

1. `robot2` で SLAM 地図を作る
2. その地図を画像として書き出す
3. `traffic-editor` でその画像を背景にして建物マップを作る
4. charger, waypoint, lane, door を入れる
5. RMF 用 building map / nav graph を生成する
6. `rmf_main_ws` と `fleet_adapter_template_tb4_ws` に反映する
7. `robot5` / `robot6` は同じ building map 上の別ロボットとして合わせる

### 1. robot2 で SLAM 地図を作る

前提:

- `robot2` が正常に動いている
- `ros2 topic list | grep '^/robot2/'` で `odom`, `tf`, `scan` が見えている
- 走行中に時刻ズレや TF の大きな乱れがない

実行例:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 launch tb4_square robot2_slam.launch.py namespace:=robot2
```

このコマンドは SLAM ノードと RViz を起動します。  
保存コマンドは、**別ターミナル**で実行してください。

### localization 用 RViz の注意

通常の `robot2_rviz.sh` は robot 表示向けで、`2D Pose Estimate` 用の `initialpose` tool が入っていません。  
localization で初期姿勢を入れるときは、次を使ってください。

```bash
cd ~/turtlebot4_ws
./scripts/robot2_localization_rviz.sh
```

`robot5` / `robot6` も同様です。

```bash
cd ~/turtlebot4_ws
./scripts/robot5_localization_rviz.sh
```

```bash
cd ~/turtlebot4_ws
./scripts/robot6_localization_rviz.sh
```

別ターミナルで走行確認したいときは:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic list | grep '^/robot2/'
ros2 node list | grep '^/robot2/'
```

地図作成のコツ:

- 壁に沿ってゆっくり走る
- 角と長い廊下を丁寧に回る
- charger 周辺を必ず通る
- `robot5` と `robot6` の予定地点も含めて広めに回る

保存時は `robot2` の SLAM マップを `~/maps/robot2_map.yaml` などに分けて保存します。

地図保存の実行例:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic list | grep '^/robot2/map'
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/robot2_map \
  --ros-args -r map:=/robot2/map
```

保存後に確認するファイル:

```bash
ls -l ~/maps/robot2_map.*
```

もし `map_saver_cli` が名前空間つき `/robot2/map` を拾えない場合は、まず SLAM の起動状態を確認してください。

```bash
ros2 node list | grep '/robot2/slam_toolbox'
ros2 topic info /robot2/map -v
```

それでも `map_saver_cli` がだめなら、`slam_toolbox` の保存サービスを使います。

```bash
ros2 service list | grep '/robot2/slam_toolbox'
ros2 service call /robot2/slam_toolbox/save_map slam_toolbox/srv/SaveMap "{name: {data: 'robot2_map'}}"
```

環境や版によって保存先の解釈が少し違うことがあるので、まずは `map_saver_cli` を試し、だめなら `save_map` サービスに切り替える流れが安全です。

### 2. traffic-editor に渡す

traffic-editor 側では、`robot2` の SLAM 地図を「基準の画像」として読み込みます。

ポイント:

- 画像の向きと原点を勝手に変えない
- できれば `robot2` の map を RMF の master map として扱う
- `robot5` / `robot6` の充電器位置は、この1枚の map 上に追加する

### 3. traffic-editor で作るもの

最低限、次を入れます。

- `charger`
- `pre_dock`
- `LP1`
- `LP2`
- `LP3`
- 廊下 lane
- 交差点 waypoint
- 必要な door

charger は `is_parking_spot` を有効にしておくと、RMF の充電タスクとつながりやすいです。

### 4. building map / nav graph を作る

traffic-editor の `.building.yaml` を元に、RMF が読む building map と navigation graph を生成します。

この段階で確認したいのは次です。

- 地図のスケールが合っているか
- charger の名前が robot ごとに区別できるか
- lane が行き止まりになっていないか
- `robot2/5/6` が同じ map 上を走れるか

### 5. RMF 側に入れる情報

`fleet_adapter_template_tb4_ws/src/tb4_fleet_adapter/config_robot5.yaml` と `config_robot6.yaml` にも反映する項目です。

- `map_name`
- `charger` waypoint 名
- `pre_dock` waypoint 名
- `reference_coordinates`
- `robot_description` と localization の前提

`reference_coordinates` は、RMF の座標系と robot 側の座標系が少し違うときに使います。少なくとも4点あると安定しやすいです。

### 6. host 側で確認する順番

まず `robot2` 単体で確認します。

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot2/'
```

次に `robot5` と `robot6` を同じ要領で確認します。

```bash
cd ~/turtlebot4_ws
source scripts/robot5_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot5/'
```

```bash
cd ~/turtlebot4_ws
source scripts/robot6_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot6/'
```

3台とも見えたら、1画面 RViz と 1つの RMF に進みます。

### 7. 時刻同期の確認と復旧

#### 確認コマンド

host PC と各 robot で、それぞれ次を実行します。

```bash
timedatectl
date -Is
```

追加で、同期サービスが何を使っているか確認します。

```bash
systemctl status systemd-timesyncd chrony --no-pager
```

必要なら同期状態の詳細も見ます。

```bash
timedatectl timesync-status
```

#### 見るポイント

- `System clock synchronized: yes`
- `NTP service: active` もしくは `chrony` が active
- host と robot の `date -Is` が数秒程度以内で近い

#### おかしかったときの復旧

まず NTP を有効化します。

```bash
sudo timedatectl set-ntp true
```

そのうえで、使っている同期サービスを再起動します。

```bash
sudo systemctl restart systemd-timesyncd
```

または `chrony` を使っている環境なら:

```bash
sudo systemctl restart chrony
```

復旧後にもう一度確認します。

```bash
timedatectl
date -Is
```

#### まだずれるとき

- Wi-Fi が不安定だと NTP 同期が遅れます
- robot を再起動してから 1 分ほど待つと落ち着くことがあります
- それでも大きくずれるなら、`journalctl -u systemd-timesyncd -n 50 --no-pager` か `journalctl -u chrony -n 50 --no-pager` を見ます

#### SD カード複製が原因っぽいとき

`robot2` の SD カードを複製して `robot5` / `robot6` に使った場合は、時刻同期だけでなく次も確認してください。

```bash
hostnamectl
cat /etc/hostname
cat /etc/machine-id
ls -l /var/lib/dbus/machine-id
chronyc tracking
chronyc sources -v
```

見るポイント:

- `hostname` が `turtlebot4-5` / `turtlebot4-6` になっているか
- `machine-id` が 3台で同じになっていないか
- `chronyc sources -v` で `^*` などの同期元が見えているか

もし `robot5` / `robot6` の `hostname` が `robot2` のままなら、まずホスト名を直します。

```bash
sudo hostnamectl set-hostname turtlebot4-5
```

```bash
sudo hostnamectl set-hostname turtlebot4-6
```

`machine-id` が同一で、ネットワークや systemd の挙動が変なら、複製元の共通 ID を新しく作り直します。

```bash
sudo rm -f /etc/machine-id /var/lib/dbus/machine-id
sudo systemd-machine-id-setup
sudo reboot
```

この処理は `robot5` / `robot6` にだけ行ってください。`robot2` は基準機としてそのままで大丈夫です。

#### `chrony` で時刻を即時に合わせる

`chrony` が動いているのに `System clock synchronized: no` のままなら、まず参照元を見ます。

```bash
chronyc sources -v
chronyc tracking
```

同期元が見えているのに反映が遅いときは、強制的に一度合わせます。

```bash
sudo chronyc -a makestep
chronyc tracking
date -Is
```

それでも同期元が出てこないときは、`robot5` / `robot6` がネットワークに出られているか、DNS とルーティングが正常かを先に確認してください。

#### host が robot を NTP 許可しているか

今回の環境では host 側の `chrony.conf` が `allow 192.168.11.22` だけになっていると、`robot5` / `robot6` が時刻同期できません。

host で次を確認してください。

```bash
grep -n '^allow ' /etc/chrony/chrony.conf
```

もし `192.168.11.25` と `192.168.11.26` が無ければ追加します。

```bash
sudoedit /etc/chrony/chrony.conf
```

追加例:

```conf
allow 192.168.11.22
allow 192.168.11.25
allow 192.168.11.26
```

反映:

```bash
sudo systemctl restart chrony
chronyc sources -v
```

`robot5` と `robot6` 側では、その後に:

```bash
sudo chronyc -a makestep
chronyc tracking
date -Is
```

#### 2026-06-12 実測結果

- host の `chrony.conf` に `allow 192.168.11.25` と `allow 192.168.11.26` を追加したあと、`robot5` / `robot6` は host `192.168.11.104` を参照先として同期できた
- `chronyc sources -v` で `^* 192.168.11.104` が見えれば、時刻ずれはひとまず解消とみなしてよい

まで実行してください。

#### TF や SLAM が怪しいときの再起動順

```bash
sudo systemctl restart turtlebot4.service
turtlebot4-source
turtlebot4-daemon-restart
```

そのあとに `ros2 topic list | grep '^/robotX/'` を見て、`odom`, `tf`, `scan` が戻るか確認します。

### 8. こちらで次に埋めるところ

あなたが traffic-editor で map を作ったあと、こちらで次を詰めます。

- 3台を1画面で表示する RViz 起動
- 1つの fleet adapter で 3台を登録する設定
- `rmf_main_ws` 側の map / charger / lane 反映
- 必要なら `robot2` を基準にした `robot5` / `robot6` の座標合わせ

### 迷ったらここだけ守ればよいこと

- SLAM の基準は `robot2`
- traffic-editor では map を1枚に統一
- charger は robot ごとに名前を分ける
- `robot5` / `robot6` は同じ map に後追いで載せる
- 先に RMF をいじりすぎず、まず map と座標系を固める

### 共有 Discovery Server を使う host 側基本環境

host PC の現在の Wi-Fi 側 IP は `192.168.11.104` です。  
3台を 1 つの RMF / 1 つの RViz に寄せるなら、まず host で共通 Discovery Server を立てるのがおすすめです。

```bash
cd ~/turtlebot4_ws
./scripts/start_shared_discovery_server.sh 192.168.11.104 11811
```

別ターミナルでは:

```bash
cd ~/turtlebot4_ws
source scripts/shared_fleet_env.bash
ros2 daemon stop
ros2 daemon start
```

### robot5

```bash
cd ~/turtlebot4_ws
source scripts/robot5_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot5/'
```

```bash
cd ~/turtlebot4_ws
./scripts/robot5_status.sh
```

```bash
cd ~/turtlebot4_ws
./scripts/robot5_rviz.sh --robot
```

```bash
cd ~/turtlebot4_ws
./scripts/robot5_slam.sh
```

### robot6

```bash
cd ~/turtlebot4_ws
source scripts/robot6_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot6/'
```

```bash
cd ~/turtlebot4_ws
./scripts/robot6_status.sh
./scripts/robot6_rviz.sh --robot
./scripts/robot6_slam.sh
```

## localization / Nav2 の起動例

`robot5`:

```bash
cd ~/turtlebot4_ws
source scripts/robot5_env.bash
ros2 launch tb4_square robot2_localization_compat.launch.py \
  namespace:=robot5 \
  map:=$HOME/maps/robot5_map.yaml
```

```bash
cd ~/turtlebot4_ws
source scripts/robot5_env.bash
ros2 launch tb4_square robot2_nav2_compat.launch.py \
  namespace:=robot5 \
  params_file:=$HOME/turtlebot4_ws/src/tb4_square/config/robot2_nav2.yaml
```

`robot6` も `robot5 -> robot6` に読み替えれば同様です。

## 同時に並列運用できるか

### 結論

- `SLAM / RViz / localization / Nav2` を robot ごとに別ターミナルで動かすこと自体は可能
- `ROS_DOMAIN_ID=0` と共通 Discovery Server をそろえれば、host 側は 1つのターミナルから 3台を同時に見られる
- ただし bringup や切り分けは、引き続き `1つのターミナル = 1台の robot 用` のほうが安全

## 1つの RMF にまとめたい場合

### 可能か

- 可能です
- ただし前提は、host 側から見たときに `robot2/5/6` の必要 topic と action が同じ ROS graph に見えていることです

### いま直ちにできない理由

- Domain ID はそろえられたが、まだ各 robot が `127.0.0.1:11811;` のローカル discovery server を見ている
- このままだと host / RMF / RViz が 3 台を 1 つの graph として扱いにくい
- そのため、まず Discovery Server を host 共通へ寄せるのが先

### 目指す最終形

1. traffic-editor で 1つの建物マップを作る
2. その中に `robot2_charger` `robot5_charger` `robot6_charger` を入れる
3. host 側で 3台ぶんの `/robotX/amcl_pose` と `/robotX/navigate_to_pose` を同じ ROS graph に集約する
4. 1本の fleet adapter で `robot2/5/6` をまとめて登録する

この前提の template は

- [config_multi_robot_one_rmf_template.yaml](/home/masu_ubu/fleet_adapter_template_tb4_ws/src/tb4_fleet_adapter/config_multi_robot_one_rmf_template.yaml:1)
- [ONE_RMF_MULTI_ROBOT_PLAN.md](/home/masu_ubu/fleet_adapter_template_tb4_ws/ONE_RMF_MULTI_ROBOT_PLAN.md:1)

に用意しました。

## Discovery 設定の見直し

### 以前の案について

- 以前ここに書いていた「robot 側を `ROS_DISCOVERY_SERVER=192.168.11.104:11811;` の offboard-only に寄せる」案は、現時点では採用しないでください
- 公式ドキュメントでは、TurtleBot4 の Discovery Server は Raspberry Pi 上の onboard server を主系として使う前提です
- また Discovery 設定は `turtlebot4-setup` から Create3 / RPi terminal / robot_upstart に一貫適用する前提で、端末だけ `export` しても永続設定と食い違うと壊れやすいです

### 当面のおすすめ設定

まずは 3台とも「robot 単体で topic が見える」状態に戻します。

### host PC

- `ROS_DOMAIN_ID=0`
- host 側は当面、各 robot ごとの env script を切り替えて確認する
- 共有 Discovery Server は、robot 単体 bringup が完全に戻るまで必須ではない

### robot2 / robot5 / robot6

- `ROS_DOMAIN_ID=0`
- namespace はそれぞれ `robot2 / robot5 / robot6`
- Discovery Server は `turtlebot4-setup` から設定する
- Onboard Server ID は各 robot で一意にする
- Offboard Server IP はいったん空欄に戻す

### 復旧後にやる確認

各 robot で:

```bash
turtlebot4-source
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION
echo $ROS_DISCOVERY_SERVER
sudo systemctl restart turtlebot4.service
turtlebot4-daemon-restart
ros2 topic list
ros2 topic list | grep '^/robot'
ros2 node list
```

期待値:

- `/parameter_events` と `/rosout` だけではない
- `/robot2/*` または `/robot5/*` または `/robot6/*` が並ぶ
- `ros2 node list` が空ではない

### それでも復旧しない場合に送ってほしい情報

各 robot で次を送ってください。

```bash
turtlebot4-source
ros2 topic list
ros2 node list
sudo systemctl status turtlebot4.service --no-pager
sudo journalctl -u turtlebot4.service -n 100 --no-pager
grep -nE 'ROS_DOMAIN_ID|ROBOT_NAMESPACE|DISCOVERY_SERVER|RMW_IMPLEMENTATION' /etc/turtlebot4/setup.bash
```

### RMF / fleet adapter について

- `tb4_fleet_adapter` 側は、今回の変更で robot ごとに別 topic/action 設定を持てるようにしてある
- したがって、host 側 ROS graph に `/robot2/*` `/robot5/*` `/robot6/*` が同時に見えれば、1 本の adapter で 3 台を登録する土台はある
- 先に必要なのは adapter 改修よりも Discovery / TF / RViz 側の統合

### 現実的な選択肢

1. まずは `robot2 / robot5 / robot6` を個別に bringup できる状態まで持っていく
2. その後、同時運用したいなら次のどちらかへ進む
3. `bridge / relay / Zenoh / TCP` で host 側へ各 robot topic を寄せて、同一 host domain に再配置する
4. あるいは fleet adapter を multi-robot / multi-prefix 前提に改修する

## こちらでまだ埋め切れない情報

### RMF で必要

- `robot5` の charger 実位置
- `robot6` の charger 実位置
- `robot5_charger` / `robot6_charger` を入れた nav graph の waypoint 名
- `robot5` / `robot6` の `reference_coordinates`

### 最低限ほしい座標

各 robot について、できれば次の 5 点です。

- charger
- pre_dock
- LP1
- LP2
- LP3

RMF 側座標と robot map 側座標の対応が必要です。  
いまの `robot2` 相当で進めるなら、`fleet_adapter_template_tb4_ws/src/tb4_fleet_adapter/config_robot5.yaml` / `config_robot6.yaml` にこれを入れます。

## こちら側でしてほしい操作

### 1. 実機の時刻同期確認

PC と各 robot の時刻ずれが大きいと、`TF_OLD_DATA` や `LaserScan が古い扱い` になりやすいです。

PC と各 robot で:

```bash
timedatectl
date -Is
```

確認したい点:

- `System clock synchronized: yes`
- `NTP service: active` もしくは同等の同期状態
- PC と robot の時刻差が大きくないこと

もしずれていたら、`chrony` か `systemd-timesyncd` で揃えてください。

### 2. 実機側の基本確認

各 robot で:

```bash
turtlebot4-source
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION
echo $ROS_DISCOVERY_SERVER
turtlebot4-daemon-restart
ros2 topic list | grep '^/robot5/'
```

`robot6` は `robot5 -> robot6` に読み替えます。

### 3. host 側の接続確認

```bash
cd ~/turtlebot4_ws
source scripts/robot5_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot5/'
```

```bash
cd ~/turtlebot4_ws
source scripts/robot6_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep '^/robot6/'
```

### 4. map を作るなら robot ごとに保存名を分ける

例:

- `~/maps/robot5_map.yaml`
- `~/maps/robot6_map.yaml`

## 次にこちらへ送ってほしい情報

優先順は次の通りです。

1. `robot5` と `robot6` の charger 実位置が、`robot2` と同じ場所か別場所か
2. `robot5_map.yaml` / `robot6_map.yaml` を今後別ファイルで持つか、既存 `robot2_map` を共用するか
3. 可能なら `robot5` / `robot6` の 5点実測:
   `charger, pre_dock, LP1, LP2, LP3`
4. RMF で最終的にやりたい形:
   `個別運用でよい` か `3台を同時にRMF fleetとして動かしたい` か

この4点がそろえば、次の段階として

- `fleet_adapter_template_tb4_ws` の `config_robot5.yaml / config_robot6.yaml` の本値化
- `rmf_main_ws` の nav graph / building map への charger 追加
- 必要なら multi-robot 同時運用向け構成の整理

まで一気に進められます。
