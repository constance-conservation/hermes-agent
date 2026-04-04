# Governance context (agentic company policy pack)

This file lives at `HERMES_HOME/.hermes.md`. Hermes loads it **first** in project context (before cwd `.hermes.md` / `AGENTS.md`), so paths stay visible when `MESSAGING_CWD` or the shell cwd is not the policy tree.

## Where materialized files live (absolute paths on this host)

- **Workspace root (start here for runtime pack):** `{{WORKSPACE_ROOT}}`
  - **Bootstrap (read first among runtime files):** `{{WORKSPACE_ROOT}}/BOOTSTRAP.md`
  - **Session / read order:** `{{WORKSPACE_ROOT}}/AGENTS.md`
  - **Layout index:** `{{WORKSPACE_ROOT}}/WORKSPACE.md`
  - **Operations registers:** `{{WORKSPACE_ROOT}}/operations/`
  - **Nested editable policy tree (generated + full pack mirror):** `{{WORKSPACE_ROOT}}/policies/`

- **Canonical policy bundle (read-mostly, full repo `policies/` tree):** `{{POLICY_ROOT}}`

## How to use this with Hermes

After the pipeline runs, Hermes injects this file plus (when present) the contents of `BOOTSTRAP.md` and `AGENTS.md` under the workspace root into the model context, so the agent knows where policies and runtime files are.

**Governance read order** in the canonical tree: `{{POLICY_ROOT}}/README.md`, then `{{POLICY_ROOT}}/core/security-first-setup.md`, then the sequence in that tree.

For production messaging uptime, see `{{POLICY_ROOT}}/core/gateway-watchdog.md` and run `hermes gateway watchdog-check`.
