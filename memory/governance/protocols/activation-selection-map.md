# Governance Activation Selection Map

This file is the governance activation gate. Load this first for governance scope.

## Mandatory Start Sequence

1. `../policy/enforcement-and-standards.md`
2. `../prompt/role-prompt-injection-rules.md`
3. `artifacts-template-protocol.md`

## Selective Retrieval Rules

- Need security, trust boundaries, browser/code execution controls -> load `../policy/enforcement-and-standards.md` section `Security Core`.
- Need model-tier, token, tool, and channel behavior -> load `../policy/enforcement-and-standards.md` section `Token, Model, Tool, Channel`.
- Need org structure and role responsibilities -> load `../policy/enforcement-and-standards.md` section `Org and Role Standards`.
- Need role execution prompt text -> load `../prompt/role-prompt-injection-rules.md` and apply mapped prompt hooks.
- Need register layout, generated docs, and archival rules -> load `artifacts-template-protocol.md`.

## Enforcement

Standards in this governance pack are non-negotiable. If a template or prompt conflicts with a standard, the standard wins.

## Read Next

- `../policy/enforcement-and-standards.md`
- `../prompt/role-prompt-injection-rules.md`
- `../../knowledge/references/index/concept-index.md`
