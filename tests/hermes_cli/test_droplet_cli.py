"""Tests for ``hermes droplet`` (VPS hop) argv handling and profile name guardrails."""

import pytest


def test_strip_trailing_droplet_hop_argv():
    from hermes_cli.main import _strip_trailing_droplet_hop_argv

    assert _strip_trailing_droplet_hop_argv(["droplet"]) == []
    assert _strip_trailing_droplet_hop_argv(["chat", "droplet"]) == ["chat"]
    assert _strip_trailing_droplet_hop_argv(["-p", "droplet"]) is None
    assert _strip_trailing_droplet_hop_argv(["--profile", "droplet"]) is None
    assert _strip_trailing_droplet_hop_argv(["profile", "list"]) is None
    assert _strip_trailing_droplet_hop_argv([]) is None


def test_validate_profile_name_rejects_droplet():
    from hermes_cli.profiles import validate_profile_name

    with pytest.raises(ValueError, match="VPS hop"):
        validate_profile_name("droplet")


def test_resolve_profile_env_droplet_rejected_at_validate(tmp_path, monkeypatch):
    from hermes_cli.profiles import resolve_profile_env

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    with pytest.raises(ValueError, match="VPS hop"):
        resolve_profile_env("droplet")
