"""Tests for the gateway /autoresearch command flow."""

import asyncio
from unittest.mock import MagicMock

from gateway.config import Platform
from gateway.platforms.base import MessageEvent
from gateway.session import SessionSource


def _make_event(
    text="/autoresearch",
    platform=Platform.TELEGRAM,
    user_id="12345",
    chat_id="67890",
):
    source = SessionSource(
        platform=platform,
        user_id=user_id,
        chat_id=chat_id,
        user_name="testuser",
    )
    return MessageEvent(text=text, source=source)


def _make_runner():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner._pending_autoresearch = {}
    runner._background_tasks = set()
    runner.session_store = MagicMock()
    runner._session_key_for_source = lambda _source: "sess_autoresearch"
    return runner


class TestGatewayAutoresearchCommand:
    def test_no_args_returns_step1_prompt(self):
        runner = _make_runner()
        event = _make_event(text="/autoresearch")

        result = asyncio.run(runner._handle_autoresearch_command(event))

        assert "step 1 of 2" in result.lower()
        assert "very next message" in result
        assert runner._pending_autoresearch["sess_autoresearch"]["phase"] == "await_instructions"

    def test_show_returns_paths(self):
        runner = _make_runner()
        event = _make_event(text="/autoresearch show")

        result = asyncio.run(runner._handle_autoresearch_command(event))

        assert "Autoresearch repo:" in result
        assert "Program file:" in result
        assert "two-step" in result.lower()

    def test_inline_instructions_sets_await_duration(self):
        runner = _make_runner()
        event = _make_event(text="/autoresearch improve safety")

        result = asyncio.run(runner._handle_autoresearch_command(event))

        assert "step 2 of 2" in result.lower()
        pend = runner._pending_autoresearch["sess_autoresearch"]
        assert pend["phase"] == "await_duration"
        assert pend["instructions"] == "improve safety"
