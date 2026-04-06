#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-${AGENT_HOME:-${HERMES_HOME:-}}/workspace}"
POLICY_ROOT="${POLICY_ROOT:-${AGENT_HOME:-${HERMES_HOME:-}}/policies}"

if [[ -z "${WORKSPACE_ROOT}" || -z "${POLICY_ROOT}" ]]; then
  echo "Set AGENT_HOME or HERMES_HOME, or pass WORKSPACE_ROOT and POLICY_ROOT."
  exit 1
fi

cd "${REPO_ROOT}"
python "policies/core/scripts/start_pipeline.py" \
  --workspace-root "${WORKSPACE_ROOT}" \
  --policy-root "${POLICY_ROOT}"

echo "Runtime memory activation complete."
