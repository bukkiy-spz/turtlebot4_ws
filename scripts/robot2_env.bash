#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Source this file instead:"
  echo "  source scripts/robot2_env.bash"
  exit 1
fi

_tb4_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=robot_env_common.bash
source "${_tb4_script_dir}/robot_env_common.bash"

export TB4_ROS_DOMAIN_ID=0
export TB4_DISCOVERY_SERVER="192.168.11.22:11811;"
export TB4_DISCOVERY_SERVER_ID=2

tb4_setup_robot_env "robot2" "0" "192.168.11.22:11811;" "2" "${BASH_SOURCE[0]}"
