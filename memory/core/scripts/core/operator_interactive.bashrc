# Hermes operator SSH — used as: bash --rcfile THIS_FILE -i
# Purple (venv)(venv) + ssh label; suppress duplicate (venv) from activate.
_PURP='\[\033[38;5;141m\]'
_RST='\[\033[0m\]'
_HERMES_OR="${HERMES_OPERATOR_REPO:-$HOME/hermes-agent}"
export VIRTUAL_ENV_DISABLE_PROMPT=1
if [[ -f "${_HERMES_OR}/venv/bin/activate" ]]; then
  # shellcheck disable=SC1090
  . "${_HERMES_OR}/venv/bin/activate"
fi
if [[ -f "${HOME}/.bashrc" ]]; then
  # shellcheck disable=SC1090
  . "${HOME}/.bashrc"
fi
if [[ -f "${_HERMES_OR}/venv/bin/activate" ]]; then
  . "${_HERMES_OR}/venv/bin/activate"
fi
_dst="${HERMES_OPERATOR_SSH_DST:-}"
_PS1_TAIL="${_PURP}\u@\h:\W\$${_RST}"
if [[ -n "$_dst" ]]; then
  export PS1="${_PURP}(venv)${_RST}${_PURP}(venv)${_RST} ${_dst} ${_PS1_TAIL}"
else
  export PS1="${_PURP}(venv)${_RST}${_PURP}(venv)${_RST} ${_PS1_TAIL}"
fi
unset _HERMES_OR _PURP _RST _dst _PS1_TAIL
