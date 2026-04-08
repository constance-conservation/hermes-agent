"""Delegation context review and model gating.

Before a delegated agent runs, this module:
1. Reviews the delegation context for sufficiency (using a free model).
2. Ensures delegated agents use cheaper-or-equal models vs the parent.
3. Blocks consultant-tier models for delegated agents.

All review calls use the free model (gemma-4-31b-it via Gemini API) to
keep overhead at zero cost.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)
_DEBUG_LOG_PATH = "/Users/agent-os/hermes-agent/.cursor/debug-98bb66.log"


def _dbg98(hypothesis_id: str, location: str, message: str, data: Dict[str, Any]) -> None:
    try:
        payload = {
            "sessionId": "98bb66",
            "runId": "gemma-debug-1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass

_COST_RANK = {
    "free": 0,
    "low_cost": 1,
    "paid": 2,
}

_CONSULTANT_TIER_SUBSTRINGS = (
    "opus",
    "gpt-5.4",
    "gpt-5.3-codex",
)

_MAX_DELEGATE_TIER = "D"


def is_consultant_tier_model(model_id: str) -> bool:
    """True if the model is in the consultant tier (should not be used by delegates)."""
    mid = (model_id or "").strip().lower()
    return any(s in mid for s in _CONSULTANT_TIER_SUBSTRINGS)


def _opm_allows_subprocess_model(proposed_model: str, parent_agent: Any) -> bool:
    """True when openai_primary_mode is on and *proposed_model* is in the allowlist."""
    try:
        from agent.openai_primary_mode import resolve_openai_primary_mode

        opm, opm_meta = resolve_openai_primary_mode(parent_agent)
        if not opm_meta.get("enabled", False):
            return False
        allowed = opm.get("allowed_subprocess_models") or []

        def _core(mid: str) -> str:
            m = (mid or "").strip().lower()
            if m.startswith("openai/"):
                return m.split("/", 1)[1]
            return m

        mid = _core(proposed_model)
        allowed_core = {_core(str(a)) for a in allowed if str(a).strip()}
        return mid in allowed_core
    except Exception:
        return False


def gate_delegate_model(
    proposed_model: str,
    parent_model: str,
    parent_agent: Any = None,
) -> Tuple[str, str]:
    """Enforce model gating for delegated agents.

    Returns ``(approved_model, reason)`` — the model may be downgraded.
    """
    from agent.subprocess_governance import classify_model_cost, default_free_subprocess_model_id
    # region agent log
    _dbg98(
        "H4",
        "agent/delegation_review.py:gate_delegate_model",
        "gate delegate model entry",
        {"proposed_model": str(proposed_model or ""), "parent_model": str(parent_model or "")},
    )
    # endregion

    if is_consultant_tier_model(proposed_model):
        # When OPM is active, GPT models in allowed_subprocess_models are exempt
        # from consultant-tier blocking (they ARE the baseline, not consultants).
        _skip_block = _opm_allows_subprocess_model(proposed_model, parent_agent)
        if not _skip_block:
            free = default_free_subprocess_model_id()
            # region agent log
            _dbg98(
                "H4",
                "agent/delegation_review.py:gate_delegate_model",
                "consultant tier blocked",
                {"proposed_model": str(proposed_model or ""), "fallback_model": str(free or "")},
            )
            # endregion
            return free, f"consultant model {proposed_model!r} blocked for delegates; using {free}"

    parent_cost = _COST_RANK.get(classify_model_cost(parent_model), 2)
    child_cost = _COST_RANK.get(classify_model_cost(proposed_model), 2)

    if child_cost > parent_cost:
        # Parent may be on a free/cheap tier (gemma) while OPM still mandates GPT delegates.
        if parent_agent is not None and _opm_allows_subprocess_model(proposed_model, parent_agent):
            return proposed_model, "approved (openai_primary_mode subprocess baseline)"

        free = default_free_subprocess_model_id()
        # region agent log
        _dbg98(
            "H4",
            "agent/delegation_review.py:gate_delegate_model",
            "delegate cost downgraded",
            {
                "proposed_model": str(proposed_model or ""),
                "parent_model": str(parent_model or ""),
                "fallback_model": str(free or ""),
                "child_cost": int(child_cost),
                "parent_cost": int(parent_cost),
            },
        )
        # endregion
        return free, (
            f"delegate model {proposed_model!r} more expensive than parent "
            f"{parent_model!r}; downgraded to {free}"
        )

    # region agent log
    _dbg98(
        "H4",
        "agent/delegation_review.py:gate_delegate_model",
        "delegate model approved",
        {"proposed_model": str(proposed_model or ""), "parent_model": str(parent_model or "")},
    )
    # endregion
    return proposed_model, "approved"


def review_delegation_context(
    goal: str,
    context: Optional[str],
    proposed_model: str,
) -> Dict[str, Any]:
    """Quick review of delegation context using the free model.

    Returns a dict with ``approved`` (bool), optional ``improved_context``,
    and optional ``model_override``.

    On any failure returns ``{"approved": True}`` (fail-open).
    """
    if not goal or not goal.strip():
        return {"approved": True, "note": "empty goal — skipped review"}

    snippet = (goal[:200] + "..." if len(goal) > 200 else goal)
    ctx_snippet = ""
    if context:
        ctx_snippet = context[:150] + ("..." if len(context) > 150 else "")

    prompt = (
        "You are a delegation reviewer. Evaluate if the context below is "
        "sufficient for a sub-agent to complete the goal. Respond ONLY with "
        'a JSON object: {"approved": true} or {"approved": true, '
        '"improved_context": "one sentence of additional guidance"}.\n\n'
        f"Goal: {snippet}\n"
    )
    if ctx_snippet:
        prompt += f"Context: {ctx_snippet}\n"
    prompt += f"Model: {proposed_model}\n"

    try:
        from agent.auxiliary_client import call_llm

        raw = call_llm(
            prompt=prompt,
            model="gemma-4-31b-it",
            provider="gemini",
            max_tokens=80,
            temperature=0.0,
        )
        text = (raw or "").strip()
        if text.startswith("{"):
            return json.loads(text)
    except Exception as exc:
        logger.debug("delegation review call failed: %s", exc)

    return {"approved": True}
