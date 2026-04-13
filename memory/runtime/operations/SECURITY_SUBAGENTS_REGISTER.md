# Security sub-agents register (REM-006)

> **Status:** Registry + **in-repo role prompts** + optional **Hermes profiles** (`security-*` in `scripts/core/org_agent_profiles_manifest.yaml`). Roles are **delegated subagents** via `delegate_task(..., hermes_profile=…)` unless the operator chooses long-lived sessions.
> Canonical phase list: `policies/core/unified-deployment-and-security.md` (Phase 4) and `policies/core/agentic-company-deployment-pack.md` (Phase 3).

**AG-ID numbering:** `AG-005` is reserved for the **Project Lead** (`agentic-company`). Nine security foundation roles use `AG-004` and `AG-006`–`AG-013`.

| AG-ID | Hermes profile | Role | Unified doc § | Policy / prompt anchor |
|-------|----------------|------|---------------|-------------------------|
| AG-004 | `security-preflight` | Startup Preflight Security Agent | Phase 4 #4 | `canonical-ai-agent-security-policy.md` + `role-prompts/security-foundation-agents-role-prompts.md` § AG-004 |
| AG-006 | `security-drift` | Continuous Drift and Monitoring Agent | Phase 4 #5 | same file § AG-006 |
| AG-007 | `security-filesystem` | Filesystem and Execution Security Agent | Phase 4 #6 | same file § AG-007 |
| AG-008 | `security-browser` | Browser and Web Security Agent | Phase 4 #7 | same file § AG-008 |
| AG-009 | `security-integration` | Integration and Identity Security Agent | Phase 4 #8 | same file § AG-009 + allowlists / `gateway/run.py` |
| AG-010 | `security-prompt-memory` | Prompt Injection and Memory Defense Agent | Phase 4 #9 | same file § AG-010 |
| AG-011 | `security-exfiltration` | Outbound Exfiltration Guard Agent | Phase 4 #10 | same file § AG-011 |
| AG-012 | `security-supply-chain` | Patch, Dependency, and Supply-Chain Security Agent | Phase 4 #11 | same file § AG-012 + `SKILL_INVENTORY_REGISTER.md` |
| AG-013 | `security-incident` | Incident Response Agent | Phase 4 #12 | same file § AG-013 + `INCIDENT_REGISTER.md`, `SECURITY_ALERT_REGISTER.md` |

## Instantiation checklist (operator)

1. Run `./venv/bin/python scripts/core/bootstrap_org_agent_profiles.py` (chief source profile must exist, e.g. `chief-orchestrator`).
2. Map tool/channel constraints via **profile config** (manifest), env (e.g. allowlists), and `hermes_token_governance.runtime.yaml` per `agent/token_governance_runtime.py`.
3. Chief delegates with **`hermes_profile`** per `CHIEF_ORCHESTRATION_PLAYBOOK.md`.

## Automation note

- Scheduled drift / preflight jobs remain **operator-defined** (cron on the relevant profile); core does not auto-spawn nine OS processes.
