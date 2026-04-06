# Project Brief: agentic-company (AG-005)

## Objectives
Establish a scalable, governed framework for deploying and managing agentic company structures, ensuring tight control over token usage, model routing, and communication channels.

## Constraints
- Must adhere to the Global Agentic Company Deployment Policy.
- Must utilize the `chief-orchestrator` profile for high-level coordination.
- Runtime governance must be strictly enforced via `hermes_token_governance.runtime.yaml`.

## Success Criteria
1. **Governance Pack Materialized**: All canonical policies (deployment pack, global policy, etc.) are present in the policy root.
2. **Token Governance Runtime Active**: `hermes_token_governance.runtime.yaml` is active and correctly mapping tiers to models.
3. **Messaging Allowlists Set**: `CHANNEL_ARCHITECTURE.md` is populated and synced with gateway environment variables.
4. **Watchdog Healthy**: Gateway process is stable, monitored by the watchdog, and free of PID conflicts.
5. **Zero Policy Drift**: Operational state matches canonical policies.
