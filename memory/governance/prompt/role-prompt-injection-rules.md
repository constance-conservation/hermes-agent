# Role Prompt Injection Rules

This file defines automatic prompt loading hooks for governance execution.

## Injection Directive

When a governance policy section is loaded, the mapped prompt file must be loaded as prompt context before acting.

Injection behavior:

1. Read standard section in `../policy/enforcement-and-standards.md`.
2. Load mapped role prompt file below.
3. Execute under standard constraints; prompts cannot override standards.

## Standards to Prompt Hooks

- Security core -> `policies/core/security-prompts.md` and `workspace/memory/governance/source/role-prompts/security-foundation-agents-role-prompts.md`
- Token/model/tool/channel -> `workspace/memory/governance/source/role-prompts/implement-token-model-and-tool-and-channel-governance-prompt.md`
- Org mapper/HR -> `workspace/memory/governance/source/role-prompts/org-mapper-hr-controller.md`
- Functional director -> `workspace/memory/governance/source/role-prompts/functional-director-template.md`
- Project lead -> `workspace/memory/governance/source/role-prompts/project-lead-template.md`
- Supervisor -> `workspace/memory/governance/source/role-prompts/supervisor-template.md`
- Worker specialist -> `workspace/memory/governance/source/role-prompts/worker-specialist-template.md`
- Board review -> `workspace/memory/governance/source/role-prompts/board-of-directors-review.md`
- Task state/evidence -> `workspace/memory/governance/source/role-prompts/task-state-evidence-enforcer.md`
- Channel architecture planning -> `workspace/memory/governance/source/role-prompts/future-channel-architecture-planner.md`
- Client deployment intake -> `workspace/memory/governance/source/role-prompts/client-intake-deployment-template.md`
- Lifecycle hygiene -> `workspace/memory/governance/source/role-prompts/agent-lifecycle-org-hygiene-controller.md`
- Agentic company template generation -> `workspace/memory/governance/source/role-prompts/markdown-playbook-generator.md`
- Deployment order enforcement -> `workspace/memory/governance/source/role-prompts/minimal-default-deployment-order.md`

## Security Foundation Role Bundle

For AG-004 through AG-013 security foundations, load:

- `workspace/memory/governance/source/role-prompts/security-foundation-agents-role-prompts.md`

These role prompts are always bound to canonical security standards and cannot be executed outside that security baseline.

## Read Next

- `../policy/enforcement-and-standards.md`
- `../protocols/artifacts-template-protocol.md`
- `../../runtime/tasks/procedures/orchestration-and-escalation.md`
