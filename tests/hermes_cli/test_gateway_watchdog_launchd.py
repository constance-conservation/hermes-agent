"""Tests for macOS watchdog LaunchAgent helpers (hermes_cli.gateway)."""

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.parametrize(
    "rel_under_hermes,expected_label",
    [
        (None, "ai.hermes.gateway-watchdog"),
        ("coder", "ai.hermes.gateway-watchdog-coder"),
    ],
)
def test_watchdog_launchd_label_matches_gateway_scoping(
    tmp_path, monkeypatch, rel_under_hermes, expected_label
):
    from hermes_cli import gateway as gw

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    base = tmp_path / ".hermes"
    if rel_under_hermes:
        home = base / "profiles" / rel_under_hermes
    else:
        home = base
    home.mkdir(parents=True)
    with patch.object(gw, "get_hermes_home", return_value=home):
        assert gw.get_watchdog_launchd_label() == expected_label


def test_generate_watchdog_launchd_plist_contains_bash_and_script(tmp_path, monkeypatch):
    from hermes_cli import gateway as gw

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    prof = tmp_path / ".hermes" / "profiles" / "chief-orchestrator"
    prof.mkdir(parents=True)
    with patch.object(gw, "get_hermes_home", return_value=prof):
        plist = gw.generate_watchdog_launchd_plist()
        label = gw.get_watchdog_launchd_label()
    assert "/bin/bash" in plist
    assert str(prof / "bin" / "gateway-watchdog.sh") in plist
    assert "HERMES_HOME" in plist
    assert label in plist
    assert label == "ai.hermes.gateway-watchdog-chief-orchestrator"
