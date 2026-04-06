"""Build ``fallback_providers`` from ``free_model_routing`` in config.yaml.

Default (v18+): **Kimi tier router first** → optional HF Inference Providers (explicit
opt-in) → optional Gemini. The Inference Providers hop must set ``inference.enabled: true``
or it is skipped (legacy YAML with only ``model``/``policy`` no longer runs first).

Order when synthesized:

1. **Kimi tiered router** — router model picks one id from configured tiers by prompt.
2. **Inference routing** (optional) — only if ``inference.enabled`` is **true** and ``model`` is set.
3. **Optional Gemini** — last-resort hosted Gemma if enabled (optional_gemini).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _strip(s: Any) -> str:
    return str(s).strip() if s is not None else ""


def normalize_kimi_tiers(raw: Any) -> List[Dict[str, Any]]:
    """Return ``[{"id": str, "description": str, "models": [str, ...]}, ...]``."""
    out: List[Dict[str, Any]] = []
    if not raw:
        return out
    if isinstance(raw, dict):
        # Single object with models — one tier
        mids = raw.get("models")
        if isinstance(mids, list) and any(str(x).strip() for x in mids):
            out.append(
                {
                    "id": _strip(raw.get("id")) or "tier-0",
                    "description": _strip(raw.get("description")) or "",
                    "models": [str(x).strip() for x in mids if str(x).strip()],
                }
            )
        return out
    if not isinstance(raw, list):
        return out
    for i, tier in enumerate(raw):
        if isinstance(tier, dict):
            mids = tier.get("models")
            if not isinstance(mids, list):
                continue
            models = [str(x).strip() for x in mids if str(x).strip()]
            if not models:
                continue
            out.append(
                {
                    "id": _strip(tier.get("id")) or f"tier-{i}",
                    "description": _strip(tier.get("description")),
                    "models": models,
                }
            )
        elif isinstance(tier, list):
            models = [str(x).strip() for x in tier if str(x).strip()]
            if models:
                out.append(
                    {
                        "id": f"tier-{i}",
                        "description": "",
                        "models": models,
                    }
                )
    return out


def build_free_fallback_chain(config: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return fallback chain dicts from ``free_model_routing`` (may be empty)."""
    if not config or not isinstance(config, dict):
        return []
    fmr = config.get("free_model_routing")
    if not isinstance(fmr, dict):
        return []
    if not fmr.get("enabled", False):
        return []

    chain: List[Dict[str, Any]] = []

    kr = fmr.get("kimi_router") or {}
    if isinstance(kr, dict):
        router_model = _strip(kr.get("router_model"))
        tiers = normalize_kimi_tiers(kr.get("tiers"))
        if router_model and tiers:
            flat = [m for t in tiers for m in t.get("models", [])]
            if not flat:
                logger.warning("free_model_routing.kimi_router: tiers have no model ids — skipping Kimi tier")
            else:
                chain.append(
                    {
                        "provider": "huggingface",
                        "model": router_model,
                        "hf_router": True,
                        "hf_router_tiers": tiers,
                    }
                )
        elif router_model and not tiers:
            logger.warning(
                "free_model_routing.kimi_router: router_model set but tiers empty — "
                "configure kimi_router.tiers for tiered routing",
            )

    inf = fmr.get("inference") or {}
    if isinstance(inf, dict) and inf.get("enabled") is True:
        mid = _strip(inf.get("model"))
        pol = _strip(inf.get("policy"))
        if mid:
            entry: Dict[str, Any] = {"provider": "huggingface", "model": mid}
            if pol in ("fastest", "cheapest", "preferred"):
                entry["hf_inference_policy"] = pol
            elif pol:
                logger.warning("free_model_routing.inference: unknown policy %r — omitting suffix", pol)
            chain.append(entry)

    og = fmr.get("optional_gemini") or {}
    if isinstance(og, dict) and og.get("enabled") and _strip(og.get("model")):
        chain.append(
            {
                "provider": "gemini",
                "model": _strip(og.get("model")),
                "only_rate_limit": bool(og.get("only_rate_limit", True)),
                "restore_health_check": bool(og.get("restore_health_check", True)),
            }
        )

    return chain


def _prefer_synth_over_plain_hf_first(synth: List[Dict[str, Any]], first_fb: Dict[str, Any]) -> bool:
    """True when *synth* starts with Kimi ``hf_router`` but *first_fb* is plain HF (Inference API style)."""
    if not synth or not isinstance(first_fb, dict):
        return False
    if not synth[0].get("hf_router"):
        return False
    prov = str(first_fb.get("provider") or "").strip().lower()
    return prov == "huggingface" and not first_fb.get("hf_router")


def resolve_fallback_providers(config: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Resolve ``fallback_providers`` with ``free_model_routing`` when appropriate.

    - If ``fallback_providers`` is ``[]`` → no fallback (explicit opt-out).
    - If ``fallback_providers`` is a non-empty list → use as-is **unless** the first entry is a
      plain ``huggingface`` hub id (no ``hf_router``) while ``free_model_routing`` synthesizes
      a Kimi tier router first — then use the synthesized chain (fixes legacy YAML that pinned
      Inference Providers before Kimi).
    - Legacy ``fallback_model`` single dict → same Kimi-vs-plain-HF rule, else one-element list.
    - If ``fallback_providers`` is missing or ``None`` → build from ``free_model_routing``.
    """
    if not config or not isinstance(config, dict):
        return []
    synth = build_free_fallback_chain(config)
    fp = config.get("fallback_providers")
    if fp == []:
        return []
    if isinstance(fp, list) and len(fp) > 0:
        cleaned = [x for x in fp if isinstance(x, dict) and x.get("provider") and x.get("model")]
        if not cleaned:
            return synth
        if _prefer_synth_over_plain_hf_first(synth, cleaned[0]):
            return synth
        return cleaned
    fm = config.get("fallback_model")
    if isinstance(fm, dict) and fm.get("provider") and fm.get("model"):
        if _prefer_synth_over_plain_hf_first(synth, fm):
            return synth
        return [fm]
    return synth
