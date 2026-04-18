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
    include_state: bool = False,
    include_skills: bool = False,
    include_bootstrap: bool = False,
    include_routing_indexes: bool = False,
    include_promotion: bool = False,
    include_observability: bool = False,
    include_semantic: bool = False,
    include_cases: bool = False,
    include_hazards: bool = False,
    include_prospective: bool = False,
    include_social_roles: bool = False,
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

    # Optional deep retrieval slices, planned per-turn.
    if include_state:
        state_file = mem_root / "STATE.md"
        if state_file.is_file():
            stxt = _read_text(state_file, max_chars=1800)
            if stxt:
                parts.append(f"## STATE.md (on-demand)\n\n{stxt}")

    if include_skills:
        skills_idx = mem_root / "SKILLS.md"
        if skills_idx.is_file():
            sktxt = _read_text(skills_idx, max_chars=1800)
            if sktxt:
                parts.append(f"## SKILLS.md (on-demand)\n\n{sktxt}")

    if include_bootstrap:
        bootstrap = mem_root / "BOOTSTRAP.md"
        if bootstrap.is_file():
            btxt = _read_text(bootstrap, max_chars=1800)
            if btxt:
                parts.append(f"## BOOTSTRAP.md (on-demand)\n\n{btxt}")

    if include_routing_indexes:
        for rel in ("indexes/retrieval-map.md", "indexes/memory-catalog.md"):
            p = mem_root / rel
            if p.is_file():
                txt = _read_text(p, max_chars=2200)
                if txt:
                    parts.append(f"## {rel} (on-demand)\n\n{txt}")

    if include_promotion:
        for rel in (
            "constitution/PROMOTION.md",
            "indexes/promotion-map.md",
        ):
            p = mem_root / rel
            if p.is_file():
                txt = _read_text(p, max_chars=2200)
                if txt:
                    parts.append(f"## {rel} (on-demand)\n\n{txt}")

    if include_observability:
        obs_manifest = mem_root / "observability" / "MANIFEST.md"
        if obs_manifest.is_file():
            otxt = _read_text(obs_manifest, max_chars=1800)
            if otxt:
                parts.append(f"## observability/MANIFEST.md (on-demand)\n\n{otxt}")

    if include_semantic:
        sem_refs = mem_root / "semantic-graph" / "knowledge" / "references"
        if sem_refs.is_dir():
            for rel in ("memory.md", "concept-index.md"):
                p = sem_refs / rel
                if p.is_file():
                    txt = _read_text(p, max_chars=2200)
                    if txt:
                        parts.append(f"## semantic-graph/knowledge/references/{rel} (on-demand)\n\n{txt}")

    if include_cases:
        for rel in (
            "case-memory/README.md",
            "case-memory/operations/remediation-patterns.md",
        ):
            p = mem_root / rel
            if p.is_file():
                txt = _read_text(p, max_chars=2000)
                if txt:
                    parts.append(f"## {rel} (on-demand)\n\n{txt}")

    if include_hazards:
        for rel in (
            "hazard-memory/operations/README.md",
            "hazard-memory/operations/anti-patterns.md",
        ):
            p = mem_root / rel
            if p.is_file():
                txt = _read_text(p, max_chars=2000)
                if txt:
                    parts.append(f"## {rel} (on-demand)\n\n{txt}")

    if include_prospective:
        for rel in (
            "prospective-memory/operations/README.md",
            "prospective-memory/operations/open-loops.md",
        ):
            p = mem_root / rel
            if p.is_file():
                txt = _read_text(p, max_chars=2000)
                if txt:
                    parts.append(f"## {rel} (on-demand)\n\n{txt}")

    if include_social_roles:
        srm = mem_root / "social-role-memory"
        if srm.is_dir():
            for rel in ("README.md", "registers/operator-profile.md"):
                p = srm / rel
                if p.is_file():
                    txt = _read_text(p, max_chars=2000)
                    if txt:
                        parts.append(f"## social-role-memory/{rel} (on-demand)\n\n{txt}")

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

