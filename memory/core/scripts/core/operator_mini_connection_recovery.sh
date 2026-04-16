#!/usr/bin/env bash
# Run **on the operator Mac mini** (Terminal.app, Screen Sharing, or iTerm) when the laptop
# cannot SSH in (timeouts on Tailscale / LAN) or after you want the latest `main` plus Hermes
# SSH listen fixes in one shot.
#
# What it does (in order):
#   1. `git pull --ff-only` this repo on `main` (brings routing + script updates from pushes).
#   2. Ensures Tailscale reports an IPv4 (`tailscale ip -4`).
#   3. If Hermes sshd drop-in exists, runs `operator_mini_refresh_tailscale_listenaddress.sh` so
#      `ListenAddress` matches the current Tailscale IP (common cause of 100.x:52822 timeouts).
#   4. Optionally restarts the chief gateway after code changes.
#
# Prerequisites:
#   - Tailscale installed; menu bar “Connected” (or run `tailscale up` once if prompted).
#   - For step 3: sudo password (refreshes `/etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf`).
#
# Usage:
#   cd ~/hermes-agent && bash scripts/core/operator_mini_connection_recovery.sh
#   HERMES_AGENT_REPO=/Users/operator/hermes-agent bash scripts/core/operator_mini_connection_recovery.sh --gateway-restart
#
# Options:
#   --skip-git          Do not run git pull.
#   --skip-sudo-fixes   Only print diagnostics; do not run sudo refresh/kickstart.
#   --gateway-restart   After fixes: `./venv/bin/python -m hermes_cli.main -p chief-orchestrator gateway restart --sync`
#
set -euo pipefail

SKIP_GIT=0
SKIP_SUDO=0
GATEWAY_RESTART=0
for arg in "$@"; do
  case "$arg" in
    --skip-git) SKIP_GIT=1 ;;
    --skip-sudo-fixes) SKIP_SUDO=1 ;;
    --gateway-restart) GATEWAY_RESTART=1 ;;
    -h|--help)
      sed -n '1,40p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (use --help)" >&2
      exit 2
      ;;
  esac
done

_ts_bin() {
  if [[ -x /Applications/Tailscale.app/Contents/MacOS/tailscale ]]; then
    echo "/Applications/Tailscale.app/Contents/MacOS/tailscale"
  elif command -v tailscale >/dev/null 2>&1; then
    command -v tailscale
  else
    echo ""
  fi
}

