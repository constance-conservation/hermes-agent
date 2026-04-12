"""Tests for chief → child profile .env overlay during delegation."""

from __future__ import annotations

import os


def test_overlay_fills_missing_key_from_parent_env(tmp_path, monkeypatch):
    from agent import delegation_env_overlay as mod

    chief = tmp_path / "chief"
    chief.mkdir()
    (chief / ".env").write_text("OPENROUTER_API_KEY=chief-or-secret\n", encoding="utf-8")

    monkeypatch.setattr(
        mod,
        "_overlay_keys_from_config",
        lambda: ["OPENROUTER_API_KEY"],
    )
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    mod.apply_parent_env_overlay_for_delegate(str(chief))
    assert os.environ.get("OPENROUTER_API_KEY") == "chief-or-secret"


def test_overlay_skips_when_child_already_has_key(tmp_path, monkeypatch):
    from agent import delegation_env_overlay as mod

    chief = tmp_path / "chief"
    chief.mkdir()
    (chief / ".env").write_text("OPENROUTER_API_KEY=chief-only\n", encoding="utf-8")

    monkeypatch.setattr(
        mod,
        "_overlay_keys_from_config",
        lambda: ["OPENROUTER_API_KEY"],
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "child-wins")

    mod.apply_parent_env_overlay_for_delegate(str(chief))
    assert os.environ.get("OPENROUTER_API_KEY") == "child-wins"
