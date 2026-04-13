#!/usr/bin/env bash
# Print the Mac mini's current Tailscale IPv4 (compare to MACMINI_SSH_HOST in ~/.env/.env).
# Tries LAN first so a stale 100.x in the env file does not cause an 8s timeout.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
export MACMINI_SSH_TRY_LAN_FIRST="${MACMINI_SSH_TRY_LAN_FIRST:-1}"
exec bash "$ROOT/hermes_cli/scripts/core/ssh_operator.sh" \
  'echo -n "tailscale_ipv4="; tailscale ip -4 2>/dev/null | head -1; echo'
