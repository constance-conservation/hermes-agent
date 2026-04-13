"""Assemble the effective user prompt for a scheduled cron job (skills + constraints)."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_ENVELOPE_SPEC = (
    "[SYSTEM — CRON DELIVERY (mandatory): The user only sees what you put in the JSON block "
    "below. You may reason, use tools, and write drafts before it; that prose is NOT delivered.\n"
    "End your reply with EXACTLY these markers and a single JSON object between them "
    "(optionally wrapped in ```json … ```):\n"
    "###HERMES_CRON_DELIVERY_JSON\n"
    '{ "silent": true }\n'
    "###END_HERMES_CRON_DELIVERY_JSON\n"
    "If there is something to report, use non-empty lines (plain strings, no nested objects):\n"
    "###HERMES_CRON_DELIVERY_JSON\n"
    '{ "silent": false, "lines": ["watchdog-check: ok all_connected=whatsapp,telegram", "sev: 0"] }\n'
    "###END_HERMES_CRON_DELIVERY_JSON\n"
    "Rules: (1) Nothing after ###END_HERMES_CRON_DELIVERY_JSON. "
    "(2) At most 16 lines; each line under ~280 characters; total size respects delivery_max_chars. "
    "(3) Lines must be factual (states, numbers, paths, command output) — no narration, no "
    "“I am sending…”, no web-search essay. "
    "(4) Use {\"silent\": true} when there is no new factual delta since the last run. "
    "(5) Do not use [SILENT], “[Silently …]”, or “I will respond with [SILENT]” — only the JSON block. "
    "(6) If your profile sets cron.strict_delivery_envelope, missing or invalid JSON suppresses "
    "messaging entirely.]\n\n"
)


def build_cron_job_prompt(job: dict[str, Any]) -> str:
    """Build the effective prompt for a cron job, optionally loading one or more skills first."""
    prompt = job.get("prompt", "")
    skills = job.get("skills")

    prompt = _ENVELOPE_SPEC + prompt
    if skills is None:
        legacy = job.get("skill")
        skills = [legacy] if legacy else []

    skill_names = [str(name).strip() for name in skills if str(name).strip()]
    if not skill_names:
        return prompt

    from tools.skills_tool import skill_view

    parts: list[str] = []
    skipped: list[str] = []
    for skill_name in skill_names:
        loaded = json.loads(skill_view(skill_name))
        if not loaded.get("success"):
            error = loaded.get("error") or f"Failed to load skill '{skill_name}'"
            logger.warning(
                "Cron job '%s': skill not found, skipping — %s",
                job.get("name", job.get("id")),
                error,
            )
            skipped.append(skill_name)
            continue

        content = str(loaded.get("content") or "").strip()
        if parts:
            parts.append("")
        parts.extend(
            [
                f'[SYSTEM: The user has invoked the "{skill_name}" skill, indicating they want you to follow its instructions. The full skill content is loaded below.]',
                "",
                content,
            ]
        )

    if skipped:
        notice = (
            f"[SYSTEM: The following skill(s) were listed for this job but could not be found "
            f"and were skipped: {', '.join(skipped)}. "
            f"Include that in your JSON lines if the user should know, e.g. "
            f'{{"silent": false, "lines": ["⚠️ Skills skipped: {", ".join(skipped)}"]}}]'
        )
        parts.insert(0, notice)

    if prompt:
        parts.extend(
            ["", f"The user has provided the following instruction alongside the skill invocation: {prompt}"]
        )
    return "\n".join(parts)
