# Bootstrap

## Objective

Apply runtime directives through root anchors, then expand context only by index-guided retrieval.

## Startup Procedure

1. Load `.hermes.md`.
2. Load `README.md`, `agents.md`, and `../../../README.md`.
3. Load `../../concepts/*` and `../../../runtime/state/*`.
4. Use `../index/concept-index.md` before reading domain or log shards.
5. Apply procedural docs only for in-scope operations.

## Activation Commands

```bash
./policies/core/runtime/agent/memory/runtime/tasks/scripts/activate-runtime-memory.sh
./policies/core/runtime/agent/memory/runtime/tasks/scripts/deploy-operations-artifacts.sh
```

## CLAW Verbatim Loop

CLAW doctrine excerpt (integrated):

> Implement and enforce this loop:  
> `Analysis -> Planning -> Coding/Tools -> Verification -> Review -> (repeat until done)`

## Mem0 Foundation Rule

Durable memory is written to Mem0 first. Local memory reorganization is allowed only after successful Mem0 upload and verification.

## Read Next

- `agents.md`
- `../../../runtime/tasks/procedures/session-and-bootstrap.md`
- `../../../runtime/tasks/procedures/generated-artifacts-and-deployment.md`
