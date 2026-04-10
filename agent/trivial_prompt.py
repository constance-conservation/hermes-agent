"""Heuristics for ultra-short / acknowledgement prompts (cost-aware routing)."""

from __future__ import annotations

import re
from typing import Optional

# One-line acknowledgements — do not force OPM tier E/F or expensive clamps.
_TRIVIAL_ONE_WORD = frozenset(
    {
        "ping",
        "pong",
        "ok",
        "k",
        "hi",
        "hello",
        "hey",
        "thanks",
        "thx",
        "ty",
        "yes",
        "no",
        "y",
        "n",
        "bye",
        "test",
    }
)

_TRIVIAL_PHRASE = frozenset({"thank you"})


def trivial_message_skips_opm_tier_uplift(user_message: Optional[str]) -> bool:
    """True for very short prompts that should stay on low tiers (A/B/C) under OPM."""
    t = (user_message or "").strip()
    if not t:
        return True
    if "\n" in t or "\r" in t:
        return False
    if len(t) > 96:
        return False
    tl = t.lower().strip()
    if tl in _TRIVIAL_PHRASE:
        return True
    parts = re.split(r"\s+", tl)
    if len(parts) == 1 and parts[0] in _TRIVIAL_ONE_WORD:
        return True
    return False
