#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TB4_ROBOT_NAME=robot5 TB4_ENV_SCRIPT="${script_dir}/robot5_env.bash" \
  exec "${script_dir}/robot_slam_generic.sh" "$@"
