#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Source this file instead:"
  echo "  source scripts/shared_fleet_env.bash"
  exit 1
fi

export TB4_ROS_DOMAIN_ID=0
export TB4_DISCOVERY_SERVER="${TB4_DISCOVERY_SERVER:-192.168.11.104:11811;}"

_tb4_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=robot_env_common.bash
source "${_tb4_script_dir}/robot_env_common.bash"

tb4_setup_robot_env "tb4_fleet" "${TB4_ROS_DOMAIN_ID}" "${TB4_DISCOVERY_SERVER}" "${BASH_SOURCE[0]}"
