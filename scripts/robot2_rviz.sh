#!/usr/bin/env bash
# RViz ビジュアライザー起動スクリプト（ロボットデータ源は別途必要）
#
# 使用方法：
#   ./scripts/robot2_rviz.sh              # 自動判定 (実機 topic が見えれば robot, それ以外は sim)
#   ./scripts/robot2_rviz.sh --robot      # ロボット実機 (Discovery Server 使用)
#   ./scripts/robot2_rviz.sh --sim        # シミュレーション
#
# 完全なシミュレーション環境を起動したい場合：
#   ros2 launch tb4_square turtlebot4_sim.launch.py rviz:=true
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mode="auto"
if [[ ${1-} == "--robot" ]]; then
	mode="robot"
	shift
elif [[ ${1-} == "--sim" ]]; then
	mode="sim"
	shift
fi

has_use_sim_time_arg=0
for arg in "$@"; do
	if [[ "${arg}" == use_sim_time:=* ]]; then
		has_use_sim_time_arg=1
		break
	fi
done

setup_robot_env() {
	# shellcheck source=robot2_env.bash
	source "${script_dir}/robot2_env.bash"
}

setup_sim_env() {
	# Sim向け既定: ローカル discovery を使う。
	# set -u 有効時でも colcon 生成 setup を安全に読めるようにする。
	export COLCON_TRACE="${COLCON_TRACE-}"
	export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES-}"

	restore_nounset=0
	if [[ $- == *u* ]]; then
		restore_nounset=1
		set +u
	fi

	source /opt/ros/humble/setup.bash
	if [[ -f "${script_dir}/../install/setup.bash" ]]; then
		source "${script_dir}/../install/setup.bash"
	fi

	if [[ ${restore_nounset} -eq 1 ]]; then
		set -u
	fi

	unset ROS_DISCOVERY_SERVER
	unset ROS_STATIC_PEERS
	unset ROS_SUPER_CLIENT
	unset FASTRTPS_DEFAULT_PROFILES_FILE
}

restart_ros_daemon() {
	ros2 daemon stop
	ros2 daemon start
}

robot_topics_ready() {
	local topics
	topics="$(ros2 topic list 2>/dev/null || true)"
	grep -Eq '^/robot2/odom$' <<<"${topics}" && grep -Eq '^/robot2/tf$' <<<"${topics}"
}

wait_for_robot_topics() {
	local attempt
	for attempt in {1..6}; do
		if robot_topics_ready; then
			if [[ ${attempt} -gt 1 ]]; then
				echo "[INFO] robot topics detected after ${attempt} checks"
			fi
			return 0
		fi
		sleep 2
	done
	return 1
}

if [[ "${mode}" == "robot" ]]; then
	setup_robot_env
	restart_ros_daemon
	wait_for_robot_topics || echo "[WARN] /robot2/odom と /robot2/tf がまだ見えていません。RViz は起動しますが空表示の可能性があります。"
elif [[ "${mode}" == "sim" ]]; then
	setup_sim_env
	restart_ros_daemon
else
	setup_robot_env
	restart_ros_daemon
	if wait_for_robot_topics; then
		mode="robot"
		echo "[INFO] mode=auto -> robot topics detected, using Discovery Server"
	else
		echo "[WARN] mode=auto -> robot topics not detected, falling back to sim"
		setup_sim_env
		restart_ros_daemon
		mode="sim"
	fi
fi

launch_args=("$@")
if [[ ${has_use_sim_time_arg} -eq 0 ]]; then
	if [[ "${mode}" == "robot" ]]; then
		launch_args+=("use_sim_time:=false")
		echo "[INFO] mode=robot -> use_sim_time:=false"
	else
		clock_pub_count="$(ros2 topic info /clock -v 2>/dev/null | awk -F': ' '/Publisher count/ {print $2; exit}' || true)"
		if [[ -n "${clock_pub_count}" && "${clock_pub_count}" != "0" ]]; then
			launch_args+=("use_sim_time:=true")
			echo "[INFO] /clock publisher detected (${clock_pub_count}) -> use_sim_time:=true"
		else
			launch_args+=("use_sim_time:=false")
			echo "[WARN] /clock publisher not detected -> use_sim_time:=false"
		fi
	fi
fi

ros2 launch tb4_square robot2_rviz.launch.py "${launch_args[@]}"
