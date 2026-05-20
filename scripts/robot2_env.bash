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

_robot2_discovery_server="192.168.11.22:11811;"
_robot2_discovery_host="${_robot2_discovery_server%%:*}"

_robot2_write_fastdds_profile() {
  local profile_dir profile_path profile_user local_ip

  profile_dir="${XDG_RUNTIME_DIR:-/tmp}"
  profile_user="${USER:-$(id -un)}"
  profile_path="${profile_dir}/robot2_pc_fastdds_${profile_user}.xml"
  local_ip="$(
    ip -4 route get "${_robot2_discovery_host}" 2>/dev/null |
      awk '{
        for (i = 1; i <= NF; ++i) {
          if ($i == "src" && (i + 1) <= NF) {
            print $(i + 1)
            exit
          }
        }
      }'
  )"

  if [[ -z "${local_ip}" ]]; then
    local_ip="$(
      ip -4 -o addr show up scope global 2>/dev/null |
        awk 'NR == 1 { split($4, cidr, "/"); print cidr[1] }'
    )"
  fi

  if [[ -z "${local_ip}" ]]; then
    unset FASTRTPS_DEFAULT_PROFILES_FILE
    echo "[WARN] Fast DDS profile was not generated because no IPv4 address was found for robot discovery."
    return 0
  fi

  mkdir -p "${profile_dir}"
  cat >"${profile_path}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
  <transport_descriptors>
    <transport_descriptor>
      <transport_id>robot2_pc_udp_whitelist</transport_id>
      <type>UDPv4</type>
      <interfaceWhiteList>
        <address>127.0.0.1</address>
        <address>${local_ip}</address>
      </interfaceWhiteList>
    </transport_descriptor>
  </transport_descriptors>

  <participant profile_name="robot2_pc_participant" is_default_profile="true">
    <rtps>
      <useBuiltinTransports>false</useBuiltinTransports>
      <userTransports>
        <transport_id>robot2_pc_udp_whitelist</transport_id>
      </userTransports>
    </rtps>
  </participant>
</profiles>
EOF

  export FASTRTPS_DEFAULT_PROFILES_FILE="${profile_path}"
}

export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
_robot2_write_fastdds_profile
# Keep this aligned with /etc/turtlebot4_discovery/setup.bash on the robot/PC.
# Fast DDS examples accept the first server without a leading ';', but we keep
# the same trailing ';' format here to avoid drift between shell entrypoints.
export ROS_SUPER_CLIENT="${ROBOT2_ROS_SUPER_CLIENT:-True}"
export ROS_DISCOVERY_SERVER="${_robot2_discovery_server}"

echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
echo "FASTRTPS_DEFAULT_PROFILES_FILE=${FASTRTPS_DEFAULT_PROFILES_FILE-}"
echo "ROS_SUPER_CLIENT=${ROS_SUPER_CLIENT}"
echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
