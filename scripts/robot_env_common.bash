#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Source this file from a robot-specific env script instead."
  exit 1
fi

tb4_write_fastdds_profile() {
  local profile_tag="$1"
  local discovery_host="$2"
  local discovery_port="${3:-11811}"
  local discovery_server_id="${4:-0}"
  local profile_dir profile_path profile_user local_ip server_id_hex server_prefix

  profile_dir="${XDG_RUNTIME_DIR:-/tmp}"
  profile_user="${USER:-$(id -un)}"
  profile_path="${profile_dir}/${profile_tag}_pc_fastdds_${profile_user}.xml"
  local_ip="$(
    ip -4 route get "${discovery_host}" 2>/dev/null |
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

  server_id_hex="$(printf '%02x' "${discovery_server_id}")"
  server_prefix="44.53.${server_id_hex}.5f.45.50.52.4f.53.49.4d.41"

  mkdir -p "${profile_dir}"
  cat >"${profile_path}" <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<dds>
  <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <transport_descriptors>
      <transport_descriptor>
        <transport_id>${profile_tag}_pc_udp_whitelist</transport_id>
        <type>UDPv4</type>
        <interfaceWhiteList>
          <address>127.0.0.1</address>
          <address>${local_ip}</address>
        </interfaceWhiteList>
      </transport_descriptor>
    </transport_descriptors>

    <participant profile_name="${profile_tag}_pc_participant" is_default_profile="true">
      <rtps>
        <useBuiltinTransports>false</useBuiltinTransports>
        <userTransports>
          <transport_id>${profile_tag}_pc_udp_whitelist</transport_id>
        </userTransports>
        <builtin>
          <discovery_config>
            <discoveryProtocol>SUPER_CLIENT</discoveryProtocol>
            <discoveryServersList>
              <RemoteServer prefix="${server_prefix}">
                <metatrafficUnicastLocatorList>
                  <locator>
                    <udpv4>
                      <address>${discovery_host}</address>
                      <port>${discovery_port}</port>
                    </udpv4>
                  </locator>
                </metatrafficUnicastLocatorList>
              </RemoteServer>
            </discoveryServersList>
          </discovery_config>
        </builtin>
      </rtps>
    </participant>
  </profiles>
</dds>
EOF

  export FASTRTPS_DEFAULT_PROFILES_FILE="${profile_path}"
  export FASTDDS_DEFAULT_PROFILES_FILE="${profile_path}"
}

