# TB4 free_fleet Real Robot Troubleshooting

このファイルは `turtlebot4_ws` 視点の Robot 側トラブルメモです。

## 1. Robot 再起動後に時計が戻る

症状:

- `date` が 2025 に戻る
- `chronyc tracking` が `506 Cannot talk to daemon`

確認:

```bash
date
chronyc tracking
curl -I http://192.168.186.2
```

`curl` の `Date:` は Create3 側の現在時刻の参考になります。

対処:

```bash
grep '^server ' /etc/chrony/chrony.conf
sudo timedatectl set-ntp false
sudo date -s '2026-05-14 16:07:39'
sudo systemctl enable --now chrony
sleep 3
chronyc tracking
chronyc sources -v
```

正しい upstream:

```text
server 192.168.11.104
```

## 2. `scan` だけ古い

確認:

```bash
date +%s
timeout 5 ros2 topic echo /robot2/scan --once
```

対処:

```bash
turtlebot4-daemon-restart
sleep 10
```

戻らなければ robot 再起動。

## 3. `amcl_pose` は出るのに `map -> odom` が安定しない

まず少し待つ:

```bash
timeout 10 ros2 run tf2_ros tf2_echo map odom --ros-args -r /tf:=/robot2/tf -r /tf_static:=/robot2/tf_static
```

起動直後は 1 回だけ `Invalid frame ID "map"` が出てもよいです。
その後に transform が出れば正常です。

## 4. `map -> odom` は `/robot2/tf` にいるが container に流れない

原因:

- bridge は global `/tf` を見ている
- `map -> odom` は `/robot2/tf` 側にいる

対処:

- Robot 側 `/robot2/tf -> /tf` relay を起動
- Robot 側 bridge を再起動

## 5. Nav2/costmap が `rplidar_link` を捨てる

症状:

```text
Message Filter dropping message: frame 'rplidar_link' ...
```

意味:

- costmap がその scan 時刻の TF を見つけられない

まず見るもの:

```bash
date +%s
timeout 5 ros2 topic echo /robot2/scan --once
timeout 5 ros2 topic echo /robot2/tf --once
timeout 5 ros2 topic echo /robot2/odom --once
```

## 6. 手動で robot を動かしたあとに Nav2 が崩れた

おすすめ復旧順:

1. `nav2_send_navigate_to_pose.py` 停止
2. Robot 側 `nav2.launch.py` 停止
3. Robot 側 `localization.launch.py` 停止
4. `scan/tf/odom` の時刻確認
5. `localization` 起動
6. `initialpose`
7. `amcl_pose` と `map -> odom` 確認
8. relay
9. bridge
10. `nav2.launch.py`

## 7. Robot 側 direct Nav2 で動くか切り分ける

```bash
ros2 action send_goal /robot2/navigate_to_pose nav2_msgs/action/NavigateToPose \
"{pose: {header: {frame_id: map}, pose: {position: {x: -1.25, y: -0.55, z: 0.0}, orientation: {w: 1.0}}}}"
```

これで動けば、free_fleet より先に robot 側 Nav2 は OK です。

## 8. 使ってはいけない地図パス

NG:

```text
/home/masu_ubu/rmf_ws/maps/tb4/tb4_map.yaml
```

OK:

```text
/home/ubuntu/maps/tb4/tb4_map.yaml
```

## 9. `Behavior Tree tick rate 100.00 was exceeded!`

この warning 単体は、実機 Nav2 ではそこまで珍しくない。

見方:

- 制御周期 100Hz に対して BT の処理が少し遅れた
- 単発なら様子見でよい
- `Reached the goal!` まで出ていれば致命傷ではない

## 10. `Failed to make progress` のあとにゴールできる

今回のように:

- `Failed to make progress`
- `clear entirely the local_costmap`
- 再試行
- `Reached the goal!`

という流れなら、Nav2 の recovery が効いている。

改善の方向:

- waypoint を壁や障害物から少し離す
- 近すぎる waypoint を離す
- `initialpose` の向きを実機の向きに合わせる

## 11. `map_saver_cli` が `Failed to spin map subscription`

原因:

- 実際の map topic が `/robot2/map`
- なのに `map_saver_cli` が `/map` を見ていた

対処:

```bash
source /opt/ros/humble/setup.bash
turtlebot4-source

ros2 run nav2_map_server map_saver_cli \
  -f /home/ubuntu/maps/tb4/tb4_map_20260518 \
  --ros-args -r map:=/robot2/map
```
