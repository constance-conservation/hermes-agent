# Skill inventory register (W004)

> **Owner:** AG-012 (supply-chain) with chief oversight.  
> **Purpose:** Track **installed skills** with **source**, **version**, and **effective permissions** (filesystem, network, secrets). Aligns with security remediation **W004**.

## Inventory

| Skill name (folder) | Source (URL or path) | Version / commit | Filesystem scope | Network | Secrets / env | Last reviewed |
|---------------------|----------------------|------------------|------------------|---------|---------------|---------------|
| *(template row)* | `~/.hermes/skills/...` or git URL | | read-only / write paths | yes/no | e.g. `API_KEY` | YYYY-MM-DD |
| | | | | | | |

## Rules

1. **No shadow copies:** one canonical path per skill under `HERMES_HOME/skills/` (or documented override).
2. **Upgrade discipline:** record version bump and smoke test in `GOVERNANCE_CHANGELOG.md` or project notes.
3. **High-risk patterns:** skills that run shell or call external APIs get **quarterly** review.

## Hygiene

- Cross-link new skills from `ORG_REGISTRY` or project README when a skill is org-mandatory.
- Remove rows when a skill is deleted; archive evidence path if required by policy.
