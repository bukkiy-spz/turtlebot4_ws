#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=robot2_env.bash
source "${script_dir}/robot2_env.bash"

check_topic_visible() {
	local topic="$1"
	if grep -qx "${topic}" <<<"${topic_list}"; then
		echo "[OK] ${topic} is visible"
		return 0
	fi

	echo "[ERROR] ${topic} is not visible"
	return 1
}

get_publisher_count() {
	local topic="$1"
	local info

	if ! info="$(ros2 topic info "${topic}" -v 2>/dev/null)"; then
		echo "unknown"
		return 1
	fi

	awk -F': ' '/Publisher count/ {print $2; exit}' <<<"${info}"
}

report_publisher_count() {
	local topic="$1"
	local count

	count="$(get_publisher_count "${topic}")" || true
	if [[ "${count}" == "unknown" || -z "${count}" ]]; then
		echo "[WARN] ${topic} publisher count could not be read"
		return 1
	fi

	if [[ "${count}" == "0" ]]; then
		echo "[ERROR] ${topic} has 0 publishers"
		return 1
	fi

	echo "[OK] ${topic} has ${count} publisher(s)"
	return 0
}

check_live_sample() {
	local topic="$1"
	shift

	if timeout 3s ros2 topic echo "${topic}" --once "$@" >/dev/null 2>&1; then
		echo "[OK] ${topic} delivered a sample"
		return 0
	fi

	echo "[WARN] ${topic} did not deliver a sample within 3 seconds"
	return 1
}

ros2 daemon stop >/dev/null 2>&1 || true
ros2 daemon start >/dev/null 2>&1 || true
sleep 2
topic_list="$(ros2 topic list 2>/dev/null || true)"

echo "== Environment =="
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
echo

echo "== Reachability =="
ping -c 1 192.168.188.22 >/dev/null 2>&1 && echo "[OK] robot ping succeeded" || echo "[WARN] robot ping failed"
echo

echo "== Topic visibility =="
cmd_vel_ok=0
scan_ok=0
tf_ok=0
scan_pub_ok=0
tf_pub_ok=0

check_topic_visible /robot2/cmd_vel || cmd_vel_ok=1
check_topic_visible /robot2/scan || scan_ok=1
check_topic_visible /robot2/tf || tf_ok=1
report_publisher_count /robot2/scan || scan_pub_ok=1
report_publisher_count /robot2/tf || tf_pub_ok=1
echo

echo "== Live data =="
live_scan_ok=0
check_live_sample /robot2/robot_description --qos-durability transient_local || true
check_live_sample /robot2/scan --qos-reliability best_effort || live_scan_ok=1
echo

echo "== Nodes =="
ros2 node list | sort || true
echo

if ((cmd_vel_ok != 0)); then
	echo "== Diagnosis =="
	echo "[ERROR] /robot2/cmd_vel is missing."
	if ((live_scan_ok != 0)); then
		echo "[ERROR] Live robot topics also look down, so robot-side bringup is likely unhealthy."
	fi
	echo "Suggested commands on the robot:"
	echo "  turtlebot4-source"
	echo "  turtlebot4-daemon-restart"
	echo "  ros2 topic list | grep cmd_vel"
	echo "  ros2 node list | grep -E 'create3|repub|twist|mux'"
	exit 1
fi

if ((scan_pub_ok != 0)); then
	echo "== Diagnosis =="
	echo "[ERROR] /robot2/scan is listed but has no publishers."
	echo "[ERROR] Robot-side sensor/drive bringup is likely partial or stale."
	exit 1
fi

echo "== Diagnosis =="
echo "[OK] /robot2/cmd_vel is visible from this PC."
