#!/bin/bash
# Hermes — operator mini SSH helper (macOS). Double-click in Finder.
# • First run: create keypair, copy pubkey, walk through "sent to admin?" → optional Connect.
# • Later runs: Connect with one dialog (no commands to remember).
#
# Gatekeeper: first open may require right-click → Open.
#
# Leak resistance: a private key file always works from any machine that has it, UNLESS the admin
# adds a from="YOUR_TAILSCALE_IP/32" prefix on your pubkey line. This script shows your Tailscale
# IPv4 so you can ask the admin to lock your line to this device (best-effort; IP can change if
# Tailscale is reinstalled — admin updates authorized_keys).
#
set -uo pipefail
cd "$(dirname "$0")"

CONFIG_DIR="${HOME}/.config/hermes-operator-access"
CONFIG_FILE="${CONFIG_DIR}/session.env"
DEFAULT_HOST="${HERMES_OPERATOR_DEFAULT_HOST:-100.67.17.9}"
DEFAULT_PORT="${HERMES_OPERATOR_DEFAULT_PORT:-52822}"
DEFAULT_USER="${HERMES_OPERATOR_DEFAULT_USER:-operator}"

die_dialog() {
  osascript -e "display dialog \"$1\" buttons {\"OK\"} default button 1 with icon stop" 2>/dev/null || true
  exit 1
}

_ts_ip() {
  if [[ -x /Applications/Tailscale.app/Contents/MacOS/tailscale ]]; then
    /Applications/Tailscale.app/Contents/MacOS/tailscale ip -4 2>/dev/null | head -1 | tr -d '[:space:]'
  elif command -v tailscale >/dev/null 2>&1; then
    tailscale ip -4 2>/dev/null | head -1 | tr -d '[:space:]'
  fi
}

load_config() {
  KEY_FILE=""
  HERMES_OPERATOR_KEY=""
  HERMES_OPERATOR_HOST=""
  HERMES_OPERATOR_PORT=""
  HERMES_OPERATOR_USER=""
  if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
    KEY_FILE="${HERMES_OPERATOR_KEY:-}"
  fi
}

save_config() {
  mkdir -p "$CONFIG_DIR"
  umask 077
  {
    echo "# Hermes operator SSH session (do not share). Regenerate: delete this file and the private key."
    echo "HERMES_OPERATOR_KEY=$(printf '%q' "$KEY_FILE")"
    echo "HERMES_OPERATOR_HOST=$(printf '%q' "$HERMES_OPERATOR_HOST")"
    echo "HERMES_OPERATOR_PORT=$(printf '%q' "${HERMES_OPERATOR_PORT:-52822}")"
    echo "HERMES_OPERATOR_USER=$(printf '%q' "${HERMES_OPERATOR_USER:-operator}")"
  } >"$CONFIG_FILE"
  chmod 600 "$CONFIG_FILE"
}

do_connect() {
  load_config
  if [[ -z "${KEY_FILE:-}" || ! -f "$KEY_FILE" ]]; then
    die_dialog "No saved session. Run this script again to create a key (or restore ${CONFIG_FILE})."
  fi
  if [[ -z "${HERMES_OPERATOR_HOST:-}" ]]; then
    die_dialog "Missing host in ${CONFIG_FILE}"
  fi
  exec /usr/bin/ssh \
    -o IdentitiesOnly=yes \
    -o IdentityAgent=none \
    -o AddKeysToAgent=no \
    -i "$KEY_FILE" \
    -p "${HERMES_OPERATOR_PORT:-$DEFAULT_PORT}" \
    "${HERMES_OPERATOR_USER:-$DEFAULT_USER}@${HERMES_OPERATOR_HOST}" "$@"
}

# --- Existing install: offer quick connect ---
load_config
if [[ -n "${KEY_FILE:-}" && -f "$KEY_FILE" && -f "$CONFIG_FILE" ]]; then
  CHOICE="$(osascript -e 'display dialog "Connect to the operator Mac mini now?" buttons {"Exit", "Copy pubkey again", "Connect"} default button "Connect"' -e 'button returned of result' 2>/dev/null || echo "Exit")"
  case "$CHOICE" in
    Connect)
      do_connect
      ;;
    "Copy pubkey again")
      /usr/bin/pbcopy <"${KEY_FILE}.pub"
      osascript -e 'display dialog "Public key copied to clipboard again." buttons {"OK"} default button 1'
      ;;
    *)
      exit 0
      ;;
  esac
  exit 0
