#!/usr/bin/env bash
#
# Copy gateway-watchdog.sh into HERMES_HOME/bin and restart a single instance.
#
# Use this from SSH/automation instead of inlining pkill + nohup: a one-liner
# `bash -c '... pkill -f gateway-watchdog ...'` often matches the supervisor's
# own argv and kills the session before nohup runs.
#
# Environment: same as gateway-watchdog.sh for HERMES_HOME / HERMES_PROFILE_BASE /
# HERMES_WATCHDOG_PROFILE / HERMES_AGENT_DIR (optional).

set -euo pipefail

REPO="${HERMES_AGENT_DIR:-${HOME}/hermes-agent}"
SRC="${REPO}/scripts/core/gateway-watchdog.sh"
if [[ ! -f "$SRC" ]]; then
  echo "install_and_restart_gateway_watchdog: missing ${SRC}" >&2
  exit 1
fi

_PROFILE_BASE="${HERMES_PROFILE_BASE:-${HOME}/.hermes}"
_PROFILES_ROOT="${_PROFILE_BASE}/profiles"

if [[ -n "${HERMES_HOME:-}" ]]; then
  HERMES="${HERMES_HOME}"
elif [[ -n "${HERMES_WATCHDOG_PROFILE:-}" ]]; then
  HERMES="${_PROFILE_BASE}/profiles/${HERMES_WATCHDOG_PROFILE}"
else
  if [[ -d "${_PROFILES_ROOT}/chief-orchestrator" ]]; then
    HERMES="${_PROFILES_ROOT}/chief-orchestrator"
  else
    HERMES="${_PROFILE_BASE}"
  fi
fi

BIN="${HERMES}/bin/gateway-watchdog.sh"
LOG_DIR="${HERMES}/logs"
OUTER_LOG="${LOG_DIR}/gateway-watchdog.outer.log"

mkdir -p "$(dirname "$BIN")" "${LOG_DIR}"
cp -f "$SRC" "$BIN"
chmod +x "$BIN"

# Match only processes whose argv includes the installed script path.
if pkill -f "${BIN}" 2>/dev/null; then
  sleep 2
fi

nohup "${BIN}" >>"${OUTER_LOG}" 2>&1 &
echo "gateway-watchdog started pid=$! bin=${BIN}"
