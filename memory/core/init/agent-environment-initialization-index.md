# Agent Environment Initialization Index

This memory maps all initialization files used to set up the agent environment.

## When To Use

- If asked how to initialize or deploy the agent environment.
- If asked where setup rules and runbooks are located.
- If asked for startup or watchdog/restart procedures.

## Initialization File Set

- `README.md`
- `agentic-company-deployment-pack.md`
- `chief-orchestrator-directive.md`
- `deployment-handoff.md`
- `firewall-exceptions-workflow.md`
- `gateway-watchdog.md`
- `global-agentic-company-deployment-policy.md`
- `hermes-model-delegation-and-tier-runtime.md`
- `pipeline-runbook.md`
- `security-first-setup.md`
- `security-prompts.md`
- `unified-deployment-and-security.md`

## Initialization Read Order

1. `README.md`
2. `deployment-handoff.md`
3. `unified-deployment-and-security.md`
4. `pipeline-runbook.md`
5. `gateway-watchdog.md`
6. security and role behavior docs as needed

## Scripts For Initialization

- runtime scripts: `../scripts/`
- policy scripts: `../policy-scripts/`

## Rule For Initialization Questions

When prompted about agent initialization, load this file first, then load the minimum subset of referenced init files needed to answer accurately.
