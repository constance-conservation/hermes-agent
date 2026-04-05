# Functional Directors register (REM-007)

> **REM-007 (active pipeline test):** Directors are **ACTIVE** for delegation testing. Hermes profiles: `fd-product`, `fd-engineering`, `fd-operations`, `fd-it-security` (see `scripts/org_agent_profiles_manifest.yaml` + `scripts/bootstrap_org_agent_profiles.py`). Canonical policy slots remain in `policies/core/unified-deployment-and-security.md` Phase 6.

| Role | Hermes profile | Policy template | Prompt template | Status |
|------|----------------|-----------------|-----------------|--------|
| Product Director | `fd-product` | `policies/core/governance/standards/functional-director-policy-template.md` (tailor title) | `policies/core/governance/role-prompts/functional-director-template.md` | **ACTIVE** |
| Engineering Director | `fd-engineering` | same | same | **ACTIVE** |
| Operations Director | `fd-operations` | same | same | **ACTIVE** |
| IT / Security Director | `fd-it-security` | same | same | **ACTIVE** |

## Chief usage

- Delegate department-level coordination with `delegate_task(..., hermes_profile="fd-<lane>")` per `CHIEF_ORCHESTRATION_PLAYBOOK.md`.
- Stand down a director: remove or comment its manifest entry, `hermes profile delete fd-…`, and set status back to DORMANT in a fork of this register if needed.

## Cadence

- Hermes does not schedule director reviews unless you add **cron** or a **manual** cadence on the chief profile.
