#!/usr/bin/env python3
"""
Apply ``hermes_slack_manifest_dict()`` to the **operator** Slack app via Manifest API.

Requires ``SLACK_CONFIG_TOKEN`` (xoxe) or ``SLACK_CONFIG_TOKEN_OPERATOR`` / ``SLACK_MANIFEST_KEY``
in the environment or merged from ``--env-from`` files (same line parser as
``slack_workspace_bootstrap`` — safe for values with spaces).

Does **not** create ``SLACK_APP_TOKEN`` (xapp): Slack has no API for that; create it in the
developer UI: App → **Socket Mode** → **App-Level Tokens** → add token with ``connections:write``.

Default ``--app-id`` is the hermes-operator workspace app (from ``bots.info`` / install URL).

Usage (repo root, venv optional if imports work):
  python scripts/dev/apply_operator_slack_manifest.py \\
    --env-from /path/to/operator_env/.env \\
    [--app-id A0AT2H8GPU0] [--dry-run validate-only]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Repo root (parent of scripts/)
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _merge_env(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        os.environ[key] = val.strip().strip('"').strip("'")


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Hermes Slack manifest (operator app)")
    ap.add_argument(
        "--env-from",
        action="append",
        default=[],
        metavar="PATH",
        help="Merge KEY=value lines into os.environ (repeat)",
    )
    ap.add_argument(
        "--app-id",
        default="A0AT2H8GPU0",
        help="Slack App ID (default: operator hermes-operator app)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Only run apps.manifest.validate, not update",
    )
    args = ap.parse_args()

    for ef in args.env_from:
        _merge_env(Path(os.path.expanduser(ef)))

    from hermes_cli.slack_admin import hermes_slack_manifest_dict, _slack_tooling_api_with_token

    tok = (
        (os.getenv("SLACK_CONFIG_TOKEN_OPERATOR") or "").strip()
        or (os.getenv("SLACK_CONFIG_TOKEN") or "").strip()
        or (os.getenv("SLACK_APP_CONFIG_TOKEN") or "").strip()
        or (os.getenv("SLACK_MANIFEST_KEY") or "").strip()
    )
    if not tok.startswith("xoxe"):
        print(
            "Error: set SLACK_CONFIG_TOKEN (xoxe) in an --env-from file or environment.\n"
            "Generate: https://api.slack.com/authentication/basics → App configuration tokens",
            file=sys.stderr,
        )
        return 1

    manifest = hermes_slack_manifest_dict()
    mj = json.dumps(manifest, separators=(",", ":"))
    aid = args.app_id.strip()

    val = _slack_tooling_api_with_token("apps.manifest.validate", tok, app_id=aid, manifest=mj)
    if not val.get("ok"):
        print(f"validate failed: {val.get('error')}", file=sys.stderr)
        for err in val.get("errors") or []:
            if isinstance(err, dict):
                print(f"  - {err.get('pointer')}: {err.get('message')}", file=sys.stderr)
            else:
                print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"ok=true apps.manifest.validate app_id={aid}")

    if args.dry_run:
        print("(dry-run: skipping apps.manifest.update)")
        return 0

    j = _slack_tooling_api_with_token("apps.manifest.update", tok, app_id=aid, manifest=mj)
    if not j.get("ok"):
        print(f"update failed: {j.get('error')}", file=sys.stderr)
        for err in j.get("errors") or []:
            if isinstance(err, dict):
                print(f"  - {err.get('pointer')}: {err.get('message')}", file=sys.stderr)
            else:
                print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"ok=true apps.manifest.update app_id={j.get('app_id')} permissions_updated={j.get('permissions_updated')}")
    print(
        "Next: OAuth & Permissions → reinstall app to hermes-operator workspace if prompted.\n"
        "Then create SLACK_APP_TOKEN (xapp, connections:write) under Socket Mode and add to ~/.hermes/.env."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
