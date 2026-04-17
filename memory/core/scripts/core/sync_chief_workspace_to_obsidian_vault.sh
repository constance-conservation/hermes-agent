#!/usr/bin/env bash
# Mirror chief-orchestrator HERMES_HOME/workspace into the Obsidian vault raw layer.
#
# Vault layout (sibling to workspace/):
#   ${HERMES_HOME}/obsidian-vault/raw/workspace/  ← mirror
#
# Usage (from a login with HERMES_HOME set, or pass profile):
#   HERMES_HOME=~/.hermes/profiles/chief-orchestrator ./sync_chief_workspace_to_obsidian_vault.sh
#   ./sync_chief_workspace_to_obsidian_vault.sh /path/to/chief-orchestrator-as-HERMES_HOME
#
set -euo pipefail

if [[ -n "${1:-}" ]]; then
  export HERMES_HOME="$(cd "$1" && pwd)"
elif [[ -z "${HERMES_HOME:-}" ]]; then
  echo "usage: HERMES_HOME=... $0   OR   $0 /path/to/profile/home" >&2
  exit 1
fi

SRC="${HERMES_HOME}/workspace"
DST="${HERMES_HOME}/obsidian-vault/raw/workspace"

if [[ ! -d "$SRC" ]]; then
  echo "missing workspace dir: $SRC" >&2
  exit 1
fi

mkdir -p "$DST"

RSYNC_EXCLUDES=(
  --exclude '.DS_Store'
  --exclude '._*'
  --exclude '.git/'
  --exclude '__pycache__/'
  --exclude '*.pyc'
  --exclude '.venv/'
  --exclude 'node_modules/'
)

# trailing slashes: copy contents of workspace into raw/workspace
rsync -a --delete "${RSYNC_EXCLUDES[@]}" "$SRC/" "$DST/"

echo "synced: $SRC -> $DST"
