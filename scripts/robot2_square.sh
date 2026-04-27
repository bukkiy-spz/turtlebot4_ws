#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=robot2_env.bash
source "${script_dir}/robot2_env.bash"

wait_for_cmd_vel() {
	local attempts=10
	local delay_sec=1

	for ((i = 1; i <= attempts; i++)); do
		if ros2 topic list | grep -qx '/robot2/cmd_vel'; then
			return 0
		fi
		sleep "${delay_sec}"
	done

	return 1
}

wait_for_cmd_vel_subscriber() {
	local attempts=12
	local delay_sec=1
	local info_output

	for ((i = 1; i <= attempts; i++)); do
		info_output="$(ros2 topic info -v /robot2/cmd_vel 2>/dev/null || true)"
		if grep -q "Node name: create3_repub" <<<"${info_output}"; then
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

if ! wait_for_cmd_vel; then
	echo "[ERROR] /robot2/cmd_vel is not visible from this PC."
	echo "[ERROR] The robot-side command bridge is likely not running."
	echo
	echo "Try this next:"
	echo "  ./scripts/robot2_status.sh"
	echo
	echo "On the robot:"
	echo "  turtlebot4-source"
	echo "  turtlebot4-daemon-restart"
	echo "  ros2 topic list | grep cmd_vel"
	echo "  ros2 node list | grep -E 'create3|repub|twist|mux'"
	echo
	echo "Back on this PC:"
	echo "  source scripts/robot2_env.bash"
	echo "  ros2 daemon stop"
	echo "  ros2 daemon start"
	exit 1
fi

if ! wait_for_cmd_vel_subscriber; then
	echo "[ERROR] /robot2/cmd_vel is visible, but robot subscriber 'create3_repub' did not appear."
	echo "[ERROR] Waiting longer did not help, so launching square_driver is likely to fail."
	echo
	echo "Try this next:"
	echo "  ./scripts/robot2_status.sh"
	echo "  ros2 node info /robot2/create3_repub"
	exit 1
fi

ros2 launch tb4_square square_driver.launch.py \
	cmd_vel_topic:=/robot2/cmd_vel \
	wait_for_subscriber_sec:=8.0 \
	"$@"
