#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TB4_ROBOT_NAME=robot2
export TB4_ENV_SCRIPT="${script_dir}/robot2_env.bash"
export TB4_RVIZ_CONFIG="${script_dir}/../src/tb4_square/rviz/robot2_slam.rviz"

exec "${script_dir}/robot_localization_rviz_generic.sh" "$@"
