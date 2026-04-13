#!/usr/bin/env python3
"""
Add ``state_skip_gate`` to stateful WhatsApp/monitor crons and normalize prompts.

- Operator paths: ``/Users/operator/.hermes/cron-state/...`` (override with --cron-state-root).
- WhatsApp ``deliver`` jobs: ensure OpenRouter ``openrouter/free`` (synthetic free router) and
  ``--operator --chief-orchestrator`` prompt suffix.

Run on the host that owns the profile (e.g. Mac mini):

  HERMES_HOME=~/.hermes/profiles/chief-orchestrator \\
    ./venv/bin/python scripts/core/patch_chief_whatsapp_cron_state_gate.py --apply

Dry run (default): prints planned edits only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _default_cron_state_root(home: Path) -> Path:
    """Infer ~/Library/... vs /Users/operator from HERMES_HOME parent."""
    return home.parent.parent / "cron-state"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write jobs.json (default is dry run)",
    )
    ap.add_argument(
        "--cron-state-root",
        type=Path,
        help="Directory containing per-job state dirs (default: ~/.hermes/cron-state for default profile)",
    )
    args = ap.parse_args()

    hh = os.environ.get("HERMES_HOME", "").strip()
    if not hh:
        print("Set HERMES_HOME to the profile directory.", file=__import__("sys").stderr)
        return 2
    home = Path(hh).expanduser()
    root = args.cron_state_root or _default_cron_state_root(home)

    gates = {
        "6bc442ae2aec": {
            "path": str(root / "whatsapp-gateway-watchdog" / "state.json"),
            "keys": ["last_status_key", "connected_platforms"],
        },
        "75756dc8e257": {
            "path": str(root / "intervention-request-escalation-monitor" / "state.json"),
            "keys": ["last_status_key"],
        },
        "abc03fa38b2a": {
            "path": str(root / "whatsapp-last-resort-operator-escalation" / "state.json"),
            "keys": ["last_status_key"],
        },
    }

    suffix = (
        "\n\nAppend a final line containing exactly: --operator --chief-orchestrator\n"
        "(Place it on its own line after the message content.)"
    )
    marker = "Append a final line containing exactly: --operator --chief-orchestrator"

    jobs_path = home / "cron" / "jobs.json"
    if not jobs_path.is_file():
        print(f"Missing {jobs_path}", file=__import__("sys").stderr)
        return 1

    data = json.loads(jobs_path.read_text(encoding="utf-8"))
    droplet_prefix = "/home/hermesuser/.hermes/cron-state/"

    edits = 0
    for job in data.get("jobs", []):
        jid = job.get("id")
        if jid in gates:
            job["state_skip_gate"] = gates[jid]
            job.pop("last_state_gate_fingerprint", None)
            edits += 1
            print(f"state_skip_gate: {job.get('name')} ({jid})")
        d = job.get("deliver") or ""
        if str(d).startswith("whatsapp:"):
            pr = job.get("prompt") or ""
            if droplet_prefix in pr:
                pr = pr.replace(droplet_prefix, str(root) + "/")
                edits += 1
                print(f"prompt paths: {job.get('name')}")
            if marker not in pr:
                job["prompt"] = pr.rstrip() + suffix
                edits += 1
                print(f"suffix: {job.get('name')}")
            if job.get("model") != "openrouter/free" or job.get("provider") != "openrouter":
                job["model"] = "openrouter/free"
                job["provider"] = "openrouter"
                job["base_url"] = None
                edits += 1
                print(f"model: {job.get('name')} -> openrouter/free")

    if not edits:
        print("No changes needed.")
        return 0
    if not args.apply:
        print(f"\nDry run: {edits} change(s). Pass --apply to write {jobs_path}")
        return 0

    jobs_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {jobs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
