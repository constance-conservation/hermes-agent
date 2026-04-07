# AGENT_CREATION_WORKFLOW.md - Governed agent creation (three tiers)

This workspace-local file summarizes governed agent creation in the agentic-company model and serves as a practical operating reference.

If anything here diverges from the unified runbook, the unified runbook wins. Update this file via repo/materialization workflows rather than ad hoc runtime edits.

## Three tiers of creation

| Tier | What it means | When to use | Registration / tooling |
| --- | --- | --- | --- |
| 1 - Logical agent (same Hermes runtime) | A role enacted inside one profile: prompts, delegate-tool subagents, narrow tasks. | Extra help without new credentials, gateway, or disk isolation. | Update org/lifecycle registers when the role is a named governed unit; otherwise document in project charter or archival memory. |
| 2 - New Hermes profile (separate runtime) | A new ~/.hermes/profiles/<slug>/ with its own config, secrets, sessions, and optional gateway. | Isolation of credentials, messaging identity, or state. | Run hermes profile create <slug> from the repo venv and record slug-to-role mapping in org/lifecycle registers. |
| 3 - Full org spawn (runbook order) | Chief-directed creation of directors, security agents, leads, and workers in unified deployment order. | Greenfield expansion after security baseline. | Follow unified spawn order; every active governed agent is registered before activation. |

## Mandatory sequence (all tiers that change org truth)

Applies whenever a new named agent appears on the org chart or lifecycle registers.

1. Define: name, role title, department, supervisor, project (if any), mission, scope/non-scope, permissions, success metrics, lifecycle = Proposed. Security-sensitive roles also define trust level, attack surfaces, approval gates, and WARNING/CRITICAL/safe-mode implications.
2. Register: ORG_REGISTRY.md + AGENT_LIFECYCLE_REGISTER.md (and security registers when applicable). No agent becomes Active before registration.
3. Instantiate: minimal shell only (identity, supervisor, department, project, mission, scope, permissions).
4. Startup bundle: identity, scope, boundaries, rules, and current objective.
5. First task: assign one concrete mission; avoid overloading startup with backlog.

## Hermes operator quick reference

- Same runtime, new agent: usually tier 1 (prompts + delegate_task); register only when the role is durable and governed.
- Separate bot/secrets/home: tier 2 profile; never fake isolation using folders in one profile.
- Re-read canonical runbooks before spawning governed roles.

## Canonical sources in this memory tree

- ../../../core/init/unified-deployment-and-security.md
- ../../../core/init/deployment-handoff.md
- ../../../governance/source/standards/agent-lifecycle-org-hygiene-policy.md
- ../../../governance/source/artifacts-and-archival-memory.md
- ../../../runtime/tasks/procedures/agent-creation-and-lifecycle.md

## Rule

No named governed agent is activated before registration and lifecycle assignment.
