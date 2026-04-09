"""Tests for venv env mirroring when CLI runs as venv/bin/python."""

import os
import sys

import pytest


def test_ensure_venv_env_for_subprocesses_sets_virtual_env_and_path(
    monkeypatch, tmp_path
):
    from hermes_cli import main as main_mod

    venv = tmp_path / "venv"
    bindir = venv / "bin"
    bindir.mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text("home = /usr\n")
    fake_py = bindir / "python"
    fake_py.write_text("#!/bin/sh\n")
    monkeypatch.setattr(sys, "executable", str(fake_py.resolve()))
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    main_mod._ensure_venv_env_for_subprocesses()

    assert os.environ.get("VIRTUAL_ENV") == str(venv.resolve())
    assert os.environ["PATH"].startswith(str(bindir.resolve()) + os.pathsep)


def test_ensure_venv_skips_without_pyvenv_cfg(monkeypatch, tmp_path):
    from hermes_cli import main as main_mod

    bindir = tmp_path / "bin"
    bindir.mkdir(parents=True)
    fake_py = bindir / "python"
    fake_py.write_text("")
    monkeypatch.setattr(sys, "executable", str(fake_py.resolve()))
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    before = dict(os.environ)

    main_mod._ensure_venv_env_for_subprocesses()

    assert os.environ.get("VIRTUAL_ENV") == before.get("VIRTUAL_ENV")
