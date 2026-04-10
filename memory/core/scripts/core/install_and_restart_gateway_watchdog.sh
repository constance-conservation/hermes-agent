#!/usr/bin/env bash
# Copy gateway-watchdog.sh into $HERMES_HOME/bin and restart a single supervisor instance.
#
# Run as the same Unix user that runs the gateway (e.g. hermesuser). Requires a
# writable HERMES_HOME and hermes-agent checkout with venv (HERMES_AGENT_DIR).
#
# This script does NOT kill the messaging gateway — only prior copies of
# gateway-watchdog.sh that match the destination path (best-effort), so it does
# not fight ``hermes gateway`` / systemd gateway units.
#
# Usage:
#   export HERMES_HOME=~/.hermes/profiles/chief-orchestrator   # or your profile
#   export HERMES_AGENT_DIR=~/hermes-agent
#   ./scripts/core/install_and_restart_gateway_watchdog.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="${SCRIPT_DIR}/gateway-watchdog.sh"
HERMES_AGENT_DIR="${HERMES_AGENT_DIR:-${HERMES_AGENT_REPO:-$REPO}}"
export HERMES_AGENT_DIR

if [[ ! -f "$SRC" ]]; then
  echo "install_and_restart_gateway_watchdog: missing $SRC" >&2
  exit 1
fi

HERMES_PROFILE_BASE="${HERMES_PROFILE_BASE:-$HOME/.hermes}"
if [[ -z "${HERMES_HOME:-}" ]]; then
  if [[ -n "${HERMES_WATCHDOG_PROFILE:-}" ]]; then
    export HERMES_HOME="${HERMES_PROFILE_BASE}/profiles/${HERMES_WATCHDOG_PROFILE}"
  elif [[ -d "${HERMES_PROFILE_BASE}/profiles/chief-orchestrator" ]]; then
    export HERMES_HOME="${HERMES_PROFILE_BASE}/profiles/chief-orchestrator"
  else
    export HERMES_HOME="${HERMES_PROFILE_BASE}"
  fi
fi
export HERMES_HOME

DEST_DIR="${HERMES_HOME}/bin"
DEST="${DEST_DIR}/gateway-watchdog.sh"
mkdir -p "$DEST_DIR"
cp -f "$SRC" "$DEST"
chmod 755 "$DEST"

# Stop prior watchdog loops that are running THIS script path (avoid broad pkill -f gateway).
if command -v pgrep >/dev/null 2>&1; then
  for opid in $(pgrep -f "gateway-watchdog.sh" 2>/dev/null || true); do
    line="$(ps -p "$opid" -o args= 2>/dev/null || true)"
    if echo "$line" | grep -qF "$DEST"; then
      kill "$opid" 2>/dev/null || true
    fi
  done
  sleep 2
fi

LOG="${HERMES_HOME}/logs/gateway-watchdog-install.log"
mkdir -p "$(dirname "$LOG")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) starting watchdog from $DEST" | tee -a "$LOG"
nohup env HERMES_HOME="$HERMES_HOME" HERMES_AGENT_DIR="$HERMES_AGENT_DIR" HERMES_PROFILE_BASE="$HERMES_PROFILE_BASE" \
  "$DEST" >>"${HERMES_HOME}/logs/gateway-watchdog.log" 2>&1 &
echo "gateway-watchdog PID $! (log: ${HERMES_HOME}/logs/gateway-watchdog.log)" | tee -a "$LOG"
