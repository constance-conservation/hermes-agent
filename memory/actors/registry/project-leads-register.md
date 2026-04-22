# Project Leads register (REM-009)

| AG-ID | Project slug | Status | Policy | Prompt |
|-------|--------------|--------|--------|--------|
| **AG-005** | `agentic-company` | **ACTIVE (registry)** | `workspace/memory/governance/source/standards/project-lead-policy-template.md` | `workspace/memory/governance/source/role-prompts/project-lead-template.md` — Hermes profile **`project-lead-agentic-company`** (manifest bootstrap) |
| **AG-014** | `moonshot-engine` | **ACTIVE (registry)** | `workspace/memory/governance/source/standards/project-lead-policy-template.md` | `workspace/memory/governance/source/role-prompts/project-lead-template.md` — Hermes profile **`project-lead-moonshot-engine`** (manifest bootstrap) |

## Project brief (agentic-company)

- **Scope:** Operate the in-repo **agentic company** deployment: policies under `HERMES_HOME/policies`, workspace under `HERMES_HOME/workspace`, Hermes gateway + chief-orchestrator profile, remediation items (REM-*), and alignment with `policies/core/deployment-handoff.md`.
- **Success:** Governance pack materialized, token governance runtime active, messaging allowlists set, watchdog healthy, no drift vs canonical `policies/` without recorded exception.
- **Escalation:** Chief Orchestrator for cross-project strategy; IT/Security Director (when activated) for trust-boundary changes.

## Project brief (moonshot-engine)

- **Scope:** Operate the **Moonshot Engine** project lane — crypto trading + on-chain integrations (Alchemy, Binance, Coinbase, Kraken) and social signal ingestion (X/Twitter, Messari, CoinMarketCap, FreeCryptoAPI, Base RPC). Live trading is gated by `ARM_LIVE_TRADING` in the profile `.env`.
- **Success:** Credentials scoped to the project-lead profile (not chief), project folder materialised on droplet under chief-orchestrator's workspace, bootstrap-created Hermes profile available for `delegate_task(..., hermes_profile="project-lead-moonshot-engine")`.
- **Escalation:** Chief Orchestrator for cross-project strategy; IT/Security Director for credential rotation / trust-boundary changes (live exchange keys are sensitive).

## Paths

- agentic-company workspace folder: `memory/knowledge/projects/agentic-company/` (see `README.md` there).
- moonshot-engine workspace folder (droplet-only): `~/.hermes/profiles/chief-orchestrator/workspace/memory/semantic-graph/knowledge/projects/moonshot-engine/` (chief-orchestrator runtime; not mirrored in repo).

## Delegation

- Bootstrap profile: `./venv/bin/python scripts/bootstrap_org_agent_profiles.py` → **`project-lead-agentic-company`**, **`project-lead-moonshot-engine`**. Chief calls `delegate_task(..., hermes_profile="project-lead-<slug>")` for project-lane work.

## Operator-owned

- Irreversible production changes (SSH, firewall, secrets rotation) remain human-owned unless policy explicitly delegates.
