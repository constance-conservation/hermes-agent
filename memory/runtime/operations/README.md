# Runtime Operations Runbooks

This directory is the canonical operational runbook pack used by the chief-orchestrator runtime.

## Scope

Includes governance matrices, delegation templates, role/lifecycle registers, incident and security runbooks, and runtime governance YAML references.

## Primary files

- `AGENT_CREATION_WORKFLOW.md`
- `ROLE_TEMPLATES_AND_STANDARDS.md`
- `MODEL_ROUTING_REGISTRY.md`
- `TOOL_AUTHORITY_MATRIX.md`
- `CHANNEL_GOVERNANCE_MATRIX.md`
- `DELEGATION_PACKET_TEMPLATE.md`
- `CONSULTANT_REQUEST_REGISTER.md`
- `CONSULTANT_CHALLENGE_TEMPLATE.md`
- `AGENT_LIFECYCLE_REGISTER.md`
- `ORG_REGISTRY.md`

## Runtime state links

- `../state/hermes-token-governance.runtime.yaml`
- `runtime_governance.runtime.yaml`
- `role_assignments.yaml`

Keep references in this directory internal and avoid dependencies on the removed `workspace/memory/runtime/operations/` path.
