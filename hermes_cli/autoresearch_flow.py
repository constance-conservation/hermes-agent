from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import shlex
from typing import Any, Mapping, Optional, Tuple
import uuid

from hermes_constants import get_hermes_home
from hermes_cli.integration_repos import resolve_autoresearch_repo


class AutoresearchFlowError(RuntimeError):
    """Raised when the autoresearch runtime flow cannot proceed."""


@dataclass(frozen=True)
class AutoresearchAppendResult:
    repo_path: Path
    program_path: Path


@dataclass(frozen=True)
class AutoresearchPreparedRun:
    repo_path: Path
    program_path: Path
    prompt_text: str
    job_id: str
    job_dir: Path
    prompt_path: Path
    log_path: Path
    wall_clock_seconds: int
    wall_clock_override_minutes: int | None = None


def _expand_path(path: Path) -> str:
    try:
        return str(path).replace(str(Path.home()), "~", 1)
    except Exception:
        return str(path)


def resolve_autoresearch_repo_path(config: Optional[Mapping[str, Any]] = None) -> Path:
    configured = resolve_autoresearch_repo(config)
    if configured:
        return Path(configured).expanduser()
    return get_hermes_home() / "skills" / "external-repos" / "autoresearch"


def resolve_autoresearch_program_path(config: Optional[Mapping[str, Any]] = None) -> Path:
    return resolve_autoresearch_repo_path(config) / "program.md"


def resolve_autoresearch_jobs_root() -> Path:
    return get_hermes_home() / "workspace" / "memory" / "runtime" / "autoresearch-jobs"


def format_autoresearch_jobs_status(
    _config: Optional[Mapping[str, Any]] = None, *, limit: int = 10
) -> str:
    """List recent job directories and log paths for the active ``HERMES_HOME`` profile.

    Helps operators copy a **real** path in a second terminal. Placeholder text like
    ``<JOB_ID>`` in docs must never be pasted into the shell literally.
    """
    root = resolve_autoresearch_jobs_root()
    lines: list[str] = [
        "Autoresearch — recent jobs on this host (newest first). "
        "Copy a path below; do not paste angle-bracket placeholders (e.g. <JOB_ID>) into the shell.",
        "",
        f"Jobs directory: {_expand_path(root)}",
        "",
    ]
    probe = (
        "Check for a live worker on this machine:\n"
        "  pgrep -fl hermes_cli.autoresearch_background\n"
        "(no output means no background autoresearch worker process)"
    )

    if not root.is_dir():
        lines.append(
            "(No autoresearch-jobs folder yet — no /autoresearch run has created jobs here.)"
        )
        lines.extend(["", probe])
        return "\n".join(lines)

    subdirs = [p for p in root.iterdir() if p.is_dir()]
    try:
        subdirs.sort(
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=True,
        )
    except OSError:
        subdirs.sort(key=lambda p: p.name, reverse=True)

    if not subdirs:
        lines.append("(No job folders yet.)")
        lines.extend(["", probe])
        return "\n".join(lines)

    for d in subdirs[:limit]:
        logf = d / "run.log"
        extra = ""
        if logf.is_file():
            try:
                extra = f" — {logf.stat().st_size} bytes"
            except OSError:
                extra = " — (size unreadable)"
        else:
            extra = " — (run.log missing)"
        lines.append(f"• {d.name}{extra}")
        lines.append(f"  {_expand_path(logf)}")

    if len(subdirs) > limit:
        lines.append(f"… and {len(subdirs) - limit} older job(s).")

    lines.extend(
        [
            "",
            "In Hermes on this host, `/autoresearch jobs` reprints this list.",
            "",
            probe,
        ]
    )
    return "\n".join(lines)


