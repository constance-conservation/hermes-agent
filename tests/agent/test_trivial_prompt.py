"""Tests for trivial / acknowledgement prompt detection (OPM cost routing)."""

from __future__ import annotations

from agent.trivial_prompt import trivial_message_skips_opm_tier_uplift


def test_trivial_one_word_ping():
    assert trivial_message_skips_opm_tier_uplift("ping") is True
    assert trivial_message_skips_opm_tier_uplift("PING") is True


def test_non_trivial_long_message():
    assert trivial_message_skips_opm_tier_uplift("please summarize this long document") is False


def test_non_trivial_multiline():
    assert trivial_message_skips_opm_tier_uplift("line1\nline2") is False


def test_empty_is_trivial():
    assert trivial_message_skips_opm_tier_uplift("") is True
    assert trivial_message_skips_opm_tier_uplift("   ") is True
