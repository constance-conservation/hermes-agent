# AI Memory Runtime

Primary index for the runtime memory system.

## Launch Order

1. `ATTENTION.md`
2. `INDEX.md`
3. `README.md`
4. `knowledge/references/anchors/agents.md`

## Core Domains

- `core/` - initialization and environment setup policy + scripts
- `governance/` - policies, prompt wiring, and operational protocols
- `actors/` - role registry, persona components, orchestration artifacts
- `knowledge/` - concepts, domains, projects, and references
- `runtime/` - state, tasks, scripts, templates, and logs

## Most Important Files

- `governance/protocols/activation-selection-map.md`
- `governance/policy/enforcement-and-standards.md`
- `governance/prompt/role-prompt-injection-rules.md`
- `core/init/agent-environment-initialization-index.md`
- `knowledge/concepts/foundation-memory-contract.md`
- `knowledge/references/index/concept-index.md`
- `runtime/state/current-focus.md`

## Prompt Activation Rule

When a governance file is loaded, apply mapped prompt hooks from:

- `governance/prompt/role-prompt-injection-rules.md`

Prompts are additive. Standards always override prompt text.
