# Role Prompt Injection Rules

This file defines automatic prompt loading hooks for governance execution.

## Injection Directive

When a governance policy section is loaded, the mapped prompt file must be loaded as prompt context before acting.

Injection behavior:

1. Read standard section in `../policy/enforcement-and-standards.md`.
2. Load mapped role prompt file below.
3. Execute under standard constraints; prompts cannot override standards.

## Standards to Prompt Hooks

- Security core -> `policies/core/security-prompts.md` and `policies/core/runtime/agent/memory/governance/source/role-prompts/security-foundation-agents-role-prompts.md`
- Token/model/tool/channel -> `policies/core/runtime/agent/memory/governance/source/role-prompts/implement-token-model-and-tool-and-channel-governance-prompt.md`
- Org mapper/HR -> `policies/core/runtime/agent/memory/governance/source/role-prompts/org-mapper-hr-controller.md`
- Functional director -> `policies/core/runtime/agent/memory/governance/source/role-prompts/functional-director-template.md`
- Project lead -> `policies/core/runtime/agent/memory/governance/source/role-prompts/project-lead-template.md`
- Supervisor -> `policies/core/runtime/agent/memory/governance/source/role-prompts/supervisor-template.md`
- Worker specialist -> `policies/core/runtime/agent/memory/governance/source/role-prompts/worker-specialist-template.md`
- Board review -> `policies/core/runtime/agent/memory/governance/source/role-prompts/board-of-directors-review.md`
- Task state/evidence -> `policies/core/runtime/agent/memory/governance/source/role-prompts/task-state-evidence-enforcer.md`
- Channel architecture planning -> `policies/core/runtime/agent/memory/governance/source/role-prompts/future-channel-architecture-planner.md`
- Client deployment intake -> `policies/core/runtime/agent/memory/governance/source/role-prompts/client-intake-deployment-template.md`
- Lifecycle hygiene -> `policies/core/runtime/agent/memory/governance/source/role-prompts/agent-lifecycle-org-hygiene-controller.md`
- Agentic company template generation -> `policies/core/runtime/agent/memory/governance/source/role-prompts/markdown-playbook-generator.md`
- Deployment order enforcement -> `policies/core/runtime/agent/memory/governance/source/role-prompts/minimal-default-deployment-order.md`

## Security Foundation Role Bundle

For AG-004 through AG-013 security foundations, load:

- `policies/core/runtime/agent/memory/governance/source/role-prompts/security-foundation-agents-role-prompts.md`

These role prompts are always bound to canonical security standards and cannot be executed outside that security baseline.

## Read Next

- `../policy/enforcement-and-standards.md`
- `../protocols/artifacts-template-protocol.md`
- `../../runtime/tasks/procedures/orchestration-and-escalation.md`
