# TurtleBot4 Gazebo シミュレータ制御ガイド

## 概要
このガイドでは、Gazeboシミュレータ上でTurtleBot4ロボットを制御する方法を説明します。

## ステップ1: シミュレーションの起動

ターミナルで以下を実行します：

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch tb4_square turtlebot4_sim.launch.py rviz:=true localization:=false nav2:=false slam:=false
```

**起動内容:**
- Gazebo: 3D物理シミュレータ
- RViz: ロボット可視化ツール
- ロボット: TurtleBot4（warehouse環境）

**起動時間:** 約10-15秒

## ステップ2: ロボットを操作する方法

### 方法A: Pythonコントローラスクリプト（推奨）

別のターミナルで以下を実行します：

```bash
cd ~/turtlebot4_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

# デモンストレーション実行
python3 scripts/robot_controller.py demo

# または個別コマンド：
python3 scripts/robot_controller.py square 0.5      # 正方形描画 (辺0.5m)
python3 scripts/robot_controller.py circle 0.3 8    # 円描画 (半径0.3m, 8秒)
python3 scripts/robot_controller.py forward 0.5    # 前進 (0.5m)
python3 scripts/robot_controller.py rotate 90      # 回転 (90度)
```

### 方法B: 直接ROS 2トピックでコマンド送信

```bash
# 前進（0.2 m/sで5秒）
ros2 topic pub -1 /cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {z: 0.0}}"

# 回転（0.5 rad/sで反時計回り）
ros2 topic pub -1 /cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {z: 0.5}}"

# 停止
ros2 topic pub -1 /cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {z: 0.0}}"
```

### 方法C: キーボード操作

teleop_twist_keyboardパッケージがインストールされている場合：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

キー操作:
- `i`: 前進
- `,`: 後退
- `j`: 左回転
- `l`: 右回転
- `k`: 停止

### 方法D: 既存スクリプト（四角形運動）

```bash
cd ~/turtlebot4_ws && bash scripts/robot2_square.sh
```

## トラブルシューティング

### ロボットが動かない場合

1. **Gazeboが起動しているか確認:**
   ```bash
   ps aux | grep gazebo
   ```

2. **トピックが存在するか確認:**
   ```bash
   ros2 topic list | grep cmd_vel
   ```

3. **手動でコマンド送信してテスト:**
   ```bash
   ros2 topic pub -1 /cmd_vel geometry_msgs/Twist \
     "{linear: {x: 0.1}, angular: {}}"
   ```

### Gazeboが遅い場合

グラフィックスを無効化（ロボット制御のみの場合）：

```bash
ros2 launch tb4_square turtlebot4_sim.launch.py \
  rviz:=false localization:=false nav2:=false slam:=false
```

## 制御パラメータの説明

### linear.x (前後移動)
- 正の値: 前進
- 負の値: 後退
- 単位: m/s
- 推奨範囲: -0.5 ～ 0.5

### angular.z (回転)
- 正の値: 反時計回り
- 負の値: 時計回り
- 単位: rad/s
- 推奨範囲: -1.0 ～ 1.0

## 実装例

### 自分の制御スクリプト作成

```python
#!/usr/bin/env python3
import rclpy
from geometry_msgs.msg import Twist
import time

rclpy.init()
node = rclpy.create_node('my_controller')
pub = node.create_publisher(Twist, '/cmd_vel', 10)

msg = Twist()
msg.linear.x = 0.2    # 前進0.2 m/s
msg.angular.z = 0.0   # 回転なし

# 5秒間送信
for i in range(100):
    pub.publish(msg)
    time.sleep(0.05)

rclpy.shutdown()
```

## 次のステップ

- Nav2ナビゲーションを有効化: `nav2:=true`
- SLAMマッピング: `slam:=true`
- 自己位置推定: `localization:=true`

詳細は[TurtleBot4公式ドキュメント](https://turtlebot.github.io/)を参照してください。
