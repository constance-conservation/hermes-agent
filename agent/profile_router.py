"""Optional LLM-based routing of user prompts to named Hermes profiles (CLI).

When ``agent.profile_router.enabled`` is true, the CLI may delegate a user turn
to another profile via ``delegate_task(hermes_profile=...)`` *before* the main
``run_conversation`` loop, so the specialist profile's config/toolsets apply.

This is **off by default** (extra latency + cost; chief/orchestrator stays in control).
Does not mutate sticky ``active_profile`` — only per-turn delegation.

Automatic profile creation and ORG_REGISTRY edits are handled by
``hermes workspace org-automation apply`` / ``sync_org_automation`` (see
``hermes_cli.org_automation``), not by this router. Destructive lifecycle
actions stay out of scope; use ``hermes profile lifecycle-audit`` (advisory).
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _profiles_root() -> Path:
    return Path.home() / ".hermes" / "profiles"


def list_routable_profile_names() -> List[str]:
    """Return sorted directory names under ~/.hermes/profiles (kebab-case slugs)."""
    root = _profiles_root()
    if not root.is_dir():
        return []
    names = [
        p.name
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    ]
    return sorted(names)


def _keyword_route_profile(
    user_message: str,
    candidates: List[str],
    *,
    current_profile: str,
    skip_current: bool,
    threshold: float,
) -> Optional[Tuple[str, float, str]]:
    """Fast path: route obvious security/compliance questions without an LLM (no OpenRouter cost).

    Used when auxiliary APIs are exhausted or to avoid latency; still respects
    ``only_when_current_profiles`` / filters via *candidates*.
    """
    low = (user_message or "").strip().lower()
    if len(low) < 10:
        return None

    security_q = any(
        k in low
        for k in (
            "security posture",
            "security audit",
            "security review",
            "security status",
            "threat model",
            "vulnerability assessment",
            "compliance posture",
            "preflight security",
        )
    ) or (
        "security" in low
        and any(w in low for w in ("posture", "today", "status", "review", "audit", "risk", "threat"))
    )
    if not security_q:
        return None

    # Require an unambiguous specialist slug — avoid grabbing generic ``sec-bot``-style
    # names where "sec" is just a token (those stay on the LLM router).
    scored: List[Tuple[int, str]] = []
    for slug in candidates:
        s = slug.lower()
        strong = (
            "security" in s
            or "preflight" in s
            or "compliance" in s
            or "infosec" in s
            or "ag-sec" in s
            or s.startswith("sec-ops")
            or "sec-guard" in s
        )
        if strong:
            scored.append((50 + len(s), slug))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1]
    if skip_current and best == current_profile:
        return None, 0.0, "keyword target is current profile"
    conf = max(float(threshold), 0.78)
    return best, conf, "keyword security routing"


def _parse_router_json(text: str) -> Optional[Dict[str, Any]]:
    if not text or not text.strip():
        return None
    raw = text.strip()
    # Strip markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```\s*$", "", raw)
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _user_text_from_messages(messages: List[Dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


def _call_profile_router_llm(
    messages: List[Dict[str, Any]],
    router_cfg: Dict[str, Any],
) -> Any:
    """Run the profile-router JSON classifier on Hugging Face Inference only.

    Order (when ``use_free_model_routing`` is true, the default):

    1. Optional pinned ``router_provider``/``router_model`` if both are set to
       ``huggingface`` + a hub id (tried first; on failure, continue).
    2. ``free_model_routing.inference`` — official policy suffix on ``router.huggingface.co``.
    3. ``free_model_routing.kimi_router`` — Kimi router model picks one hub id from *tiers*,
       then that model runs the JSON classification.

    Requires ``HF_TOKEN`` (or ``HUGGING_FACE_HUB_TOKEN``). No Gemini / paid Google path.
    """
    from agent.auxiliary_client import call_llm

    use_free = router_cfg.get("use_free_model_routing", True)
    explicit_p = (router_cfg.get("router_provider") or "").strip().lower()
    explicit_m = (router_cfg.get("router_model") or "").strip()

    kwargs = dict(
        task=None,
        messages=messages,
        temperature=0.1,
        max_tokens=256,
    )

    if not use_free:
        if explicit_p and explicit_m:
            return call_llm(provider=explicit_p, model=explicit_m, **kwargs)
        raise RuntimeError(
            "profile_router: with use_free_model_routing=false, set router_provider and router_model",
        )

    tok = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or ""
    ).strip()
    base = (os.environ.get("HF_BASE_URL", "").strip() or "https://router.huggingface.co/v1").rstrip("/")
    if not tok:
        raise RuntimeError(
            "Profile router requires HF_TOKEN (or HUGGING_FACE_HUB_TOKEN) for Hugging Face Inference — "
            "set in ~/.hermes/.env or the profile .env (shared parent .env is loaded for profiles).",
        )

    from hermes_cli.config import load_config

    from agent.free_model_routing import normalize_kimi_tiers
    from agent.hf_fallback_router import apply_hf_inference_policy, resolve_hf_routed_model

    cfg = load_config()
    fmr = (cfg.get("free_model_routing") or {}) if isinstance(cfg, dict) else {}
    if not (isinstance(fmr, dict) and fmr.get("enabled")):
        fmr = {}

    user_text = _user_text_from_messages(messages)

    if explicit_p == "huggingface" and explicit_m:
        try:
            return call_llm(provider="huggingface", model=explicit_m, **kwargs)
        except Exception as exc:
            logger.warning(
                "profile_router: pinned router_model failed, using free_model_routing chain: %s",
                exc,
            )

    inf = fmr.get("inference") if isinstance(fmr.get("inference"), dict) else {}
    mid = str(inf.get("model") or "").strip()
    if mid:
        pol = str(inf.get("policy") or "").strip()
        pol_use = pol if pol in ("fastest", "cheapest", "preferred") else None
        routed_mid = apply_hf_inference_policy(mid, pol_use)
        try:
            return call_llm(provider="huggingface", model=routed_mid, **kwargs)
        except Exception as exc:
            logger.warning(
                "profile_router: HF inference route failed, trying Kimi tier pick: %s",
                exc,
            )

    kr = fmr.get("kimi_router") if isinstance(fmr.get("kimi_router"), dict) else {}
    router_model = str(kr.get("router_model") or "").strip()
    tiers = normalize_kimi_tiers(kr.get("tiers"))
    if router_model and tiers:
        picked = resolve_hf_routed_model(
            user_text,
            api_key=tok,
            base_url=base,
            router_model=router_model,
            tiers=tiers,
        )
        return call_llm(provider="huggingface", model=picked, **kwargs)

    raise RuntimeError(
        "profile_router: set free_model_routing.inference.model and/or kimi_router in config.yaml, "
        "or agent.profile_router with router_provider=huggingface and router_model=<hub id>.",
    )


def classify_profile_for_prompt(
    user_message: str,
    *,
    candidates: List[str],
    current_profile: str,
    router_cfg: Dict[str, Any],
) -> Tuple[Optional[str], float, str]:
    """Call auxiliary LLM; return (target_profile or None, confidence, reason)."""
    if not candidates:
        return None, 0.0, "no profiles"
    threshold = float(router_cfg.get("confidence_threshold") or 0.72)
    min_chars = int(router_cfg.get("min_message_chars") or 12)
    if len((user_message or "").strip()) < min_chars:
        return None, 0.0, "message too short"

    exclude = set(router_cfg.get("exclude_profiles") or [])
    allow_only = router_cfg.get("allow_only_profiles") or []
    if allow_only:
        candidates = [c for c in candidates if c in allow_only]
    candidates = [c for c in candidates if c not in exclude]
    if not candidates:
        return None, 0.0, "no candidates after filters"

    only_from = router_cfg.get("only_when_current_profiles") or []
    if only_from and current_profile not in only_from:
        return None, 0.0, "current profile not in only_when_current_profiles"

    skip_current = router_cfg.get("exclude_current_profile", True)
    if skip_current and current_profile in candidates and current_profile != "default":
        # Still allow routing *to* another profile when current is chief; remove self from targets only if same name chosen later
        pass

    kw = _keyword_route_profile(
        user_message,
        candidates,
        current_profile=current_profile,
        skip_current=skip_current,
        threshold=threshold,
    )
    if kw and kw[0]:
        return kw[0], kw[1], kw[2]

    system = (
        "You route user turns to Hermes profile slugs (each profile is an isolated agent runtime). "
        "Reply with ONLY valid JSON, no markdown.\n"
        'Schema: {"profile": "<exact slug from list or null>", "confidence": number 0-1, "reason": "brief"}\n'
        "When the user's request clearly fits a specialist (infer from slug words: security, legal, "
        "hr, finance, infra, director, product, compliance, preflight, audit, etc.), choose that slug "
        "with confidence 0.7–1.0.\n"
        "Use profile null with confidence below 0.5 when the orchestrator should answer or no slug fits.\n"
        "Never invent slugs; profile must be exactly one of the listed names or null."
    )
    user = (
        f"Current session profile: {current_profile!r}\n"
        f"Available profile slugs: {', '.join(candidates)}\n\n"
        f"User message:\n{user_message.strip()[:8000]}"
    )

    from agent.auxiliary_client import extract_content_or_reasoning

    _messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    text: Optional[str] = None
    try:
        resp = _call_profile_router_llm(_messages, router_cfg)
        text = extract_content_or_reasoning(resp)
    except Exception as exc:
        logger.warning("profile_router LLM call failed: %s", exc)
        return None, 0.0, f"router error: {exc}"

    if not (text and str(text).strip()):
        return None, 0.0, "empty router model output"

    data = _parse_router_json(text)
    if not data:
        logger.debug("profile_router: unparseable response: %s", text[:200])
        return None, 0.0, "unparseable router output"

    name = data.get("profile")
    if name is not None and not isinstance(name, str):
        name = None
    if name is not None:
        name = name.strip()
        if name == "" or name.lower() == "null":
            name = None

    try:
        conf = float(data.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
    reason = str(data.get("reason") or "").strip()[:500]

    if name is None or conf < threshold:
        return None, conf, reason or "below threshold"

    if name not in candidates:
        logger.info("profile_router: model chose unknown profile %r", name)
        return None, conf, "unknown profile slug"

    if skip_current and name == current_profile:
        return None, conf, "target is current profile"

    return name, conf, reason


def route_and_delegate_if_configured(
    *,
    user_message: str,
    parent_agent: Any,
    agent_config: Dict[str, Any],
    current_profile: str,
) -> Optional[str]:
    """If routing applies, run delegate_task and return markdown for the user; else None."""
    router_cfg = agent_config if isinstance(agent_config, dict) else {}
    if not router_cfg.get("enabled"):
        return None

    candidates = list_routable_profile_names()
    target, conf, reason = classify_profile_for_prompt(
        user_message,
        candidates=candidates,
        current_profile=current_profile,
        router_cfg=router_cfg,
    )
    if not target:
        return None

    from tools.delegate_tool import delegate_task

    payload = delegate_task(
        goal=user_message.strip(),
        context=(
            f"Routed automatically from profile {current_profile!r} "
            f"(router confidence {conf:.2f}). Reason: {reason}"
        ),
        hermes_profile=target,
        parent_agent=parent_agent,
    )
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and data.get("error"):
        logger.warning("profile_router delegate failed: %s", data.get("error"))
        return None

    # Format a concise reply for the CLI (delegate returns JSON with results[])
    results = data.get("results")
    body = payload
    if isinstance(results, list) and results:
        first = results[0]
        if isinstance(first, dict):
            body = first.get("summary") or first.get("response") or json.dumps(first, indent=2)[:12000]
    header = f"_Delegated to profile `{target}` (router confidence {conf:.2f})_\n\n"
    return header + (body if isinstance(body, str) else str(body))
