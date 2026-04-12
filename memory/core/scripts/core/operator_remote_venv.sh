#!/usr/bin/env bash
# shellcheck shell=bash
# Prefix remote bash commands: cd to Hermes checkout on the Mac mini, activate venv.
# Sourced by ssh_operator.sh — do not run directly.
#
# On the remote shell, HERMES_OPERATOR_REPO may be exported by ssh_operator.sh; otherwise
# default is $HOME/hermes-agent.
#
# Optional: HERMES_REMOTE_VENV_QUIET=1 — skip stderr one-liner confirming venv (see droplet_remote_venv.sh).

_operator_wrap_cmd_with_venv() {
  local user_cmd="$1"
  local pre
  pre='repo="${HERMES_OPERATOR_REPO:-$HOME/hermes-agent}"; cd "$repo" 2>/dev/null || exit 1; '
  pre+='[ -f "$repo/venv/bin/activate" ] && . "$repo/venv/bin/activate"; '
  pre+='export VIRTUAL_ENV="$repo/venv"; export PATH="${VIRTUAL_ENV}/bin:${PATH}"; '
  pre+='if [[ "${HERMES_REMOTE_VENV_QUIET:-0}" != "1" ]]; then command -v python >/dev/null 2>&1 && printf "[hermes] operator: Hermes venv active (VIRTUAL_ENV=%s; python=%s)\n" "${VIRTUAL_ENV:-}" "$(command -v python)" >&2; fi; '
  printf '%s%s' "$pre" "$user_cmd"
}

_operator_interactive_shell_cmd() {
  # Do not use `exec bash -l` here — login shells often source ~/.bash_profile and can drop the
  # checkout venv from PATH. Use a dedicated --rcfile (operator_interactive.bashrc) so venv wins.
  _operator_wrap_cmd_with_venv 'repon="${HERMES_OPERATOR_REPO:-$HOME/hermes-agent}"; rcfile="$repon/scripts/core/operator_interactive.bashrc"; if [[ -f "$rcfile" ]]; then exec bash --rcfile "$rcfile" -i; else exec bash -i; fi'
}
