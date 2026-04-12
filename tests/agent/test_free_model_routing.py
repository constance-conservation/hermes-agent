"""Tests for config-driven free_model_routing (no hardcoded hub ids in code)."""

from agent.free_model_routing import (
    build_free_fallback_chain,
    normalize_kimi_tiers,
    resolve_fallback_providers,
)


def test_normalize_kimi_tiers_list_of_dicts():
    t = normalize_kimi_tiers(
        [
            {"id": "a", "description": "d0", "models": ["m1", "m2"]},
            {"models": ["m3"]},
        ]
    )
    assert len(t) == 2
    assert t[0]["models"] == ["m1", "m2"]
    assert t[1]["id"] == "tier-1"
    assert t[1]["models"] == ["m3"]


def test_resolve_fallback_providers_strips_disallowed_when_opm_enabled(monkeypatch):
    from agent.disallowed_model_family import disallowed_family_fixture_slug

    bad = disallowed_family_fixture_slug()
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {
            "openai_primary_mode": {"enabled": True},
            "free_model_routing": {
                "enabled": True,
                "filter_free_tier_models_by_local_hub": False,
                "kimi_router": {
                    "router_model": bad,
                    "tiers": [{"id": "t", "models": [bad]}],
                },
                "openrouter_last_resort": {"enabled": False},
            },
        },
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    monkeypatch.setattr(
        "agent.openai_native_runtime.native_openai_runtime_tuple",
        lambda: None,
    )
    from hermes_cli.config import load_config

    out = resolve_fallback_providers(load_config())
    assert out
    from agent.disallowed_model_family import model_id_contains_disallowed_family

    assert all(not model_id_contains_disallowed_family(str(e.get("model") or "")) for e in out)


def test_resolve_fallback_providers_empty_when_opm_suppresses_native(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {
            "openai_primary_mode": {"enabled": True},
            "free_model_routing": {"enabled": True},
        },
    )
    monkeypatch.setattr("agent.token_governance_runtime.load_runtime_config", lambda: {})
    monkeypatch.setattr(
        "agent.openai_native_runtime.native_openai_runtime_tuple",
        lambda: ("https://api.openai.com/v1", "k"),
    )
    from hermes_cli.config import load_config

    assert resolve_fallback_providers(load_config()) == []


def test_top_level_tiers_preferred_over_legacy_kimi_router():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "filter_free_tier_models_by_local_hub": False,
            "tiers": [{"id": "top", "models": ["org/top"]}],
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "legacy", "models": ["org/legacy"]}],
            },
        }
    }
    ch = build_free_fallback_chain(cfg)
    assert ch
    flat = [m for t in ch[0]["gemini_tier_router_tiers"] for m in t["models"]]
    assert "org/top" in flat
    assert "org/legacy" not in flat


def test_fallback_tier_when_all_hub_models_filtered(monkeypatch):
    monkeypatch.setattr(
        "agent.free_model_routing.filter_hub_model_ids_by_local_state",
        lambda ids, enabled=True: [],
    )
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "filter_free_tier_models_by_local_hub": True,
            "fallback_free_routed_model": "gemini-2.5-flash",
            "gemini_native_tier_models": ["gemini-2.5-flash"],
            "kimi_router": {
                "router_provider": "gemini",
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "local", "models": ["org/local-32b"]}],
            },
        }
    }
    ch = build_free_fallback_chain(cfg)
    assert ch
    assert ch[0].get("gemini_tier_router") is True
    flat = [m for t in ch[0]["gemini_tier_router_tiers"] for m in t["models"]]
    assert "gemini-2.5-flash" in flat


def test_build_chain_kimi_then_optional_gemini():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "t", "models": ["org/a", "org/b"]}],
            },
            "optional_gemini": {
                "enabled": True,
                "model": "gemini-test",
                "only_rate_limit": True,
                "restore_health_check": True,
            },
            "openrouter_last_resort": {"enabled": False},
        }
    }
    ch = build_free_fallback_chain(cfg)
    assert len(ch) == 2
    assert ch[0]["gemini_tier_router"] is True
    assert ch[0]["provider"] == "gemini"
    assert ch[0]["model"] == "gemini-2.5-flash"
    assert len(ch[0]["gemini_tier_router_tiers"]) == 1
    assert "gemini-2.5-flash" in (ch[0].get("gemini_native_tier_models") or [])
    assert ch[1]["provider"] == "gemini"


def test_filtered_tiers_preserve_gemini_native_models(monkeypatch):
    monkeypatch.setattr(
        "agent.free_model_routing.filter_hub_model_ids_by_local_state",
        lambda ids, enabled=True: [x for x in ids if "org/local" not in x],
    )
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "filter_free_tier_models_by_local_hub": True,
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "local", "models": ["gemini-2.5-flash", "org/local-32b"]}],
            },
        }
    }
    ch = build_free_fallback_chain(cfg)
    assert ch
    flat = [m for t in ch[0]["gemini_tier_router_tiers"] for m in t["models"]]
    assert "gemini-2.5-flash" in flat
    assert "org/local-32b" not in flat


