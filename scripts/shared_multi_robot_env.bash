#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Source this file instead:"
  echo "  source scripts/shared_multi_robot_env.bash"
  exit 1
fi

_tb4_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=robot_env_common.bash
source "${_tb4_script_dir}/robot_env_common.bash"

export TB4_ROS_DOMAIN_ID=0

tb4_setup_multi_robot_env \
  "tb4_multi_robot" \
  "${TB4_ROS_DOMAIN_ID}" \
  "${BASH_SOURCE[0]}" \
  "192.168.11.22:11811:2" \
  "192.168.11.25:11811:5" \
  "192.168.11.26:11811:6"
