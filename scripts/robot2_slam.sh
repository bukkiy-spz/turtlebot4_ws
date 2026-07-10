#!/usr/bin/env bash
# robot2 向け SLAM Toolbox + RViz 起動スクリプト
#
# 使用方法:
#   ./scripts/robot2_slam.sh
#   ./scripts/robot2_slam.sh rviz:=false
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=robot2_env.bash
source "${script_dir}/robot2_env.bash"

ros2 daemon stop >/dev/null 2>&1 || true
ros2 daemon start >/dev/null 2>&1 || true

topic_list="$(ros2 topic list 2>/dev/null || true)"
if ! grep -qx "/robot2/scan" <<<"${topic_list}" || ! grep -qx "/robot2/tf" <<<"${topic_list}"; then
  echo "[WARN] /robot2/scan または /robot2/tf がまだ見えていません。"
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

ros2 launch tb4_square robot2_slam.launch.py "${launch_args[@]}"
