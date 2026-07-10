#!/usr/bin/env bash
set -euo pipefail

listen_ip="${1:-192.168.11.104}"
port="${2:-11811}"
server_id="${3:-0}"

export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES-}"
export AMENT_PYTHON_EXECUTABLE="${AMENT_PYTHON_EXECUTABLE-$(command -v python3)}"

restore_nounset=0
if [[ $- == *u* ]]; then
  restore_nounset=1
  set +u
fi

source /opt/ros/humble/setup.bash

if [[ ${restore_nounset} -eq 1 ]]; then
  set -u
fi

exec fastdds discovery -i "${server_id}" -l "${listen_ip}" -p "${port}"
