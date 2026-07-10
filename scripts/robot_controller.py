#!/usr/bin/env python3
"""
TurtleBot4 シミュレータ制御スクリプト
Gazeboでロボットを動かすための簡単なコントローラ
"""

import rclpy
from geometry_msgs.msg import Twist
import time
import math
import sys


class RobotController:
    def __init__(self, cmd_vel_topic="/cmd_vel"):
        rclpy.init()
        self.node = rclpy.create_node('robot_controller')
        self.publisher = self.node.create_publisher(Twist, cmd_vel_topic, 10)
        self.cmd_vel_topic = cmd_vel_topic
        print(f"[INFO] ロボットコントローラ初期化完了 ({cmd_vel_topic})")
        time.sleep(1)  # publisherが準備されるのを待つ

    def send_command(self, linear_x=0.0, angular_z=0.0, duration=1.0):
        """指定時間、速度コマンドを送信"""
        msg = Twist()
        msg.linear.x = linear_x
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = angular_z
        
        start_time = time.time()
        while time.time() - start_time < duration:
            self.publisher.publish(msg)
            rclpy.spin_once(self.node, timeout_sec=0.01)
            time.sleep(0.05)
        
        # 停止
        stop_msg = Twist()
        self.publisher.publish(stop_msg)

    def move_forward(self, distance=0.5, speed=0.2):
        """前に移動"""
        duration = distance / speed
        print(f"[MOVE] 前進: {distance}m (速度: {speed}m/s, 時間: {duration:.2f}s)")
        self.send_command(linear_x=speed, duration=duration)

    def move_backward(self, distance=0.5, speed=0.2):
        """後ろに移動"""
        duration = distance / speed
        print(f"[MOVE] 後退: {distance}m")
        self.send_command(linear_x=-speed, duration=duration)

    def rotate(self, angle_rad=math.pi/2, speed=0.5):
        """指定角度回転 (反時計回り)"""
        duration = angle_rad / speed
        angle_deg = math.degrees(angle_rad)
        print(f"[MOVE] 回転: {angle_deg:.1f}° (角速度: {speed}rad/s, 時間: {duration:.2f}s)")
        self.send_command(angular_z=speed, duration=duration)

    def draw_square(self, side_length=0.5, speed=0.2):
        """正方形を描く"""
        print(f"\n[SQUARE] 正方形描画開始 (辺の長さ: {side_length}m)")
        for i in range(4):
            print(f"  辺 {i+1}/4")
            self.move_forward(distance=side_length, speed=speed)
            time.sleep(0.2)
            self.rotate(angle_rad=math.pi/2, speed=0.5)
            time.sleep(0.2)
        print("[SQUARE] 正方形描画完了\n")

    def draw_circle(self, radius=0.3, speed=0.2, duration=10.0):
        """円を描く"""
        print(f"[CIRCLE] 円描画開始 (半径: {radius}m, 時間: {duration}s)")
        # 円運動: v = rω より ω = v/r
        angular_speed = speed / radius
        msg = Twist()
        msg.linear.x = speed
        msg.angular.z = angular_speed
        
        start_time = time.time()
        while time.time() - start_time < duration:
            self.publisher.publish(msg)
            rclpy.spin_once(self.node, timeout_sec=0.01)
            time.sleep(0.05)
        
        # 停止
        stop_msg = Twist()
        self.publisher.publish(stop_msg)
        print("[CIRCLE] 円描画完了\n")

    def demo_sequence(self):
        """デモンストレーションシーケンス"""
        print("\n" + "="*50)
        print("TurtleBot4 シミュレータ デモンストレーション開始")
        print("="*50 + "\n")
        
        # 1. 前進
        print("ステップ1: 前進")
        self.move_forward(distance=0.5, speed=0.2)
        time.sleep(1)
        
        # 2. 90度回転
        print("\nステップ2: 90度回転")
        self.rotate(angle_rad=math.pi/2, speed=0.5)
        time.sleep(1)
        
        # 3. 正方形描画
        print("\nステップ3: 正方形描画")
        self.draw_square(side_length=0.4, speed=0.15)
        time.sleep(1)
        
        # 4. 円描画
        print("\nステップ4: 円描画")
        self.draw_circle(radius=0.3, speed=0.15, duration=8.0)
        
        print("\n" + "="*50)
        print("デモンストレーション完了")
        print("="*50 + "\n")

    def shutdown(self):
        """クリーンアップ"""
        # 停止コマンド送信
        stop_msg = Twist()
        self.publisher.publish(stop_msg)
        rclpy.shutdown()


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "demo"
    
    controller = RobotController()
    
    try:
        if command == "demo":
            controller.demo_sequence()
        elif command == "square":
            side = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
            controller.draw_square(side_length=side)
        elif command == "circle":
            radius = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
            duration = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
            controller.draw_circle(radius=radius, duration=duration)
        elif command == "forward":
            distance = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
            controller.move_forward(distance=distance)
        elif command == "rotate":
            angle_deg = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
            controller.rotate(angle_rad=math.radians(angle_deg))
        else:
            print(f"未知のコマンド: {command}")
            print("使用方法:")
            print("  python3 robot_controller.py demo            # デモ実行")
            print("  python3 robot_controller.py square [0.5]    # 正方形描画")
            print("  python3 robot_controller.py circle [0.3] [10]  # 円描画")
            print("  python3 robot_controller.py forward [0.5]   # 前進")
            print("  python3 robot_controller.py rotate [90]     # 回転(度数法)")
    finally:
        controller.shutdown()


if __name__ == "__main__":
    main()
