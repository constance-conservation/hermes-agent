"""Tests for hermes_constants path safety (HERMES_HOME / delegate launch home)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_get_hermes_home_ignores_magicmock_poisoned_env(monkeypatch, tmp_path):
    import hermes_constants as hc

    good = tmp_path / "good-hermes"
    good.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(good))
    assert hc.get_hermes_home().resolve() == good.resolve()

    poison = "<MagicMock name='mock._delegate_launch_hermes_home' id='999'>"
    monkeypatch.setenv("HERMES_HOME", poison)
    assert poison not in str(hc.get_hermes_home())
    assert hc.get_hermes_home() == Path.home() / ".hermes"


def test_safe_hermes_home_directory_rejects_mock_and_non_dirs(tmp_path):
    from hermes_constants import safe_hermes_home_directory

    assert safe_hermes_home_directory(None) is None
    assert safe_hermes_home_directory(MagicMock()) is None
    assert safe_hermes_home_directory(12345) is None

    d = tmp_path / "h"
    d.mkdir()
    assert safe_hermes_home_directory(str(d)) == str(d.resolve())

    assert safe_hermes_home_directory(str(tmp_path / "nope")) is None


def test_get_hermes_home_context_override_takes_precedence(monkeypatch, tmp_path):
    import hermes_constants as hc

    env_home = tmp_path / "from-env"
    env_home.mkdir()
    override_home = tmp_path / "override"
    override_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(env_home))

    tok = hc.set_hermes_home_override(override_home)
    try:
        assert hc.get_hermes_home().resolve() == override_home.resolve()
    finally:
        hc.reset_hermes_home_override(tok)

    assert hc.get_hermes_home().resolve() == env_home.resolve()


def test_hermes_home_override_context_manager(tmp_path, monkeypatch):
    import hermes_constants as hc

    base = tmp_path / "base"
    base.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(base))

    with hc.hermes_home_override(other):
        assert hc.get_hermes_home().resolve() == other.resolve()
    assert hc.get_hermes_home().resolve() == base.resolve()
