from unittest.mock import MagicMock

from agent.disallowed_model_family import (
    disallowed_family_fixture_slug,
    disallowed_family_openrouter_hub_slug,
    model_id_contains_disallowed_family,
)
from agent.openai_primary_mode import (
    _opm_merge_parent_anchor,
    attach_opm_session_agent_for_turn,
    coerce_opm_disallowed_routing_slugs,
    coerce_under_opm_if_disallowed_family,
    detach_opm_session_agent_for_turn,
    filter_fallback_chain_disallowed,
    is_opm_blocked_openrouter_auto_slug,
    manual_pipeline_opm_bypass_enabled,
    opm_coercion_effective,
    opm_effective_for_tier_routing_uplift,
    opm_enabled,
    opm_manual_override_active,
    opm_suppresses_free_model_fallback,
    resolve_openai_primary_mode,
)


def test_opm_merge_parent_anchor_magicmock_unset_is_none():
    """MagicMock.__getattr__ must not fabricate a delegation anchor."""
    assert _opm_merge_parent_anchor(MagicMock()) is None


def test_opm_merge_parent_anchor_explicit_on_mock():
    chief = object()
    m = MagicMock()
    m._opm_merge_parent = chief
    assert _opm_merge_parent_anchor(m) is chief


def test_opm_suppresses_free_model_fallback_true_when_enabled_and_native(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    monkeypatch.setattr(
        "agent.openai_native_runtime.native_openai_runtime_tuple",
        lambda: ("https://api.openai.com/v1", "k"),
    )
    assert opm_suppresses_free_model_fallback() is True


def test_opm_suppresses_free_model_fallback_false_without_native(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    monkeypatch.setattr(
        "agent.openai_native_runtime.native_openai_runtime_tuple",
        lambda: None,
    )
    assert opm_suppresses_free_model_fallback() is False


def test_opm_suppresses_merges_parent_governance_cache(monkeypatch):
    """``opm_suppresses_free_model_fallback(agent)`` must see parent's runtime OPM flags."""
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": False}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    monkeypatch.setattr(
        "agent.openai_native_runtime.native_openai_runtime_tuple",
        lambda: ("https://api.openai.com/v1", "k"),
    )

    class _P:
        _token_governance_cfg = {"openai_primary_mode": {"enabled": True}}

    assert opm_suppresses_free_model_fallback(_P()) is True


def test_opm_precedence_parent_over_runtime_over_config(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {
            "openai_primary_mode": {
                "enabled": False,
                "default_model": "cfg-default",
                "codex_model": "cfg-codex",
            }
        },
    )
    monkeypatch.setattr(
        "agent.token_governance_runtime.load_runtime_config",
        lambda: {
            "openai_primary_mode": {
                "enabled": True,
                "default_model": "rt-default",
            }
        },
    )
    monkeypatch.setattr(
        "agent.openai_native_runtime.native_openai_runtime_tuple",
        lambda: ("https://api.openai.com/v1", "key"),
    )

    class _Parent:
        _token_governance_cfg = {
            "openai_primary_mode": {
                "enabled": True,
                "default_model": "parent-default",
            }
        }

    opm, meta = resolve_openai_primary_mode(_Parent())
    assert opm["enabled"] is True
    assert opm["default_model"] == "parent-default"
    assert opm["codex_model"] == "cfg-codex"
    assert meta["source"] == "parent_cached"


def test_model_id_contains_disallowed_family():
    fx = disallowed_family_fixture_slug()
    hub = disallowed_family_openrouter_hub_slug()
    assert model_id_contains_disallowed_family(fx)
    assert model_id_contains_disallowed_family(hub)
    assert not model_id_contains_disallowed_family("google/gemini-2.5-flash")
    assert not model_id_contains_disallowed_family("")


def test_coerce_under_opm_when_disallowed_and_enabled(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True, "default_model": "gpt-5.4"}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    bad = disallowed_family_fixture_slug()
    assert coerce_under_opm_if_disallowed_family(bad, None) == "gpt-5.4"
    assert coerce_under_opm_if_disallowed_family("gpt-5.4", None) == "gpt-5.4"


def test_coerce_passthrough_when_opm_disabled(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": False}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    bad = disallowed_family_fixture_slug()
    assert coerce_under_opm_if_disallowed_family(bad, None) == bad


def test_opm_enabled_follows_enabled_flag(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    assert opm_enabled() is True

    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": False}},
    )
    assert opm_enabled() is False


def test_opm_enabled_truthy_string_enabled(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": "true"}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    assert opm_enabled() is True


def test_is_opm_blocked_openrouter_auto_slug():
    assert is_opm_blocked_openrouter_auto_slug("openrouter/auto")
    assert is_opm_blocked_openrouter_auto_slug("openrouter-auto")
    assert is_opm_blocked_openrouter_auto_slug("OpenRouter_Auto")
    assert not is_opm_blocked_openrouter_auto_slug("openai/gpt-5.4")


def test_coerce_opm_disallowed_openrouter_auto(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True, "default_model": "gpt-5.4"}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    assert coerce_opm_disallowed_routing_slugs("openrouter/auto", None) == "gpt-5.4"


def test_coerce_opm_passthrough_auto_when_opm_off(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": False}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    assert coerce_opm_disallowed_routing_slugs("openrouter/auto", None) == "openrouter/auto"


def test_opm_coercion_effective_false_when_manual_bypass_default(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {
            "openai_primary_mode": {
                "enabled": True,
                "manual_pipeline_forces_opm_bypass": True,
            }
        },
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})

    class _Manual:
        _defer_opm_primary_coercion = True

    assert manual_pipeline_opm_bypass_enabled() is True
    assert opm_coercion_effective(_Manual()) is False
    assert opm_coercion_effective(None) is True


def test_opm_coercion_effective_false_when_turn_suppressed(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})

    class _Sup:
        _defer_opm_primary_coercion = False
        _opm_suppressed_for_turn = True

    assert opm_coercion_effective(_Sup()) is False


def test_opm_tier_uplift_false_when_turn_suppressed(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})

    class _Sup:
        _defer_opm_primary_coercion = False
        _opm_suppressed_for_turn = True

    assert opm_effective_for_tier_routing_uplift(_Sup()) is False


def test_opm_coercion_effective_false_when_bypass_disabled_but_manual_defer(monkeypatch):
    """Manual /models defer must disable OPM coercion even if YAML disables 'bypass' flag."""
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {
            "openai_primary_mode": {
                "enabled": True,
                "manual_pipeline_forces_opm_bypass": False,
            }
        },
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})

    class _Manual:
        _defer_opm_primary_coercion = True

    assert manual_pipeline_opm_bypass_enabled() is False
    assert opm_coercion_effective(_Manual()) is False


