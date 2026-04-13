#!/usr/bin/env bash
# SSH to operator mini using a break-glass private key (no sshd from= on that pubkey line).
#
# Host/user/port default from the same ~/.env/.env keys as ssh_operator.sh (MACMINI_SSH_*),
# so you do not drift from a stale hardcoded IP. Override with OPERATOR_* env vars if needed.
#
# Key resolution (first hit wins):
#   1) OPERATOR_BREAKGLASS_KEY=file
#   2) $PWD / script dir: id_ed25519, operator_breakglass, breakglass_ed25519, .operator_key, operator_key
#   3) $HOME/.env/.breakglass as FILE or dir with those key names
#
# Reliability: forces IPv4 (-4) for 100.x Tailscale targets (avoids some dual-stack stalls).
# If raw TCP still times out while `tailscale ping` works, fix the mini (see
#   scripts/core/operator_mini_ssh_tcp_diagnostic.sh) — usually sshd ListenAddress vs current
#   `tailscale ip -4`, org.hermes.tailscale.sshd, or Application Firewall blocking 52822.
#
# Optional: OPERATOR_BREAKGLASS_USE_TAILSCALE_SSH=1 uses `tailscale ssh` (port 22 on peer
# unless your tailnet maps otherwise) — only helps if your mini still exposes SSH on 22 for that path.
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${HERMES_OPERATOR_ENV:-${HERMES_DROPLET_ENV:-${HOME}/.env/.env}}"

_ef_host=""
_ef_port=""
_ef_user=""
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    if [[ "$key" == export* ]]; then
      key="${key#export}"
      key="${key##[[:space:]]}"
      key="${key%%[[:space:]]}"
    fi
    if [[ "$val" =~ ^\"(.*)\"$ ]]; then
      val="${BASH_REMATCH[1]}"
    fi
    case "$key" in
      MACMINI_SSH_HOST) _ef_host="${val}" ;;
      SSH_IP_OPERATOR)
        [[ "$val" != *"@"* ]] && _ef_host="${val}"
        ;;
      MACMINI_SSH_PORT) _ef_port="${val}" ;;
      MACMINI_SSH_USER) _ef_user="${val}" ;;
    esac
  done <"$ENV_FILE"
fi

HOST="${OPERATOR_TAILSCALE_HOST:-${MACMINI_SSH_HOST:-${_ef_host:-100.67.17.9}}}"
PORT="${OPERATOR_SSH_PORT:-${MACMINI_SSH_PORT:-${_ef_port:-52822}}}"
USER_NAME="${OPERATOR_SSH_USER:-${MACMINI_SSH_USER:-${_ef_user:-operator}}}"

_resolve_breakglass_key() {
  local f
  if [[ -n "${OPERATOR_BREAKGLASS_KEY:-}" && -f "${OPERATOR_BREAKGLASS_KEY}" ]]; then
    echo "${OPERATOR_BREAKGLASS_KEY}"
    return 0
  fi
  for f in \
    "${PWD}/id_ed25519" \
    "${PWD}/operator_breakglass" \
    "${PWD}/breakglass_ed25519" \
    "${PWD}/.operator_key" \
    "${PWD}/operator_key" \
    "${SCRIPT_DIR}/id_ed25519" \
    "${SCRIPT_DIR}/operator_breakglass" \
    "${SCRIPT_DIR}/breakglass_ed25519" \
    "${SCRIPT_DIR}/.operator_key" \
    "${SCRIPT_DIR}/operator_key"; do
    if [[ -f "$f" && ! "$f" =~ \.pub$ ]]; then
      echo "$f"
      return 0
    fi
  done
  local bg="${HOME}/.env/.breakglass"
  if [[ -f "$bg" ]]; then
    echo "$bg"
    return 0
  fi
  if [[ -d "$bg" ]]; then
    for f in "$bg/id_ed25519" "$bg/operator_breakglass" "$bg/breakglass_ed25519" "$bg/.operator_key" "$bg/operator_key"; do
      if [[ -f "$f" ]]; then
        echo "$f"
        return 0
      fi
    done
  fi
  return 1
}

KEY="$(_resolve_breakglass_key || true)"
if [[ -z "$KEY" ]]; then
  echo "No break-glass private key found." >&2
  echo "Set OPERATOR_BREAKGLASS_KEY, put .operator_key or id_ed25519 beside this script (${SCRIPT_DIR}), in \$PWD, or under ~/.env/.breakglass/." >&2
  exit 1
fi

CTO="${HERMES_OPERATOR_SSH_CONNECT_TIMEOUT:-20}"
_SSH_BASE=(
  -4
  -o BatchMode=no
  -o IdentitiesOnly=yes
  -o IdentityAgent=none
  -o AddKeysToAgent=no
  -o ControlMaster=no
  -o ControlPath=none
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout="$CTO"
  -o ServerAliveInterval=10
  -o ServerAliveCountMax=6
  -o TCPKeepAlive=yes
  -o PreferredAuthentications=publickey
  -o PubkeyAuthentication=yes
  -i "$KEY"
  -p "$PORT"
)
if [[ "$(uname -s)" == "Darwin" ]]; then
  _SSH_BASE+=(-o UseKeychain=no)
fi

if [[ "${OPERATOR_BREAKGLASS_USE_TAILSCALE_SSH:-0}" == "1" ]] && command -v tailscale >/dev/null 2>&1; then
  # Uses tailnet SSH feature; remote port is often 22 — only if your ACLs / sshd allow it.
  exec tailscale ssh "${USER_NAME}@${HOST}" "$@"
fi

exec ssh "${_SSH_BASE[@]}" "${USER_NAME}@${HOST}" "$@"
