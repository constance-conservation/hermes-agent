"""Tests for hermes_cli.integration_repos (paperclip / autoresearch slash helpers)."""

from hermes_cli.integration_repos import (
    format_autoresearch_message,
    format_paperclip_message,
    resolve_autoresearch_repo,
    resolve_paperclip_repo,
)


def test_resolve_paperclip_repo_from_config(monkeypatch, tmp_path):
    monkeypatch.delenv("HERMES_PAPERCLIP_REPO", raising=False)
    cfg = {"integrations": {"paperclip": {"repo": str(tmp_path)}}}
    assert resolve_paperclip_repo(cfg) == str(tmp_path)


def test_resolve_paperclip_repo_env_overrides(monkeypatch, tmp_path):
    other = tmp_path / "other"
    monkeypatch.setenv("HERMES_PAPERCLIP_REPO", str(other))
    cfg = {"integrations": {"paperclip": {"repo": "/nope"}}}
    assert resolve_paperclip_repo(cfg) == str(other)


def test_format_paperclip_help_contains_upstream():
    text = format_paperclip_message("/paperclip help", {})
    assert "cc-org-au/paperclip" in text
    assert "npx paperclipai onboard" in format_paperclip_message("/paperclip onboard", {})


def test_format_autoresearch_prepare_has_uv():
    text = format_autoresearch_message("/autoresearch prepare", {})
    assert "uv run prepare.py" in text


def test_format_autoresearch_unknown_topic_falls_back():
    text = format_autoresearch_message("/autoresearch bogus", {})
    assert "Unknown topic" in text
    assert "cc-org-au/autoresearch" in text


def test_resolve_autoresearch_repo_empty():
    assert resolve_autoresearch_repo({}) == ""