def test_manual_pipeline_bypass_env_forces_off(monkeypatch):
    monkeypatch.setenv("HERMES_MANUAL_PIPELINE_BYPASS_OPM", "0")
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True, "manual_pipeline_forces_opm_bypass": True}},
    )
    assert manual_pipeline_opm_bypass_enabled() is False


def test_coerce_opm_skips_when_manual_override_on_agent(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True, "default_model": "gpt-5.4"}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})

    class _Manual:
        _defer_opm_primary_coercion = True

    assert opm_manual_override_active(_Manual()) is True
    assert coerce_opm_disallowed_routing_slugs("openrouter/auto", _Manual()) == "openrouter/auto"


def test_coerce_opm_skips_when_session_thread_bound(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"openai_primary_mode": {"enabled": True, "default_model": "gpt-5.4"}},
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})

    class _Manual:
        _defer_opm_primary_coercion = True

    attach_opm_session_agent_for_turn(_Manual())
    try:
        assert opm_manual_override_active(None) is True
        assert coerce_opm_disallowed_routing_slugs("openrouter/auto", None) == "openrouter/auto"
    finally:
        detach_opm_session_agent_for_turn()


def test_filter_fallback_chain_disallowed():
    bad = disallowed_family_fixture_slug()
    chain = [
        {"provider": "gemini", "model": bad},
        {"provider": "gemini", "model": "google/gemini-2.5-flash"},
    ]
    out = filter_fallback_chain_disallowed(chain)
    assert len(out) == 1
    assert "gemini-2.5" in out[0]["model"]


def test_filter_fallback_chain_drops_tier_router_if_any_candidate_disallowed():
    bad = disallowed_family_fixture_slug()
    chain = [
        {
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "gemini_tier_router": True,
            "gemini_tier_router_tiers": [
                {"models": ["gemini-2.5-flash", bad]},
            ],
        },
    ]
    assert filter_fallback_chain_disallowed(chain) == []


def test_opm_runtime_overrides_config_field_by_field(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {
            "openai_primary_mode": {
                "enabled": True,
                "default_model": "cfg-default",
                "codex_model": "cfg-codex",
                "require_direct_openai": True,
            }
        },
    )
    monkeypatch.setattr(
        "agent.token_governance_runtime.load_runtime_config",
        lambda: {
            "openai_primary_mode": {
                "enabled": False,
                "default_model": "rt-default",
            }
        },
    )
    monkeypatch.setattr(
        "agent.openai_native_runtime.native_openai_runtime_tuple",
        lambda: None,
    )
    opm, meta = resolve_openai_primary_mode(None)
    assert opm["enabled"] is False
    assert opm["default_model"] == "rt-default"
    assert opm["codex_model"] == "cfg-codex"
    assert opm["require_direct_openai"] is True
    assert meta["source"] == "runtime_yaml"
    assert meta["has_native_openai_runtime"] is False
