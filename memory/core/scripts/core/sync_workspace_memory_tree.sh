#!/usr/bin/env bash
# Merge a local directory into HERMES_HOME/workspace/memory on operator and/or droplet.
#
# Usage:
#   ./scripts/core/sync_workspace_memory_tree.sh /path/to/memory
#
# Copies with rsync. Default: does NOT delete extra files on the remote.
# Default remotes (override with env):
#   OPERATOR_REMOTE=operator@host:/Users/operator/.hermes/profiles/chief-orchestrator/workspace/memory
#   DROPLET_REMOTE=hermesuser@host:/home/hermesuser/.hermes/profiles/chief-orchestrator/workspace/memory
#
# Requires: rsync, ssh; same keys as ssh_operator.sh / ssh_droplet.sh.
set -euo pipefail

SRC="${1:?usage: $0 /path/to/memory (folder containing AGENTS.md etc.)}"
SRC="$(cd "$SRC" && pwd)"
[[ -d "$SRC" ]] || { echo "not a directory: $SRC" >&2; exit 1; }

RSYNC_FLAGS=(-av --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r)
RSYNC_FLAGS+=(--exclude '.DS_Store')

if [[ "${SYNC_OPERATOR:-1}" == "1" ]] && [[ -n "${OPERATOR_REMOTE:-}" ]]; then
  echo "rsync -> operator: $OPERATOR_REMOTE"
  rsync "${RSYNC_FLAGS[@]}" "$SRC/" "$OPERATOR_REMOTE/"
fi

if [[ "${SYNC_DROPLET:-1}" == "1" ]] && [[ -n "${DROPLET_REMOTE:-}" ]]; then
  echo "rsync -> droplet: $DROPLET_REMOTE"
  rsync "${RSYNC_FLAGS[@]}" "$SRC/" "$DROPLET_REMOTE/"
fi

if [[ -z "${OPERATOR_REMOTE:-}" ]] && [[ -z "${DROPLET_REMOTE:-}" ]]; then
  echo "Set OPERATOR_REMOTE and/or DROPLET_REMOTE to rsync targets, e.g.:" >&2
  echo '  OPERATOR_REMOTE=operator@100.x.x.x:/Users/operator/.hermes/profiles/chief-orchestrator/workspace/memory \' >&2
  echo '  DROPLET_REMOTE=hermesuser@host:/home/hermesuser/.hermes/profiles/chief-orchestrator/workspace/memory \' >&2
  echo "  $0 $SRC" >&2
  exit 1
fi

echo "done."
