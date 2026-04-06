# Delegation Packet Template

## Required Fields

- Task id
- Parent task
- Delegating agent
- Delegate date
- Assigned role and agent id
- Assigned model and fallback
- Allowed tools and forbidden tools
- Scope boundaries (workspace, filesystem, network)
- Objective
- Success test
- Stop conditions
- Context capsule
- Output format and destination
- Budget (tokens, tool calls, wall-clock)

## Validation

- Context is minimal and relevant.
- Success criteria are verifiable.
- Stop conditions prevent runaway loops.
- Tool scope follows least privilege.
