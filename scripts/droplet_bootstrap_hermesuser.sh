#!/usr/bin/env bash
# Run on the VPS as root:
#   cd /home/hermesadmin/hermes-agent   # or any checkout readable by root
#   sudo bash scripts/droplet_bootstrap_hermesuser.sh
#
# Ensures hermesuser has ~/hermes-agent with venv, pip install -e ., sticky profile
# chief-orchestrator, and materialized policies under that profile's HERMES_HOME.
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "droplet_bootstrap_hermesuser.sh: run as root, e.g. sudo bash $0" >&2
  exit 1
fi

RU=hermesuser
HR="/home/${RU}"
RA="${HR}/hermes-agent"
CO="${HR}/.hermes/profiles/chief-orchestrator"
REPO_URL="${HERMES_AGENT_REPO_URL:-https://github.com/cc-org-au/hermes-agent.git}"

install -d -o "${RU}" -g "${RU}" "${HR}"

if [[ ! -d "${RA}/.git" ]]; then
  echo "Cloning hermes-agent into ${RA} as ${RU}..."
  sudo -u "${RU}" git clone "${REPO_URL}" "${RA}"
else
  echo "Updating ${RA}..."
  sudo -u "${RU}" git -C "${RA}" pull --ff-only
fi

echo "Python venv + editable install..."
sudo -u "${RU}" bash -lc "cd '${RA}' && python3 -m venv venv && ./venv/bin/pip install -q -U pip && ./venv/bin/pip install -q -e ."

echo "Hermes profile chief-orchestrator + sticky default..."
sudo -u "${RU}" bash -lc "cd '${RA}' && ./venv/bin/python -m hermes_cli.main -p default profile create chief-orchestrator --no-alias || true && ./venv/bin/python -m hermes_cli.main -p default profile use chief-orchestrator"

echo "Materialize policies into ${CO}..."
sudo -u "${RU}" install -d -m 755 -o "${RU}" -g "${RU}" "${CO}/workspace" "${CO}/policies"
sudo -u "${RU}" bash -lc "cd '${RA}' && HERMES_HOME='${CO}' ./venv/bin/python policies/core/scripts/start_pipeline.py --workspace-root '${CO}/workspace' --policy-root '${CO}/policies' --write-governance-md '${CO}/.hermes.md'"

echo "droplet_bootstrap_hermesuser.sh: done. hermes … droplet -> ${RU} venv, HERMES_HOME=${CO}"
