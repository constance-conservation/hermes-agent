#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FileSpec:
    relpath: str
    content: str


def _write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _layer_guides(layer_name: str, include_promotion: bool) -> list[FileSpec]:
    guides: list[FileSpec] = [
        FileSpec(
            f"{layer_name}/MANIFEST.md",
            f"""# {layer_name}/ — MANIFEST

## Purpose
This layer is part of **Cortical Lattice Memory** under `workspace/memory/`.

## What lives here
- See `SCHEMA.md` for object shapes
- See `WHEN_TO_READ.md` and `WHEN_TO_WRITE.md` for retrieval + writeback rules
""",
        ),
        FileSpec(
            f"{layer_name}/SCHEMA.md",
            """# SCHEMA

This layer stores Markdown objects (human-readable mirrors) plus optional `*.meta.json` sidecars.

## Required axes (meta.json)
- type
- time: observed_at, valid_from, valid_to, last_used
- abstraction: trace | episode | fact | case | skill | doctrine
- agency: self | user | other-agent | org | project | environment | tool | codebase
- confidence: observed | inferred | hypothesis | contested | superseded
- utility: critical | recurring | high-value | low-value
- access_mode: pinned | hot | on-demand | cold
- scope: private | shared | org | global

## Provenance (meta.json)
- sources: file paths, tool outputs, run ids
- supersession/conflict links
""",
        ),
        FileSpec(
            f"{layer_name}/WHEN_TO_READ.md",
            """# WHEN_TO_READ

Read this layer when the task requires its memory *type* or *abstraction level* and the expected utility outweighs token cost.

Default: do **not** load this whole layer into prompts; retrieve selectively via the retrieval planner / compiler.
""",
        ),
        FileSpec(
            f"{layer_name}/WHEN_TO_WRITE.md",
            """# WHEN_TO_WRITE

Write to this layer only when information is:
- durable (survives the current task/session)
- operationally useful (prevents repeated mistakes / enables reuse)
- retrieval-worthy (likely to be needed again)

Do **not** write verbose narration. Prefer structured, minimal objects + provenance.
""",
        ),
    ]
    if include_promotion:
        guides.append(
            FileSpec(
                f"{layer_name}/PROMOTION.md",
                """# PROMOTION

Promotion ladder:
Trace → Episode → Fact → Case → Skill → Doctrine

## Rules (high-level)
- Promote only when criteria are met; keep provenance links back downward.
- Superseded items stay visible with `confidence: superseded` and a forward pointer.
""",
            )
        )
    return guides


