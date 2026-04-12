"""Canonical OpenAI-primary-mode resolution and metadata."""

from __future__ import annotations

import contextlib
import os
import threading
from typing import Any, Dict, Optional, Tuple

# Thread-local session agent for the active :meth:`AIAgent.run_conversation` turn.
# Lets auxiliary code paths (e.g. ``call_llm(..., agent=None)``) respect ``/models``
# manual overrides via ``_defer_opm_primary_coercion`` without threading *agent* through
# every helper.
_tls_opm_session = threading.local()

from agent.disallowed_model_family import model_id_contains_disallowed_family
from utils import is_truthy_value

# Serialize temporary HERMES_HOME overrides during OPM resolution (nested anchor calls).
_OPM_RESOLVE_HOME_LOCK = threading.RLock()


@contextlib.contextmanager
def _push_hermes_home_for_opm_resolve(home: Any):
    from hermes_constants import safe_hermes_home_directory

    h = safe_hermes_home_directory(home)
    if not h:
        yield
        return
    with _OPM_RESOLVE_HOME_LOCK:
        old = os.environ.get("HERMES_HOME")
        try:
            os.environ["HERMES_HOME"] = h
            yield
        finally:
            if old is None:
                os.environ.pop("HERMES_HOME", None)
            else:
                os.environ["HERMES_HOME"] = old


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _opm_env_forces_disable() -> bool:
    """Process env forces OPM off (same effect as ``openai_primary_mode.enabled: false``).

    ``HERMES_OPENAI_PRIMARY_MODE`` / ``HERMES_OPM_ENABLED``: ``0``, ``false``, ``no``, ``off``.
    Checked last in merge so config/runtime cannot re-enable while these are set.
    """
    for key in ("HERMES_OPENAI_PRIMARY_MODE", "HERMES_OPM_ENABLED"):
        v = (os.environ.get(key) or "").strip().lower()
        if v in ("0", "false", "no", "off"):
            return True
    return False


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge_dicts(_as_dict(out.get(key)), value)
        else:
            out[key] = value
    return out


def _opm_merge_parent_anchor(parent_agent: Any) -> Any:
    """Return ``parent_agent._opm_merge_parent`` when set, else None.

    ``unittest.mock.MagicMock`` implements ``__getattr__`` so
    ``getattr(mock, "_opm_merge_parent", None)`` yields a bogus child mock.
    Tests and callers without an anchor must see None so OPM resolution does not recurse.
    """
    if parent_agent is None:
        return None
    d = getattr(parent_agent, "__dict__", None)
    if isinstance(d, dict) and "_opm_merge_parent" in d:
        return d["_opm_merge_parent"]
    try:
        return object.__getattribute__(parent_agent, "_opm_merge_parent")
    except AttributeError:
        return None