def resolve_hermes_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def format_autoresearch_capture_prompt(config: Optional[Mapping[str, Any]] = None) -> str:
    program_path = resolve_autoresearch_program_path(config)
    repo_path = resolve_autoresearch_repo_path(config)
    return "\n".join(
        [
            "Autoresearch — step 1 of 3: your run brief (instructions).",
            "",
            "Reply with your full instructions in your very next message.",
            "",
            "Include everything Hermes should use for this run:",
            "- your full program.md content or the exact additions you want appended",
            "- any preferred run tag, branch naming, total outer runtime, budget, model, or test constraints",
            "- any hard requirements about what Hermes must or must not change",
            "",
            "If you leave run-tag or branch details out, Hermes will choose deterministic defaults.",
            "You can name an outer runtime in this message; step 2 still lets you override it with a hard cap in minutes.",
            "",
            f"After step 2, Hermes will append your brief to: {_expand_path(program_path)}",
            f"Autoresearch repo: {_expand_path(repo_path)}",
            "",
            "Step 3 (after step 2) starts the Hermes worker as a background subprocess and shows how to tail the log.",
            "",
            "Use /autoresearch cancel to abort or /autoresearch show to print the repo/program paths again.",
        ]
    )


def format_autoresearch_duration_prompt(config: Optional[Mapping[str, Any]] = None) -> str:
    program_path = resolve_autoresearch_program_path(config)
    return "\n".join(
        [
            "Autoresearch — step 2 of 3: total wall-clock runtime for this Hermes worker.",
            "",
            "Reply with ONE of:",
            '- `default` — use the duration implied by your instructions (and program.md / doc default 600 min if none).',
            "- a positive integer — **minutes** only for the hard cap (e.g. `600` for 10 hours, `120` for 2 hours).",
            "",
            f"Your instructions are ready to append to: {_expand_path(program_path)}",
            "",
            "Step 3 launches the worker (subprocess), writes a log file, and prints the exact `tail -f` line for a second terminal.",
            "",
            "Use /autoresearch cancel to abort.",
        ]
    )


def format_autoresearch_target_message(config: Optional[Mapping[str, Any]] = None) -> str:
    repo_path = resolve_autoresearch_repo_path(config)
    program_path = resolve_autoresearch_program_path(config)
    return "\n".join(
        [
            f"Autoresearch repo: {_expand_path(repo_path)}",
            f"Program file: {_expand_path(program_path)}",
            "Run /autoresearch for a three-step flow: (1) instructions, (2) total runtime in minutes or `default`, "
            "(3) background worker + second-terminal `tail -f` command.",
        ]
    )


def format_autoresearch_live_log_shell_command(log_path: Path) -> str:
    """Two-line shell snippet for the host where the worker runs.

    A single long ``tail -n 200 -f /very/long/path/run.log`` often **wraps** in the
    TUI; users then paste a newline between ``-f`` and the path, so ``tail`` reads
    **stdin** and the log file never streams. Using ``LOG_FILE=…`` on one line and
    a short ``tail … "$LOG_FILE"`` on the next avoids that failure mode.
    """
    resolved = str(log_path.resolve())
    return f"LOG_FILE={shlex.quote(resolved)}\ntail -n 200 -f \"$LOG_FILE\""


def format_gateway_autoresearch_step_banner(step: int, inner_text: str) -> str:
    """Plain-text section headers for gateway/messaging (no ANSI)."""
    if step == 1:
        return f"📋 STEP 1/3 — What to send Hermes\n\n{inner_text}"
    if step == 2:
        return f"⏱ STEP 2/3 — Total wall-clock runtime\n\n{inner_text}"
    return inner_text


def format_autoresearch_live_log_follow_instructions(log_path: Path) -> str:
    """Copy-paste block: runnable shell command + what the log file is (CLI + gateway)."""
    cmd = format_autoresearch_live_log_shell_command(log_path)
    display = _expand_path(log_path.resolve())
    return "\n".join(
        [
            "Autoresearch — step 3 of 3: watch the background worker (subprocess).",
            "",
            "Open a new terminal on this same host (new tab, split pane, or another SSH session). "
            "Paste both lines below into that shell (same session, in order), then press Enter after the second line. "
            "Ctrl+C stops `tail` only; the Hermes worker subprocess keeps running.",
            "",
            cmd,
            "",
            f"The log is plain text at {display}. It is not an executable — use `tail -f` (or the line above); do not run the file as a program.",
            "",
            "Use `/autoresearch jobs` in Hermes on this host to list recent jobs and exact log paths (avoid placeholder text like <JOB_ID> in the shell).",
        ]
    )


