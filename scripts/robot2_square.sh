#!/usr/bin/env bash
# 実機の正方形走行デモを起動する。
# 新しいターミナルから直接呼ばれても動くように、
# ROS 2 本体とこの workspace の setup をここで読み込む。
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_dir="$(cd "${script_dir}/.." && pwd)"

selected_cmd_vel_topic="/robot2/cmd_vel"
selected_subscriber_hint="create3_repub"
selected_reliability="reliable"
selected_control_mode="cmd_vel"
selected_drive_distance_action="/robot2/drive_distance"
selected_rotate_angle_action="/robot2/rotate_angle"

setup_workspace_env() {
	# set -u 有効時でも colcon 生成 setup を安全に読めるようにする。
	export COLCON_TRACE="${COLCON_TRACE-}"
	export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES-}"

	local restore_nounset=0
	if [[ $- == *u* ]]; then
		restore_nounset=1
		set +u
	fi

	if [[ -f /opt/ros/humble/setup.bash ]]; then
		# ROS 2 標準コマンドと依存パッケージを先に読み込む。
		source /opt/ros/humble/setup.bash
	else
		echo "[ERROR] /opt/ros/humble/setup.bash が見つかりません。"
		exit 1
	fi

	if [[ -f "${workspace_dir}/install/setup.bash" ]]; then
		# この workspace でビルドした最新の tb4_square を使う。
		source "${workspace_dir}/install/setup.bash"
	else
		echo "[ERROR] ${workspace_dir}/install/setup.bash が見つかりません。"
		echo "[ERROR] 先に 'colcon build --packages-select tb4_square' を実行してください。"
		exit 1
	fi

	if [[ ${restore_nounset} -eq 1 ]]; then
		set -u
	fi
}

setup_workspace_env

# shellcheck source=robot2_env.bash
source "${script_dir}/robot2_env.bash"

wait_for_topic() {
	local topic="$1"
	local attempts=10
	local delay_sec=1

	for ((i = 1; i <= attempts; i++)); do
		if ros2 topic list | grep -qx "${topic}"; then
			return 0
		fi
		sleep "${delay_sec}"
	done

	return 1
}

detect_cmd_vel_topic() {
	local topic_list
	local info_output

	topic_list="$(ros2 topic list 2>/dev/null || true)"
	if grep -qx '/robot2/cmd_vel_nav' <<<"${topic_list}"; then
		info_output="$(ros2 topic info -v /robot2/cmd_vel_nav 2>/dev/null || true)"
		if grep -q "Node name: velocity_smoother" <<<"${info_output}" || \
			ros2 node list 2>/dev/null | grep -qx '/robot2/velocity_smoother'; then
			selected_cmd_vel_topic="/robot2/cmd_vel_nav"
			selected_subscriber_hint="velocity_smoother"
			selected_reliability="reliable"
			return 0
		fi
	fi

	selected_cmd_vel_topic="/robot2/cmd_vel"
	selected_subscriber_hint="create3_repub"
	selected_reliability="reliable"
	return 0
}

wait_for_actions() {
	local drive_action="$1"
	local rotate_action="$2"
	local attempts=12
	local delay_sec=1
	local action_list

	for ((i = 1; i <= attempts; i++)); do
		action_list="$(ros2 action list 2>/dev/null || true)"
		if grep -qx "${drive_action}" <<<"${action_list}" && grep -qx "${rotate_action}" <<<"${action_list}"; then
			return 0
		fi
		sleep "${delay_sec}"
	done

	return 1
}

wait_for_cmd_vel_subscriber() {
	local topic="$1"
	local preferred_node="$2"
	local attempts=12
	local delay_sec=1
	local info_output

	for ((i = 1; i <= attempts; i++)); do
		info_output="$(ros2 topic info -v "${topic}" 2>/dev/null || true)"
		if [[ -n "${preferred_node}" ]] && grep -q "Node name: ${preferred_node}" <<<"${info_output}"; then
			printf '%s\n' "${info_output}"
			return 0
		fi
		if grep -Eq 'Subscription count: [1-9][0-9]*' <<<"${info_output}"; then
			printf '%s\n' "${info_output}"
			return 0
		fi
		sleep "${delay_sec}"
	done

	printf '%s\n' "${info_output}"
	return 1
}

ros2 daemon stop
ros2 daemon start

detect_cmd_vel_topic

if ! wait_for_topic "${selected_cmd_vel_topic}"; then
	selected_control_mode="action"
	echo "[WARN] ${selected_cmd_vel_topic} is not visible from this PC."
	echo "[INFO] Trying Create3 action mode instead: ${selected_drive_distance_action}, ${selected_rotate_angle_action}"
fi

launch_args=()

if [[ "${selected_control_mode}" == "action" ]]; then
	echo "[INFO] square_driver will use Create3 action mode."
elif [[ "${selected_cmd_vel_topic}" == "/robot2/cmd_vel_nav" ]]; then
	echo "[INFO] Detected active Nav2 velocity smoother; square_driver will publish to ${selected_cmd_vel_topic}."
else
	echo "[INFO] square_driver will publish directly to ${selected_cmd_vel_topic}."
	echo "[INFO] Using reliability=${selected_reliability} so hidden reliable subscribers can still match."
fi

if [[ "${selected_control_mode}" == "cmd_vel" ]] && ! wait_for_cmd_vel_subscriber "${selected_cmd_vel_topic}" "${selected_subscriber_hint}"; then
	echo "[WARN] ${selected_cmd_vel_topic} is visible, but subscriber '${selected_subscriber_hint}' did not appear."
	echo "[INFO] Proceeding with direct ${selected_cmd_vel_topic} publish because cmd_vel itself is visible."
	echo "[INFO] In this robot setup, DDS graph introspection can miss the real subscriber even when motion works."
fi

if [[ "${selected_control_mode}" == "action" ]]; then
	launch_args+=(
		control_mode:=action
		require_subscriber:=false
		wait_for_action_server_sec:=8.0
		drive_distance_action_name:="${selected_drive_distance_action}"
		rotate_angle_action_name:="${selected_rotate_angle_action}"
	)
else
	launch_args+=(
		control_mode:=cmd_vel
		require_subscriber:=false
		wait_for_subscriber_sec:=0.0
		reliability:="${selected_reliability}"
	)
fi

ros2 launch tb4_square square_driver.launch.py \
	cmd_vel_topic:="${selected_cmd_vel_topic}" \
	"${launch_args[@]}" \
	"$@"
