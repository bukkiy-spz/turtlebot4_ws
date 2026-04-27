# TurtleBot4 コマンドメモ

このファイルは、`TurtleBot4` 実機を `Remote-SSH` と `RViz` を使って動かすときのメモです。  
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
ssh ubuntu@192.168.188.22
```

## 2. PC側: 実機に届くか確認する

```bash
ping 192.168.188.22
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

##　cmd_velがなければ再起動
'''bash
sudo reboot
'''

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

## 11. PC側: RViz を起動する

`robot2` 用の設定済み RViz を起動します。  
`/robot2/tf` や `/robot2/tf_static` のリマップも自動で入ります。

```bash
cd ~/turtlebot4_ws
./scripts/robot2_rviz.sh
```

## 12. PC側: 実機に正方形走行を指示する

```bash
cd ~/turtlebot4_ws
./scripts/robot2_square.sh
```

`./scripts/robot2_square.sh` は、先に `/robot2/cmd_vel` が見えるか確認してから起動します。  
見えない場合はそのまま launch せず、実機側 bringup の確認を促して止まります。

手早く状態確認したいとき:

```bash
cd ~/turtlebot4_ws
./scripts/robot2_status.sh
```

`ros2 topic info -v /robot2/cmd_vel` で `Subscription count: 1` と `/robot2/create3_repub` が見えてから実行します。

## 13. PC側: 正方形走行のパラメータを変える

```bash
cd ~/turtlebot4_ws
./scripts/robot2_square.sh \
  side_length:=0.3 \
  linear_speed:=0.08 \
  angular_speed:=0.5 \
  pause_time:=0.3
```

## 14. PC側: キーボードで実機を操作する

まず `teleop_twist_keyboard` が入っていない場合はインストールします。

```bash
sudo apt install ros-humble-teleop-twist-keyboard
```

実機をキーボードで動かすときは次を使います。

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/robot2/cmd_vel
```

よく使うキー:

- `i`: 前進
- `,`: 後退
- `j`: 左回転
- `l`: 右回転
- `k`: 停止

## 15. PC側: RViz 表示用のトピックを確認する

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic echo /robot2/robot_description --once
ros2 topic echo /robot2/tf --once
ros2 topic echo /robot2/tf_static --once
ros2 topic echo /robot2/odom --once
ros2 topic echo /robot2/scan --once
```

## 16. このプロジェクトでよく使うトピック

- `/robot2/cmd_vel`
  実機へ速度指令を送るトピック
- `/robot2/robot_description`
  `RViz` でロボットモデルを表示するためのトピック
- `/robot2/scan`
  `LiDAR` の表示用トピック
- `/robot2/odom`
  オドメトリ表示用トピック
- `/robot2/tf`
  動的な座標変換
- `/robot2/tf_static`
  静的な座標変換
- `/robot2/path`
  `RViz` で軌跡を線として表示するためのトピック

## 17. 実際によく使う流れ

### 1. 実機側で実行

```bash
turtlebot4-source
turtlebot4-daemon-restart
ros2 topic list | grep robot2
```

### 2. PC側で通信設定を入れる

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep robot2
```

### 3. PC側で RViz を開く

```bash
cd ~/turtlebot4_ws
./scripts/robot2_rviz.sh
```

## 18. Humble 用と Jazzy/free_fleet 用を分けて運用する

今後の前提は次です。

- ホストPC側:
  `Humble` で `TurtleBot4` 実機操作やシミュレーションを行う
- Docker コンテナ側:
  `Jazzy` で `free_fleet` 関連だけを動かす
- Git:
  `Humble` 用と `Jazzy/free_fleet` 用を別リポジトリで管理する

この前提なら、`VSCode` のウィンドウも分けるのが一番わかりやすいです。

### 18-1. フォルダ構成のおすすめ

```text
~/turtlebot4_ws
  -> Humble 用
  -> 実機操作 / シミュレーション用
  -> Git も Humble 用リポジトリ

~/jazzy_ff_ws
  -> Jazzy + free_fleet 用
  -> Docker コンテナからマウントして使う
  -> Git も Jazzy/free_fleet 用リポジトリ
