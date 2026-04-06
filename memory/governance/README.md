# Governance Memory Pack

Consolidated runtime memory for `governance/source/` with strict enforcement rules and prompt-injection hooks.

## Files

- `protocols/activation-selection-map.md` - simplified load order and selective retrieval logic
- `policy/enforcement-and-standards.md` - non-negotiable standards contract
- `prompt/role-prompt-injection-rules.md` - role prompt mapping and auto-load directives
- `protocols/artifacts-template-protocol.md` - generated/template/runtime-zone contract

## Source Fidelity

Canonical source content is preserved through direct mapping from:

- `policies/core/runtime/agent/memory/governance/source/standards/*.md`
- `policies/core/runtime/agent/memory/governance/source/role-prompts/*.md`
- `policies/core/runtime/agent/memory/governance/source/generated/*`
- `policies/core/runtime/agent/memory/governance/source/artifacts-and-archival-memory.md`

## Prompt Injection Behavior

This pack embeds role-prompt hooks inside standards sections. When a standards section is read, load its mapped prompt(s) before execution.

## Read Next

- `protocols/activation-selection-map.md`
- `policy/enforcement-and-standards.md`
- `../knowledge/references/index/memory-network.md`
