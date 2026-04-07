# Tool Authority Matrix

Purpose: map role levels to tool-risk classes.

## Tool classes

- T0: reasoning only
- T1: read-only
- T2: workspace write
- T3: controlled execution/delegation
- T4: coordination/admin
- T5: high-risk privileged operations

## Governance

- Least privilege is default.
- Temporary privilege elevation requires explicit justification.
- Revocation occurs on misuse, drift, or phase change.

## Cross-links

- `MODEL_ROUTING_REGISTRY.md`
- `DELEGATION_PACKET_TEMPLATE.md`
- `CHANNEL_GOVERNANCE_MATRIX.md`