tb4_write_fastdds_profile_multi() {
  local profile_tag="$1"
  shift
  local server_specs=("$@")
  local profile_dir profile_path profile_user local_ip
  local spec discovery_host discovery_port discovery_server_id
  local server_entries="" first_host=""

  if [[ ${#server_specs[@]} -eq 0 ]]; then
    unset FASTRTPS_DEFAULT_PROFILES_FILE
    unset FASTDDS_DEFAULT_PROFILES_FILE
    echo "[WARN] Fast DDS multi profile was not generated because no discovery servers were provided."
    return 0
  fi

  first_host="${server_specs[0]}"
  first_host="${first_host%%:*}"

  profile_dir="${XDG_RUNTIME_DIR:-/tmp}"
  profile_user="${USER:-$(id -un)}"
  profile_path="${profile_dir}/${profile_tag}_pc_fastdds_${profile_user}.xml"
  local_ip="$(
    ip -4 route get "${first_host}" 2>/dev/null |
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
    unset FASTDDS_DEFAULT_PROFILES_FILE
    echo "[WARN] Fast DDS multi profile was not generated because no IPv4 address was found for robot discovery."
    return 0
  fi

  for spec in "${server_specs[@]}"; do
    IFS=':' read -r discovery_host discovery_port discovery_server_id <<<"${spec}"
    if [[ -z "${discovery_host}" || -z "${discovery_server_id}" ]]; then
      continue
    fi
    if [[ -z "${discovery_port}" ]]; then
      discovery_port="11811"
    fi
    local server_id_hex server_prefix
    server_id_hex="$(printf '%02x' "${discovery_server_id}")"
    server_prefix="44.53.${server_id_hex}.5f.45.50.52.4f.53.49.4d.41"
    server_entries+=$'\n'"              <RemoteServer prefix=\"${server_prefix}\">"
    server_entries+=$'\n'"                <metatrafficUnicastLocatorList>"
    server_entries+=$'\n'"                  <locator>"
    server_entries+=$'\n'"                    <udpv4>"
    server_entries+=$'\n'"                      <address>${discovery_host}</address>"
    server_entries+=$'\n'"                      <port>${discovery_port}</port>"
    server_entries+=$'\n'"                    </udpv4>"
    server_entries+=$'\n'"                  </locator>"
    server_entries+=$'\n'"                </metatrafficUnicastLocatorList>"
    server_entries+=$'\n'"              </RemoteServer>"
  done

  mkdir -p "${profile_dir}"
  cat >"${profile_path}" <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<dds>
  <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <transport_descriptors>
      <transport_descriptor>
        <transport_id>${profile_tag}_pc_udp_whitelist</transport_id>
        <type>UDPv4</type>
        <interfaceWhiteList>
          <address>127.0.0.1</address>
          <address>${local_ip}</address>
        </interfaceWhiteList>
      </transport_descriptor>
    </transport_descriptors>

    <participant profile_name="${profile_tag}_pc_participant" is_default_profile="true">
      <rtps>
        <useBuiltinTransports>false</useBuiltinTransports>
        <userTransports>
          <transport_id>${profile_tag}_pc_udp_whitelist</transport_id>
        </userTransports>
        <builtin>
          <discovery_config>
            <discoveryProtocol>SUPER_CLIENT</discoveryProtocol>
            <discoveryServersList>${server_entries}
            </discoveryServersList>
          </discovery_config>
        </builtin>
      </rtps>
    </participant>
  </profiles>
</dds>
EOF

  export FASTRTPS_DEFAULT_PROFILES_FILE="${profile_path}"
  export FASTDDS_DEFAULT_PROFILES_FILE="${profile_path}"
}

tb4_setup_robot_env() {
  local robot_name="$1"
  local domain_id="$2"
  local discovery_server="$3"
  local discovery_server_id="${4:-0}"
  local script_path="${5:-${BASH_SOURCE[1]-}}"
  local script_dir ws restore_nounset discovery_host discovery_port

  script_dir="$(cd "$(dirname "${script_path}")" && pwd)"
  ws="$(cd "${script_dir}/.." && pwd)"

  cd "${ws}" || return
  export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES-}"
  export AMENT_PYTHON_EXECUTABLE="${AMENT_PYTHON_EXECUTABLE-$(command -v python3)}"

  restore_nounset=0
  if [[ $- == *u* ]]; then
    restore_nounset=1
    set +u
  fi

  source /opt/ros/humble/setup.bash
  if [[ -f "${ws}/install/setup.bash" ]]; then
    source "${ws}/install/setup.bash"
  fi

  if [[ ${restore_nounset} -eq 1 ]]; then
    set -u
  fi

  discovery_host="${discovery_server%%:*}"
  discovery_port="${discovery_server#*:}"
  discovery_port="${discovery_port%;}"
  if [[ "${discovery_port}" == "${discovery_server}" || -z "${discovery_port}" ]]; then
    discovery_port="11811"
  fi

  if [[ -n "${TB4_DISCOVERY_SERVER-}" ]]; then
    discovery_server="${TB4_DISCOVERY_SERVER}"
    discovery_host="${discovery_server%%:*}"
    discovery_port="${discovery_server#*:}"
    discovery_port="${discovery_port%;}"
    if [[ "${discovery_port}" == "${discovery_server}" || -z "${discovery_port}" ]]; then
      discovery_port="11811"
    fi
  fi
  if [[ -n "${TB4_ROS_DOMAIN_ID-}" ]]; then
    domain_id="${TB4_ROS_DOMAIN_ID}"
  fi
  if [[ -n "${TB4_DISCOVERY_SERVER_ID-}" ]]; then
    discovery_server_id="${TB4_DISCOVERY_SERVER_ID}"
  fi

  export ROS_DOMAIN_ID="${domain_id}"
  export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
  tb4_write_fastdds_profile "${robot_name}" "${discovery_host}" "${discovery_port}" "${discovery_server_id}"
  export ROS_SUPER_CLIENT="${TB4_ROS_SUPER_CLIENT:-True}"
  export ROS_DISCOVERY_SERVER="${discovery_server}"

  echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
  echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
  echo "FASTRTPS_DEFAULT_PROFILES_FILE=${FASTRTPS_DEFAULT_PROFILES_FILE-}"
  echo "FASTDDS_DEFAULT_PROFILES_FILE=${FASTDDS_DEFAULT_PROFILES_FILE-}"
  echo "ROS_SUPER_CLIENT=${ROS_SUPER_CLIENT}"
  echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
  echo "TB4_DISCOVERY_SERVER_ID=${discovery_server_id}"
}

tb4_setup_multi_robot_env() {
  local profile_tag="$1"
  local domain_id="$2"
  local script_path="$3"
  shift 3
  local server_specs=("$@")
  local script_dir ws restore_nounset spec discovery_server_list=""

  script_dir="$(cd "$(dirname "${script_path}")" && pwd)"
  ws="$(cd "${script_dir}/.." && pwd)"

  cd "${ws}" || return
  export AMENT_TRACE_SETUP_FILES="${AMENT_TRACE_SETUP_FILES-}"
  export AMENT_PYTHON_EXECUTABLE="${AMENT_PYTHON_EXECUTABLE-$(command -v python3)}"

  restore_nounset=0
  if [[ $- == *u* ]]; then
    restore_nounset=1
    set +u
  fi

  source /opt/ros/humble/setup.bash
  if [[ -f "${ws}/install/setup.bash" ]]; then
    source "${ws}/install/setup.bash"
  fi

  if [[ ${restore_nounset} -eq 1 ]]; then
    set -u
  fi

  if [[ -n "${TB4_ROS_DOMAIN_ID-}" ]]; then
    domain_id="${TB4_ROS_DOMAIN_ID}"
  fi

  export ROS_DOMAIN_ID="${domain_id}"
  export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
  tb4_write_fastdds_profile_multi "${profile_tag}" "${server_specs[@]}"
  export ROS_SUPER_CLIENT="${TB4_ROS_SUPER_CLIENT:-True}"

  for spec in "${server_specs[@]}"; do
    IFS=':' read -r host port server_id <<<"${spec}"
    if [[ -z "${host}" ]]; then
      continue
    fi
    if [[ -z "${port}" ]]; then
      port="11811"
    fi
    discovery_server_list+="${host}:${port};"
  done
  export ROS_DISCOVERY_SERVER="${discovery_server_list}"

  echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
  echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
  echo "FASTRTPS_DEFAULT_PROFILES_FILE=${FASTRTPS_DEFAULT_PROFILES_FILE-}"
  echo "FASTDDS_DEFAULT_PROFILES_FILE=${FASTDDS_DEFAULT_PROFILES_FILE-}"
  echo "ROS_SUPER_CLIENT=${ROS_SUPER_CLIENT}"
  echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
  echo "TB4_MULTI_DISCOVERY_SERVERS=${server_specs[*]}"
}
