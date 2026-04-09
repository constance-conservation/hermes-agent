"""OPM native OpenAI quota downgrade ladder (routing_canon ``opm_native_quota_downgrade``).

When OpenAI-primary mode is active and api.openai.com hits quota/rate limits, step down
through configured model lists *before* activating cross-provider fallback. Per turn,
tier routing still picks the top model first; ladder only applies within a single
``run_conversation`` retry loop.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from utils import is_truthy_value

logger = logging.getLogger(__name__)


def _bare_slug(model_id: str) -> str:
    m = (model_id or "").strip()
    low = m.lower()
    if low.startswith("openai/"):
        return m[7:].strip()
    return m


def _normalize_ladder(entries: Any) -> List[str]:
    if not isinstance(entries, list):
        return []
    out: List[str] = []
    for x in entries:
        s = _bare_slug(str(x).strip())
        if s and s not in out:
            out.append(s)
    return out


def load_opm_native_quota_downgrade_config() -> Dict[str, Any]:
    """Return merged canon block with normalized lists and a precomputed id set."""
    from agent.routing_canon import load_merged_routing_canon

    canon = load_merged_routing_canon()
    raw = canon.get("opm_native_quota_downgrade")
    if not isinstance(raw, dict):
        raw = {}
    enabled = is_truthy_value(raw.get("enabled"), default=True)
    chat = _normalize_ladder(raw.get("chat_models"))
    codex = _normalize_ladder(raw.get("codex_models"))
    ladder_set = frozenset(chat) | frozenset(codex)
    return {
        "enabled": enabled,
        "chat_models": chat,
        "codex_models": codex,
        "ladder_model_set": ladder_set,
    }


def opm_native_ladder_model_uses_openai_tuple(agent: Any, model_id: str) -> bool:
    """True when *model_id* is listed in the quota ladder and OPM + ladder are enabled."""
    try:
        from agent.openai_primary_mode import opm_enabled

        cfg = load_opm_native_quota_downgrade_config()
        if not cfg.get("enabled") or not ladder_model_set_non_empty(cfg):
            return False
        if not opm_enabled(agent):
            return False
        bare = _bare_slug(model_id).lower()
        return bare in {x.lower() for x in cfg["ladder_model_set"]}
    except Exception:
        logger.debug("opm_native_ladder_model_uses_openai_tuple failed", exc_info=True)
        return False


def ladder_model_set_non_empty(cfg: Dict[str, Any]) -> bool:
    return bool(cfg.get("ladder_model_set"))


def ladder_for_api_mode(cfg: Dict[str, Any], api_mode: str) -> List[str]:
    if (api_mode or "").strip() == "codex_responses":
        return list(cfg.get("codex_models") or [])
    return list(cfg.get("chat_models") or [])


def next_quota_downgrade_model(
    *,
    current_model: str,
    api_mode: str,
    cfg: Dict[str, Any],
) -> Optional[str]:
    """Return the next rung after *current_model* in the appropriate ladder, or None."""
    ladder = ladder_for_api_mode(cfg, api_mode)
    if not ladder:
        return None
    cur = _bare_slug(current_model).lower()
    idx = -1
    for i, m in enumerate(ladder):
        if m.lower() == cur:
            idx = i
            break
    if idx < 0:
        return None
    if idx + 1 >= len(ladder):
        return None
    return ladder[idx + 1]


def should_attempt_opm_native_downgrade(
    agent: Any,
    *,
    quota_style: bool,
    pool_may_recover: bool,
) -> Tuple[bool, Dict[str, Any]]:
    """Return (eligible, cfg) for trying a native ladder step on this error."""
    cfg = load_opm_native_quota_downgrade_config()
    if not cfg.get("enabled") or not ladder_model_set_non_empty(cfg):
        return False, cfg
    if not quota_style:
        return False, cfg
    if pool_may_recover:
        return False, cfg
    try:
        from agent.openai_primary_mode import opm_enabled, opm_manual_override_active

        if not opm_enabled(agent) or opm_manual_override_active(agent):
            return False, cfg
    except Exception:
        return False, cfg
    if getattr(agent, "_fallback_activated", False):
        return False, cfg
    try:
        if not agent._is_direct_openai_url():
            return False, cfg
    except Exception:
        return False, cfg
    return True, cfg
