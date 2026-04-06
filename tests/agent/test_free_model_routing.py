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


def test_build_chain_inference_then_kimi_then_optional_gemini():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "inference": {"model": "org/inf", "policy": "cheapest"},
            "kimi_router": {
                "router_model": "org/router",
                "tiers": [{"id": "t", "models": ["org/a", "org/b"]}],
            },
            "optional_gemini": {
                "enabled": True,
                "model": "gemma-test",
                "only_rate_limit": True,
                "restore_health_check": True,
            },
        }
    }
    ch = build_free_fallback_chain(cfg)
    assert len(ch) == 3
    assert ch[0] == {
        "provider": "huggingface",
        "model": "org/inf",
        "hf_inference_policy": "cheapest",
    }
    assert ch[1]["hf_router"] is True
    assert ch[1]["model"] == "org/router"
    assert len(ch[1]["hf_router_tiers"]) == 1
    assert ch[2]["provider"] == "gemini"


def test_resolve_explicit_fallback_providers_wins():
    cfg = {
        "fallback_providers": [{"provider": "openai", "model": "gpt-4o"}],
        "free_model_routing": {"enabled": True, "inference": {"model": "x/x"}},
    }
    assert resolve_fallback_providers(cfg) == [{"provider": "openai", "model": "gpt-4o"}]


def test_resolve_explicit_empty_list():
    cfg = {"fallback_providers": [], "free_model_routing": {"enabled": True, "inference": {"model": "x/x"}}}
    assert resolve_fallback_providers(cfg) == []


def test_build_chain_kimi_only_when_inference_disabled():
    cfg = {
        "free_model_routing": {
            "enabled": True,
            "inference": {"enabled": False},
            "kimi_router": {
                "router_model": "org/router",
                "tiers": [{"id": "t", "models": ["org/a", "org/b"]}],
            },
        },
    }
    ch = build_free_fallback_chain(cfg)
    assert len(ch) == 1
    assert ch[0]["hf_router"] is True
    assert ch[0]["model"] == "org/router"


def test_resolve_legacy_fallback_model_dict():
    cfg = {
        "fallback_model": {"provider": "zai", "model": "glm-9"},
    }
    assert resolve_fallback_providers(cfg) == [{"provider": "zai", "model": "glm-9"}]
