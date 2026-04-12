#!/usr/bin/env bash
# Fix ownership on chief-orchestrator profile policies and rsync from the git checkout.
# Run **on the droplet as a user with sudo** (typically hermesadmin), e.g.:
#   ./scripts/core/droplet_run.sh 'bash -s' < droplet_sync_chief_profile_policies.sh
# Or from workstation (recommended — uses SSH_SUDO_PASSWORD for hermesadmin):
#   ./scripts/core/droplet_run.sh \
#     'bash /home/hermesuser/hermes-agent/memory/core/scripts/core/droplet_sync_chief_profile_policies.sh'
#
# Do **not** run `sudo` as hermesuser unless that account is in sudoers with a known password.
set -euo pipefail
POLICY_DIR=/home/hermesuser/.hermes/profiles/chief-orchestrator/policies
REPO_POLICIES=/home/hermesuser/hermes-agent/policies

if [[ "$(id -u)" -ne 0 ]]; then
  SUDO=sudo
else
  SUDO=
fi

$SUDO chown -R hermesuser:hermesuser "$POLICY_DIR"
# Stale root-owned marker from earlier experiments
$SUDO rm -f "$POLICY_DIR/READ_ONLY_POLICY_NOTICE.md" 2>/dev/null || true

if [[ ! -d "$REPO_POLICIES" ]]; then
  echo "droplet_sync_chief_profile_policies: missing $REPO_POLICIES — git pull hermes-agent first." >&2
  exit 1
fi

sudo -u hermesuser rsync -av --delete "$REPO_POLICIES/" "$POLICY_DIR/"
echo "droplet_sync_chief_profile_policies: ok — $POLICY_DIR synced from $REPO_POLICIES"
