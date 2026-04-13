#!/usr/bin/env bash
# Run ON the operator Mac mini as root. Maintains /etc/ssh/sshd_config.d/201-hermes-lan-ssh.conf
# with ListenAddress = current primary IPv4 (en0 then en1 …). Restarts Hermes sshd when the
# address changes — safe to run every few minutes (no spurious kickstart when unchanged).
#
# Used by: operator_mini_add_lan_listenaddress_sshd.sh (manual) and
#           org.hermes.lan-ssh-listen-refresh LaunchDaemon (automatic).
#
# Hermes sshd (200-hermes-tailscale-only.conf) binds loopback + Tailscale only by default.
# Without this drop-in, LAN SSH to 192.168.x.x:52822 returns **connection refused**. DHCP changes
# can leave a **stale** ListenAddress here; sshd may then fail to bind or behave oddly — this
# script removes stale / empty-LAN drop-ins so Tailscale + loopback keep working.
#
# Remote from a hotspot: use the mini's **Tailscale** IP (100.x), not 192.168.x.x.
#
set -euo pipefail

if [[ "$(id -u)" != "0" ]]; then
  echo "Run with sudo." >&2
  exit 1
fi

DROP="/etc/ssh/sshd_config.d/201-hermes-lan-ssh.conf"
HERMES_SSHD_LABEL="system/org.hermes.tailscale.sshd"

_collect_live_ipv4() {
  local _if _a
  for _if in en0 en1 en2 en3 en4; do
    _a="$(ipconfig getifaddr "$_if" 2>/dev/null || true)"
    [[ -n "$_a" ]] && printf '%s\n' "$_a"
  done
}

_ip_in_live_list() {
  local want="$1" line
  while IFS= read -r line; do
    [[ "$line" == "$want" ]] && return 0
  done <<<"$(_collect_live_ipv4)"
  return 1
}

_existing_drop_listen() {
  [[ -f "$DROP" ]] || return 1
  awk '/^[[:space:]]*ListenAddress[[:space:]]+/ {print $2; exit}' "$DROP" 2>/dev/null || true
}

_reload_hermes_sshd() {
  if ! /usr/sbin/sshd -t; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) sshd -t failed — fix config before SSH will listen" >&2
    return 1
  fi
  launchctl kickstart -k "$HERMES_SSHD_LABEL" 2>/dev/null || launchctl kickstart -k system/com.openssh.sshd 2>/dev/null || true
}

LAN_IP="${1:-}"
if [[ -z "$LAN_IP" ]]; then
  for _if in en0 en1 en2 en3 en4; do
    LAN_IP="$(ipconfig getifaddr "$_if" 2>/dev/null || true)"
    [[ -n "$LAN_IP" ]] && break
  done
fi

changed=0
existing_listen="$(_existing_drop_listen || true)"
if [[ -n "$existing_listen" ]] && ! _ip_in_live_list "$existing_listen"; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) removing stale $DROP (ListenAddress ${existing_listen} not on en*) — restoring Tailscale/loopback-only until LAN returns" >&2
  rm -f "$DROP"
  changed=1
fi

if [[ -z "$LAN_IP" ]]; then
  if [[ -f "$DROP" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) no LAN IPv4 on en* — removing $DROP (loopback + Tailscale only)" >&2
    rm -f "$DROP"
    changed=1
  fi
  if [[ "$changed" -eq 1 ]]; then
    _reload_hermes_sshd || true
  fi
  exit 0
fi

if [[ -f "$DROP" ]] && grep -qE "^ListenAddress[[:space:]]+${LAN_IP//./\\.}([[:space:]]|$)" "$DROP" 2>/dev/null; then
  exit 0
fi

umask 022
{
  echo "# Hermes: LAN fallback (auto-refreshed). Port / AllowUsers / auth: 200-hermes-tailscale-only.conf"
  echo "ListenAddress ${LAN_IP}"
} >"$DROP"
chmod 644 "$DROP"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) updated $DROP -> ListenAddress ${LAN_IP}" >&2

_reload_hermes_sshd
exit 0
