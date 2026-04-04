#!/usr/bin/env bash
# Materialize repo policies/ into HERMES_HOME/policies and HERMES_HOME/workspace,
# write path-filled HERMES_HOME/.hermes.md, and lay runtime pack files at the workspace
# root (BOOTSTRAP.md, AGENTS.md, …) so Hermes can load them (see agent/prompt_builder.py).
#
# Usage (on the host that has the hermes-agent checkout + venv):
#   export HERMES_HOME=/home/hermesuser/.hermes   # or ~/.hermes
#   ./scripts/materialize_policies_into_hermes_home.sh
#
# Optional: SKIP_GOVERNANCE_MD=1 to skip writing HERMES_HOME/.hermes.md (paths-only stub).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${HERMES_HOME:?Set HERMES_HOME to the Hermes profile directory (e.g. /home/hermesuser/.hermes)}"
export HERMES_HOME
PY="${ROOT}/venv/bin/python3"
if [[ ! -x "$PY" ]]; then
  PY="${ROOT}/venv/bin/python"
fi
if [[ ! -x "$PY" ]]; then
  echo "materialize: no venv python at ${ROOT}/venv/bin — activate venv or set PYTHON" >&2
  exit 1
fi
ARGS=(
  "${ROOT}/policies/core/scripts/start_pipeline.py"
  --workspace-root "${HERMES_HOME}/workspace"
  --policy-root "${HERMES_HOME}/policies"
)
if [[ "${SKIP_GOVERNANCE_MD:-0}" != "1" ]]; then
  ARGS+=(--write-governance-md "${HERMES_HOME}/.hermes.md")
fi
"$PY" "${ARGS[@]}"
echo "materialize: done — policy root: ${HERMES_HOME}/policies workspace: ${HERMES_HOME}/workspace (flat runtime files at workspace root)"
