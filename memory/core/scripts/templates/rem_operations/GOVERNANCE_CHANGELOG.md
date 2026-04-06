# Governance changelog (applied)

Append **dated** entries when material policy, registers, or infra posture changes. One paragraph per entry is enough.

## Entries

### 2026-04-05 — Repo sync (templates + security prompts)

- **Security role prompts:** merged into single file `policies/core/governance/role-prompts/security-foundation-agents-role-prompts.md` (sections AG-004, AG-006–AG-013); old per-role `security-agent-*.md` files removed from repo.
- **Session 11 registers:** `SECURITY_ALERT_REGISTER.md` updated — W001 mitigated (SSH 40227 + Tailscale posture), W002 documented (browser strategy), W003 in progress (allowlist tables in `CHANNEL_ARCHITECTURE.md`), W004 mitigated (`SKILL_INVENTORY_REGISTER.md`).
- **Session 10:** `CHANNEL_ARCHITECTURE.md` template filled with env var mapping and ID tables for operator completion.
- **Workflows:** `CONSULTANT_REQUEST_REGISTER.md`, `BOARD_REVIEW_REGISTER.md` populated with operational sections.
- **Memory strategy:** `MEMORY_INTEGRATION_OVERRIDE.md` completed for register vs MEMORY.md split.
- **Enforcement:** Confirmed canonical code path is `agent/token_governance_runtime.py` (not `agent/governance.py`). Set **`max_agent_turns: 50`** in `hermes_token_governance.runtime.yaml` if Session 6–7 requires a 50 cap (template default may differ — align with policy).
- **Droplet:** `REM_OPERATIONS_FORCE=1` materialize from `hermes-agent` repo; optional append to `memories/MEMORY.md` via `MEMORY_MD_APPEND_SNIPPET.txt`.
