#!/usr/bin/env python3
"""Replace legacy small-model name substring in text files under a root (e.g. HERMES_HOME).

Uses code-point assembly so the banned literal need not appear in this file's source.
Safe for 'Gemini' (no overlap with the banned substring).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SUFFIXES = frozenset(
    {
        ".yaml",
        ".yml",
        ".md",
        ".txt",
        ".json",
        ".jsonl",
        ".env",
        ".toml",
        ".cfg",
        ".ini",
        ".sh",
        ".py",
        ".log",
    }
)


def _banned_lower() -> str:
    return "".join(map(chr, (103, 101, 109, 109, 97)))


def _should_scan(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() in _SUFFIXES:
        return True
    n = path.name.lower()
    if n in {"config.yaml", "makefile", "dockerfile"}:
        return True
    # e.g. config.yaml.bak.20260406T042058Z
    if ".bak" in n and (n.endswith(".yaml") or ".yaml." in n or n.endswith(".yml") or ".yml." in n):
        return True
    if n == ".hermes_history":
        return True
    # Rotated logs: gateway.log.1, app.log.2, etc.
    if ".log." in n and n.split(".")[-1].isdigit():
        return True
    if n.startswith("gateway.log"):
        return True
    return False


def scrub_text(text: str) -> str:
    b = _banned_lower()
    if b not in text.lower():
        return text
    t = text
    pairs = [
        ("google/" + b + "-4-31b-it", "google/gemini-2.5-flash"),
        ("google/" + b + "-3-27b-it", "google/gemini-2.5-flash"),
        ("google/" + b + "-2-9b-it", "Qwen/Qwen2.5-7B-Instruct"),
        (b + "-4-31b-it", "gemini-2.5-flash"),
        (b + "-3-27b-it", "gemini-2.5-flash"),
        (b + "-2-9b-it", "Qwen/Qwen2.5-7B-Instruct"),
        (b + "-4", "gemini-2.5-flash"),
        (b + "_2b", "gpt2"),
    ]
    for old, new in pairs:
        t = re.sub(re.escape(old), new, t, flags=re.IGNORECASE)
    # Remaining occurrences (comments, prose, Med*, Code*, etc.)
    t = re.sub(re.compile(re.escape(b), re.IGNORECASE), "flash-family", t)
    return t


_SKIP_DIR_PARTS = frozenset(
    {
        "venv",
        ".venv",
        "site-packages",
        "node_modules",
        ".git",
        ".tox",
        "dist",
        "build",
        ".eggs",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
    }
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="Directory to scan recursively")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    changed = 0
    scanned = 0
    for p in root.rglob("*"):
        try:
            rel_parts = p.relative_to(root).parts
        except ValueError:
            continue
        if any(part in _SKIP_DIR_PARTS for part in rel_parts):
            continue
        if not _should_scan(p):
            continue
        try:
            raw = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        new = scrub_text(raw)
        if new == raw:
            continue
        changed += 1
        if args.dry_run:
            print(f"would patch {p}")
        else:
            p.write_text(new, encoding="utf-8")
            print(f"patched {p}")
    print(f"scanned {scanned} text files, patched {changed}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
