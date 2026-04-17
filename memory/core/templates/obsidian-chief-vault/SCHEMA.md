# Wiki schema — chief-orchestrator Obsidian vault

This file is the **control plane** for how Hermes (and you) maintain this vault. Co-evolve it as workflows mature.

## Purpose

Implement the **three-layer pattern**:

1. **Raw sources** — `raw/workspace/` mirrors `${HERMES_HOME}/workspace/`. Immutable from the wiki process: refresh only via `sync_chief_workspace_to_obsidian_vault.sh` (rsync). Agents read sources here when integrating “what the workspace actually contains.”

2. **Wiki** — `wiki/` holds LLM-authored Markdown: entity pages, topic notes, synthesis, comparisons. Prefer wikilinks `[[Page Title]]` where helpful. Frontmatter is optional; if used, YAML with `date`, `tags`, `source` is enough for Dataview later.

3. **Schema** — this document plus `README.md`: structure, tone, and **operations** below.

## Hermes memory stack (how this fits)

| Mechanism | Role |
|-----------|------|
| `${HERMES_HOME}/memories/MEMORY.md` / `USER.md` | Builtin §-delimited curated memory (session snapshot). |
| `${HERMES_HOME}/workspace/memory/` | Root anchors and routing (AGENTS, INDEX, governance trees). |
| **This vault** | Obsidian-friendly mirror + compounding wiki for browsing and long-horizon synthesis. |
| **Mem0** (optional) | If `memory.provider` / Mem0 is enabled and keys are set, semantic long-term memory elsewhere — **not** duplicated here automatically; link or summarize in wiki when relevant. |

## Operations

### Ingest (new or updated sources)

After syncing raw mirror, the agent should:

- Read new/changed files under `raw/workspace/` (or targeted paths).
- Update `wiki/` pages: summaries, entities, contradictions, cross-links.
- Update `index.md` (catalog) and append `log.md` (see below).

### Query

- Prefer consulting `index.md` then drilling into `wiki/` and cited `raw/` paths.
- Answers that should persist → new or updated pages under `wiki/`, then `index.md` + `log.md`.

### Lint (periodical)

- Orphan wiki pages, stale claims vs `raw/`, missing links, contradictions — file findings in `wiki/` or append `log.md` with a lint section.

## Index and log (required files)

- **`index.md`** — Content catalog: wiki pages with one-line summaries and categories (entities, concepts, sources, meta). Updated on substantive ingests.
- **`log.md`** — Append-only timeline. Suggested line shape: `## [YYYY-MM-DD] ingest | <title>` or `## [YYYY-MM-DD] query | <topic>` so `grep '^## \\[' log.md` works.

## Paths (fill for this host)

- **HERMES_HOME**: `~/.hermes/profiles/chief-orchestrator`
- **Workspace**: `HERMES_HOME/workspace`
- **This vault**: `HERMES_HOME/obsidian-vault`

## Conventions

- ASCII filenames preferred; spaces OK inside wiki titles for Obsidian.
- Do not edit files under `raw/workspace/` except by re-running the sync script (they are overwritten on sync).
- Large binaries: if workspace grows huge, consider expanding rsync excludes in the sync script rather than bloating git.
