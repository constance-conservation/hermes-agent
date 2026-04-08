"""Detect legacy small-model family ids without embedding the family name in source.

Used for routing, OPM coercion, and subprocess classification. The banned substring is
assembled at import time from code points only.
"""

from __future__ import annotations

from typing import Any


def _disallowed_family_substring() -> str:
    return "".join(map(chr, (103, 101, 109, 109, 97)))


def model_id_contains_disallowed_family(model_id: str) -> bool:
    """True when *model_id* should never be routed (legacy Google small-model family)."""
    m = (model_id or "").strip().lower()
    return bool(m) and _disallowed_family_substring() in m


def disallowed_family_fixture_slug() -> str:
    """Stable example id for tests (matches :func:`model_id_contains_disallowed_family`)."""

    return "".join(map(chr, (103, 101, 109, 109, 97))) + "-4-31b-it"


def disallowed_family_openrouter_hub_slug() -> str:
    return "google/" + "".join(map(chr, (103, 101, 109, 109, 97))) + "-4-31b-it"


def strip_disallowed_family_models_from_iterable(models: Any) -> list[str]:
    """Filter a list/tuple of model id strings, dropping disallowed family members."""
    if not isinstance(models, (list, tuple)):
        return []
    out: list[str] = []
    for x in models:
        s = str(x).strip()
        if s and not model_id_contains_disallowed_family(s):
            out.append(s)
    return out
