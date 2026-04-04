"""Tests for hermes_cli.slack_admin (no network)."""

from unittest.mock import MagicMock

import pytest


def test_tokens_from_env_missing_exits(monkeypatch):
    import hermes_cli.slack_admin as sa

    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        sa._tokens_from_env()


def test_tokens_from_env_comma_separated(monkeypatch):
    import hermes_cli.slack_admin as sa

    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-a, xoxb-b")
    assert sa._tokens_from_env() == ["xoxb-a", "xoxb-b"]


def test_slack_command_dispatches_join_public(monkeypatch):
    import hermes_cli.slack_admin as sa

    called = {}

    def fake_join(*, dry_run=False):
        called["dry_run"] = dry_run

    monkeypatch.setattr(sa, "slack_join_public_channels", fake_join)
    args = MagicMock(slack_command="join-public", dry_run=True)
    sa.slack_command(args)
    assert called["dry_run"] is True


def test_slack_command_dispatches_whoami(monkeypatch):
    import hermes_cli.slack_admin as sa

    called = {}

    def fake_whoami():
        called["ok"] = True

    monkeypatch.setattr(sa, "slack_whoami", fake_whoami)
    args = MagicMock(slack_command="whoami")
    sa.slack_command(args)
    assert called.get("ok") is True
