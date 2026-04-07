"""Tests for agent.pipeline_models.collect_pipeline_models."""

from agent.pipeline_models import collect_pipeline_models


def test_collect_pipeline_models_order_and_dedupe():
    cfg = {
        "model": {"default": "anthropic/claude-sonnet-4"},
        "free_model_routing": {
            "enabled": True,
            "filter_free_tier_models_by_local_hub": False,
            "kimi_router": {
                "router_model": "gemma-4-31b-it",
                "router_provider": "gemini",
                "tiers": [
                    {
                        "id": "general",
                        "description": "General",
                        "models": ["Qwen/QwQ-32B", "org/other"],
                    },
                ],
            },
            "optional_gemini": {
                "enabled": True,
                "model": "gemma-4-31b-it",
            },
        },
    }
    rows = collect_pipeline_models(cfg)
    models = [r["model"] for r in rows]
    # Primary first; router (gemma-4 = gemini); Qwen + tier other; optional_gemini dedupes gemma-4
    assert models[0] == "anthropic/claude-sonnet-4"
    assert models.count("Qwen/QwQ-32B") == 1
    assert "gemma-4-31b-it" in models
    assert "org/other" in models
    g4 = [r for r in rows if r["model"] == "gemma-4-31b-it"]
    assert g4 and all(r["provider_kind"] == "gemini" for r in g4)


def test_collect_pipeline_models_disabled():
    cfg = {
        "model": {"default": "x"},
        "free_model_routing": {"enabled": False},
    }
    rows = collect_pipeline_models(cfg)
    assert len(rows) == 1
    assert rows[0]["model"] == "x"


def test_collect_pipeline_models_routing_tiers():
    cfg = {
        "model": {"default": "anthropic/claude-sonnet-4"},
        "free_model_routing": {
            "enabled": True,
            "filter_free_tier_models_by_local_hub": False,
            "kimi_router": {
                "router_model": "gemma-4-31b-it",
                "router_provider": "gemini",
                "tiers": [{"id": "g", "models": ["only-tier-model"]}],
            },
        },
    }
    rows = collect_pipeline_models(cfg)
    models = [r["model"] for r in rows]
    assert "only-tier-model" in models
