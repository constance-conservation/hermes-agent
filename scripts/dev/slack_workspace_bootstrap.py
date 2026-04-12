#!/usr/bin/env python3
"""
Slack Web API helper (bot token only): print SLACK_ALLOWED_TEAMS / SLACK_ALLOWED_CHANNELS,
join public channels, optionally send a test DM.

The live gateway also needs SLACK_APP_TOKEN (xapp-…) for Socket Mode — this script does not
create that; it only uses SLACK_BOT_TOKEN (xoxb-…) for REST calls.

Usage (from repo root, venv active):
  python scripts/dev/slack_workspace_bootstrap.py \\
    --env-from ~/.hermes/.env \\
    --env-from ~/.hermes/profiles/chief-orchestrator/.env \\
    [--send-test-dm] [--max-channels 80]

  (--env-from avoids shell sourcing when .env values contain spaces.)
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def upsert_env_keys(path: Path, updates: dict[str, str]) -> None:
    """Replace or append KEY=value lines (UTF-8)."""
    lines: list[str] = []
    if path.is_file():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    pending = set(updates.keys())
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in pending:
                out.append(f"{key}={updates[key]}")
                pending.discard(key)
                continue
        out.append(line)
    for key in sorted(pending):
        out.append(f"{key}={updates[key]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")


def merge_env_file(path: str | Path) -> None:
    """Merge KEY=value lines into os.environ (later calls win). Safe for values with spaces."""
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip().strip('"').strip("'")
        os.environ[key] = val


def _urlopen(req: urllib.request.Request, *, timeout: float = 60):
    try:
        import certifi  # type: ignore[import-untyped]

        ctx = ssl.create_default_context(cafile=certifi.where())
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)
    except ImportError:
        return urllib.request.urlopen(req, timeout=timeout)


def _api(method: str, token: str, **kwargs: Any) -> dict[str, Any]:
    body = {"token": token, **kwargs}
    data = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with _urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Slack workspace bootstrap via bot token")
    ap.add_argument(
        "--env-from",
        action="append",
        default=[],
        metavar="PATH",
        help="Hermes-style .env to merge into environment (repeat; later files override)",
    )
    ap.add_argument("--send-test-dm", action="store_true", help="POST test message to SLACK_ALLOWED_USERS DM")
    ap.add_argument("--max-channels", type=int, default=80, help="Max channel IDs to list in SLACK_ALLOWED_CHANNELS")
    ap.add_argument(
        "--write-allowlists-to",
        action="append",
        default=[],
        metavar="PATH",
        help="Update SLACK_ALLOWED_TEAMS and SLACK_ALLOWED_CHANNELS in this .env (repeat for multiple files)",
    )
    args = ap.parse_args()

    for ef in args.env_from:
        merge_env_file(os.path.expanduser(ef))

    tok = (os.getenv("SLACK_BOT_TOKEN") or "").strip()
    if not tok.startswith("xoxb-"):
        print("Error: SLACK_BOT_TOKEN (xoxb-) required in environment.", file=sys.stderr)
        return 1

    auth = _api("auth.test", tok)
    if not auth.get("ok"):
        print(f"auth.test failed: {auth.get('error')}", file=sys.stderr)
        return 1

    team_id = auth.get("team_id") or ""
    team_name = auth.get("team") or ""
    bot_user = auth.get("user_id") or ""
    print(f"# Workspace: {team_name!r} team_id={team_id} bot_user={bot_user}")
    print(f"SLACK_ALLOWED_TEAMS={team_id}")

    cursor = ""
    channel_ids: list[str] = []
    while len(channel_ids) < args.max_channels:
        page = _api(
            "conversations.list",
            tok,
            types="public_channel,private_channel",
            limit=200,
            cursor=cursor or None,
        )
        if not page.get("ok"):
            print(f"conversations.list failed: {page.get('error')}", file=sys.stderr)
            break
        for ch in page.get("channels") or []:
            cid = ch.get("id")
            if isinstance(cid, str) and (cid.startswith("C") or cid.startswith("G")):
                channel_ids.append(cid)
        cursor = (page.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break

    joined = 0
    for cid in channel_ids[: args.max_channels]:
        j = _api("conversations.join", tok, channel=cid)
        if j.get("ok"):
            joined += 1
        elif j.get("error") not in ("already_in_channel", "method_not_supported_for_channel_type"):
            pass  # missing scope or archived — ignore

    print(f"# Joined {joined} channel(s) (best-effort; needs channels:join scope).")
    csv = ""
    if channel_ids:
        csv = ",".join(channel_ids[: args.max_channels])
        print(f"SLACK_ALLOWED_CHANNELS={csv}")
    else:
        print("# No channel IDs collected (check bot scopes: channels:read, groups:read).")

    for wf in args.write_allowlists_to:
        target = Path(os.path.expanduser(wf))
        upsert_env_keys(
            target,
            {
                "SLACK_ALLOWED_TEAMS": team_id,
                "SLACK_ALLOWED_CHANNELS": csv,
            },
        )
        print(f"# Wrote allowlists to {target}")

    if args.send_test_dm:
        allow = (os.getenv("SLACK_ALLOWED_USERS") or "").strip()
        if not allow or allow == "*":
            print("Error: set SLACK_ALLOWED_USERS to a member ID (U…) for --send-test-dm", file=sys.stderr)
            return 1
        uid = allow.split(",")[0].strip()
        op = _api("conversations.open", tok, users=uid)
        if not op.get("ok"):
            print(f"conversations.open failed: {op.get('error')}", file=sys.stderr)
            return 1
        ch = (op.get("channel") or {}) if isinstance(op.get("channel"), dict) else {}
        dm = ch.get("id")
        if not dm:
            print("conversations.open: no channel id", file=sys.stderr)
            return 1
        msg = _api(
            "chat.postMessage",
            tok,
            channel=dm,
            text="[Hermes] Slack bootstrap test message — gateway still needs SLACK_APP_TOKEN for Socket Mode.",
        )
        if not msg.get("ok"):
            print(f"chat.postMessage failed: {msg.get('error')}", file=sys.stderr)
            return 1
        print(f"# Test DM sent to channel {dm}")

    if not (os.getenv("SLACK_APP_TOKEN") or "").strip():
        print(
            "# Reminder: set SLACK_APP_TOKEN (xapp-…) for Socket Mode or the gateway Slack adapter stays disconnected.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
