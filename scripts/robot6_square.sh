#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TB4_ROBOT_NAME=robot6 TB4_ENV_SCRIPT="${script_dir}/robot6_env.bash" \
  exec "${script_dir}/robot_square_generic.sh" "$@"
