#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
robot_name="${TB4_ROBOT_NAME:-robot2}"
env_script="${TB4_ENV_SCRIPT:-${script_dir}/robot2_env.bash}"
workspace_dir="$(cd "${script_dir}/.." && pwd)"
rviz_config="${TB4_RVIZ_CONFIG:-${workspace_dir}/src/tb4_square/rviz/robot2.rviz}"

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
  # shellcheck disable=SC1090
  source "${env_script}"
}

setup_sim_env() {
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
  grep -Eq "^/${robot_name}/odom$" <<<"${topics}" && grep -Eq "^/${robot_name}/tf$" <<<"${topics}"
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
  wait_for_robot_topics || echo "[WARN] /${robot_name}/odom と /${robot_name}/tf がまだ見えていません。RViz は起動しますが空表示の可能性があります。"
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

ros2 launch tb4_square robot2_rviz.launch.py \
  namespace:="${robot_name}" \
  rviz_config:="${rviz_config}" \
  "${launch_args[@]}"
