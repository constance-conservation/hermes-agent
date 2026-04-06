"""Tests for Hugging Face inference policy suffix on fallback chain entries."""

from agent.hf_fallback_router import apply_hf_inference_policy


def test_apply_policy_appends_fastest():
    assert apply_hf_inference_policy("openai/gpt-oss-120b", "fastest") == "openai/gpt-oss-120b:fastest"


def test_apply_policy_respects_existing_suffix():
    assert apply_hf_inference_policy("moonshotai/Kimi-K2-Thinking:novita", "fastest") == (
        "moonshotai/Kimi-K2-Thinking:novita"
    )


def test_empty_policy_noop():
    assert apply_hf_inference_policy("google/gemma-4-31B-it", None) == "google/gemma-4-31B-it"
    assert apply_hf_inference_policy("google/gemma-4-31B-it", "") == "google/gemma-4-31B-it"
