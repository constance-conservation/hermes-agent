"""Unit tests for cron.state_gate fingerprinting."""

from __future__ import annotations

import json

import pytest

from cron.state_gate import fingerprint_for_state_skip_gate, should_skip_llm_for_unchanged_state


def test_fingerprint_stable_key_order(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(
        json.dumps({"b": 2, "a": 1, "last_status_key": "up"}),
        encoding="utf-8",
    )
    job = {
        "id": "j1",
        "state_skip_gate": {"path": str(p), "keys": ["last_status_key", "b"]},
    }
    fp1 = fingerprint_for_state_skip_gate(job)
    fp2 = fingerprint_for_state_skip_gate(job)
    assert fp1 == fp2
    assert len(fp1) == 64


def test_missing_file_sentinel(tmp_path):
    missing = tmp_path / "nope.json"
    job = {"id": "j2", "state_skip_gate": {"path": str(missing), "keys": ["x"]}}
    fp = fingerprint_for_state_skip_gate(job)
    assert fp is not None


def test_skip_when_matches_last(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"last_status_key": "steady", "connected_platforms": ["wa"]}), encoding="utf-8")
    job = {
        "id": "j3",
        "state_skip_gate": {"path": str(p), "keys": ["last_status_key", "connected_platforms"]},
    }
    cur = fingerprint_for_state_skip_gate(job)
    assert cur is not None
    job["last_state_gate_fingerprint"] = cur
    skip, _ = should_skip_llm_for_unchanged_state(job)
    assert skip is True


def test_no_skip_when_last_absent(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"last_status_key": "a"}), encoding="utf-8")
    job = {
        "id": "j4",
        "state_skip_gate": {"path": str(p), "keys": ["last_status_key"]},
    }
    skip, cur = should_skip_llm_for_unchanged_state(job)
    assert skip is False
    assert cur is not None


def test_no_skip_when_state_changed(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"last_status_key": "v1"}), encoding="utf-8")
    job = {
        "id": "j5",
        "state_skip_gate": {"path": str(p), "keys": ["last_status_key"]},
    }
    job["last_state_gate_fingerprint"] = fingerprint_for_state_skip_gate(job)
    p.write_text(json.dumps({"last_status_key": "v2"}), encoding="utf-8")
    skip, _ = should_skip_llm_for_unchanged_state(job)
    assert skip is False


def test_disabled_gate(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"last_status_key": "x"}), encoding="utf-8")
    job = {
        "id": "j6",
        "state_skip_gate": {"enabled": False, "path": str(p), "keys": ["last_status_key"]},
        "last_state_gate_fingerprint": "deadbeef",
    }
    assert fingerprint_for_state_skip_gate(job) is None
    skip, _ = should_skip_llm_for_unchanged_state(job)
    assert skip is False


def test_invalid_json_returns_none(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    job = {"id": "j7", "state_skip_gate": {"path": str(p), "keys": ["k"]}}
    assert fingerprint_for_state_skip_gate(job) is None
