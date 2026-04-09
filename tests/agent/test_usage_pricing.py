from decimal import Decimal
from types import SimpleNamespace

import pytest

from agent.usage_pricing import (
    CanonicalUsage,
    estimate_usage_cost,
    get_pricing_entry,
    normalize_usage,
)


def test_normalize_usage_anthropic_keeps_cache_buckets_separate():
    usage = SimpleNamespace(
        input_tokens=1000,
        output_tokens=500,
        cache_read_input_tokens=2000,
        cache_creation_input_tokens=400,
    )

    normalized = normalize_usage(usage, provider="anthropic", api_mode="anthropic_messages")

    assert normalized.input_tokens == 1000
    assert normalized.output_tokens == 500
    assert normalized.cache_read_tokens == 2000
    assert normalized.cache_write_tokens == 400
    assert normalized.prompt_tokens == 3400


def test_normalize_usage_openai_subtracts_cached_prompt_tokens():
    usage = SimpleNamespace(
        prompt_tokens=3000,
        completion_tokens=700,
        prompt_tokens_details=SimpleNamespace(cached_tokens=1800),
    )

    normalized = normalize_usage(usage, provider="openai", api_mode="chat_completions")

    assert normalized.input_tokens == 1200
    assert normalized.cache_read_tokens == 1800
    assert normalized.output_tokens == 700


def test_openrouter_models_api_pricing_is_converted_from_per_token_to_per_million(monkeypatch):
    monkeypatch.setattr(
        "agent.usage_pricing.fetch_model_metadata",
        lambda: {
            "anthropic/claude-opus-4.6": {
                "pricing": {
                    "prompt": "0.000005",
                    "completion": "0.000025",
                    "input_cache_read": "0.0000005",
                    "input_cache_write": "0.00000625",
                }
            }
        },
    )

    entry = get_pricing_entry(
        "anthropic/claude-opus-4.6",
        provider="openrouter",
        base_url="https://openrouter.ai/api/v1",
    )

    assert float(entry.input_cost_per_million) == 5.0
    assert float(entry.output_cost_per_million) == 25.0
    assert float(entry.cache_read_cost_per_million) == 0.5
    assert float(entry.cache_write_cost_per_million) == 6.25


def test_estimate_usage_cost_marks_subscription_routes_included():
    result = estimate_usage_cost(
        "gpt-5.3-codex",
        CanonicalUsage(input_tokens=1000, output_tokens=500),
        provider="openai-codex",
        base_url="https://chatgpt.com/backend-api/codex",
    )

    assert result.status == "included"
    assert float(result.amount_usd) == 0.0


def test_estimate_usage_cost_refuses_cache_pricing_without_official_cache_rate(monkeypatch):
    monkeypatch.setattr(
        "agent.usage_pricing.fetch_model_metadata",
        lambda: {
            "google/gemini-2.5-pro": {
                "pricing": {
                    "prompt": "0.00000125",
                    "completion": "0.00001",
                }
            }
        },
    )

    result = estimate_usage_cost(
        "google/gemini-2.5-pro",
        CanonicalUsage(input_tokens=1000, output_tokens=500, cache_read_tokens=100),
        provider="openrouter",
        base_url="https://openrouter.ai/api/v1",
    )

    assert result.status == "unknown"


def test_custom_endpoint_models_api_pricing_is_supported(monkeypatch):
    monkeypatch.setattr(
        "agent.usage_pricing.fetch_endpoint_model_metadata",
        lambda base_url, api_key=None: {
            "zai-org/GLM-5-TEE": {
                "pricing": {
                    "prompt": "0.0000005",
                    "completion": "0.000002",
                }
            }
        },
    )

    entry = get_pricing_entry(
        "zai-org/GLM-5-TEE",
        provider="custom",
        base_url="https://llm.chutes.ai/v1",
        api_key="test-key",
    )

    assert float(entry.input_cost_per_million) == 0.5
    assert float(entry.output_cost_per_million) == 2.0


def test_normalize_usage_openrouter_extracts_usage_cost():
    usage = SimpleNamespace(
        prompt_tokens=1000,
        completion_tokens=500,
        cost=0.0123,
    )
    normalized = normalize_usage(
        usage,
        provider="openrouter",
        api_mode="chat_completions",
        base_url="https://openrouter.ai/api/v1",
    )
    assert normalized.billed_usd == Decimal("0.0123")


def test_normalize_usage_openrouter_cost_detected_via_base_url():
    usage = SimpleNamespace(
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.01,
    )
    normalized = normalize_usage(
        usage,
        provider="custom",
        api_mode="chat_completions",
        base_url="https://openrouter.ai/api/v1",
    )
    assert normalized.billed_usd == Decimal("0.01")


def test_estimate_usage_cost_prefers_openrouter_billed_usd():
    result = estimate_usage_cost(
        "openai/gpt-4o",
        CanonicalUsage(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            billed_usd=Decimal("3.42"),
        ),
        provider="openrouter",
        base_url="https://openrouter.ai/api/v1",
    )
    assert result.status == "actual"
    assert result.source == "provider_cost_api"
    assert float(result.amount_usd) == pytest.approx(3.42)


def test_get_pricing_entry_gpt54_native_openai():
    entry = get_pricing_entry("gpt-5.4", provider="openai")
    assert entry is not None
    assert float(entry.input_cost_per_million) == 2.5
    assert float(entry.output_cost_per_million) == 15.0
    assert float(entry.cache_read_cost_per_million) == 0.25