```

### 18-2. VSCode のおすすめ運用

- `Humble` 用:
  ホスト側で `~/turtlebot4_ws` を開いた `VSCode` ウィンドウ
- `Jazzy/free_fleet` 用:
  `Dev Containers` か Docker 接続でコンテナに入った `VSCode` ウィンドウ

見分けやすくするコツ:

- `Humble` 側ウィンドウ:
  ワークスペース名を `turtlebot4_ws (Humble)` と意識する
- `Jazzy` 側ウィンドウ:
  ワークスペース名を `jazzy_ff_ws (Jazzy)` と意識する
- ターミナルを開いたら最初に `pwd` と `printenv ROS_DISTRO` を見る

### 18-3. Humble 側リポジトリの扱い

`Humble` 側は今の `~/turtlebot4_ws` をそのまま使います。  
実機用コードやシミュレーション用コードはこちらに残します。

確認コマンド:

```bash
cd ~/turtlebot4_ws
pwd
git remote -v
printenv ROS_DISTRO
```

保存するとき:

```bash
cd ~/turtlebot4_ws
git status
git add .
git commit -m "Update Humble workspace"
git push
```

### 18-4. Jazzy/free_fleet 側リポジトリを作る

`Jazzy` 側は `Humble` 側とは別フォルダ、別リポジトリにします。  
コピーして流用するより、`free_fleet` 用として独立させたほうが今後の整理が楽です。

```bash
cd ~
mkdir -p jazzy_ff_ws/src
cd ~/jazzy_ff_ws
git init
```

`.gitignore` の例:

```gitignore
build/
install/
log/
__pycache__/
*.pyc
.vscode/
```

作成コマンド:

```bash
cd ~/jazzy_ff_ws
cat > .gitignore <<'EOF'
build/
install/
log/
__pycache__/
*.pyc
.vscode/
EOF
```

### 18-5. Jazzy 側を別リモートへ push できるようにする

GitHub などで `Jazzy/free_fleet` 用の空リポジトリを作ってから、次を実行します。

```bash
cd ~/jazzy_ff_ws
git add .
git commit -m "Initial Jazzy free_fleet workspace"
git remote add origin <Jazzy用の新しいリポジトリURL>
git branch -M main
git push -u origin main
```

確認コマンド:

```bash
cd ~/jazzy_ff_ws
git remote -v
git status
```

### 18-6. コンテナ内の変更を Jazzy 側リポジトリへ保存する

大事なのは、Docker コンテナが `~/jazzy_ff_ws` をマウントしていることです。  
そうすれば、コンテナ内で編集した内容をホスト側でも同じ Git リポジトリとして扱えます。

保存の流れ:

```bash
cd ~/jazzy_ff_ws
git status
git add .
git commit -m "Update Jazzy free_fleet workspace"
git push
```

### 18-7. どちらに push するか迷ったときの判断基準

- `TurtleBot4` 実機操作、`RViz`、シミュレーション、`Humble` 用コード:
  `~/turtlebot4_ws`
- `Dockerfile`、`.devcontainer/`、`free_fleet`、`Jazzy` 専用設定:
  `~/jazzy_ff_ws`

### 18-8. 混ぜないための確認コマンド

```bash
pwd
git remote -v
printenv ROS_DISTRO
printenv | grep ROS
```

### 18-9. いちばん安全な実運用の流れ

1. `Humble` 用はホスト側 `VSCode` ウィンドウで `~/turtlebot4_ws` を開く
2. `Jazzy/free_fleet` 用はコンテナ側 `VSCode` ウィンドウで `~/jazzy_ff_ws` を開く
3. `Humble` は `~/turtlebot4_ws` のリポジトリへ push する
4. `Jazzy/free_fleet` は `~/jazzy_ff_ws` のリポジトリへ push する
5. 同じターミナルで `Humble` と `Jazzy` を混ぜて `source` しない

### 4. 別の PC 側ターミナルで実機を動かす

```bash
cd ~/turtlebot4_ws
./scripts/robot2_square.sh
```

### 5. 別の PC 側ターミナルでキーボード操作する場合

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/robot2/cmd_vel
```

## 19. よくある確認コマンド

### 実機側で Discovery Server の設定を確認

```bash
turtlebot4-source
echo $ROS_DISCOVERY_SERVER
```

### PC側で実機のトピックが見えないとき

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ping 192.168.188.22
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep robot2
```

### 実機側では見えるのに PC側で見えないとき

実機側:

```bash
turtlebot4-source
echo $ROS_DISCOVERY_SERVER
ros2 topic list | grep robot2
```

### `/robot2/cmd_vel` だけ消えたとき

PC側:

```bash
cd ~/turtlebot4_ws
./scripts/robot2_status.sh
```

`/robot2/robot_description` は見えるのに `/robot2/cmd_vel` と `/robot2/scan` が来ない場合は、PC 側設定よりも実機側 bringup の不調の可能性が高いです。

実機側:

```bash
turtlebot4-source
turtlebot4-daemon-restart
ros2 topic list | grep cmd_vel
ros2 node list | grep -E 'create3|repub|twist|mux'
```

PC側に戻って:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep cmd_vel
```

