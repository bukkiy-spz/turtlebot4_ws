#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
robot_name="${TB4_ROBOT_NAME:-robot2}"
env_script="${TB4_ENV_SCRIPT:-${script_dir}/robot2_env.bash}"

# shellcheck disable=SC1090
source "${env_script}"

discovery_host="${ROS_DISCOVERY_SERVER%%:*}"
discovery_host="${discovery_host%;}"

cmd_vel_topic="/${robot_name}/cmd_vel"
scan_topic="/${robot_name}/scan"
tf_topic="/${robot_name}/tf"
odom_topic="/${robot_name}/odom"
joint_states_topic="/${robot_name}/joint_states"
robot_description_topic="/${robot_name}/robot_description"
drive_distance_action="/${robot_name}/drive_distance"
rotate_angle_action="/${robot_name}/rotate_angle"

refresh_topic_list() {
  local attempt

  for attempt in 1 2 3 4 5; do
    topic_list="$(ros2 topic list 2>/dev/null || true)"
    if grep -qx "${scan_topic}" <<<"${topic_list}" || \
      grep -qx "${tf_topic}" <<<"${topic_list}" || \
      grep -qx "${odom_topic}" <<<"${topic_list}"; then
      return 0
    fi
    sleep 2
  done

  return 1
}

refresh_action_list() {
  local attempt

  for attempt in 1 2 3 4 5; do
    action_list="$(ros2 action list 2>/dev/null || true)"
    if grep -qx "${drive_distance_action}" <<<"${action_list}" || \
      grep -qx "${rotate_angle_action}" <<<"${action_list}"; then
      return 0
    fi
    sleep 2
  done

  return 1
}

check_topic_visible() {
  local topic="$1"
  if grep -qx "${topic}" <<<"${topic_list}"; then
    echo "[OK] ${topic} is visible"
    return 0
  fi

  local count
  count="$(get_publisher_count "${topic}")" || true
  if [[ "${count}" != "unknown" && -n "${count}" && "${count}" != "0" ]]; then
    echo "[WARN] ${topic} is not listed by 'ros2 topic list', but publisher count is ${count}"
    return 0
  fi

  echo "[ERROR] ${topic} is not visible"
  return 1
}

check_action_visible() {
  local action_name="$1"
  if grep -qx "${action_name}" <<<"${action_list}"; then
    echo "[OK] ${action_name} is visible"
    return 0
  fi

  echo "[WARN] ${action_name} is not visible"
  return 1
}

get_publisher_count() {
  local topic="$1"
  local info
  local attempt

  for attempt in 1 2 3; do
    if info="$(ros2 topic info "${topic}" -v 2>/dev/null)"; then
      awk -F': ' '/Publisher count/ {print $2; exit}' <<<"${info}"
      return 0
    fi
    sleep 1
  done

  echo "unknown"
  return 1
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

  if timeout 5s ros2 topic echo "${topic}" --once "$@" >/dev/null 2>&1; then
    echo "[OK] ${topic} delivered a sample"
    return 0
  fi

  echo "[WARN] ${topic} did not deliver a sample within 5 seconds"
  return 1
}

ros2 daemon stop >/dev/null 2>&1 || true
ros2 daemon start >/dev/null 2>&1 || true
sleep 2
refresh_topic_list || true
refresh_action_list || true

echo "== Environment =="
echo "ROBOT_NAME=${robot_name}"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
echo "FASTRTPS_DEFAULT_PROFILES_FILE=${FASTRTPS_DEFAULT_PROFILES_FILE-}"
echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
echo

echo "== Reachability =="
ping -c 1 "${discovery_host}" >/dev/null 2>&1 && echo "[OK] robot ping succeeded" || echo "[WARN] robot ping failed"
echo

echo "== Topic visibility =="
cmd_vel_ok=0
scan_ok=0
tf_ok=0
odom_ok=0
joint_states_ok=0
scan_pub_ok=0
tf_pub_ok=0
drive_distance_action_ok=0
rotate_angle_action_ok=0

check_topic_visible "${cmd_vel_topic}" || cmd_vel_ok=1
check_topic_visible "${scan_topic}" || scan_ok=1
check_topic_visible "${tf_topic}" || tf_ok=1
check_topic_visible "${odom_topic}" || odom_ok=1
check_topic_visible "${joint_states_topic}" || joint_states_ok=1
report_publisher_count "${scan_topic}" || scan_pub_ok=1
report_publisher_count "${tf_topic}" || tf_pub_ok=1
check_action_visible "${drive_distance_action}" || drive_distance_action_ok=1
check_action_visible "${rotate_angle_action}" || rotate_angle_action_ok=1
echo

echo "== Live data =="
live_scan_ok=0
live_odom_ok=0
live_joint_states_ok=0
check_live_sample "${robot_description_topic}" --qos-durability transient_local || true
check_live_sample "${scan_topic}" --qos-reliability best_effort || live_scan_ok=1
check_live_sample "${odom_topic}" --qos-reliability best_effort || live_odom_ok=1
check_live_sample "${joint_states_topic}" --qos-reliability best_effort || live_joint_states_ok=1
echo

echo "== Nodes =="
ros2 node list | sort || true
echo

if ((cmd_vel_ok != 0)); then
  echo "== Diagnosis =="
  echo "[ERROR] ${cmd_vel_topic} is missing."
  if ((drive_distance_action_ok == 0 && rotate_angle_action_ok == 0)); then
    echo "[WARN] Create3 action servers are visible, so square_driver の action フォールバックは使える可能性があります."
  fi
  if ((scan_pub_ok == 0 || tf_pub_ok == 0)); then
    echo "[WARN] Discovery metadata for some robot topics is visible, but live data is not flowing."
    echo "[WARN] This points more to DDS transport / NIC mismatch than a total robot-side bringup failure."
  else
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
  echo "[ERROR] ${scan_topic} is listed but has no publishers."
  echo "[ERROR] Robot-side sensor/drive bringup is likely partial or stale."
  exit 1
fi

if ((live_scan_ok != 0 || live_odom_ok != 0 || live_joint_states_ok != 0)); then
  echo "== Diagnosis =="
  echo "[WARN] Robot topics are visible, but one or more live samples did not arrive."
  echo "[WARN] RViz でモデルだけ見えて LaserScan や移動が出ないときの典型です."
  echo "[WARN] Discovery は通っていても、実データ通信や実機側 bringup が不安定な可能性があります."
  exit 1
fi

echo "== Diagnosis =="
echo "[OK] ${cmd_vel_topic} is visible from this PC."
