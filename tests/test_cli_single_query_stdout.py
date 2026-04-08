"""Single-query CLI: piped stdout should not run the interactive banner path."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest


def test_single_query_non_tty_skips_banner_and_forces_quiet_path(monkeypatch, tmp_path):
    import cli as cli_mod

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    mock_cli = MagicMock()
    mock_cli._ensure_runtime_credentials.return_value = False
    monkeypatch.setattr(cli_mod, "HermesCLI", lambda **kwargs: mock_cli)

    with pytest.raises(SystemExit) as excinfo:
        cli_mod.main(query="hello", quiet=False)

    assert excinfo.value.code == 1
    mock_cli.show_banner.assert_not_called()
    assert mock_cli.tool_progress_mode == "off"


def test_single_query_tty_still_shows_banner_when_not_quiet(monkeypatch, tmp_path):
    import cli as cli_mod

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    mock_cli = MagicMock()
    mock_cli.chat = MagicMock()
    mock_cli._print_exit_summary = MagicMock()
    monkeypatch.setattr(cli_mod, "HermesCLI", lambda **kwargs: mock_cli)

    cli_mod.main(query="hello", quiet=False)

    mock_cli.show_banner.assert_called()
    mock_cli.chat.assert_called_once_with("hello")
