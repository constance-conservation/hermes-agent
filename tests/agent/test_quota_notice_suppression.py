"""Session-scoped suppression of user-visible quota/rate-limit notices."""

from __future__ import annotations

from pathlib import Path

import pytest

from run_agent import (
    AIAgent,
    _quota_ux_registry_key,
    persist_quota_suppress_to_registry,
    sync_quota_suppress_from_registry,
    _quota_ux_suppress_by_session,
    _quota_ux_suppress_lock,
)


@pytest.fixture
def agent():
    a = AIAgent(quiet_mode=True, skip_context_files=True, skip_memory=True)
    a.session_id = "test_sess_quota"
    return a


@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home


def test_quota_notice_resets_when_session_id_changes(agent):
    agent._quota_notice_session_id = "old"
    agent._session_suppress_quota_user_notices = True

    # Simulate run_conversation header logic
    agent.session_id = "new_sess"
    _q_sid = str(getattr(agent, "session_id", "") or "")
    _prev_q = getattr(agent, "_quota_notice_session_id", None)
    if _prev_q is not None and _prev_q != _q_sid:
        agent._session_suppress_quota_user_notices = False
    agent._quota_notice_session_id = _q_sid

    assert agent._session_suppress_quota_user_notices is False
    assert agent._quota_notice_session_id == "new_sess"


def test_emit_quota_user_notice_suppressed_after_flag(agent, caplog):
    import logging

    agent._session_suppress_quota_user_notices = True
    emitted = []

    def _cb(et, msg):
        emitted.append((et, msg))

    agent.status_callback = _cb
    with caplog.at_level(logging.INFO, logger="run_agent"):
        agent._emit_quota_user_notice("⚠️ Quota test", "lifecycle")
    assert emitted == []
    assert any("quota user notice suppressed" in r.getMessage() for r in caplog.records)


def test_session_note_quota_exhausted_sets_skip_native_only(agent):
    agent._opm_qf_phase = "or_explicit"
    agent._session_suppress_quota_user_notices = False
    agent._session_skip_opm_native_quota_ladder = False
    agent._session_note_quota_cascade_exhausted_if_applicable()
    assert agent._session_suppress_quota_user_notices is False
    assert agent._session_skip_opm_native_quota_ladder is True


def test_emit_status_suppresses_quota_class_when_session_muted(agent, caplog):
    import logging

    agent._session_suppress_quota_user_notices = True
    emitted = []

    def _cb(et, msg):
        emitted.append(msg)

    agent.status_callback = _cb
    with caplog.at_level(logging.INFO, logger="run_agent"):
        agent._emit_status(
            "⚠️ Provider custom blacklisted for this session — quota exceeded",
        )
    assert emitted == []
    assert any("quota-class status suppressed" in r.getMessage() for r in caplog.records)


def test_quota_suppress_registry_survives_new_agent_same_session(profile_env):
    """Gateway may recreate AIAgent when config signature changes; mute must persist."""
    with _quota_ux_suppress_lock:
        _quota_ux_suppress_by_session.clear()
    a1 = AIAgent(quiet_mode=True, skip_context_files=True, skip_memory=True)
    a1.session_id = "stable_gateway_sess"
    a1._turn_had_quota_ux_for_cli_latch = True
    persist_quota_suppress_to_registry(a1)
    a2 = AIAgent(quiet_mode=True, skip_context_files=True, skip_memory=True)
    a2.session_id = "stable_gateway_sess"
    assert a2._session_suppress_quota_user_notices is False
    sync_quota_suppress_from_registry(a2)
    assert a2._session_suppress_quota_user_notices is True


def test_reset_session_state_clears_quota_suppress_registry(profile_env):
    with _quota_ux_suppress_lock:
        _quota_ux_suppress_by_session.clear()
    a = AIAgent(quiet_mode=True, skip_context_files=True, skip_memory=True)
    a.session_id = "reset_sess"
    a._turn_had_quota_ux_for_cli_latch = True
    persist_quota_suppress_to_registry(a)
    key = _quota_ux_registry_key(a)
    assert _quota_ux_suppress_by_session.get(key) is True
    a.reset_session_state()
    assert _quota_ux_suppress_by_session.get(key) is None


def test_emit_quota_user_notice_suppresses_repeats_even_when_verbose(agent):
    """verbose_logging must not bypass CLI session repeat suppression."""
    agent.verbose_logging = True
    agent._session_suppress_quota_user_notices = False

    def _should_suppress():
        return True

    agent.quota_user_notice_should_suppress = _should_suppress
    emitted = []

    def _cb(_et, msg):
        emitted.append(msg)

    agent.status_callback = _cb
    agent._emit_quota_user_notice("⚠️ ladder step")
    assert emitted == []