PC側:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep robot2
```

### RViz にロボットが出ないとき

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 topic echo /robot2/robot_description --once
ros2 topic info -v /robot2/robot_description
ros2 topic echo /robot2/tf --once
ros2 topic echo /robot2/tf_static --once
```

`RobotModel` が赤エラーになる場合は、RViz の `RobotModel > Description Topic` が次になっているか確認します。

- `Value`: `/robot2/robot_description`
- `Durability Policy`: `Transient Local`
- `Fixed Frame`: `odom`

`left_wheel` などで `No transform from [left_wheel] to [odom]` が出る場合は、実機側の wheel TF が出ていない状態です。  
`robot2_rviz.launch.py` では RViz 表示用の wheel TF 補助ノードも一緒に起動します。  
最新版の `wheel_tf_publisher` は `joint_states` が一時的に来なくてもフォールバックの wheel TF を出し続けます。  
さらに `odom_tf_publisher` が `/robot2/odom` 不在時も RViz 用の `odom -> base_link` を補うので、RViz は `./scripts/robot2_rviz.sh` から起動するのが前提です。

補助ノードだけ確認するとき:

```bash
cd ~/turtlebot4_ws
source scripts/robot2_env.bash
ros2 run tb4_square wheel_tf_publisher --ros-args -r /tf:=/robot2/tf
```

## 20. ノードや launch を止める

`ros2 launch` や `ros2 run` を実行したターミナルで `Ctrl+C` を押します。

## 21. Remote-SSH 関連でよく使うコマンド

### PC側: 実機にログインする

```bash
ssh ubuntu@192.168.188.22
```

### PC側: X転送つきで接続する

```bash
ssh -X ubuntu@192.168.188.22
```

### PC側: 実機との接続確認をする

```bash
ping 192.168.188.22
ssh ubuntu@192.168.188.22
```

## 22. GitHub への push が重いとき

このワークスペースでは、`build/`、`install/`、`log/`、`.vscode/` のような自動生成ファイルは Git に入れないのが基本です。  
すでに `.gitignore` は追加してあるので、次は「今 Git 管理に入ってしまっている生成物を外す」作業をします。

### まず今後の生成物を無視する

`.gitignore` に次のような設定を入れています。

- `build/`
- `install/`
- `log/`
- `.vscode/`
- `__pycache__/`

### すでに Git 管理に入っている生成物を index から外す

以下のコマンドは、ローカルのファイル自体は消さずに、Git の管理対象からだけ外します。

```bash
cd ~/turtlebot4_ws
git rm -r --cached .vscode build install log
git add .gitignore
git status
git commit -m "Remove generated files from git tracking"
```

### そのあと push する

```bash
git push origin main
```

### それでも重い場合

過去のコミット履歴に大きいファイルが残っている可能性があります。  
特に `.vscode/browse.vc.db` のような大きいファイルが履歴にあると、push や clone が重いままです。

この場合は `git filter-repo` などを使って履歴を書き換える必要があります。  
ただしこれは影響が大きいので、実行前にバックアップや共同作業者への共有が必要です。

履歴から巨大ファイルを消す例:

```bash
git filter-repo --path .vscode/browse.vc.db --invert-paths
git push --force-with-lease origin main
```

注意:

- 履歴を書き換えたあとの push は `git push --force-with-lease origin main` を使う
- `git push --force-with-lease` でも共同作業中のリポジトリでは要注意
- 履歴を書き換える前に `git clone --mirror` などでバックアップを取るのがおすすめ

## 23. Humble で TurtleBot4 シミュレーションを試す

実機に行く前に、まず `Gazebo` 上で `TurtleBot4` を動かすと確認しやすいです。  
`Ubuntu 22.04 + ROS 2 Humble` 前提です。

### まずシミュレータを入れる

```bash
# パッケージ一覧を最新にする
sudo apt update
# TurtleBot4 シミュレータ本体と Create3 関連ノードを入れる
sudo apt install -y \
  ros-humble-turtlebot4-simulator \
  ros-humble-irobot-create-nodes
```

