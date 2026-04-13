#!/usr/bin/env python3
"""Trigger every cron job with deliver=slack:*, then run one scheduler tick for those jobs only.

Patches cron.scheduler.get_due_jobs for the duration of tick() so other due jobs are not run.

Usage:
  HERMES_HOME=~/.hermes/profiles/chief-orchestrator \\
    ./venv/bin/python memory/core/scripts/core/run_slack_cron_burst_now.py [--no-dedupe]

``--no-dedupe`` sets ``HERMES_CRON_DELIVERY_DEDUPE=0`` so repeat check-ins are not skipped
when body fingerprints match the last successful delivery.

``--ping '…'`` skips the LLM and posts the same text to every ``slack:`` cron target (routing /
allowlist smoke test). Run once per ``HERMES_HOME`` profile that owns those jobs.

``--ping-job-prompt`` posts each job's own ``prompt`` field (the scheduled policy text) so every
channel shows what that role is asked to post.

``--policy-checkin`` posts a *one-off* upward summary shaped like
``chief-orchestrator-directive.md`` / ``unified-deployment-and-security.md`` (objective, status,
evidence, blocker, next action, decision, memory recommendation), then the scheduled prompt excerpt
so each delegated channel visibly matches org reporting policy plus the cron contract.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

_SLACK_JOB_SLUG_SUFFIX = re.compile(r"-([CD][A-Z0-9]+)$")


def _role_slug_from_slack_job_name(name: str) -> str:
    """Parse role slug from ``daily-slack-role-status-<slug>-<channelId>`` (sync_slack_role_cron_jobs)."""
    n = (name or "").strip()
    if not n.startswith("daily-slack-role-status-"):
        return n or "unknown-role"
    body = n[len("daily-slack-role-status-") :]
    m = _SLACK_JOB_SLUG_SUFFIX.search(body)
    if m:
        slug = body[: m.start()].strip()
        return slug or "unknown-role"
    return body or "unknown-role"


def _build_policy_checkin_message(job: dict) -> str:
    role = _role_slug_from_slack_job_name(str(job.get("name") or ""))
    deliver = str(job.get("deliver", "")).strip()
    jid = str(job.get("name") or job.get("id") or "")
    raw_prompt = (job.get("prompt") or "").strip()
    excerpt = raw_prompt if len(raw_prompt) <= 7000 else raw_prompt[:6900] + "\n…(truncated)"
    return (
        f"*Delegated agent check-in (one-off, policy-shaped)* — `{jid}`\n\n"
        f"Role slug: `{role}` · Target: `{deliver}`\n\n"
        "Per *chief-orchestrator-directive* (UPWARD SUMMARY PROTOCOL) and "
        "*unified-deployment-and-security* (Agent Startup Bundle / reporting format), this channel "
        "receives the standard upward structure:\n"
        "• *objective:* Daily Slack-only status for this role remit (Australia/Sydney cadence per job spec).\n"
        "• *current status:* Manual Hermes publish — no LLM turn for this message; confirms routing and visibility.\n"
        "• *evidence:* Role alignment with `HERMES_HOME/policies/`; operational rules in the scheduled prompt below "
        "(unique per channel, no cross-surface paste).\n"
        "• *blocker:* None asserted in this one-off.\n"
        "• *next action:* Normal staggered cron resumes; respond `[SILENT]` when there is no material delta.\n"
        "• *requested decision:* None.\n"
        "• *memory recommendation:* keep active\n\n"
        "Channel architecture context: `policies/core/governance/standards/channel-architecture-policy.md` "
        "(purpose-specific channels; summaries flow upward).\n\n"
        "---\n*Scheduled job prompt (authoritative contract for daily copy):*\n\n"
        f"{excerpt or '(no prompt stored for this job)'}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Disable cron delivery fingerprint dedupe for this run (test / forced check-ins).",
    )
    mx = ap.add_mutually_exclusive_group()
    mx.add_argument(
        "--ping",
        metavar="TEXT",
        default=None,
        help="Post TEXT to each slack:* cron target via gateway delivery (no LLM / no tick).",
    )
    mx.add_argument(
        "--ping-job-prompt",
        action="store_true",
        help="Post each job's stored prompt (policy text) to its slack:* target (no LLM / no tick).",
    )
    mx.add_argument(
        "--policy-checkin",
        action="store_true",
        help="Post policy-shaped upward summary + scheduled prompt excerpt per slack job (no LLM / no tick).",
    )
    args = ap.parse_args()
    if args.no_dedupe:
        os.environ["HERMES_CRON_DELIVERY_DEDUPE"] = "0"

    hh = os.environ.get("HERMES_HOME", "").strip()
    if not hh:
        print("Set HERMES_HOME to the active profile directory.", file=sys.stderr)
        return 2
    os.environ["HERMES_HOME"] = os.path.expanduser(hh)

    repo = os.path.expanduser("~/hermes-agent")
    if repo not in sys.path:
        sys.path.insert(0, repo)

    from hermes_cli.env_loader import load_hermes_dotenv

    load_hermes_dotenv(hermes_home=Path(os.environ["HERMES_HOME"]))

    from cron.jobs import load_jobs, trigger_job
    import cron.scheduler as sch

    slack_jobs = [j for j in load_jobs() if str(j.get("deliver", "")).startswith("slack:")]
    if not slack_jobs:
        print("No slack:* deliver cron jobs in this profile.", file=sys.stderr)
        return 1

    if args.ping_job_prompt or args.policy_checkin or args.ping is not None:
        from cron.delivery import deliver_cron_result

        fails = 0
        for j in slack_jobs:
            target = str(j.get("deliver", ""))
            if args.policy_checkin:
                text = _build_policy_checkin_message(j)
                if len(text) > 35000:
                    text = text[:34900] + "\n…(truncated)"
            elif args.ping_job_prompt:
                raw = (j.get("prompt") or "").strip()
                text = (
                    f"*Scheduled Slack role policy (test)* — `{j.get('name', j.get('id'))}`\n\n"
                    f"{raw or '(no prompt stored for this job)'}"
                )
                if len(text) > 12000:
                    text = text[:11900] + "\n…(truncated)"
            else:
                text = str(args.ping).strip() or "(empty ping)"
            ok = bool(deliver_cron_result(j, text))
            print(f"ping {j.get('name', j.get('id'))} {target} -> {'ok' if ok else 'FAIL'}", file=sys.stderr)
            if not ok:
                fails += 1
        return 1 if fails else 0

    slack_ids = [j["id"] for j in slack_jobs]
    print(f"Triggering {len(slack_ids)} slack cron job(s)", file=sys.stderr)
    for jid in slack_ids:
        trigger_job(jid)

    _orig = sch.get_due_jobs
    slack_set = frozenset(slack_ids)

    def _slack_due():
        return [j for j in _orig() if j["id"] in slack_set]

    sch.get_due_jobs = _slack_due
    try:
        total = 0
        # tick() may return 0 if another process holds ~/.hermes/.../cron/.tick.lock (e.g. gateway).
        for attempt in range(60):
            n = sch.tick(verbose=True)
            total += n
            if n > 0:
                print(f"tick executed {n} job(s) (attempt {attempt + 1})", file=sys.stderr)
                break
            due = _slack_due()
            if not due:
                print("No slack jobs remain due after tick — done or already advanced.", file=sys.stderr)
                break
            time.sleep(5)
        else:
            print("Gave up waiting for cron tick lock (gateway may hold it).", file=sys.stderr)
            return 3
    finally:
        sch.get_due_jobs = _orig
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