def parse_autoresearch_duration_minutes_reply(text: str) -> Tuple[bool, Optional[int], str]:
    """Parse step-2 duration reply.

    Returns:
        (True, None, "") — use default / resolve from program.md
        (True, minutes, "") — hard cap in minutes
        (False, None, err) — invalid
    """
    s = (text or "").strip()
    if not s:
        return True, None, ""
    low = s.lower()
    if low in (
        "default",
        "def",
        "auto",
        "program",
        "instructions",
        "doc",
        "docs",
    ):
        return True, None, ""
    m = re.fullmatch(r"(\d+)\s*m", low)
    if m:
        s = m.group(1)
    elif not re.fullmatch(r"\d+", s):
        return (
            False,
            None,
            "Expected `default` or a whole number of minutes (e.g. `600`).",
        )
    try:
        minutes = int(s)
    except ValueError:
        return False, None, "Invalid number."
    if minutes < 1:
        return False, None, "Minutes must be at least 1."
    if minutes > 10080:
        return False, None, "Maximum is 10080 minutes (7 days)."
    return True, minutes, ""


def append_outer_runtime_step2_minutes(program_path: Path, minutes: int) -> None:
    """Record step-2 override in program.md for humans and for future parses."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    block = (
        f"\n\n<!-- HERMES_AUTORESEARCH_STEP2_RUNTIME {ts} -->\n"
        f"### Outer runtime (Hermes /autoresearch step 2)\n\n"
        f"**Total outer runtime for this run:** {minutes} minutes "
        f"(hard cap enforced by the autoresearch worker).\n"
    )
    existing = program_path.read_text(encoding="utf-8")
    program_path.write_text(existing.rstrip() + block + "\n", encoding="utf-8")


def _build_managed_block(user_instructions: str) -> str:
    cleaned = (user_instructions or "").strip()
    if not cleaned:
        raise AutoresearchFlowError("No autoresearch instructions were provided.")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    return (
        f"<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_START {timestamp} -->\n"
        f"## Hermes Runtime Instructions ({timestamp})\n\n"
        "The following instructions were provided through `/autoresearch`. "
        "Treat the newest Hermes Runtime Instructions block as the active run brief when it conflicts with older local addenda.\n\n"
        f"{cleaned}\n\n"
        "### Hermes Runtime Notes\n"
        "- Repository target: `efecanbasoz/autoresearch-cpu`\n"
        "- Prefer editing `train.py` unless the user explicitly asks for changes elsewhere.\n"
        "- Treat `prepare.py` as one-time data/tokenizer prep unless the user explicitly asks to change it.\n"
        "- If this block specifies a total outer runtime or wall-clock budget for the overall autoresearch loop, Hermes should treat it as a hard stop for the full run. If no outer runtime is specified, default to 600 minutes total for the outer loop rather than running indefinitely.\n"
        "- Hermes `/autoresearch` background workers bypass the normal Hermes max-iterations cap for this run; outer runtime is the stop condition instead.\n"
        "<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_END -->\n"
    )


def _build_autoresearch_runtime_brief() -> str:
    return "\n".join(
        [
            "Read the repo's `program.md`, especially the newest `Hermes Runtime Instructions` block, and use it as the active run brief.",
            "Treat the user's just-submitted message as the only required interactive input for this run.",
            "Do not ask follow-up questions about run tags, branch tags, branch names, naming conventions, or similar setup trivia.",
            "If a run tag, branch name, artifact name, or similar identifier is needed, choose a deterministic default yourself and continue.",
            "If `program.md` or the newest Hermes Runtime Instructions block specifies a total outer runtime or wall-clock budget for the full autoresearch loop, treat that as a hard stop for the overall run.",
            "If no total outer runtime is specified, default to 600 minutes total for the overall autoresearch loop instead of running indefinitely.",
            "Keep the outer-loop runtime budget separate from any per-run `train.py` budget that the autoresearch repo already enforces.",
            "For Hermes `/autoresearch` background runs, bypass the normal Hermes max-iterations cap and let the outer runtime budget stop the run instead.",
            "Start the work immediately.",
            "When it is safe and useful, split the work into a small set of parallel delegated subprocesses for distinct workstreams.",
            "Continue autonomously until the run is complete or you hit a true hard blocker that only a human can resolve.",
            "Emit concise milestone-style progress updates and a final summary in normal output.",
        ]
    )


def _build_autoresearch_runtime_note(result: AutoresearchAppendResult) -> str:
    return " ".join(
        [
            f"The user's instructions were appended to `{_expand_path(result.program_path)}`.",
            f"The autoresearch repo for this Hermes profile is `{_expand_path(result.repo_path)}`.",
            "This is intended to run as a background-friendly autoresearch job.",
        ]
    )


def _build_autoresearch_skill_message(
    result: AutoresearchAppendResult,
    *,
    task_id: str | None = None,
) -> str:
    from agent.skill_commands import build_explicit_skill_invocation_message

    msg = build_explicit_skill_invocation_message(
        str(result.repo_path),
        _build_autoresearch_runtime_brief(),
        task_id=task_id,
        runtime_note=_build_autoresearch_runtime_note(result),
    )
    if not msg:
        raise AutoresearchFlowError(
            "Failed to load the installed autoresearch skill after updating program.md."
        )
    return msg


def _new_autoresearch_job_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"autoresearch_{timestamp}_{uuid.uuid4().hex[:6]}"


def prepare_autoresearch_background_run(
    *,
    user_instructions: str,
    task_id: str | None = None,
    config: Optional[Mapping[str, Any]] = None,
    wall_clock_override_minutes: int | None = None,
) -> AutoresearchPreparedRun:
    result = append_autoresearch_instructions(
        user_instructions=user_instructions,
        config=config,
    )
    if wall_clock_override_minutes is not None:
        append_outer_runtime_step2_minutes(
            result.program_path, wall_clock_override_minutes
        )

    prompt_text = _build_autoresearch_skill_message(result, task_id=task_id)

    job_id = _new_autoresearch_job_id()
    job_dir = resolve_autoresearch_jobs_root() / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = job_dir / "prompt.txt"
    prompt_path.write_text(prompt_text, encoding="utf-8")
    log_path = job_dir / "run.log"

    from hermes_cli.autoresearch_wall_clock import resolve_autoresearch_wall_clock_seconds

    if wall_clock_override_minutes is not None:
        wall_clock_seconds = max(60, int(wall_clock_override_minutes) * 60)
    else:
        _prog_text = result.program_path.read_text(encoding="utf-8")
        wall_clock_seconds = resolve_autoresearch_wall_clock_seconds(_prog_text)

    return AutoresearchPreparedRun(
        repo_path=result.repo_path,
        program_path=result.program_path,
        prompt_text=prompt_text,
        job_id=job_id,
        job_dir=job_dir,
        prompt_path=prompt_path,
        log_path=log_path,
        wall_clock_seconds=wall_clock_seconds,
        wall_clock_override_minutes=wall_clock_override_minutes,
    )


def build_autoresearch_worker_command(
    prompt_path: Path,
    *,
    python_executable: str,
) -> str:
    return " ".join(
        [
            shlex.quote(python_executable),
            "-u",
            "-m",
            "hermes_cli.autoresearch_background",
            "--prompt-file",
            shlex.quote(str(prompt_path)),
        ]
    )


def append_autoresearch_instructions(
    user_instructions: str,
    config: Optional[Mapping[str, Any]] = None,
) -> AutoresearchAppendResult:
    repo_path = resolve_autoresearch_repo_path(config)
    program_path = resolve_autoresearch_program_path(config)

    if not repo_path.exists():
        raise AutoresearchFlowError(
            f"Autoresearch repo not found at `{_expand_path(repo_path)}`."
        )

    existing = ""
    if program_path.exists():
        existing = program_path.read_text(encoding="utf-8")
    else:
        program_path.parent.mkdir(parents=True, exist_ok=True)
        existing = "# autoresearch\n"

    block = _build_managed_block(user_instructions)
    prefix = existing.rstrip()
    new_text = f"{prefix}\n\n{block}" if prefix else block
    program_path.write_text(new_text, encoding="utf-8")
    return AutoresearchAppendResult(repo_path=repo_path, program_path=program_path)


def append_and_build_autoresearch_skill_message(
    *,
    user_instructions: str,
    task_id: str | None = None,
    config: Optional[Mapping[str, Any]] = None,
) -> tuple[AutoresearchAppendResult, str]:
    prepared = prepare_autoresearch_background_run(
        user_instructions=user_instructions,
        task_id=task_id,
        config=config,
    )
    return (
        AutoresearchAppendResult(
            repo_path=prepared.repo_path,
            program_path=prepared.program_path,
        ),
        prepared.prompt_text,
    )
