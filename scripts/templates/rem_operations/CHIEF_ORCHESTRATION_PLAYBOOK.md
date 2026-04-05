# Chief orchestration playbook (operator)

Use this with the **chief-orchestrator** profile as the primary interactive + gateway operator.

## 1. Org-scoped delegation (`delegate_task`)

- For a **named role** (security sub-agent, director, HR, project lead), call `delegate_task` with **`hermes_profile`** set to the profile name from `scripts/org_agent_profiles_manifest.yaml` (after bootstrap).
- **Single task only** when using `hermes_profile` (no multi-item `tasks[]`). Parallel batch delegation stays on the chief profile without `hermes_profile`.
- Create or refresh profiles: `./venv/bin/python scripts/bootstrap_org_agent_profiles.py` (add `--refresh-config` to merge toolsets / `agent.max_turns` from the manifest).
- Remove a role: `hermes profile delete <name>`, remove or comment the entry in the manifest, and stop referencing that `hermes_profile` in playbooks.

## 2. Messaging (Slack and other surfaces)

- **One gateway process** uses **one bot token** per Hermes profile. The chief profile gateway can serve **multiple channels** where the app is invited, constrained by **`SLACK_ALLOWED_CHANNELS`** / **`SLACK_ALLOWED_WORKSPACE_TEAMS`** (and analogous vars for other platforms) per policy.
- **Directors and specialists** are normally **delegated subagents** under the chief, not separate long-lived OS processes. If a role must have its **own** bot identity, create a **separate profile + gateway** (separate token) and document the token lock / allowlist split.
- Materialize workspace registers: `./scripts/materialize_rem_operations.sh` with `HERMES_HOME` set to the chief (or target) profile.

## 3. Pipeline activation

- Functional directors are **ACTIVE** in the register for org testing; the chief should **delegate** department-level work to `fd-*` profiles when policy calls for it.
- Security rows map to `ag-sec-*` profiles and in-repo role prompt bundle `policies/core/governance/role-prompts/security-foundation-agents-role-prompts.md` (sections AG-004, AG-006–AG-013).

## 4. HR / org structure changes

- Proposals for **new or redundant** agents: follow `ORG_AGENT_ESCALATION_PLAYBOOK.md` (escalation chain → HR → chief decision). Automation here is **policy + scripts**, not a silent background loop.