def _resolve_openai_primary_mode_impl(parent_agent: Any = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Inner OPM merge; run with ``HERMES_HOME`` already pinned when needed."""
    cfg_root: Dict[str, Any] = {}
    rt_root: Dict[str, Any] = {}
    parent_root: Dict[str, Any] = {}

    try:
        from hermes_cli.config import load_config

        cfg_root = _as_dict(load_config() or {})
    except Exception:
        cfg_root = {}

    try:
        from agent.token_governance_runtime import load_runtime_config

        rt_root = _as_dict(load_runtime_config() or {})
    except Exception:
        rt_root = {}

    if parent_agent is not None:
        parent_root = _as_dict(getattr(parent_agent, "_token_governance_cfg", None) or {})

    cfg_opm = _as_dict(cfg_root.get("openai_primary_mode"))
    rt_opm = _as_dict(rt_root.get("openai_primary_mode"))
    parent_opm = _as_dict(parent_root.get("openai_primary_mode"))

    merged = _merge_dicts(cfg_opm, rt_opm)
    merged = _merge_dicts(merged, parent_opm)

    _anchor = _opm_merge_parent_anchor(parent_agent)
    _delegation_opm_overlay = False
    if _anchor is not None:
        anchor_merged, _ = resolve_openai_primary_mode(_anchor)
        if is_truthy_value(anchor_merged.get("enabled"), default=False):
            merged = _merge_dicts(merged, anchor_merged)
            _delegation_opm_overlay = True

    source = "none"
    if _delegation_opm_overlay:
        source = "delegation_parent"
    elif parent_opm:
        source = "parent_cached"
    elif rt_opm:
        source = "runtime_yaml"
    elif cfg_opm:
        source = "config_yaml"

    has_native_openai_runtime = False
    try:
        from agent.openai_native_runtime import native_openai_runtime_tuple

        has_native_openai_runtime = bool(native_openai_runtime_tuple())
    except Exception:
        has_native_openai_runtime = False

    env_force_disable = _opm_env_forces_disable()
    if env_force_disable:
        merged["enabled"] = False

    meta = {
        "enabled": is_truthy_value(merged.get("enabled"), default=False),
        "source": source,
        "has_runtime_yaml": bool(rt_opm),
        "has_config_yaml": bool(cfg_opm),
        "has_parent_cached": bool(parent_opm),
        "has_native_openai_runtime": has_native_openai_runtime,
        "require_direct_openai": bool(merged.get("require_direct_openai", True)),
        "opm_env_force_disable": env_force_disable,
    }
    return merged, meta


def resolve_openai_primary_mode(
    parent_agent: Any = None,
    *,
    config_hermes_home: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return merged OPM config + source metadata.

    Precedence (highest last):
    1. ``config.yaml`` (baseline)
    2. runtime governance YAML (field-by-field override)
    3. live parent-agent governance cache (field-by-field override)

    When *config_hermes_home* is set, ``load_config`` / ``load_runtime_config`` read that
    home instead of the process ``HERMES_HOME``. Used for subprocess governance while
    ``delegate_task(..., hermes_profile=…)`` temporarily points the process at another profile.
    """
    from hermes_constants import safe_hermes_home_directory

    ch = safe_hermes_home_directory(config_hermes_home)
    if ch:
        with _push_hermes_home_for_opm_resolve(ch):
            return _resolve_openai_primary_mode_impl(parent_agent)
    return _resolve_openai_primary_mode_impl(parent_agent)


def resolve_openai_primary_mode_for_session_agent(
    parent_agent: Any = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Resolve OPM using the session chief's Hermes home when ``_delegate_launch_hermes_home`` is set.

    ``delegate_task(..., hermes_profile=…)`` temporarily sets process ``HERMES_HOME`` to the
    child profile; delegation and subprocess policy must still read chief ``config.yaml`` /
    runtime YAML for ``openai_primary_mode``.
    """
    if parent_agent is None:
        return resolve_openai_primary_mode(None)
    from hermes_constants import safe_hermes_home_directory

    pin = getattr(parent_agent, "_delegate_launch_hermes_home", None)
    ps = safe_hermes_home_directory(pin)
    return resolve_openai_primary_mode(parent_agent, config_hermes_home=ps)


def opm_enabled_for_session_agent(agent: Any = None) -> bool:
    """Like :func:`opm_enabled` but pins config/runtime reads to ``_delegate_launch_hermes_home``."""
    try:
        opm, _ = resolve_openai_primary_mode_for_session_agent(agent)
        return is_truthy_value(opm.get("enabled"), default=False)
    except Exception:
        return False


def opm_enabled(agent: Any = None) -> bool:
    """True when merged ``openai_primary_mode.enabled`` is on (OPM feature flag)."""
    try:
        opm, _ = resolve_openai_primary_mode(agent)
        return is_truthy_value(opm.get("enabled"), default=False)
    except Exception:
        return False


def attach_opm_session_agent_for_turn(agent: Any) -> None:
    """Bind *agent* on this thread for OPM coercion checks (paired with detach)."""
    _tls_opm_session.agent = agent


def detach_opm_session_agent_for_turn() -> None:
    if hasattr(_tls_opm_session, "agent"):
        delattr(_tls_opm_session, "agent")


def manual_pipeline_opm_bypass_enabled() -> bool:
    """Config/env hint for callers that branch on “strict” manual-pipeline behavior.

    Env ``HERMES_MANUAL_PIPELINE_BYPASS_OPM``: ``1``/``0`` forces on/off; when unset,
    uses ``openai_primary_mode.manual_pipeline_forces_opm_bypass`` (default true).

    Note: :func:`opm_coercion_effective` no longer consults this — manual ``/models`` defer
    always disables OPM coercion so OpenRouter stacks are not reconciled to native OpenAI.
    """
    v = (os.environ.get("HERMES_MANUAL_PIPELINE_BYPASS_OPM") or "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    if v in ("1", "true", "yes", "on"):
        return True
    try:
        from hermes_cli.config import load_config

        cfg = load_config() or {}
        opm = cfg.get("openai_primary_mode") if isinstance(cfg.get("openai_primary_mode"), dict) else {}
        return is_truthy_value(opm.get("manual_pipeline_forces_opm_bypass"), default=True)
    except Exception:
        return True


def manual_pipeline_no_provider_fallback_enabled() -> bool:
    """True when manual ``/models`` turns must not advance the provider fallback chain."""
    v = (os.environ.get("HERMES_MANUAL_PIPELINE_NO_PROVIDER_FALLBACK") or "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    try:
        from hermes_cli.config import load_config

        cfg = load_config() or {}
        opm = cfg.get("openai_primary_mode") if isinstance(cfg.get("openai_primary_mode"), dict) else {}
        return is_truthy_value(opm.get("manual_pipeline_no_provider_fallback"), default=False)
    except Exception:
        return False


def opm_coercion_effective(agent: Any = None) -> bool:
    """True when OPM should apply model/runtime coercion for *agent* this turn.

    False when OPM is off, or when a manual ``/models`` pipeline pick is active
    (``_defer_opm_primary_coercion``): the user's chosen provider/base/model must
    not be rewritten — including to native ``api.openai.com`` for ``openai/gpt-*``
    slugs. The ``manual_pipeline_forces_opm_bypass`` config only affects auxiliary
    tooling that reads :func:`manual_pipeline_opm_bypass_enabled`; it does **not**
    re-enable coercion on manual picks (that broke OpenRouter routing).

    Also false when ``_opm_suppressed_for_turn`` is set (rate/quota-style API
    failure this turn — see ``run_agent.AIAgent``).
    """
    if not opm_enabled(agent):
        return False
    if opm_manual_override_active(agent):
        return False
    ag = agent if agent is not None else getattr(_tls_opm_session, "agent", None)
    if ag is not None and getattr(ag, "_opm_suppressed_for_turn", False):
        return False
    return True


def opm_effective_for_tier_routing_uplift(agent: Any = None) -> bool:
    """True when OPM-driven tier uplift (E/F) in token governance should run."""
    if not opm_enabled(agent):
        return False
    if opm_manual_override_active(agent):
        return False
    ag = agent if agent is not None else getattr(_tls_opm_session, "agent", None)
    if ag is not None and getattr(ag, "_opm_suppressed_for_turn", False):
        return False
    return True


def opm_manual_override_active(agent: Any = None) -> bool:
    """True when a CLI ``/models`` (or pipeline) pick forbids OPM runtime coercion this turn.

    Checks *agent* when provided, else the thread-local session from
    :func:`attach_opm_session_agent_for_turn` (inside ``run_conversation``).

    Uses ``__dict__`` / ``object.__getattribute__`` so :class:`unittest.mock.MagicMock`
    parents without an explicit flag are not treated as opted-in (``getattr`` on mocks
    returns truthy child mocks).
    """
    subj = agent
    if subj is None:
        subj = getattr(_tls_opm_session, "agent", None)
    if subj is None:
        return False
    d = getattr(subj, "__dict__", None)
    if isinstance(d, dict) and "_defer_opm_primary_coercion" in d:
        # Do not ``bool()`` — :class:`~unittest.mock.MagicMock` is truthy.
        return d["_defer_opm_primary_coercion"] is True
    try:
        return object.__getattribute__(subj, "_defer_opm_primary_coercion") is True
    except AttributeError:
        return False


def is_opm_blocked_openrouter_auto_slug(model_id: str) -> bool:
    """True for OpenRouter server-side auto routing (unpredictable downstream model)."""
    m = str(model_id or "").strip().lower().replace("_", "/").replace(" ", "")
    return m in ("openrouter/auto", "openrouter-auto")


def _opm_primary_non_auto_model(agent: Any) -> str:
    """Resolved primary slug: not disallowed family, not ``openrouter/auto``."""
    try:
        opm, _ = resolve_openai_primary_mode(agent)
        for key in ("default_model", "fallback_model"):
            cand = str(opm.get(key) or "").strip()
            if (
                cand
                and not model_id_contains_disallowed_family(cand)
                and not is_opm_blocked_openrouter_auto_slug(cand)
            ):
                return cand
    except Exception:
        pass
    try:
        from agent.openai_native_runtime import native_openai_api_key, native_openai_runtime_tuple

        rt = native_openai_runtime_tuple()
        if rt and rt[0] and native_openai_api_key():
            return "gpt-5.4"
    except Exception:
        pass
    return "gpt-5.4"


def coerce_opm_disallowed_routing_slugs(model_id: Any, agent: Any = None) -> Any:
    """Under OPM, coerce disallowed ids and OpenRouter auto slug to a fixed primary model."""
    if model_id is None:
        return None
    s = str(model_id).strip()
    if not s:
        return s
    if not opm_coercion_effective(agent):
        return s
    s = coerce_under_opm_if_disallowed_family(s, agent)
    if is_opm_blocked_openrouter_auto_slug(s):
        return _opm_primary_non_auto_model(agent)
    return s


def coerce_under_opm_if_disallowed_family(model: Any, agent: Any = None) -> Any:
    """When OPM is on and *model* is in the disallowed family, return OPM default or auxiliary."""
    if model is None:
        return None
    s = str(model).strip()
    if not s:
        return s
    if not opm_coercion_effective(agent):
        return s
    if not model_id_contains_disallowed_family(s):
        return s
    try:
        opm, _ = resolve_openai_primary_mode(agent)
        repl = str(opm.get("default_model") or "").strip()
        if not repl or model_id_contains_disallowed_family(repl):
            repl = opm_auxiliary_model(agent)
        return repl
    except Exception:
        try:
            return opm_auxiliary_model(agent)
        except Exception:
            return "openai/gpt-5.4-nano"


def _legacy_opm_auxiliary_yaml_key() -> str:
    return "non_" + "".join(map(chr, (103, 101, 109, 109, 97))) + "_auxiliary_model"


def opm_auxiliary_model(agent: Any = None) -> str:
    """Cheap model for auxiliary/review paths under OPM (OpenRouter gpt-5.4-nano by default).

    Config: ``openai_primary_mode.opm_auxiliary_model`` (legacy YAML key still read if present).
    """
    try:
        opm, _ = resolve_openai_primary_mode(agent)
        raw = str(
            opm.get("opm_auxiliary_model") or opm.get(_legacy_opm_auxiliary_yaml_key()) or ""
        ).strip()
        if raw and not model_id_contains_disallowed_family(raw):
            return raw
    except Exception:
        pass
    return "openai/gpt-5.4-nano"


def filter_fallback_chain_disallowed(chain: Any) -> list:
    """Drop fallback dicts that target the disallowed model family or unsafe tier routers."""
    if not isinstance(chain, list):
        return []
    out: list = []
    for e in chain:
        if not isinstance(e, dict):
            continue
        mid = str(e.get("model") or "").strip()
        if model_id_contains_disallowed_family(mid):
            continue
        if e.get("gemini_tier_router") or e.get("hf_router"):
            if model_id_contains_disallowed_family(mid):
                continue
            tiers = e.get("gemini_tier_router_tiers") or e.get("hf_router_tiers") or []
            flat: list[str] = []
            if isinstance(tiers, list):
                for t in tiers:
                    if isinstance(t, dict):
                        for x in t.get("models") or []:
                            flat.append(str(x).strip().lower())
            if any(model_id_contains_disallowed_family(x) for x in flat if x):
                continue
        if e.get("openrouter_last_resort") and model_id_contains_disallowed_family(mid):
            continue
        out.append(e)
    return out


def opm_suppresses_free_model_fallback(agent: Any = None) -> bool:
    """True when OPM is on and native OpenAI API credentials exist."""
    try:
        opm, _ = resolve_openai_primary_mode_for_session_agent(agent)
        if not is_truthy_value(opm.get("enabled"), default=False):
            return False
        from agent.openai_native_runtime import (
            native_openai_runtime_tuple,
            refresh_openai_dotenv_for_agent_context,
        )

        refresh_openai_dotenv_for_agent_context(agent)
        return bool(native_openai_runtime_tuple())
    except Exception:
        return False
