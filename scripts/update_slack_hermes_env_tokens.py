#!/usr/bin/env python3
"""Interactively set SLACK_BOT_TOKEN and SLACK_APP_TOKEN in Hermes ~/.env (masked input).

Respects HERMES_HOME / active profile via hermes_constants.get_hermes_home().
Does not print token values. Writes atomically; optional backup of the previous file.

Usage (from repo, with venv):
  ./venv/bin/python scripts/update_slack_hermes_env_tokens.py

  HERMES_HOME=/path/to/profile ./venv/bin/python scripts/update_slack_hermes_env_tokens.py
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Repo root on sys.path so hermes_constants resolves when run as a script
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hermes_constants import display_hermes_home, get_hermes_home  # noqa: E402

_KEYS = ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN")

# Match KEY=value, optional leading whitespace, optional export
_LINE_RE = re.compile(
    r"^(\s*(?:export\s+)?)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$"
)


def _parse_env_line(line: str) -> Optional[Tuple[str, str]]:
    """Return (key, rest_after_equals) if line is an assignment, else None."""
    s = line.rstrip("\n\r")
    if not s.strip() or s.lstrip().startswith("#"):
        return None
    m = _LINE_RE.match(s)
    if not m:
        return None
    return m.group(2), m.group(3)


def _format_assignment(key: str, value: str) -> str:
    """Single line KEY=value; quote if needed for POSIX shells."""
    if not value:
        return f"{key}="
    safe = value
    if re.search(r"[\s#'\"\\$`!]", safe):
        esc = safe.replace("'", "'\"'\"'")
        return f"{key}='{esc}'"
    return f"{key}={safe}"


def apply_env_updates(
    lines: List[str],
    updates: Dict[str, str],
) -> List[str]:
    """Return new lines with keys in *updates* replaced or appended."""
    seen = {k: False for k in updates}
    out: List[str] = []
    for line in lines:
        parsed = _parse_env_line(line)
        if parsed:
            key, _ = parsed
            if key in updates:
                out.append(_format_assignment(key, updates[key]) + "\n")
                seen[key] = True
                continue
        out.append(line)
    for key in _KEYS:
        if key in updates and not seen[key]:
            out.append(_format_assignment(key, updates[key]) + "\n")
    return out


def atomic_write(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = "".join(lines)
    fd, tmp = tempfile.mkstemp(
        prefix=".env.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _file_has_key(path: Path, key: str) -> bool:
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(re.search(r"^[\s]*(?:export\s+)?" + re.escape(key) + r"\s*=", txt, re.MULTILINE))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Set SLACK_BOT_TOKEN / SLACK_APP_TOKEN in Hermes .env (masked prompts)."
    )
    ap.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Override path (default: HERMES_HOME/.env)",
    )
    ap.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not write a .env.bak.<timestamp> backup before replacing.",
    )
    ap.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip final confirmation prompt.",
    )
    args = ap.parse_args()

    env_path = args.env_file
    if env_path is None:
        env_path = get_hermes_home() / ".env"

    display = display_hermes_home()
    print(f"Hermes env file: {env_path}")
    print(f"(display path: {display}/.env)\n")

    updates: Dict[str, str] = {}

    print("Paste each token when prompted (input hidden). Leave empty to keep existing value.\n")
    for key in _KEYS:
        v = getpass.getpass(f"{key}: ").strip()
        if v:
            updates[key] = v
        elif env_path.is_file() and _file_has_key(env_path, key):
            print(f"  (keeping existing {key})")
        else:
            print(
                f"Error: {key} is required (no existing line in {env_path}).",
                file=sys.stderr,
            )
            return 1

    if not updates:
        print("Nothing to change.")
        return 0

    if env_path.is_file():
        try:
            original_lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines(
                keepends=True
            )
        except OSError as e:
            print(f"Cannot read {env_path}: {e}", file=sys.stderr)
            return 1
    else:
        original_lines = []

    # Merge: only apply keys user supplied
    new_lines = apply_env_updates(original_lines, updates)

    if new_lines == original_lines:
        print("No changes (values unchanged).")
        return 0

    if not args.yes:
        ans = input(f"\nWrite {len(merged)} key(s) to {env_path}? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            return 1

    if env_path.is_file() and not args.no_backup:
        bak = env_path.with_suffix(env_path.suffix + ".bak")
        try:
            shutil.copy2(env_path, bak)
            print(f"Backup: {bak}")
        except OSError as e:
            print(f"Warning: could not create backup: {e}", file=sys.stderr)

    try:
        atomic_write(env_path, new_lines)
    except OSError as e:
        print(f"Cannot write {env_path}: {e}", file=sys.stderr)
        return 1

    print("Done. Restart the gateway (or reload env) so the new tokens take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
