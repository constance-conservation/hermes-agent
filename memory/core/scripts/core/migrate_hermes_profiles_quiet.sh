#!/usr/bin/env bash
# Run migrate_config(interactive=False) for default HERMES_HOME and common orchestrator profiles.
# Intended after git pull on operator / droplet (non-interactive SSH).
set -euo pipefail

_migrate_one() {
  local home="$1"
  if [[ ! -f "${home}/config.yaml" ]]; then
    return 0
  fi
  echo "→ migrate_config quiet: ${home}"
  HERMES_HOME="${home}" python -c "from hermes_cli.config import migrate_config; migrate_config(interactive=False, quiet=True)"
}

_migrate_one "${HOME}/.hermes"
for _p in chief-orchestrator chief-orchestrator-droplet; do
  _migrate_one "${HOME}/.hermes/profiles/${_p}"
done
