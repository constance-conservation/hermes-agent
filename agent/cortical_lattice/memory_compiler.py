from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import os
import tempfile


@dataclass(frozen=True)
class CorticalEphemeralPack:
    """Per-turn ephemeral context injected at API-call time (not cached)."""

    content: str


def _read_text(path: Path, *, max_chars: int = 6000) -> str:
    try:
        txt = path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""
    if not txt:
        return ""
    if len(txt) <= max_chars:
        return txt
    head = txt[: int(max_chars * 0.75)]
    tail = txt[-int(max_chars * 0.25) :]
    return head + "\n\n[...truncated...]\n\n" + tail


def _workspace_memory_root(hermes_home: Path) -> Path:
    return hermes_home / "workspace" / "memory"


def compile_ephemeral_pack(
    *,
    hermes_home: Path,
    user_message: str,
    include_infrastructure: bool = False,
) -> CorticalEphemeralPack:
    """Build the minimal per-turn context pack.

    This is **ephemeral** by design so it does not break Hermes' session-level
    system-prompt caching and prefix caching.
    """
    mem_root = _workspace_memory_root(hermes_home)
    if not mem_root.is_dir():
        return CorticalEphemeralPack(content="")

    parts: list[str] = []

    # Working memory (typed pages) — small, per-turn continuity.
    wm = mem_root / "working-memory"
    if wm.is_dir():
        for rel in (
            "current-objective.md",
            "active-blockers.md",
            "pending-decisions.md",
            "next-actions.md",
            "active-files.md",
            "hypotheses.md",
        ):
            p = wm / rel
            if p.is_file():
                content = _read_text(p, max_chars=2000)
                if content:
                    parts.append(f"## working-memory/{rel}\n\n{content}")

    # External memory routing reminder (small) — helps per-turn tool selection.
    routing = mem_root / "constitution" / "memory-routing.md"
    if routing.is_file():
        rtxt = _read_text(routing, max_chars=2500)
        if rtxt:
            parts.append(f"## constitution/memory-routing.md\n\n{rtxt}")

    # Optional: include INFRASTRUCTURE.md only when explicitly requested.
    if include_infrastructure:
        infra = mem_root / "INFRASTRUCTURE.md"
        if infra.is_file():
            parts.append(f"## INFRASTRUCTURE.md (on-demand)\n\n{_read_text(infra, max_chars=8000)}")

    content = "\n\n".join(parts).strip()
    return CorticalEphemeralPack(content=content)


def write_context_pack_file(*, hermes_home: Path, pack: CorticalEphemeralPack) -> Optional[Path]:
    """Persist the current turn's pack for inspection/debugging.

    This file is **not** loaded as part of the cached system prompt; it is a mirror.
    """
    mem_root = _workspace_memory_root(hermes_home)
    wm = mem_root / "working-memory"
    if not wm.is_dir():
        return None
    out = wm / "context-pack.md"
    try:
        payload = (pack.content.strip() + "\n") if pack.content.strip() else ""
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(out.parent)) as tf:
            tf.write(payload)
            tmp_name = tf.name
        os.replace(tmp_name, out)
        return out
    except Exception:
        return None