def _root_files() -> list[FileSpec]:
    return [
        FileSpec(
            "CORTICAL_LATTICE_MEMORY.md",
            """# Cortical Lattice Memory (workspace/memory/)

## What this is
This is a **multi-layer cognitive memory system** for Hermes:

- **Control plane**: Markdown guides, manifests, schemas, routing rules
- **Data plane**: durable memory objects (Markdown mirrors + optional `*.meta.json`)
- **Compiler**: per-turn context pack (ephemeral) to avoid prompt bloat

## Minimal resident set (always small)
- Root anchors: `AGENTS.md`, `MEMORY.md`, `USER.md`, `ATTENTION.md`, `INDEX.md`
- Constitution: `constitution/CONSTITUTION.md`

## Working continuity (per turn)
- Typed working pages under `working-memory/`
- Ephemeral injection built each turn from working pages (and optional on-demand artifacts)

## Deep map
- `INFRASTRUCTURE.md` contains inventories, wiring, mapping table, and diagrams.
""",
        ),
        FileSpec(
            "INFRASTRUCTURE.md",
            """# Cortical Lattice Memory — Infrastructure

This file is the canonical **map of the brain** for `workspace/memory/`.

It is intentionally **not** always loaded by default (it can be large). Root anchors should link here.

## Contents (filled/maintained by migration + maintenance scripts)
- Current system inventory (pre-migration; absolute paths)
- New system inventory (post-migration; absolute paths)
- File-to-layer mapping table (old → new)
- Hermes wiring map (what is always loaded vs selectively retrieved)
- ASCII diagrams (system flow + file mapping)
""",
        ),
        FileSpec(
            "README.md",
            """# workspace/memory/ (Cortical Lattice Memory)

This directory is a **cognitive memory system** for Hermes (control plane + data plane), not a generic note dump.

## Always-loaded anchors (small)
- `AGENTS.md`, `MEMORY.md`, `USER.md`, `ATTENTION.md`, `INDEX.md`

## Deep map
- `INFRASTRUCTURE.md` (full inventory + wiring + diagrams)
""",
        ),
        FileSpec(
            "AGENTS.md",
            """# AGENTS.md (workspace/memory)

This is a **routing/constitution stub** for the Cortical Lattice Memory system.

## How to use this memory
- Keep always-loaded anchors tiny; do not dump deep history here.
- Use the retrieval planner + compiler to selectively pull from layers.
- When doing memory-system surgery or debugging, read `INFRASTRUCTURE.md`.
""",
        ),
        FileSpec(
            "INDEX.md",
            """# INDEX.md (workspace/memory)

## Entry points
- **Infrastructure / diagrams:** `INFRASTRUCTURE.md`
- **Constitution:** `constitution/CONSTITUTION.md`
- **Working state:** `working-memory/`
- **Episodic ledger:** `episodic-ledger/`
- **Semantic graph:** `semantic-graph/`
- **Cases:** `case-memory/`
- **Skills:** `skill-atlas/`
- **Doctrine:** `reflective-doctrine/`
- **Prospective:** `prospective-memory/`
- **Hazards:** `hazard-memory/`
- **Social/role:** `social-role-memory/`
- **Observability:** `observability/`
""",
        ),
        FileSpec(
            "MEMORY.md",
            """# MEMORY.md (workspace/memory)

Concise, always-loaded: **memory routing rules** + minimal durable invariants.

- Do not store deep project detail here.
- Prefer layered objects under `*/` plus `*.meta.json` sidecars where needed.
""",
        ),
        FileSpec(
            "USER.md",
            """# USER.md (workspace/memory)

Concise, always-loaded: stable user interaction preferences + boundaries.
Deep social/role models live in `social-role-memory/`.
""",
        ),
        FileSpec(
            "ATTENTION.md",
            """# ATTENTION.md (workspace/memory)

Always-loaded: what to prioritize when deciding what memory to retrieve/write.
""",
        ),
        FileSpec(
            "COMPASS.md",
            """# COMPASS.md (workspace/memory)

Mission + direction pointers. Keep small.
""",
        ),
        FileSpec(
            "STATE.md",
            """# STATE.md (workspace/memory)

Pointer to typed working-memory pages under `working-memory/`.
""",
        ),
        FileSpec(
            "TOOLS.md",
            """# TOOLS.md (workspace/memory)

Pointer index for memory-related tooling. Keep small; details live in layers + skills docs.
""",
        ),
        FileSpec(
            "SKILLS.md",
            """# SKILLS.md (workspace/memory)

Pointer index for the procedural skill atlas under `skill-atlas/`.
""",
        ),
        FileSpec(
            "BOOTSTRAP.md",
            """# BOOTSTRAP.md (workspace/memory)

Bootstrap pointers for initializing and migrating this memory system.
See `bootstrap/` and `INFRASTRUCTURE.md`.
""",
        ),
        FileSpec(
            "SOUL.md",
            """# SOUL.md (workspace/memory)

Identity / voice anchor. Keep small; do not include deep operating detail.
""",
        ),
    ]


def _working_memory_pages() -> list[FileSpec]:
    base = "working-memory"
    return [
        FileSpec(
            f"{base}/context-pack.md",
            """# context-pack.md

This file is written by the memory compiler each turn as the minimal resident context pack for continuity.
""",
        ),
        FileSpec(f"{base}/current-objective.md", "# current-objective\n\n- \n"),
        FileSpec(f"{base}/active-files.md", "# active-files\n\n- \n"),
        FileSpec(f"{base}/active-blockers.md", "# active-blockers\n\n- \n"),
        FileSpec(f"{base}/hypotheses.md", "# hypotheses\n\n- \n"),
        FileSpec(f"{base}/pending-decisions.md", "# pending-decisions\n\n- \n"),
        FileSpec(f"{base}/next-actions.md", "# next-actions\n\n- \n"),
    ]


