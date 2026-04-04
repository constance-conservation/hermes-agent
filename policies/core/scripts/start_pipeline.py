#!/usr/bin/env python3
"""
Global entry point for the agentic company policy pipeline.

From repository root:
  python policies/core/scripts/start_pipeline.py
  python policies/core/scripts/start_pipeline.py --dry-run   # verify only, no writes
  python policies/core/scripts/start_pipeline.py --workspace-root "$AGENT_HOME/workspace" --policy-root "$AGENT_HOME/policies"
  python policies/core/scripts/start_pipeline.py --init-operations  # legacy operations-only bootstrap
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _paths import REPO_ROOT
import pipeline_manifest
import verify_policy_tree
from generate_index import run_generate_index
import apply_read_order_navigation


def _run_init_operations_stubs(operations_root: Path | None) -> int:
    script = _SCRIPT_DIR / "init_operations_stubs.py"
    env = os.environ.copy()
    if operations_root is not None:
        env["AGENT_WORKSPACE_ROOT"] = str(operations_root)
    r = subprocess.run([sys.executable, str(script)], cwd=REPO_ROOT, env=env, check=False)
    return r.returncode


def _copy_tree(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _materialize_workspace_assets(workspace_root: Path) -> int:
    """Write runtime-editable policy assets into AGENT_HOME/workspace."""
    policies_src = REPO_ROOT / "policies"
    generated_src = policies_src / "core" / "governance" / "generated"
    runtime_agent_src = policies_src / "core" / "runtime" / "agent"

    policies_dst = workspace_root / "policies"
    generated_dst = policies_dst / "core" / "governance" / "generated"
    runtime_agent_dst = policies_dst / "core" / "runtime" / "agent"

    _copy_tree(generated_src, generated_dst)
    _copy_tree(runtime_agent_src, runtime_agent_dst)
    print(f"start_pipeline: materialized runtime-editable policies under {workspace_root}")
    return 0


def _materialize_canonical_policy_root(policy_root: Path) -> int:
    """Write canonical policy bundle outside workspace."""
    policies_src = REPO_ROOT / "policies"
    _copy_tree(policies_src, policy_root)
    print(f"start_pipeline: materialized canonical policy bundle under {policy_root}")
    return 0


def _resolve_workspace_root(args: argparse.Namespace) -> Path | None:
    if args.workspace_root is not None:
        return args.workspace_root.expanduser().resolve()
    if args.operations_root is not None:
        return args.operations_root.expanduser().resolve()
    env_value = os.environ.get("AGENT_WORKSPACE_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return None


def _resolve_policy_root(args: argparse.Namespace) -> Path | None:
    if args.policy_root is not None:
        return args.policy_root.expanduser().resolve()
    env_value = os.environ.get("AGENT_POLICY_ROOT")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Agentic company policy pipeline: verify tree, strict activation cues, refresh INDEX, update manifest.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Run verification only; print manifest diff; do not write INDEX.md or manifest (use before deploy to validate).",
    )
    ap.add_argument(
        "--init-operations",
        action="store_true",
        help="After success, run init_operations_stubs.py (creates missing operations/*.md only).",
    )
    ap.add_argument(
        "--operations-root",
        type=Path,
        default=None,
        help="Deprecated alias of --workspace-root.",
    )
    ap.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root where runtime-editable outputs are written (example: $AGENT_HOME/workspace).",
    )
    ap.add_argument(
        "--policy-root",
        type=Path,
        default=None,
        help="Canonical runtime policy root outside workspace (example: $AGENT_HOME/policies).",
    )
    ap.add_argument(
        "--skip-workspace-materialization",
        action="store_true",
        help="Skip writing runtime-editable workspace outputs even if a workspace root is set.",
    )
    ap.add_argument(
        "--no-strict",
        action="store_true",
        help="Skip activation-cue checks on policies/core/governance/standards/*.md (not recommended for deployment).",
    )
    args = ap.parse_args()
    strict = not args.no_strict
    workspace_root = _resolve_workspace_root(args)
    policy_root = _resolve_policy_root(args)

    current = pipeline_manifest.compute_manifest()
    saved = pipeline_manifest.load_saved_manifest()

    if args.dry_run:
        code, errs = verify_policy_tree.verify_tree(strict_activation=strict)
        if code != 0:
            print("start_pipeline: DRY-RUN FAILED", file=sys.stderr)
            for e in errs:
                print(" ", e, file=sys.stderr)
            return 1
        print("start_pipeline: DRY-RUN verify OK (strict activation cues)" if strict else "start_pipeline: DRY-RUN verify OK (non-strict)")
        print(" Manifest diff vs last successful run:")
        for line in pipeline_manifest.diff_manifest(current, saved):
            print(" ", line)
        print(f" Tracked: {pipeline_manifest.describe_manifest()}")
        print("start_pipeline: DRY-RUN — no files written")
        return 0

    code, errs = verify_policy_tree.verify_tree(strict_activation=strict)
    if code != 0:
        print("start_pipeline: FAILED (verification)", file=sys.stderr)
        for e in errs:
            print(" ", e, file=sys.stderr)
        return 1

    changed = pipeline_manifest.manifest_changed(current, saved)
    if changed:
        print("start_pipeline: tracked policy files changed since last run — refreshing INDEX and manifest")
        for line in pipeline_manifest.diff_manifest(current, saved):
            print(" ", line)
    else:
        print("start_pipeline: no file changes since last run — refreshing INDEX and manifest (idempotent)")

    gcode, gmsg = run_generate_index()
    if gcode != 0:
        print(f"start_pipeline: INDEX generation failed: {gmsg}", file=sys.stderr)
        return 1
    print(gmsg)

    nav_code = apply_read_order_navigation.main()
    if nav_code != 0:
        print("start_pipeline: read-order navigation refresh failed", file=sys.stderr)
        return 1

    if policy_root is not None:
        pc = _materialize_canonical_policy_root(policy_root)
        if pc != 0:
            print("start_pipeline: canonical policy materialization failed", file=sys.stderr)
            return 1

    if workspace_root is not None and not args.skip_workspace_materialization:
        wc = _materialize_workspace_assets(workspace_root)
        if wc != 0:
            print("start_pipeline: workspace policy materialization failed", file=sys.stderr)
            return 1
        ic = _run_init_operations_stubs(workspace_root)
        if ic != 0:
            print("start_pipeline: init_operations_stubs failed", file=sys.stderr)
            return 1
    elif args.init_operations:
        ic = _run_init_operations_stubs(workspace_root)
        if ic != 0:
            print("start_pipeline: init_operations_stubs failed", file=sys.stderr)
            return 1

    pipeline_manifest.write_manifest(current)
    print("start_pipeline: COMPLETE — verification passed; INDEX and manifest updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
