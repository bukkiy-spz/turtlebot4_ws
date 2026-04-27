#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Source this file instead:"
  echo "  source scripts/robot2_env.bash"
  exit 1
fi

_robot2_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_robot2_ws="$(cd "${_robot2_script_dir}/.." && pwd)"

cd "${_robot2_ws}" || return
# Guard against nounset (set -u) callers such as robot2_square.sh.
export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES-}"
export AMENT_PYTHON_EXECUTABLE="${AMENT_PYTHON_EXECUTABLE-$(command -v python3)}"

_robot2_restore_nounset=0
if [[ $- == *u* ]]; then
  _robot2_restore_nounset=1
  set +u
fi

source /opt/ros/humble/setup.bash
if [[ -f "${_robot2_ws}/install/setup.bash" ]]; then
  source "${_robot2_ws}/install/setup.bash"
fi

if [[ ${_robot2_restore_nounset} -eq 1 ]]; then
  set -u
fi

export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DISCOVERY_SERVER=192.168.188.22:11811

echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