### まず素のシミュレーションを起動する

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# ワークスペースを読み込む
source ~/turtlebot4_ws/install/setup.bash
# Gazebo 上で TurtleBot4 シミュレーションを起動する
ros2 launch tb4_square turtlebot4_sim.launch.py
```

起動したら `Gazebo` の `Play` ボタンを押して時間を進めます。

### まず Gazebo と RViz でロボット表示を確認する

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# ワークスペースを読み込む
source ~/turtlebot4_ws/install/setup.bash
# まずは Gazebo と RViz だけを起動してロボット表示を確認する
ros2 launch tb4_square turtlebot4_sim.launch.py \
  rviz:=true localization:=false nav2:=false slam:=false
```

`turtlebot4_ignition_bringup/turtlebot4_ignition.launch.py` は `nav2` や `localization` や `map` をそのまま中へ渡さないので、まずはこのラッパー launch でロボット表示を確認します。

`Gazebo` が黒画面のままなら、次でソフトウェア描画に切り替えて確認します。

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source ~/turtlebot4_ws/install/setup.bash
export LIBGL_ALWAYS_SOFTWARE=1
ros2 launch tb4_square turtlebot4_sim.launch.py \
  rviz:=true localization:=false nav2:=false slam:=false
```

### そのあと localization と Nav2 を有効にする

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# ワークスペースを読み込む
source ~/turtlebot4_ws/install/setup.bash
# ロボット表示が確認できてから localization と Nav2 を有効にする
ros2 launch tb4_square turtlebot4_sim.launch.py \
  nav2:=true slam:=false localization:=true rviz:=true
```

### 起動後に確認する

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# ゴール移動用 action が立ち上がっているか確認する
ros2 action list | grep navigate_to_pose
# tf 関連トピックが出ているか確認する
ros2 topic list | grep tf
# LiDAR の scan トピックが出ているか確認する
ros2 topic list | grep scan
```

### CLI でゴールを送る

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# map 座標系で x=1.0, y=0.0 の位置へ移動するゴールを送る
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
'{
  pose: {
    header: {frame_id: "map"},
    pose: {
      position: {x: 1.0, y: 0.0, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    }
  }
}'
```

### 別の world や map を使いたいとき

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# ワークスペースを読み込む
source ~/turtlebot4_ws/install/setup.bash
# depot world と対応する map を指定して起動する
ros2 launch tb4_square turtlebot4_sim.launch.py \
  nav2:=true slam:=false localization:=true rviz:=true \
  world:=depot \
  map:=/opt/ros/humble/share/turtlebot4_navigation/maps/depot.yaml
```

## 24. Humble で Open-RMF を試す

まずは `TurtleBot4` と直接つながなくてよいので、`RMF` のデモを単体で動かして全体像を確認します。

### RMF 本体を入れる

```bash
# パッケージ一覧を最新にする
sudo apt update
# ビルドや依存解決で使う基本ツールを入れる
sudo apt install -y ros-dev-tools
# rosdep をまだ初期化していなければ初期化する
sudo rosdep init
# 依存解決用データベースを更新する
rosdep update
# colcon の標準 mixin 設定を登録する
colcon mixin add default https://raw.githubusercontent.com/colcon/colcon-mixin-repository/master/index.yaml
# colcon mixin を最新化する
colcon mixin update default
# Open-RMF の Humble 向け開発パッケージを入れる
sudo apt install -y ros-humble-rmf-dev
```

### rmf_demos 用のワークスペースを作る

```bash
# RMF 用ワークスペースを作る
mkdir -p ~/rmf_ws/src
# ソース配置用ディレクトリへ移動する
cd ~/rmf_ws/src
# rmf_demos を Humble 向けバージョンで取得する
git clone https://github.com/open-rmf/rmf_demos.git -b 2.0.3
# ワークスペースのルートへ戻る
cd ~/rmf_ws
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# 必要な依存パッケージをまとめて入れる
rosdep install --from-paths src --ignore-src -r -y
# rmf_demos をビルドする
colcon build
```

### RMF デモを起動する

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# rmf_demos ワークスペースを読み込む
source ~/rmf_ws/install/setup.bash
# clinic world の RMF デモを起動する
ros2 launch rmf_demos_gz clinic.launch.xml
```

### 別の world を試す

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# rmf_demos ワークスペースを読み込む
source ~/rmf_ws/install/setup.bash
# office world の RMF デモを起動する
ros2 launch rmf_demos_gz office.launch.xml
```

### タスクを投げる

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# rmf_demos ワークスペースを読み込む
source ~/rmf_ws/install/setup.bash
# 巡回タスクを RMF に送る
ros2 run rmf_demos_tasks dispatch_patrol \
  -p L1_left_nurse_center L2_right_nurse_center \
  -n 2 \
  --use_sim_time
```