def build_scaffold_specs() -> list[FileSpec]:
    layers = [
        ("constitution", True),
        ("working-memory", True),
        ("episodic-ledger", True),
        ("semantic-graph", True),
        ("case-memory", True),
        ("skill-atlas", True),
        ("reflective-doctrine", True),
        ("prospective-memory", False),
        ("hazard-memory", True),
        ("social-role-memory", False),
        ("observability", False),
        ("indexes", False),
        ("bootstrap", False),
        ("legacy-archive", False),
    ]

    specs: list[FileSpec] = []
    specs.extend(_root_files())

    for layer, promo in layers:
        specs.extend(_layer_guides(layer, include_promotion=promo))

    # Minimal canonical leaf anchors
    specs.append(
        FileSpec(
            "constitution/CONSTITUTION.md",
            """# CONSTITUTION

Pinned, always-loaded principles only:
- identity
- safety + authority boundaries
- operating loop
- memory routing rule (what goes where) — see `constitution/memory-routing.md`
""",
        )
    )
    specs.append(
        FileSpec(
            "constitution/memory-routing.md",
            """# memory-routing

## External memory routing (hybrid)

- **Mem0**: preferences, repeated procedural habits, lightweight durable “how I work” recall; also reranking/thresholded recall.
- **Zep**: entities/relations/timelines; temporally valid facts with provenance and supersession.
- **Letta**: pinned/always-visible *style* of “small constitutional blocks” (modeled here as `constitution/`), plus optional pinned block synchronization if used.
- **LangMem**: lifecycle operations (extract/update/consolidate/remove outdated) + durable local store; use for maintenance passes and consolidation.
- **LangSmith**: observability feedstock; traces/runs for episodic ledger + regression analysis.

## Default rule
Prefer the lightest memory that preserves truth and prevents repetition:

- If it’s a **fact about entities & their relationships over time** → Zep + mirror into `semantic-graph/graph-mirror/` if needed.
- If it’s a **user preference** or **repeatable procedure** → Mem0 and/or `skill-atlas/`.
- If it’s a **what happened / why** record → `episodic-ledger/` (+ LangSmith when available).
- If it’s a **negative lesson / do-not-repeat** → `hazard-memory/`.
""",
        )
    )
    specs.extend(_working_memory_pages())

    # Index stubs
    specs.append(FileSpec("indexes/memory-catalog.md", "# memory-catalog\n\n- \n"))
    specs.append(FileSpec("indexes/retrieval-map.md", "# retrieval-map\n\n- \n"))
    specs.append(FileSpec("indexes/promotion-map.md", "# promotion-map\n\n- \n"))

    # Bootstrap placeholders
    specs.append(
        FileSpec(
            "bootstrap/README.md",
            """# bootstrap/

Templates and generators for Cortical Lattice Memory objects and migrations.
""",
        )
    )

    # Legacy archive guardrail
    specs.append(
        FileSpec(
            "legacy-archive/README.md",
            """# legacy-archive/

This is a retention-only archive of legacy memory structure. Do not write new active memory here.
""",
        )
    )
    return specs


def scaffold(dest: Path) -> dict[str, int]:
    created_files = 0
    created_dirs = 0

    for spec in build_scaffold_specs():
        p = dest / spec.relpath
        _ensure_dir(p.parent)
        if _write_if_missing(p, spec.content):
            created_files += 1

    # Ensure layer dirs exist even if files already existed
    for layer in [
        "constitution",
        "working-memory",
        "episodic-ledger",
        "semantic-graph",
        "case-memory",
        "skill-atlas",
        "reflective-doctrine",
        "prospective-memory",
        "hazard-memory",
        "social-role-memory",
        "observability",
        "indexes",
        "bootstrap",
        "legacy-archive",
    ]:
        p = dest / layer
        before = p.exists()
        _ensure_dir(p)
        if not before:
            created_dirs += 1

    return {"created_files": created_files, "created_dirs": created_dirs}


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scaffold Cortical Lattice Memory tree under workspace/memory/")
    ap.add_argument(
        "--dest",
        required=True,
        help="Destination directory (usually $HERMES_HOME/workspace/memory).",
    )
    args = ap.parse_args(list(argv) if argv is not None else None)
    dest = Path(args.dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    result = scaffold(dest)
    print(f"ok created_dirs={result['created_dirs']} created_files={result['created_files']} dest={dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

