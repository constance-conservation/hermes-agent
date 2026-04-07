# Functional Directors register (REM-007)

> **REM-007 (active pipeline test):** Directors are **ACTIVE** for delegation testing. Hermes profiles: `product-director`, `engineering-director`, `operations-director`, `it-security-director` (see `scripts/org_agent_profiles_manifest.yaml` + `scripts/bootstrap_org_agent_profiles.py`). Canonical policy slots remain in `policies/core/unified-deployment-and-security.md` Phase 6.

| Role | Hermes profile | Policy template | Prompt template | Status |
|------|----------------|-----------------|-----------------|--------|
| Product Director | `product-director` | `workspace/memory/governance/source/standards/functional-director-policy-template.md` (tailor title) | `workspace/memory/governance/source/role-prompts/functional-director-template.md` | **ACTIVE** |
| Engineering Director | `engineering-director` | same | same | **ACTIVE** |
| Operations Director | `operations-director` | same | same | **ACTIVE** |
| IT / Security Director | `it-security-director` | same | same | **ACTIVE** |

## Chief usage

- Delegate department-level coordination with `delegate_task(..., hermes_profile="fd-<lane>")` per `../orchestration/chief-orchestration-playbook.md`.
- Stand down a director: remove or comment its manifest entry, `hermes profile delete fd-…`, and set status back to DORMANT in a fork of this register if needed.

## Cadence

- Hermes does not schedule director reviews unless you add **cron** or a **manual** cadence on the chief profile.
