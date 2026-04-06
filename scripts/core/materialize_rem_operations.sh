#!/usr/bin/env bash
# Copy REM / org workspace templates into HERMES_HOME/workspace/operations/
#
# Usage:
#   export HERMES_HOME=/path/to/.hermes   # or profile directory
#   ./scripts/core/materialize_rem_operations.sh
#
# Overwrite existing files from repo templates (e.g. after git pull on droplet):
#   REM_OPERATIONS_FORCE=1 ./scripts/core/materialize_rem_operations.sh
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
: "${HERMES_HOME:?Set HERMES_HOME (e.g. profile directory)}"
SRC="${ROOT}/scripts/templates/rem_operations"
DEST="${HERMES_HOME}/workspace/operations"

if [[ ! -d "$SRC" ]]; then
  echo "materialize_rem: missing template dir $SRC" >&2
  exit 1
fi

mkdir -p "${DEST}/projects/agentic-company"

rem_copy() {
  local rel="$1"
  local from="${SRC}/${rel}"
  local to="${DEST}/${rel}"
  mkdir -p "$(dirname "$to")"
  if [[ -f "$to" && "${REM_OPERATIONS_FORCE:-0}" != "1" ]]; then
    echo "materialize_rem: skip (exists) $to"
    return 0
  fi
  cp "$from" "$to"
  echo "materialize_rem: installed $to"
}

rem_copy "SECURITY_SUBAGENTS_REGISTER.md"
rem_copy "FUNCTIONAL_DIRECTORS_REGISTER.md"
rem_copy "PROJECT_LEADS_REGISTER.md"
rem_copy "CHIEF_ORCHESTRATION_PLAYBOOK.md"
rem_copy "ORG_AGENT_ESCALATION_PLAYBOOK.md"
rem_copy "SECURITY_ALERT_REGISTER.md"
rem_copy "CHANNEL_ARCHITECTURE.md"
rem_copy "SKILL_INVENTORY_REGISTER.md"
rem_copy "CONSULTANT_REQUEST_REGISTER.md"
rem_copy "CONSULTANT_REQUEST_TEMPLATE.md"
rem_copy "BOARD_REVIEW_REGISTER.md"
rem_copy "MEMORY_INTEGRATION_OVERRIDE.md"
rem_copy "README.md"
rem_copy "GOVERNANCE_CHANGELOG.md"
rem_copy "MEMORY_MD_APPEND_SNIPPET.txt"
rem_copy "projects/agentic-company/README.md"

echo "materialize_rem: done DEST=$DEST (REM_OPERATIONS_FORCE=${REM_OPERATIONS_FORCE:-0})"
