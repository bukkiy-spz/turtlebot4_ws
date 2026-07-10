#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_dir="$(cd "${script_dir}/.." && pwd)"
rviz_config="${TB4_RVIZ_CONFIG:-${workspace_dir}/src/tb4_square/rviz/multi_robot_full.rviz}"

export COLCON_TRACE="${COLCON_TRACE-}"
export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES-}"

restore_nounset=0
if [[ $- == *u* ]]; then
  restore_nounset=1
  set +u
fi

source /opt/ros/humble/setup.bash
if [[ -f "${workspace_dir}/install/setup.bash" ]]; then
  source "${workspace_dir}/install/setup.bash"
fi
source "${script_dir}/shared_multi_robot_env.bash"

if [[ ${restore_nounset} -eq 1 ]]; then
  set -u
fi

ros2 daemon stop
ros2 daemon start

echo "[INFO] Starting multi-robot full RViz"
echo "[INFO] Config: ${rviz_config}"
echo "[INFO] Launching display-only TF/scan relays for robot2, robot5, robot6"

exec ros2 launch tb4_square multi_robot_rviz.launch.py \
  rviz_config:="${rviz_config}" \
  use_sim_time:=false
