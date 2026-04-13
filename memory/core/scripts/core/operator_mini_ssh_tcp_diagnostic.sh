#!/usr/bin/env bash
# Run ON the operator Mac mini (e.g. via Screen Sharing → Terminal) when:
#   tailscale ping <mini-ts-ip> works from your laptop but
#   ssh -p 52822 … times out (TCP never connects).
#
# Typical causes:
#   - /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf ListenAddress ≠ current `tailscale ip -4`
#   - org.hermes.tailscale.sshd LaunchDaemon not running (sshd not listening on :52822 on TS IP)
#   - macOS Application Firewall blocking inbound sshd on 52822
#
# Usage (on mini):
#   bash operator_mini_ssh_tcp_diagnostic.sh
#
set -euo pipefail

echo "=== date ==="
date

echo ""
echo "=== tailscale ip -4 (must match ListenAddress in 200-hermes-tailscale-only.conf) ==="
if [[ -x /Applications/Tailscale.app/Contents/MacOS/tailscale ]]; then
  /Applications/Tailscale.app/Contents/MacOS/tailscale ip -4 2>/dev/null || true
elif command -v tailscale >/dev/null 2>&1; then
  tailscale ip -4 2>/dev/null || true
else
  echo "(tailscale CLI not found)"
fi

echo ""
echo "=== sshd drop-in (Port / ListenAddress) ==="
if [[ -f /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf ]]; then
  grep -E '^(Port|ListenAddress|AllowUsers)\b' /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf 2>/dev/null || cat /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf
else
  echo "MISSING: /etc/ssh/sshd_config.d/200-hermes-tailscale-only.conf (Hermes hardening not applied?)"
fi

echo ""
echo "=== LISTEN sockets on 52822 (need sshd on 127.0.0.1 and Tailscale IP) ==="
if command -v lsof >/dev/null 2>&1; then
  sudo lsof -nP -iTCP:52822 -sTCP:LISTEN 2>/dev/null || echo "(run with sudo if empty — or nothing is listening)"
else
  echo "lsof not found"
fi

echo ""
echo "=== LaunchDaemon org.hermes.tailscale.sshd (Hermes sshd -D) ==="
launchctl print system/org.hermes.tailscale.sshd 2>&1 | head -25 || echo "(not loaded — sshd may not bind custom Port/ListenAddress)"

echo ""
echo "=== socketfilterfw global (Application Firewall) ==="
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || true

echo ""
echo "=== FIX HINTS ==="
echo "1) If ListenAddress TS IP ≠ tailscale ip -4: re-run macmini_apply_sshd_tailscale_only.sh (see repo) or edit drop-in to match, then kickstart sshd."
echo "2) If nothing listens on 52822: sudo launchctl bootstrap system /Library/LaunchDaemons/org.hermes.tailscale.sshd.plist"
echo "3) If firewall is on: allow incoming for /usr/sbin/sshd or test with firewall off briefly."
