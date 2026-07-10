#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
robot_name="${TB4_ROBOT_NAME:-robot2}"
env_script="${TB4_ENV_SCRIPT:-${script_dir}/robot2_env.bash}"
workspace_dir="$(cd "${script_dir}/.." && pwd)"
rviz_config="${TB4_RVIZ_CONFIG:-${workspace_dir}/src/tb4_square/rviz/robot2_slam.rviz}"

# shellcheck disable=SC1090
source "${env_script}"

ros2 daemon stop >/dev/null 2>&1 || true
ros2 daemon start >/dev/null 2>&1 || true

ros2 launch tb4_square robot2_rviz.launch.py \
  namespace:="${robot_name}" \
  rviz_config:="${rviz_config}" \
  tf_topic:=tf_nav \
  use_sim_time:=false \
  "$@"