fi

# --- First-time setup ---
if ! command -v ssh-keygen >/dev/null 2>&1; then
  die_dialog "ssh-keygen not found. Install Xcode Command Line Tools."
fi

HOST="$(osascript -e "display dialog \"Operator mini Tailscale IP or hostname:\" default answer \"${DEFAULT_HOST}\" buttons {\"Cancel\", \"OK\"} default button \"OK\"" -e 'text returned of result' 2>/dev/null || true)"
HOST="${HOST:-$DEFAULT_HOST}"
if [[ -z "$HOST" ]]; then
  die_dialog "Host is required."
fi

NAME="$(osascript -e 'display dialog "Label for this key (e.g. your name):" default answer "collaborator" buttons {"Cancel", "OK"} default button "OK"' -e 'text returned of result' 2>/dev/null || true)"
NAME="${NAME:-collaborator}"
SAFE="${NAME//[^a-zA-Z0-9._-]/_}"
KEY_FILE="${HOME}/.ssh/operator_access_${SAFE}_ed25519"

mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"

if [[ -f "$KEY_FILE" ]]; then
  die_dialog "Key already exists:\\n${KEY_FILE}\\n\\nDelete it and ${CONFIG_FILE} to start over."
fi

/usr/bin/ssh-keygen -t ed25519 -f "$KEY_FILE" -N "" -C "operator-access-${SAFE}" </dev/null
chmod 600 "$KEY_FILE"
/usr/bin/pbcopy <"${KEY_FILE}.pub"

TS_IP="$(_ts_ip)"
LOCK_HINT=""
SUGGESTED_LINE=""
if [[ -n "$TS_IP" ]]; then
  PUBLINE="$(tr -d '\n' <"${KEY_FILE}.pub")"
  SUGGESTED_LINE="from=\"${TS_IP}/32\" ${PUBLINE}"
  LOCK_HINT="Optional device lock: ask the admin to use ONE line in authorized_keys (shown in Terminal after OK)."
else
  LOCK_HINT="Install Tailscale on this Mac, then re-run this script to get a suggested from= line for the admin."
fi

osascript -e 'display dialog "Your PUBLIC key is on the clipboard.

1) Send it to the admin.
2) They add it to operator ~/.ssh/authorized_keys on the mini.

Optional: ask them to lock this key to this Mac using Tailscale (details in Terminal)." buttons {"OK"} default button "OK" with icon note'

if [[ -n "$SUGGESTED_LINE" ]]; then
  echo ""
  echo "=== Optional authorized_keys line (device lock via Tailscale source IP ${TS_IP}) ==="
  echo "$SUGGESTED_LINE"
  echo "=== (plain pubkey without from= also works from any tailnet IP) ==="
  echo ""
fi

CONFIRM="$(osascript -e 'display dialog "Has the admin confirmed your public key is on the server?" buttons {"Not yet", "Admin added key"} default button "Admin added key"' -e 'button returned of result' 2>/dev/null || echo "Not yet")"
if [[ "$CONFIRM" != "Admin added key" ]]; then
  osascript -e 'display dialog "When the admin has added your key, open this same script again to connect (no commands needed)." buttons {"OK"} default button 1'
  HERMES_OPERATOR_HOST="$HOST"
  HERMES_OPERATOR_PORT="$DEFAULT_PORT"
  HERMES_OPERATOR_USER="$DEFAULT_USER"
  save_config
  exit 0
fi

NOW="$(osascript -e 'display dialog "Connect to the operator mini now?" buttons {"Not now", "Connect"} default button "Connect"' -e 'button returned of result' 2>/dev/null || echo "Not now")"

HERMES_OPERATOR_HOST="$HOST"
HERMES_OPERATOR_PORT="$DEFAULT_PORT"
HERMES_OPERATOR_USER="$DEFAULT_USER"
save_config

if [[ "$NOW" == "Connect" ]]; then
  do_connect
fi

osascript -e 'display dialog "Saved. Next time, double-click this script and choose Connect." buttons {"OK"} default button 1'
exit 0
