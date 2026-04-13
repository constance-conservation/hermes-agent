"""Slack delivery smoke tests for run_slack_cron_burst_now (--ping / --ping-job-prompt)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[2]
BURST = REPO / "memory" / "core" / "scripts" / "core" / "run_slack_cron_burst_now.py"


def _load_main():
    spec = importlib.util.spec_from_file_location("run_slack_cron_burst_now", BURST)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.main


@pytest.fixture
def burst_main():
    return _load_main()


def test_ping_delivers_once_per_slack_job(
    burst_main,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    home = tmp_path / ".hermes"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    jobs = [
        {"id": "a1", "name": "daily-a", "deliver": "slack:C111"},
        {"id": "b2", "name": "daily-b", "deliver": "slack:C222"},
    ]
    with patch("cron.jobs.load_jobs", return_value=jobs):
        with patch("cron.delivery.deliver_cron_result", return_value=True) as send:
            monkeypatch.setattr(sys, "argv", ["x", "--ping", "hello test"])
            assert burst_main() == 0
            assert send.call_count == 2
            send.assert_any_call(jobs[0], "hello test")
            send.assert_any_call(jobs[1], "hello test")


def test_ping_job_prompt_sends_stored_prompt(
    burst_main,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    home = tmp_path / ".hermes"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    jobs = [
        {
            "id": "a1",
            "name": "daily-slack-role-status-example-C111",
            "deliver": "slack:C111",
            "prompt": "Use Australia/Sydney. You are the **Slack-only daily status** for role `example`.",
        },
    ]
    with patch("cron.jobs.load_jobs", return_value=jobs):
        with patch("cron.delivery.deliver_cron_result", return_value=True) as send:
            monkeypatch.setattr(sys, "argv", ["x", "--ping-job-prompt"])
            assert burst_main() == 0
            send.assert_called_once()
            body = send.call_args[0][1]
            assert "daily-slack-role-status-example-C111" in body
            assert "Slack-only daily status" in body


def test_policy_checkin_sends_upward_summary_and_slug(
    burst_main,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    home = tmp_path / ".hermes"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    jobs = [
        {
            "id": "z9",
            "name": "daily-slack-role-status-org-mapper-hr-controller-C0ABC",
            "deliver": "slack:C0ABC",
            "prompt": "You are generating the **Slack-only daily status** for role `org-mapper-hr-controller`.",
        },
    ]
    with patch("cron.jobs.load_jobs", return_value=jobs):
        with patch("cron.delivery.deliver_cron_result", return_value=True) as send:
            monkeypatch.setattr(sys, "argv", ["x", "--policy-checkin"])
            assert burst_main() == 0
            send.assert_called_once()
            body = send.call_args[0][1]
            assert "UPWARD SUMMARY" in body or "upward" in body.lower()
            assert "org-mapper-hr-controller" in body
            assert "Slack-only daily status" in body


def test_default_burst_uses_execute_due_cron_not_tick(
    burst_main,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    home = tmp_path / ".hermes"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    jobs = [{"id": "a1", "name": "daily-a", "deliver": "slack:C111"}]
    with patch("cron.jobs.load_jobs", return_value=jobs):
        with patch("cron.jobs.trigger_job") as trig:
            with patch("cron.jobs.get_job", return_value=dict(jobs[0])):
                with patch("cron.scheduler.execute_due_cron_job", return_value=True) as ex:
                    with patch("cron.scheduler.tick") as tick:
                        monkeypatch.setattr(sys, "argv", ["x"])
                        assert burst_main() == 0
                        trig.assert_called_once_with("a1")
                        ex.assert_called_once()
                        tick.assert_not_called()


def test_tick_mode_calls_scheduler_tick(
    burst_main,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    home = tmp_path / ".hermes"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    jobs = [{"id": "a1", "name": "daily-a", "deliver": "slack:C111"}]
    with patch("cron.jobs.load_jobs", return_value=jobs):
        with patch("cron.jobs.trigger_job"):
            with patch("cron.scheduler.tick", return_value=1) as tick:
                monkeypatch.setattr(sys, "argv", ["x", "--tick"])
                assert burst_main() == 0
                tick.assert_called()
