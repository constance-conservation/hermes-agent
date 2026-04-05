"""Tier letter → concrete OpenRouter model IDs from governance runtime YAML.

Aligned with ``token-model-tool-and-channel-governance-policy.md`` (Tiers A–F) and
workspace ``MODEL_ROUTING_REGISTRY.md``. Tier **IDs** live in
``workspace/operations/hermes_token_governance.runtime.yaml`` under ``tier_models`` —
edit there when pricing or availability changes; do not hardcode slugs in Hermes code.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

TIER_SENTINEL_RE = re.compile(r"^tier:([A-Fa-f])$")


def normalize_tier_models(raw: Any) -> Dict[str, str]:
    """Return upper-case tier key → model id."""
    out: Dict[str, str] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        key = str(k).strip().upper()
        if len(key) == 1 and key in "ABCDEF" and v:
            out[key] = str(v).strip()
    return out


def resolve_tier_placeholder(
    model: Optional[str],
    tier_models: Dict[str, str],
    *,
    fallback_tier: str = "D",
) -> str:
    """If *model* is ``tier:X``, return ``tier_models[X]``; else return *model*."""
    if not model:
        return tier_models.get(fallback_tier.upper(), "") or ""
    m = TIER_SENTINEL_RE.match(str(model).strip())
    if not m:
        return str(model).strip()
    tier = m.group(1).upper()
    resolved = tier_models.get(tier)
    if resolved:
        return resolved
    return tier_models.get(fallback_tier.upper(), "") or str(model).strip()


def select_tier_for_message(user_message: str, cfg: Dict[str, Any]) -> str:
    """Pick tier letter B/C/D for this user turn (conservative; policy-aligned)."""
    default = str(cfg.get("default_routing_tier") or "D").strip().upper()
    if len(default) != 1 or default not in "BCDEF":
        default = "D"

    t = (user_message or "").strip()
    if not t:
        return default

    low = t.lower()
    # Optional override for “incident” language (defaults to same tier as default to avoid surprise spend)
    incident_tier = str(cfg.get("incident_routing_tier") or default).strip().upper()
    if len(incident_tier) == 1 and incident_tier in "BCDEF":
        if any(
            k in low
            for k in (
                "production incident",
                "security breach",
                " sev-0",
                "p0 incident",
                "system down",
            )
        ):
            return incident_tier

    # Tier B — ultra-cheap: short, simple ops
    simple_kw = (
        "summarize",
        "bullet list",
        "list the",
        "extract ",
        "classify",
        "format ",
        "convert ",
        "translate ",
        "what is the capital",
        "define ",
    )
    if len(t) < 120 and "\n" not in t and any(k in low for k in simple_kw):
        return "B"
    if len(t) < 72 and t.count("\n") <= 1 and len(t.split()) <= 18:
        return "B"

    # Tier C — cheap reasoning: medium length, no heavy “build the whole repo” signals
    heavy = (
        "refactor",
        "architecture",
        "implement",
        "debug",
        "traceback",
        "kubernetes",
        "dockerfile",
        "migration",
        "oauth",
        "multi-agent",
    )
    if 120 <= len(t) <= 900 and not any(h in low for h in heavy):
        return "C"

    return default


def should_apply_per_turn_routing(cfg: Optional[Dict[str, Any]]) -> bool:
    if not cfg or not cfg.get("enabled", False):
        return False
    if not normalize_tier_models(cfg.get("tier_models")):
        return False
    # Explicit opt-out
    if cfg.get("dynamic_tier_routing") is False:
        return False
    return True
