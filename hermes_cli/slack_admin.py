"""
Slack maintenance helpers (CLI). Uses the Slack Web API with SLACK_BOT_TOKEN —
separate from the gateway Socket Mode adapter.
"""

from __future__ import annotations

import os
import sys
import time
from typing import List

from hermes_constants import display_hermes_home


def _tokens_from_env() -> List[str]:
    raw = (os.getenv("SLACK_BOT_TOKEN") or "").strip()
    if not raw:
        print(
            "Error: SLACK_BOT_TOKEN is not set.\n"
            f"Add it to {display_hermes_home()}/.env (or export it), then retry.",
            file=sys.stderr,
        )
        sys.exit(1)
    return [t.strip() for t in raw.split(",") if t.strip()]


def slack_whoami() -> None:
    """Print bot identity from auth.test (no tokens printed)."""
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
    except ImportError:
        print(
            "Error: slack_sdk is not installed. Run: pip install 'hermes-agent[slack]'",
            file=sys.stderr,
        )
        sys.exit(1)

    tokens = _tokens_from_env()
    for i, token in enumerate(tokens):
        prefix = f"[token {i + 1}] " if len(tokens) > 1 else ""
        try:
            client = WebClient(token=token)
            data = client.auth_test()
            print(
                f"{prefix}team={data.get('team', '?')} "
                f"bot_user_id={data.get('user_id', '?')} "
                f"bot_username=@{data.get('user', '?')}"
            )
        except SlackApiError as e:
            print(f"{prefix}auth.test failed: {e.response.get('error', e)}", file=sys.stderr)
            sys.exit(1)


def slack_join_public_channels(*, dry_run: bool = False) -> None:
    """Join every public channel the bot is not already in (needs channels:join)."""
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
    except ImportError:
        print(
            "Error: slack_sdk is not installed. Run: pip install 'hermes-agent[slack]'",
            file=sys.stderr,
        )
        sys.exit(1)

    joined = 0
    skipped = 0
    errors = 0
    would_join = 0
    tokens = _tokens_from_env()

    for ti, token in enumerate(tokens):
        label = f"[workspace {ti + 1}] " if len(tokens) > 1 else ""
        client = WebClient(token=token)
        try:
            ident = client.auth_test()
        except SlackApiError as e:
            print(f"{label}auth.test failed: {e.response.get('error', e)}", file=sys.stderr)
            sys.exit(1)
        team = ident.get("team", "?")
        print(f"{label}Joining public channels in team {team!r} …")

        cursor = None
        channels: List[dict] = []
        while True:
            try:
                resp = client.conversations_list(
                    types="public_channel",
                    exclude_archived=True,
                    limit=200,
                    cursor=cursor,
                )
            except SlackApiError as e:
                err = e.response.get("error", "")
                if err == "missing_scope":
                    print(
                        f"{label}Error: missing OAuth scope. Add **channels:join** under "
                        "OAuth & Permissions → Bot Token Scopes, then reinstall the app to the workspace.",
                        file=sys.stderr,
                    )
                else:
                    print(f"{label}conversations.list failed: {err}", file=sys.stderr)
                sys.exit(1)
            channels.extend(resp.get("channels") or [])
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        for ch in channels:
            cid = ch.get("id")
            name = ch.get("name", cid)
            if not cid:
                continue
            if ch.get("is_member"):
                skipped += 1
                continue
            if dry_run:
                print(f"  would join #{name} ({cid})")
                would_join += 1
                continue
            try:
                client.conversations_join(channel=cid)
                print(f"  joined #{name}")
                joined += 1
                time.sleep(0.35)  # light rate-limit courtesy
            except SlackApiError as e:
                err = e.response.get("error", "")
                if err in ("already_in_channel", "channel_not_found"):
                    skipped += 1
                    continue
                print(f"  #{name}: {err}", file=sys.stderr)
                errors += 1

    if dry_run:
        print(f"Done (dry run). would_join={would_join} already_member={skipped} errors={errors}")
    else:
        print(f"Done. joined={joined} already_member_or_skipped={skipped} errors={errors}")
    if errors and not dry_run:
        sys.exit(1)


def slack_command(args) -> None:
    """Dispatch `hermes slack …` subcommands."""
    sub = getattr(args, "slack_command", None) or ""
    if sub == "join-public":
        slack_join_public_channels(dry_run=bool(getattr(args, "dry_run", False)))
    elif sub == "whoami":
        slack_whoami()
    else:
        print(f"Unknown slack subcommand: {sub!r}", file=sys.stderr)
        sys.exit(1)
