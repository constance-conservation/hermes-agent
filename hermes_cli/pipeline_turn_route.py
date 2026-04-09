"""Shared ``/models`` pipeline → turn_route merge for CLI and gateway."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PipelineTurnRouteMerge:
    """Result of applying a manual pipeline pick onto a base :func:`resolve_turn_route` dict."""

    route: Dict[str, Any]
    clear_sticky_pick: bool = False


def merge_pipeline_models_choice_into_turn_route(
    base: Dict[str, Any],
    choice: Dict[str, Any],
    *,
    profile_api_key: str = "",
    profile_base_url: str = "",
    profile_provider: str = "",
    profile_api_mode: str = "",
    profile_command: Any = None,
    profile_args: Optional[list] = None,
    profile_credential_pool: Any = None,
    consume: bool = True,
) -> PipelineTurnRouteMerge:
    """Apply a ``/models`` row (sticky or one-shot) onto *base*.

    Mirrors ``HermesCLI._route_for_pipeline_model_once`` without mutating CLI state.
    *consume* — when True, one-shot semantics (legacy ``_pipeline_model_once``); when False, sticky.
    """
    from hermes_cli.runtime_provider import resolve_runtime_provider

    model = str(choice.get("model") or "").strip()
    pk = str(choice.get("provider_kind") or "primary").strip().lower()
    if not model:
        return PipelineTurnRouteMerge(
            route={**base, "skip_per_turn_tier_routing": base.get("skip_per_turn_tier_routing", False)},
            clear_sticky_pick=True,
        )

    def _rt_from_resolved(rt: dict) -> dict:
        return {
            "api_key": rt.get("api_key"),
            "base_url": rt.get("base_url"),
            "provider": rt.get("provider"),
            "api_mode": rt.get("api_mode"),
            "command": rt.get("command"),
            "args": list(rt.get("args") or []),
            "credential_pool": None,
        }

    try:
        if pk == "primary":
            _m = model.lower()
            if _m.startswith("gpt-"):
                from agent.openai_native_runtime import native_openai_runtime_tuple

                tup = native_openai_runtime_tuple()
                if tup:
                    bu, ak = tup
                    return PipelineTurnRouteMerge(
                        route={
                            "model": model,
                            "runtime": {
                                "api_key": ak,
                                "base_url": bu,
                                "provider": "custom",
                                "api_mode": "codex_responses",
                                "command": None,
                                "args": [],
                                "credential_pool": None,
                            },
                            "label": f"/models → {model} (native OpenAI)",
                            "skip_per_turn_tier_routing": True,
                            "signature": (
                                model,
                                "custom",
                                bu,
                                "codex_responses",
                                None,
                                (),
                            ),
                        },
                    )
                # gpt-* but no native tuple — fall through to profile primary like CLI.
            # vendor/model slugs (e.g. openai/gpt-5.4) are OpenRouter IDs. Binding them to
            # profile primary under OPM incorrectly uses api.openai.com + bare-id coercion.
            if "/" in model and not _m.startswith("gpt-"):
                rt = resolve_runtime_provider(requested="openrouter")
                _rbu = (rt.get("base_url") or "").lower()
                _ram = rt.get("api_mode") or "chat_completions"
                if "openrouter.ai" in _rbu and _ram == "codex_responses":
                    _ram = "chat_completions"
                _rt_out = _rt_from_resolved(rt)
                _rt_out["api_mode"] = _ram
                return PipelineTurnRouteMerge(
                    route={
                        "model": model,
                        "runtime": _rt_out,
                        "label": f"/models → {model} (OpenRouter)",
                        "skip_per_turn_tier_routing": True,
                        "signature": (
                            model,
                            rt.get("provider"),
                            rt.get("base_url"),
                            _ram,
                            rt.get("command"),
                            tuple(rt.get("args") or ()),
                        ),
                    },
                )
            return PipelineTurnRouteMerge(
                route={
                    "model": model,
                    "runtime": {
                        "api_key": profile_api_key,
                        "base_url": profile_base_url,
                        "provider": profile_provider,
                        "api_mode": profile_api_mode,
                        "command": profile_command,
                        "args": list(profile_args or []),
                        "credential_pool": profile_credential_pool,
                    },
                    "label": f"/models → {model}",
                    "skip_per_turn_tier_routing": True,
                    "signature": (
                        model,
                        profile_provider,
                        profile_base_url,
                        profile_api_mode,
                        profile_command,
                        tuple(profile_args or ()),
                    ),
                },
            )
        if pk == "huggingface":
            rt = resolve_runtime_provider(requested="huggingface")
            return PipelineTurnRouteMerge(
                route={
                    "model": model,
                    "runtime": _rt_from_resolved(rt),
                    "label": f"/models → {model} (HF)",
                    "skip_per_turn_tier_routing": True,
                    "signature": (
                        model,
                        rt.get("provider"),
                        rt.get("base_url"),
                        rt.get("api_mode"),
                        rt.get("command"),
                        tuple(rt.get("args") or ()),
                    ),
                },
            )
        if pk == "gemini":
            rt = resolve_runtime_provider(requested="gemini")
            return PipelineTurnRouteMerge(
                route={
                    "model": model,
                    "runtime": _rt_from_resolved(rt),
                    "label": f"/models → {model} (Gemini)",
                    "skip_per_turn_tier_routing": True,
                    "signature": (
                        model,
                        rt.get("provider"),
                        rt.get("base_url"),
                        rt.get("api_mode"),
                        rt.get("command"),
                        tuple(rt.get("args") or ()),
                    ),
                },
            )
        if pk == "local":
            import os as _os_local

            try:
                from agent.local_inference import local_inference_override_for_hub_model

                _loc = local_inference_override_for_hub_model(model)
            except Exception:
                _loc = None
            if _loc:
                _local_base, _local_key = _loc[0], _loc[1]
                _local_model = _loc[2] if len(_loc) > 2 and _loc[2] else model
            else:
                _local_base = (
                    _os_local.environ.get("HERMES_LOCAL_INFERENCE_BASE_URL", "").strip()
                    or "http://localhost:8000/v1"
                )
                if not _local_base.endswith("/v1"):
                    _local_base = _local_base.rstrip("/") + "/v1"
                _local_key = (
                    _os_local.environ.get("HERMES_LOCAL_INFERENCE_API_KEY", "").strip()
                    or "dummy-local"
                )
                _local_model = model
            return PipelineTurnRouteMerge(
                route={
                    "model": _local_model,
                    "runtime": {
                        "api_key": _local_key,
                        "base_url": _local_base,
                        "provider": "openai",
                        "api_mode": None,
                        "command": None,
                        "args": [],
                        "credential_pool": None,
                    },
                    "label": f"/models → {model} (local)",
                    "skip_per_turn_tier_routing": True,
                    "signature": (_local_model, "openai", _local_base, None, None, ()),
                },
            )
        if pk == "openrouter":
            rt = resolve_runtime_provider(requested="openrouter")
            _rbu = (rt.get("base_url") or "").lower()
            _ram = rt.get("api_mode") or "chat_completions"
            if "openrouter.ai" in _rbu and _ram == "codex_responses":
                _ram = "chat_completions"
            _rt_out = _rt_from_resolved(rt)
            _rt_out["api_mode"] = _ram
            return PipelineTurnRouteMerge(
                route={
                    "model": model,
                    "runtime": _rt_out,
                    "label": f"/models → {model} (OpenRouter)",
                    "skip_per_turn_tier_routing": True,
                    "signature": (
                        model,
                        rt.get("provider"),
                        rt.get("base_url"),
                        _ram,
                        rt.get("command"),
                        tuple(rt.get("args") or ()),
                    ),
                },
            )
        if pk == "openai_native":
            from agent.openai_native_runtime import native_openai_runtime_tuple

            tup = native_openai_runtime_tuple()
            if not tup:
                logging.warning("/models native OpenAI: OPENAI_API_KEY not set")
                return PipelineTurnRouteMerge(
                    route={
                        **base,
                        "skip_per_turn_tier_routing": base.get("skip_per_turn_tier_routing", False),
                    },
                    clear_sticky_pick=not consume,
                )
            bu, ak = tup
            return PipelineTurnRouteMerge(
                route={
                    "model": model,
                    "runtime": {
                        "api_key": ak,
                        "base_url": bu,
                        "provider": "custom",
                        "api_mode": "codex_responses",
                        "command": None,
                        "args": [],
                        "credential_pool": None,
                    },
                    "label": f"/models → {model} (native OpenAI)",
                    "skip_per_turn_tier_routing": True,
                    "signature": (
                        model,
                        "custom",
                        bu,
                        "codex_responses",
                        None,
                        (),
                    ),
                },
            )
        # Unknown provider_kind — fall back to base; clear sticky when this was a sticky pick.
        return PipelineTurnRouteMerge(
            route={**base, "skip_per_turn_tier_routing": base.get("skip_per_turn_tier_routing", False)},
            clear_sticky_pick=not consume,
        )
    except Exception as exc:
        logging.warning("pipeline model route failed, using base route: %s", exc)
        return PipelineTurnRouteMerge(
            route={**base, "skip_per_turn_tier_routing": base.get("skip_per_turn_tier_routing", False)},
            clear_sticky_pick=False,
        )
