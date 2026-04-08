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
