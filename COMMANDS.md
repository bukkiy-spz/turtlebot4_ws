# TurtleBot4 コマンドメモ

このファイルは、`TurtleBot4` 実機を `Remote-SSH` と `RViz` を使って動かすときのメモです。  
「どちらの端末で打つか」が分かるように、`PC側` と `実機側` を分けてあります。

## 0. まず確認すること

- `VSCode Remote-SSH` で開いたターミナル:
  基本的に `実機側`
- 普通の端末アプリで開いたローカル端末:
  `PC側`
- 迷ったら次で確認

```bash
hostname
whoami
pwd
```

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

## 7. PC側: ROS 通信設定を入れる

毎回新しい PC 側ターミナルを開いたら、まずこれを実行します。

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DISCOVERY_SERVER=192.168.11.22:11811
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
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch tb4_square robot2_rviz.launch.py
```

## 12. PC側: 実機に正方形走行を指示する

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch tb4_square square_driver.launch.py cmd_vel_topic:=/robot2/cmd_vel
```

## 13. PC側: 正方形走行のパラメータを変える

```bash
ros2 launch tb4_square square_driver.launch.py \
  cmd_vel_topic:=/robot2/cmd_vel \
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
source /opt/ros/humble/setup.bash
source install/setup.bash
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
source /opt/ros/humble/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DISCOVERY_SERVER=192.168.11.22:11811
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep robot2
```

### 3. PC側で RViz を開く

```bash
ros2 launch tb4_square robot2_rviz.launch.py
```

### 4. 別の PC 側ターミナルで実機を動かす

```bash
ros2 launch tb4_square square_driver.launch.py cmd_vel_topic:=/robot2/cmd_vel
```

### 5. 別の PC 側ターミナルでキーボード操作する場合

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/robot2/cmd_vel
```

## 18. よくある確認コマンド

### 実機側で Discovery Server の設定を確認

```bash
turtlebot4-source
echo $ROS_DISCOVERY_SERVER
```

### PC側で実機のトピックが見えないとき

```bash
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION
echo $ROS_DISCOVERY_SERVER
ping 192.168.11.22
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

PC側:

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DISCOVERY_SERVER=192.168.11.22:11811
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep robot2
```

### RViz にロボットが出ないとき

```bash
ros2 topic echo /robot2/robot_description --once
ros2 topic echo /robot2/tf --once
ros2 topic echo /robot2/tf_static --once
```

## 19. ノードや launch を止める

`ros2 launch` や `ros2 run` を実行したターミナルで `Ctrl+C` を押します。

## 20. Remote-SSH 関連でよく使うコマンド

### PC側: 実機にログインする

```bash
ssh ubuntu@192.168.11.22
```

### PC側: X転送つきで接続する

```bash
ssh -X ubuntu@192.168.11.22
```

### PC側: 実機との接続確認をする

```bash
ping 192.168.11.22
ssh ubuntu@192.168.11.22
```

## 21. GitHub への push が重いとき

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
git push origin --force
```

注意:

- `git push --force` は共同作業中のリポジトリでは要注意
- 履歴を書き換える前に `git clone --mirror` などでバックアップを取るのがおすすめ
