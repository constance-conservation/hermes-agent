#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-${AGENT_HOME:-${HERMES_HOME:-}}/workspace}"
OPERATIONS_ROOT="${OPERATIONS_ROOT:-${WORKSPACE_ROOT}/operations}"
HERMES_HOME="${HERMES_HOME:-${AGENT_HOME:-${HERMES_HOME:-}}}"

if [[ -z "${WORKSPACE_ROOT}" || -z "${OPERATIONS_ROOT}" ]]; then
  echo "Set AGENT_HOME or HERMES_HOME, or pass WORKSPACE_ROOT and OPERATIONS_ROOT."
  exit 1
fi

cd "${REPO_ROOT}"
python "policies/core/scripts/init_operations_stubs.py" --root "${OPERATIONS_ROOT}"

if [[ -n "${HERMES_HOME}" ]]; then
  HERMES_HOME="${HERMES_HOME}" REM_OPERATIONS_FORCE=1 "./scripts/core/materialize_rem_operations.sh"
fi

echo "Operations artifacts deployment complete."
