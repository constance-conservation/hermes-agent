#!/usr/bin/env python3
"""
Create Hermes profiles for org / REM roles from scripts/org_agent_profiles_manifest.yaml.

Copies config/.env/SOUL from clone_from (default chief-orchestrator), then merges
toolsets and agent.max_turns and appends a small SOUL marker with role pointers.

Usage (repo root, venv active optional):
  ./venv/bin/python scripts/bootstrap_org_agent_profiles.py
  ./venv/bin/python scripts/bootstrap_org_agent_profiles.py --dry-run
  ./venv/bin/python scripts/bootstrap_org_agent_profiles.py --refresh-config

Removing a role: delete the profile with `hermes profile delete <name>` and trim
the manifest; the chief should stop delegating to that hermes_profile name.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _load_manifest(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid manifest (expected mapping): {path}")
    return data


def _merge_config(profile_dir: Path, toolsets: List[str], agent_max_turns: Optional[int]) -> None:
    p = profile_dir / "config.yaml"
    if not p.exists():
        return
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    doc["toolsets"] = list(toolsets)
    if agent_max_turns is not None:
        doc.setdefault("agent", {})
        doc["agent"]["max_turns"] = int(agent_max_turns)
    p.write_text(
        yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _append_soul_marker(
    profile_dir: Path,
    name: str,
    ag_id: Optional[str],
    role_prompt: Optional[str],
) -> None:
    marker = f"<!-- bootstrap_org_agent_profiles:{name} -->"
    soul = profile_dir / "SOUL.md"
    body = soul.read_text(encoding="utf-8") if soul.exists() else ""
    if marker in body:
        return
    block = f"\n\n{marker}\n### Org profile: `{name}`\n"
    if ag_id:
        block += f"- **AG-ID:** {ag_id}\n"
    if role_prompt:
        block += f"- **Role prompt (repo):** `{ROOT / role_prompt}`\n"
    block += (
        "- **Standards:** `policies/core/governance/standards/"
        "canonical-ai-agent-security-policy.md`\n"
    )
    soul.write_text(body.rstrip() + block + "\n", encoding="utf-8")


def _create_profile(venv_python: Path, clone_from: str, name: str, dry_run: bool) -> bool:
    from hermes_cli.profiles import profile_exists

    if profile_exists(name):
        return False
    cmd = [
        str(venv_python),
        "-m",
        "hermes_cli.main",
        "profile",
        "create",
        name,
        "--clone",
        "--clone-from",
        clone_from,
        "--no-alias",
    ]
    if dry_run:
        print(f"[dry-run] would run: {' '.join(cmd)}")
        return True
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "scripts/org_agent_profiles_manifest.yaml",
        help="Path to manifest YAML",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--refresh-config",
        action="store_true",
        help="Re-merge toolsets / max_turns / SOUL markers for existing profiles",
    )
    parser.add_argument(
        "--venv-python",
        type=Path,
        default=ROOT / "venv/bin/python",
        help="Interpreter used to run hermes_cli.main",
    )
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"Manifest not found: {args.manifest}", file=sys.stderr)
        sys.exit(1)
    if not args.dry_run and not args.venv_python.is_file():
        print(f"venv python not found: {args.venv_python}", file=sys.stderr)
        sys.exit(1)

    manifest = _load_manifest(args.manifest)
    clone_from = str(manifest.get("clone_from") or "chief-orchestrator").strip()
    if not args.dry_run:
        from hermes_cli.profiles import profile_exists as _pe

        if not _pe(clone_from):
            print(
                f"Source profile {clone_from!r} does not exist. Create it first, "
                f"or set clone_from in {args.manifest}.",
                file=sys.stderr,
            )
            sys.exit(1)
    profiles = manifest.get("profiles")
    if not isinstance(profiles, list):
        print("Manifest missing 'profiles' list", file=sys.stderr)
        sys.exit(1)

    from hermes_cli.profiles import get_profile_dir, profile_exists

    for entry in profiles:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            print("skip: entry without name", file=sys.stderr)
            continue
        toolsets = entry.get("toolsets")
        if not isinstance(toolsets, list):
            print(f"skip {name}: invalid toolsets", file=sys.stderr)
            continue
        ag_id = entry.get("ag_id")
        ag_id_s = str(ag_id).strip() if ag_id else None
        rp = entry.get("role_prompt")
        rp_s = str(rp).strip() if rp else None
        max_turns = entry.get("agent_max_turns")
        max_i = int(max_turns) if max_turns is not None else None

        existed = profile_exists(name)
        if existed and not args.refresh_config:
            print(f"skip (exists): {name}  (use --refresh-config to merge manifest)")
            continue

        if not existed:
            _create_profile(args.venv_python, clone_from, name, args.dry_run)

        if args.dry_run:
            act = "create + merge" if not existed else "merge"
            print(f"[dry-run] would {act} {name}")
            continue

        profile_dir = get_profile_dir(name)
        if not profile_dir.is_dir():
            print(f"warning: profile dir missing: {profile_dir}", file=sys.stderr)
            continue

        _merge_config(profile_dir, toolsets, max_i)
        _append_soul_marker(profile_dir, name, ag_id_s, rp_s)
        print(f"ok: {name}")

    print("bootstrap_org_agent_profiles: done")


if __name__ == "__main__":
    main()
