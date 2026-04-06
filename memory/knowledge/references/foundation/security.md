# Security Guidance

## Authority Stack

1. Canonical repo policy layer (`policies/README.md` and linked core policies)
2. Runtime anchor layer in this directory
3. Domain layers under `knowledge/*`, `actors/*`, `governance/*`, and `runtime/*`

If a local convenience rule conflicts with canonical policy, canonical policy wins.

## Security Baseline

- Never expose secrets in memory files.
- Keep workspace and profile boundaries isolated.
- Distinguish local vs remote actions and verified vs pending operations.
- Do not claim execution success without evidence.

## Read Next

- `foundation-memory-contract.md`
- `../../runtime/tasks/procedures/session-and-bootstrap.md`

## Memory Network

- `../references/index/memory-network.md`
