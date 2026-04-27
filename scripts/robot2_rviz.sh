#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=robot2_env.bash
source "${script_dir}/robot2_env.bash"

ros2 daemon stop
ros2 daemon start
ros2 launch tb4_square robot2_rviz.launch.py
