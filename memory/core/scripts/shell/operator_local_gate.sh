#!/usr/bin/env bash
# Interactive gate before `operator` SSH: typed passphrase must match SSH_PASSPHRASE in the
# same ~/.env/.env used by scripts/core/ssh_operator.sh (no sudo required).
#
# Skip: HERMES_OPERATOR_SKIP_LOCAL_GATE=1
# If SSH_PASSPHRASE is unset/empty in that file, this script succeeds (SSH will still prompt if
# the key is encrypted and you are not using env-file ASKPASS).
set -euo pipefail

if [[ "${HERMES_OPERATOR_SKIP_LOCAL_GATE:-0}" == "1" ]]; then
  exit 0
fi

ENV_FILE="${HERMES_OPERATOR_ENV:-${HERMES_DROPLET_ENV:-${HOME}/.env/.env}}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "operator_local_gate: missing env file ${ENV_FILE}" >&2
  exit 1
fi

_EXPECT=""
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
  key="${line%%=*}"
  val="${line#*=}"
  if [[ "$key" == export* ]]; then
    key="${key#export}"
    key="${key##[[:space:]]}"
    key="${key%%[[:space:]]}"
  fi
  if [[ "$val" =~ ^\"(.*)\"$ ]]; then
    val="${BASH_REMATCH[1]}"
  fi
  case "$key" in
    SSH_PASSPHRASE) _EXPECT="${val}" ;;
  esac
done <"$ENV_FILE"

if [[ -z "$_EXPECT" ]]; then
  exit 0
fi

_typed=""
read -rsp "Hermes operator gate (SSH key passphrase per ${ENV_FILE}): " _typed || true
echo "" >&2
if [[ "$_typed" != "$_EXPECT" ]]; then
  echo "operator: passphrase mismatch or empty" >&2
  exit 1
fi
exit 0
