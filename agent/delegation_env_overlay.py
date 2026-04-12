"""When ``delegate_task(..., hermes_profile=…)`` runs, optionally overlay env vars from the
parent profile's ``.env`` into the process so the child agent sees missing API keys.

Child profile wins: we only use :func:`os.environ.setdefault` for each key — values already
loaded from the target profile's ``.env`` are not overwritten.

Keys come from ``config.yaml`` → ``delegation.parent_env_overlay_keys`` (see
``hermes_cli.config.DEFAULT_CONFIG``).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def _parse_dotenv_lines(path: Path) -> Dict[str, str]:
    """Minimal KEY=VALUE parse (no multiline values)."""
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, _, v = s.partition("=")
        key = k.strip()
        if not key:
            continue
        val = v.strip().strip('"').strip("'")
        out[key] = val
    return out


def _overlay_keys_from_config() -> List[str]:
    try:
        from hermes_cli.config import load_config

        cfg = load_config() or {}
        root = cfg if isinstance(cfg, dict) else {}
        del_block = root.get("delegation")
        if not isinstance(del_block, dict):
            return []
        if del_block.get("parent_env_overlay_enabled") is False:
            return []
        raw = del_block.get("parent_env_overlay_keys")
        if not isinstance(raw, list):
            return []
        return [str(x).strip() for x in raw if str(x).strip()]
    except Exception:
        return []


def apply_parent_env_overlay_for_delegate(parent_hermes_home: Any) -> None:
    """Set missing ``os.environ`` entries from *parent_hermes_home*/``.env`` for whitelisted keys."""
    keys = _overlay_keys_from_config()
    if not keys:
        return
    try:
        home = Path(str(parent_hermes_home)).expanduser().resolve()
    except Exception:
        return
    env_path = home / ".env"
    parsed = _parse_dotenv_lines(env_path)
    if not parsed:
        return
    want = set(keys)
    n = 0
    for k in want:
        if k not in parsed:
            continue
        val = parsed[k]
        if not val:
            continue
        if k not in os.environ or not (os.environ.get(k) or "").strip():
            os.environ.setdefault(k, val)
            n += 1
    if n:
        logger.info(
            "delegation_env_overlay: set %d missing key(s) from parent %s",
            n,
            env_path,
        )
