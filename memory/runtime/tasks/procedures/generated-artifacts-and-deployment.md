# Generated Artifacts and Deployment

## Purpose

Define when and how runtime-generated files are created, populated, and refreshed.

## Policy Conditions

Generate or refresh operational artifacts when:

- pipeline activation runs (`policies/core/scripts/start_pipeline.py`)
- runtime workspace is materialized for a profile
- governance updates require register refresh
- operations registers are missing in a target workspace
- rem-operations templates must be synchronized into `workspace/operations`

Primary references:

- `policies/core/deployment-handoff.md`
- `policies/core/pipeline-runbook.md`
- `policies/core/runtime/agent/memory/governance/source/artifacts-and-archival-memory.md`

## Activation Commands

```bash
./policies/core/runtime/agent/memory/runtime/tasks/scripts/activate-runtime-memory.sh
./policies/core/runtime/agent/memory/runtime/tasks/scripts/deploy-operations-artifacts.sh
```

## Governance Restart (Folded From Previous Doc)

After governance or runtime config changes, restart runtime entrypoints and verify load:

```bash
./policies/core/runtime/agent/memory/runtime/tasks/scripts/restart-governance-runtime.sh
./venv/bin/python -m hermes_cli.main -p chief-orchestrator gateway watchdog-check
```

If model governance is active, validate runtime YAML exists and is enabled:

```bash
cat ~/.hermes/profiles/chief-orchestrator/workspace/operations/hermes_token_governance.runtime.yaml | rg "enabled:"
```

## Stub Policy

Stub files under `policies/core/runtime/agent` were removed intentionally.
When needed, deploy operational files from templates under:

- `memory/runtime/tasks/templates/generated-artifacts/`

Do not recreate ad-hoc stubs; materialize through pipeline/scripts and then populate with operational content.

## Read Next

- `session-and-bootstrap.md`
- `mem0-cloud-memory-policy.md`

## Memory Network

- `../../../knowledge/references/index/memory-network.md`
