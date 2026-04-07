# Multi-Agent Execution Policy

Purpose: define parallel execution strategy for cost-efficient throughput.

## Rules

- Prefer parallel cheap agents when tasks are independent.
- Keep sequential execution when dependencies exist.
- Cap parallel fan-out by provider limits and budget.
- Do not run consultant-tier models in broad uncontrolled parallel batches.

## Execution pattern

1. Decompose into independent units.
2. Assign lowest valid tier for each unit.
3. Run bounded parallel batches.
4. Aggregate in supervisor/project-lead layer.
5. Escalate only unresolved work.

## Guardrails

- Explicit stop conditions on each delegated packet.
- Per-batch cost envelope and retry cap.
- No noisy status spam to human channels.
