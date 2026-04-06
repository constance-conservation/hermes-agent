# Session and Bootstrap Procedure

## Purpose

Consolidate startup and session boot rules into one procedure.

## Startup Sequence

1. Load root anchors: `.hermes.md`, `README.md`, `bootstrap.md`, `agents.md`.
2. Load active layers: `knowledge/concepts` and `runtime/state`.
3. Use index-driven retrieval for domain and log expansion.
4. Apply procedural docs only when their domain is in scope.

## Commanded Startup Path

```bash
./policies/core/runtime/agent/memory/runtime/tasks/scripts/activate-runtime-memory.sh
```

## CLAW Verbatim Gate

CLAW doctrine excerpt (integrated):

> 1. **Preflight gate**: environment, permissions, and dependencies checked.  
> 2. **Plan gate**: scope, constraints, and acceptance criteria captured.  
> 3. **Verification gate**: tests/lints/checks run and recorded.  
> 4. **Review gate**: regressions and risks explicitly assessed.  
>  
> No task may be marked `done` without all four gates.

## Source Canon

- `../../../knowledge/references/anchors/bootstrap.md`
- `../../../knowledge/references/anchors/agents.md`
- `../../../README.md`

## Read Next

- `orchestration-and-escalation.md`
- `agent-creation-and-lifecycle.md`
- `generated-artifacts-and-deployment.md`

## Memory Network

- `../../../knowledge/references/index/memory-network.md`
