# Policy Enforcement and Standards

Consolidated non-negotiable standards from `policies/core/runtime/agent/memory/governance/source/standards`.

## Security Core (Non-Negotiable)

Source:

- `policies/core/runtime/agent/memory/governance/source/standards/canonical-ai-agent-security-policy.md`

Enforce:

- Fail-closed behavior on privileged operations.
- Explicit authority precedence stack for policy conflicts.
- Strict workspace/profile isolation and secret-handling boundaries.
- No silent bypass of security checks, approvals, or audit evidence.

Precedence:

- Security policy remains authoritative over additive governance layers.

Prompt hook to load with this section:

- `policies/core/security-prompts.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/security-foundation-agents-role-prompts.md`

## Token, Model, Tool, Channel (Non-Negotiable)

Source:

- `policies/core/runtime/agent/memory/governance/source/standards/token-model-tool-and-channel-governance-policy.md`

Enforce:

- Token and model-tier routing by risk and task class.
- Tool and channel constraints are additive and cannot weaken security baseline.
- Consultant/premium escalation must remain auditable.
- When governance rules conflict, higher-precedence policy wins.

Additive-only rule:

- Token/model/tool/channel governance can constrain behavior further but cannot weaken security or deployment baselines.

Prompt hook to load with this section:

- `policies/core/runtime/agent/memory/governance/source/role-prompts/implement-token-model-and-tool-and-channel-governance-prompt.md`

## Org and Role Standards

Sources:

- `policies/core/runtime/agent/memory/governance/source/standards/org-mapper-hr-policy.md`
- `policies/core/runtime/agent/memory/governance/source/standards/functional-director-policy-template.md`
- `policies/core/runtime/agent/memory/governance/source/standards/project-lead-policy-template.md`
- `policies/core/runtime/agent/memory/governance/source/standards/supervisor-policy-template.md`
- `policies/core/runtime/agent/memory/governance/source/standards/worker-specialist-policy-template.md`
- `policies/core/runtime/agent/memory/governance/source/standards/board-of-directors-review-policy.md`
- `policies/core/runtime/agent/memory/governance/source/standards/agent-lifecycle-org-hygiene-policy.md`
- `policies/core/runtime/agent/memory/governance/source/standards/task-state-and-evidence-policy.md`

Enforce:

- Agent lifecycle state discipline and lean-org hygiene.
- Clear separation of responsibilities across mapper/director/lead/supervisor/worker/board.
- Task state updates require evidence, not narrative-only claims.
- Registry-driven activation/deactivation to prevent role drift and duplication.

Prompt hooks to load with this section:

- `policies/core/runtime/agent/memory/governance/source/role-prompts/org-mapper-hr-controller.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/functional-director-template.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/project-lead-template.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/supervisor-template.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/worker-specialist-template.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/board-of-directors-review.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/agent-lifecycle-org-hygiene-controller.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/task-state-evidence-enforcer.md`

## Channel and Deployment Standards

Sources:

- `policies/core/runtime/agent/memory/governance/source/standards/channel-architecture-policy.md`
- `policies/core/runtime/agent/memory/governance/source/standards/client-deployment-policy.md`
- `policies/core/runtime/agent/memory/governance/source/standards/agentic-company-template.md`

Enforce:

- Channel topology must follow approved architecture and naming semantics.
- Client deployment must pass intake and mapping controls before execution.
- Company-template deployment order must be followed for stable orchestration.

Prompt hooks to load with this section:

- `policies/core/runtime/agent/memory/governance/source/role-prompts/future-channel-architecture-planner.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/client-intake-deployment-template.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/markdown-playbook-generator.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/minimal-default-deployment-order.md`

## Prompt Hook Requirement

When a section in this file is loaded, the corresponding role prompt hook from `../prompt/role-prompt-injection-rules.md` must also be loaded before execution.

## Read Next

- `../prompt/role-prompt-injection-rules.md`
- `../protocols/artifacts-template-protocol.md`
- `../../knowledge/concepts/security-and-authority.md`
