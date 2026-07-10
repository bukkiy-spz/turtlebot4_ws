#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_dir="$(cd "${script_dir}/.." && pwd)"
robot_name="${TB4_ROBOT_NAME:-robot2}"
env_script="${TB4_ENV_SCRIPT:-${script_dir}/robot2_env.bash}"
params_file="${TB4_SLAM_PARAMS_FILE:-${workspace_dir}/src/tb4_square/config/robot2_slam.yaml}"
rviz_config="${TB4_RVIZ_CONFIG:-${workspace_dir}/src/tb4_square/rviz/robot2_slam.rviz}"

# shellcheck disable=SC1090
source "${env_script}"

ros2 daemon stop >/dev/null 2>&1 || true
ros2 daemon start >/dev/null 2>&1 || true

topic_list="$(ros2 topic list 2>/dev/null || true)"
if ! grep -qx "/${robot_name}/scan" <<<"${topic_list}" || ! grep -qx "/${robot_name}/tf" <<<"${topic_list}"; then
  echo "[WARN] /${robot_name}/scan または /${robot_name}/tf がまだ見えていません。"
  echo "[WARN] 実機との Discovery 接続を確認してから再実行してください。"
fi

launch_args=("$@")
has_use_sim_time_arg=0
for arg in "${launch_args[@]}"; do
  if [[ "${arg}" == use_sim_time:=* ]]; then
    has_use_sim_time_arg=1
    break
  fi
done

if [[ ${has_use_sim_time_arg} -eq 0 ]]; then
  launch_args+=("use_sim_time:=false")
fi

ros2 launch tb4_square robot2_slam.launch.py \
  namespace:="${robot_name}" \
  params_file:="${params_file}" \
  rviz_config:="${rviz_config}" \
  "${launch_args[@]}"
