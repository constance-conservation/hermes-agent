"""prune_slack_cron_for_non_leader.py — strip slack cron when demoting a profile."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "memory" / "core" / "scripts" / "core" / "prune_slack_cron_for_non_leader.py"


def _load_main():
    spec = importlib.util.spec_from_file_location("prune_slack_cron_for_non_leader", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.main


@pytest.fixture
def prune_main():
    return _load_main()


def test_refuses_when_leader_not_false_and_no_demote_flags(prune_main, monkeypatch, tmp_path) -> None:
    home = tmp_path / "chief"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    cfg = {"messaging": {"slack_role_cron_leader": True}}
    (home / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    jobs = [{"id": "1", "name": "daily-slack-role-status-x-C1", "deliver": "slack:C1"}]
    (home / "cron" / "jobs.json").write_text(json.dumps({"jobs": jobs}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["x"])
    assert prune_main() == 3


def test_apply_also_set_non_leader_strips_slack_jobs(prune_main, monkeypatch, tmp_path) -> None:
    home = tmp_path / "chief"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    cfg = {"messaging": {"slack_role_cron_leader": True}}
    (home / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    jobs = [
        {"id": "1", "name": "daily-slack-role-status-x-C1", "deliver": "slack:C1"},
        {"id": "2", "name": "local-task", "deliver": "local"},
    ]
    (home / "cron" / "jobs.json").write_text(json.dumps({"jobs": jobs}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["x", "--apply", "--also-set-non-leader"])
    assert prune_main() == 0
    doc = json.loads((home / "cron" / "jobs.json").read_text(encoding="utf-8"))
    out = doc.get("jobs", [])
    assert len(out) == 1 and out[0]["id"] == "2"
    cfg2 = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
    assert cfg2["messaging"]["slack_role_cron_leader"] is False