_ts_ip4() {
  local bin
  bin="$(_ts_bin)"
  [[ -n "$bin" ]] || return 1
  "$bin" ip -4 2>/dev/null | head -1 | tr -d '[:space:]'
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Repo: env > common paths > parent of scripts/core
if [[ -n "${HERMES_AGENT_REPO:-}" ]]; then
  REPO="${HERMES_AGENT_REPO}"
elif [[ -d "${HOME}/hermes-agent" ]]; then
  REPO="${HOME}/hermes-agent"
elif [[ -d "${HOME}/operator/hermes-agent" ]]; then
  REPO="${HOME}/operator/hermes-agent"
else
  REPO="$(cd "${SCRIPT_DIR}/../.." && pwd)"
fi

if [[ ! -d "$REPO/.git" ]]; then
  echo "error: not a git repo: ${REPO} (set HERMES_AGENT_REPO to your hermes-agent checkout)" >&2
  exit 1
fi

echo "=== Hermes operator mini — connection recovery ==="
echo "Repo: $REPO"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

if [[ "$SKIP_GIT" -eq 0 ]]; then
  echo "=== git pull (fast-forward only) ==="
  BRANCH="${HERMES_AGENT_BRANCH:-main}"
  git -C "$REPO" remote update origin --prune 2>/dev/null || true
  if ! git -C "$REPO" pull --ff-only origin "$BRANCH"; then
    echo "" >&2
    echo "git pull failed. Fix conflicts or stash local edits, then re-run:" >&2
    echo "  cd \"$REPO\" && git status" >&2
    exit 1
  fi
  echo "HEAD: $(git -C "$REPO" rev-parse --short HEAD)"
  echo ""
else
  echo "=== git pull skipped (--skip-git) ==="
  echo ""
fi

REFRESH_SH="${REPO}/memory/core/scripts/core/operator_mini_refresh_tailscale_listenaddress.sh"
if [[ ! -f "$REFRESH_SH" ]]; then
  echo "warning: missing ${REFRESH_SH} — git pull may be incomplete or repo path wrong." >&2
fi

echo "=== Tailscale ==="
TS_BIN="$(_ts_bin)"
if [[ -z "$TS_BIN" ]]; then
  echo "Tailscale CLI not found. Install Tailscale from https://tailscale.com/download/mac"
  echo "Then re-run this script."
  exit 1
fi

TS_IP="$(_ts_ip4 || true)"
if [[ -z "$TS_IP" ]]; then
  echo "No Tailscale IPv4 yet. Actions:"
  echo "  1) Open the Tailscale menu bar app and connect, or"
  echo "  2) Run: $TS_BIN up"
  echo "Then re-run this script."
  # Best-effort: try to open the app (non-fatal)
  open -a Tailscale 2>/dev/null || true
  exit 1
fi

echo "tailscale ip -4: $TS_IP"
echo ""

if [[ "$SKIP_SUDO" -eq 1 ]]; then
  echo "=== sudo fixes skipped (--skip-sudo-fixes) ==="
  if [[ -f /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf ]]; then
    echo "Current ListenAddress lines (non-loopback):"
    grep -E '^[[:space:]]*ListenAddress[[:space:]]+' /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf 2>/dev/null || true
  else
    echo "Missing /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf"
    echo "First-time setup: sudo MACMINI_SSH_ALLOW_USERS=operator bash \"$REPO/memory/core/scripts/core/macmini_apply_sshd_tailscale_only.sh\""
  fi
else
  if [[ -f /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf ]]; then
    echo "=== Refresh sshd ListenAddress for current Tailscale IP (sudo) ==="
    sudo bash "$REFRESH_SH"
    echo ""
    echo "=== Kickstart Hermes sshd (if loaded) ==="
    sudo launchctl kickstart -k system/org.hermes.tailscale.sshd 2>/dev/null || true
  else
    echo "=== Hermes sshd drop-in missing ==="
    echo "SSH may still be on stock port 22 or unhardened. To apply Hermes policy (52822, TS bind):"
    echo "  sudo MACMINI_SSH_ALLOW_USERS=operator bash \"$REPO/memory/core/scripts/core/macmini_apply_sshd_tailscale_only.sh\""
    echo "Then (recommended):"
    echo "  sudo bash \"$REPO/memory/core/scripts/core/macmini_sshd_tailscale_launchd_pf.sh\""
    echo "  sudo bash \"$REPO/memory/core/scripts/core/operator_mini_install_tailscale_listenaddress_watch.sh\""
  fi
fi

echo ""
echo "=== Quick listen check (52822) ==="
if command -v lsof >/dev/null 2>&1; then
  sudo lsof -nP -iTCP:52822 -sTCP:LISTEN 2>/dev/null || echo "(nothing listening on 52822 — check Remote Login + Hermes launchd plists)"
else
  echo "lsof not available"
fi

echo ""
echo "=== Workstation: update Tailscale target ==="
echo "On your laptop, set in ~/.env/.env (or HERMES_OPERATOR_ENV file):"
echo "  MACMINI_SSH_HOST=${TS_IP}"
echo "  MACMINI_SSH_PORT=52822"
echo "If you use LAN fallback when home, refresh:"
echo "  MACMINI_SSH_LAN_IP=<mini's current LAN IPv4 from System Settings → Network>"
echo ""
echo "Test from laptop (after Tailscale shows the mini online):"
echo "  ./scripts/core/ssh_operator.sh 'hostname'"

if [[ "$GATEWAY_RESTART" -eq 1 ]]; then
  echo ""
  echo "=== Gateway restart (chief-orchestrator) ==="
  if [[ ! -x "${REPO}/venv/bin/python" ]]; then
    echo "error: ${REPO}/venv/bin/python missing — create venv and pip install -e . first." >&2
    exit 1
  fi
  (cd "$REPO" && ./venv/bin/python -m hermes_cli.main -p chief-orchestrator gateway restart --sync)
  echo "Done. Optional: ./venv/bin/python -m hermes_cli.main -p chief-orchestrator gateway watchdog-check"
fi

echo ""
echo "=== Done ==="
