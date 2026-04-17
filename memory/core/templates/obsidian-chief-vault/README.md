# Chief orchestrator — Obsidian vault

This folder is the **Obsidian-facing layer** for the `chief-orchestrator` Hermes profile. It sits next to `workspace/` as a compounding knowledge surface: file-based, git-friendly, and optional to open in Obsidian on a workstation.

## Layers (see `SCHEMA.md`)

| Layer | Path here | Role |
|--------|-----------|------|
| **Raw mirror** | `raw/workspace/` | Rsync’d copy of `${HERMES_HOME}/workspace/` — treat as read-only “sources” for ingestion. |
| **Wiki** | `wiki/` | LLM-maintained synthesis, entity pages, cross-links. Hermes owns writes here during wiki workflows. |
| **Schema** | `SCHEMA.md` | Conventions, ingest/query/lint rules, and links to Mem0 / builtin memory. |

Hermes paths: `HERMES_HOME` for this profile is `~/.hermes/profiles/chief-orchestrator` on this machine.

## Sync the raw mirror

From the Hermes repo (after `source venv/bin/activate`):

```bash
export HERMES_HOME="$HOME/.hermes/profiles/chief-orchestrator"
bash memory/core/scripts/core/sync_chief_workspace_to_obsidian_vault.sh
```

Or: `./memory/core/scripts/core/sync_chief_workspace_to_obsidian_vault.sh "$HOME/.hermes/profiles/chief-orchestrator"`

Re-run after large workspace changes so Obsidian and agents see an up-to-date mirror.