## 25. 進め方のおすすめ順

### 1. TurtleBot4 シミュレータだけ確認する

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# ワークスペースを読み込む
source ~/turtlebot4_ws/install/setup.bash
# まずは Gazebo と RViz だけを起動してロボット表示を確認する
ros2 launch tb4_square turtlebot4_sim.launch.py \
  rviz:=true localization:=false nav2:=false slam:=false
```

### 2. 別ターミナルでゴールを送って動作確認する

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# map 座標系で x=1.0, y=0.0 の位置へ移動するゴールを送る
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
'{
  pose: {
    header: {frame_id: "map"},
    pose: {
      position: {x: 1.0, y: 0.0, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    }
  }
}'
```

### 3. そのあと RMF デモを別ワークスペースで試す

```bash
# ROS 2 Humble の基本環境を読み込む
source /opt/ros/humble/setup.bash
# rmf_demos ワークスペースを読み込む
source ~/rmf_ws/install/setup.bash
# clinic world の RMF デモを起動する
ros2 launch rmf_demos_gz clinic.launch.xml
```

### 4. 注意

- `TurtleBot4` と `RMF` を別々に確認してから、最後に接続段階へ進むと詰まりにくい
- `free_fleet` の現行 README は `Jazzy` 前提なので、最終的に `RMF` から `TurtleBot4` を直接つなぐ段階では別途確認が必要

## 26. Docker で Jazzy 環境を分けて作る

`Humble` のホスト環境はそのまま残して、`Docker` コンテナの中だけで `Jazzy` を使う流れです。

### 1. Docker が動いているか確認する

```bash
# Docker のバージョンを確認する
docker --version
# テスト用コンテナが動くか確認する
sudo docker run hello-world
```

### 2. 毎回 sudo を付けたくない場合

```bash
# 自分を docker グループに追加する
sudo usermod -aG docker $USER
```

このあと一度ログアウトしてログインし直します。  
ログインし直したあとは次で確認します。

```bash
# sudo なしで Docker が使えるか確認する
docker --version
docker run hello-world
```

### 3. Jazzy 用の作業フォルダを作る

```bash
# ホスト側に Jazzy 用ワークスペースを作る
mkdir -p ~/jazzy_ff_ws/src
# Git 管理を始める
cd ~/jazzy_ff_ws
git init
```

### 4. Jazzy イメージを取得する

```bash
# ROS 2 Jazzy の desktop イメージを取得する
docker pull osrf/ros:jazzy-desktop
```

### 5. GUI を出せるようにする

```bash
# Docker コンテナからローカル画面へ GUI を表示できるようにする
xhost +local:docker
```

### 6. Jazzy コンテナを起動する

```bash
# GUI とネットワークをホスト共有で使いながら Jazzy コンテナを起動する
docker run -it --rm \
  --name jazzy_ff \
  --net=host \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v ~/jazzy_ff_ws:/root/jazzy_ff_ws \
  osrf/ros:jazzy-desktop
```

### 7. コンテナの中で Jazzy か確認する

```bash
# Jazzy の ROS 環境を読み込む
source /opt/ros/jazzy/setup.bash
# いまの ROS ディストリビューションを確認する
printenv ROS_DISTRO
# ros2 コマンドが使えるか確認する
ros2 --help
```

`ROS_DISTRO` に `jazzy` と出れば OK です。

### 8. コンテナの中で free_fleet 用の作業を始める

```bash
# Jazzy 用ワークスペースの src へ移動する
cd /root/jazzy_ff_ws/src
# free_fleet を取得する
git clone https://github.com/open-rmf/free_fleet.git
# ワークスペースのルートへ戻る
cd /root/jazzy_ff_ws
# Jazzy の ROS 環境を読み込む
source /opt/ros/jazzy/setup.bash
```

### 8-1. Jazzy/free_fleet 側の変更を Git に保存する

コンテナ内で編集したファイルは、`~/jazzy_ff_ws` をマウントしていればホスト側の Git にそのまま反映されます。

```bash
cd ~/jazzy_ff_ws
git status
git add .
git commit -m "Update Jazzy free_fleet workspace"
git push
```

### 9. 使い分け

- `Humble` の TurtleBot4 シミュレーションはホスト側ターミナルで動かす
- `Jazzy` の `free_fleet` や関連確認は Docker コンテナ内ターミナルで動かす
- 同じターミナルで `Humble` と `Jazzy` を混ぜて `source` しない
- `VSCode` も `Humble` 用と `Jazzy` 用で別ウィンドウに分ける
