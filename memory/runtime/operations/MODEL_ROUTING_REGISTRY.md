# Model Routing Registry

Purpose: map org roles to model tiers, escalation gates, and allowed substitutions.

## Core routing policy

- Default work uses low-cost worker tiers first.
- Escalate tier only after bounded retries, better prompting, and scope reduction.
- Consultant-tier usage requires challenge + approval logging.

## Required governance links

- `../state/hermes-token-governance.runtime.yaml`
- `CONSULTANT_REQUEST_REGISTER.md`
- `CONSULTANT_REQUEST_TEMPLATE.md`
- `CONSULTANT_CHALLENGE_TEMPLATE.md`
- `TOOL_AUTHORITY_MATRIX.md`
- `CHANNEL_GOVERNANCE_MATRIX.md`

## Role-to-tier baseline

- Chief Orchestrator: strong production tier by default, consultant tier only with governance.
- Security Governor: strong production tier; consultant escalation for high-risk ambiguity.
- Directors / Project Leads: mid/strong tiers, consultant by request only.
- Supervisors / Workers: cheap tiers by default; bounded escalation via chain of command.

## Substitution log

Record model substitutions with date, reason, risk impact, and approver.
