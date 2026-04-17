"""Parse outer runtime from autoresearch program.md and resolve wall-clock seconds.

Default matches docs/hermes-autoresearch-one-step.md: 600 minutes when unspecified.
"""

from __future__ import annotations

import re
from typing import Optional

# docs/hermes-autoresearch-one-step.md — "If no total outer runtime is specified,
# default to 600 minutes total for the whole autoresearch loop"
DEFAULT_OUTER_RUNTIME_SECONDS = 600 * 60

# Safety cap (7 days) to catch absurd values from misparsed text
_MAX_WALL_SECONDS = 7 * 24 * 3600

_BLOCK_RE = re.compile(
    r"<!--\s*HERMES_AUTORESEARCH_INSTRUCTIONS_START[^>]*-->(.*?)<!--\s*HERMES_AUTORESEARCH_INSTRUCTIONS_END\s*-->",
    re.DOTALL | re.IGNORECASE,
)

# Prefer phrases that indicate the overall loop budget (not train.py internals)
_PRIORITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?i)(?:total\s+)?outer\s+runtime[^\n]{0,240}?(\d+(?:\.\d+)?)\s*(hours?|hrs?|h\b)"
    ),
    re.compile(
        r"(?i)(?:total\s+)?outer\s+runtime[^\n]{0,240}?(\d+(?:\.\d+)?)\s*(minutes?|mins?|min\b)"
    ),
    re.compile(
        r"(?i)wall[-\s]?clock(?:\s+budget)?[^\n]{0,120}?(\d+(?:\.\d+)?)\s*(hours?|hrs?|h\b)"
    ),
    re.compile(
        r"(?i)wall[-\s]?clock(?:\s+budget)?[^\n]{0,120}?(\d+(?:\.\d+)?)\s*(minutes?|mins?|min\b)"
    ),
]

_FALLBACK_HOURS = re.compile(
    r"(?i)\b(\d+(?:\.\d+)?)\s*(hours?|hrs?)\b"
)
_FALLBACK_MINUTES = re.compile(
    r"(?i)\b(\d+(?:\.\d+)?)\s*(minutes?|mins?|min)\b"
)


def _unit_to_seconds(num: float, unit: str) -> int:
    u = unit.lower().strip()
    if u in ("h", "hr", "hrs", "hour", "hours"):
        return int(round(num * 3600))
    if u in ("m", "min", "mins", "minute", "minutes"):
        return int(round(num * 60))
    return int(round(num * 60))


def extract_newest_autoresearch_block(src: str) -> str:
    """Return text inside the newest managed HTML block, or full ``src``."""
    matches = list(_BLOCK_RE.finditer(src or ""))
    if not matches:
        return src or ""
    return matches[-1].group(1)


def parse_outer_runtime_seconds_from_text(text: str) -> Optional[int]:
    """Return explicit seconds if the brief names an outer runtime; else ``None``."""
    blob = (text or "").strip()
    if not blob:
        return None

    for rx in _PRIORITY_PATTERNS:
        m = rx.search(blob)
        if m:
            try:
                n = float(m.group(1))
                sec = _unit_to_seconds(n, m.group(2))
                if 1 <= sec <= _MAX_WALL_SECONDS:
                    return sec
            except (ValueError, IndexError):
                continue

    # Fallback: first "N hours" / "N minutes" in the block (user often writes "10 hours")
    mh = _FALLBACK_HOURS.search(blob)
    mm = _FALLBACK_MINUTES.search(blob)
    candidates: list[tuple[int, int]] = []  # (position, seconds)
    if mh:
        try:
            sec = _unit_to_seconds(float(mh.group(1)), mh.group(2))
            if 1 <= sec <= _MAX_WALL_SECONDS:
                candidates.append((mh.start(), sec))
        except (ValueError, IndexError):
            pass
    if mm:
        try:
            sec = _unit_to_seconds(float(mm.group(1)), mm.group(2))
            if 1 <= sec <= _MAX_WALL_SECONDS:
                candidates.append((mm.start(), sec))
        except (ValueError, IndexError):
            pass
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    return None


def resolve_autoresearch_wall_clock_seconds(program_text: str) -> int:
    """Wall-clock upper bound: explicit parse from ``program_text`` or doc default."""
    block = extract_newest_autoresearch_block(program_text)
    parsed = parse_outer_runtime_seconds_from_text(block)
    if parsed is not None:
        return parsed
    return DEFAULT_OUTER_RUNTIME_SECONDS
