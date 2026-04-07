"""PROJECT_ROOT / sys.path must prefer HERMES_AGENT_REPO over site-packages layout."""

from __future__ import annotations

from pathlib import Path


def test_resolve_hermes_project_root_env_overrides(monkeypatch, tmp_path):
    monkeypatch.delenv("HERMES_AGENT_REPO", raising=False)
    fake = tmp_path / "fake-checkout"
    fake.mkdir()
    (fake / "pyproject.toml").write_text('[project]\nname = "hermes-agent"\n', encoding="utf-8")
    (fake / "agent").mkdir()
    (fake / "agent" / "pipeline_models.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_AGENT_REPO", str(fake))

    import importlib

    import hermes_cli.main as main_mod

    importlib.reload(main_mod)
    assert main_mod.PROJECT_ROOT.resolve() == fake.resolve()


def test_cli_inserts_agent_repo_on_path(monkeypatch, tmp_path):
    """cli.py prepends HERMES_AGENT_REPO when it contains agent/."""
    fake = tmp_path / "checkout"
    fake.mkdir()
    (fake / "agent").mkdir()
    (fake / "agent" / "pipeline_models.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_AGENT_REPO", str(fake))

    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[2]
    cli_path = root / "cli.py"
    spec = importlib.util.spec_from_file_location("_cli_path_test", cli_path)
    assert spec and spec.loader
    # Load fresh module name to re-run top-level path logic
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_cli_path_probe"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop("_cli_path_probe", None)
    assert str(fake.resolve()) in sys.path