def test_build_chain_router_provider_gemini():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "kimi_router": {
                "router_provider": "gemini",
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "t", "models": ["org/a", "org/b"]}],
            },
            "openrouter_last_resort": {"enabled": False},
        },
    }
    ch = build_free_fallback_chain(cfg)
    assert len(ch) == 1
    assert ch[0]["provider"] == "gemini"
    assert ch[0]["model"] == "gemini-2.5-flash"


def test_resolve_explicit_fallback_providers_wins():
    cfg = {
        "fallback_providers": [{"provider": "openai", "model": "gpt-4o"}],
        "free_model_routing": {"enabled": True, "kimi_router": {"router_model": "x", "tiers": [{"models": ["a"]}]}},
    }
    assert resolve_fallback_providers(cfg) == [{"provider": "openai", "model": "gpt-4o"}]


def test_resolve_explicit_plain_hf_dropped_for_gemini_synthesis():
    """Plain huggingface hub rows (no gemini_tier_router) are dropped — use Gemini synthesis."""
    cfg = {
        "fallback_providers": [
            {"provider": "huggingface", "model": "MiniMaxAI/MiniMax-M2.5"},
        ],
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "g", "models": ["some/hub-a"]}],
            },
            "openrouter_last_resort": {"enabled": False},
        },
    }
    out = resolve_fallback_providers(cfg)
    assert len(out) == 1
    assert out[0].get("gemini_tier_router") is True
    assert out[0]["provider"] == "gemini"
    assert out[0]["model"] == "gemini-2.5-flash"


def test_resolve_legacy_fallback_model_plain_hf_yields_to_gemini():
    cfg = {
        "fallback_model": {
            "provider": "huggingface",
            "model": "MiniMaxAI/MiniMax-M2.5",
        },
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "g", "models": ["some/hub-a"]}],
            },
        },
    }
    out = resolve_fallback_providers(cfg)
    assert out[0].get("gemini_tier_router") is True


def test_resolve_explicit_empty_list():
    cfg = {"fallback_providers": [], "free_model_routing": {"enabled": True}}
    assert resolve_fallback_providers(cfg) == []


def test_build_chain_gemini_direct():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "t", "models": ["org/a", "org/b"]}],
            },
            "openrouter_last_resort": {"enabled": False},
        },
    }
    ch = build_free_fallback_chain(cfg)
    assert len(ch) == 1
    assert ch[0]["gemini_tier_router"] is True
    assert ch[0]["provider"] == "gemini"
    assert ch[0]["model"] == "gemini-2.5-flash"


def test_openrouter_last_resort_appended_by_default():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "t", "models": ["org/a"]}],
            },
        },
    }
    ch = build_free_fallback_chain(cfg)
    assert len(ch) == 2
    assert ch[0]["provider"] == "gemini"
    assert ch[1]["provider"] == "openrouter"
    assert ch[1]["openrouter_last_resort"] is True
    assert ch[1]["only_rate_limit"] is True
    assert "nano" in ch[1]["model"].lower()


def test_openrouter_last_resort_disabled():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "budget_openrouter_fallback": {"enabled": False},
            "kimi_router": {
                "router_model": "gemini-2.5-flash",
                "tiers": [{"id": "t", "models": ["org/a"]}],
            },
            "openrouter_last_resort": {"enabled": False},
        },
    }
    ch = build_free_fallback_chain(cfg)
    assert len(ch) == 1
    assert ch[0]["provider"] == "gemini"


def test_resolve_legacy_fallback_model_dict():
    cfg = {
        "fallback_model": {"provider": "zai", "model": "glm-9"},
    }
    assert resolve_fallback_providers(cfg) == [{"provider": "zai", "model": "glm-9"}]


# ── classify_model_cost provider-awareness ────────────────────────────


def test_classify_local_slug_is_free():
    from agent.subprocess_governance import classify_model_cost

    assert classify_model_cost("local/my-model") == "free"


def test_classify_gemini_direct_is_low_cost():
    from agent.subprocess_governance import classify_model_cost

    assert classify_model_cost("gemini-2.5-flash", provider="gemini") == "low_cost"


def test_classify_openrouter_gemini_is_paid():
    from agent.subprocess_governance import classify_model_cost

    assert classify_model_cost(
        "google/gemini-2.5-flash", provider="openrouter"
    ) == "paid"
    assert classify_model_cost(
        "gemini-2.5-flash", base_url="https://openrouter.ai/api/v1"
    ) == "paid"


def test_classify_openrouter_paid_model():
    from agent.subprocess_governance import classify_model_cost

    assert classify_model_cost(
        "anthropic/claude-sonnet-4.6", provider="openrouter"
    ) == "paid"
    assert classify_model_cost(
        "openai/gpt-5.4", base_url="https://openrouter.ai/api/v1"
    ) == "paid"
