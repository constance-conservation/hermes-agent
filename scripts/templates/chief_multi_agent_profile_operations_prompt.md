# Prompt: Multi-agent profile operations (chief-orchestrator + delegates)

Copy this block into Hermes when you want the agent to **implement or maintain** the org’s multi-profile delegation system (operator + droplet, `chief-orchestrator` + role profiles).

---

**Goal:** Ensure `chief-orchestrator` can delegate to specialist Hermes profiles safely, with correct credentials, policies, and UX (status bar + gateway progress show the **active delegate profile** when `delegate_task(..., hermes_profile=…)` runs).

**Repository facts (do not contradict):**

- Delegation with `hermes_profile` temporarily sets process `HERMES_HOME` to `~/.hermes/profiles/<name>/`.
- After loading the child profile’s `.env`, Hermes may **fill missing** API keys from the **delegating** profile’s `.env` for keys listed in `config.yaml` → `delegation.parent_env_overlay_keys` (see `hermes_cli.config.DEFAULT_CONFIG` v31+). Child profile values always win when present.
- The CLI status bar reads `AIAgent._status_bar_profile_override` during profile-scoped delegation so the profile name reflects the delegate, not only the sticky `chief-orchestrator` shell.
- Gateway tool-progress lines prefix with `@<profile>` when a delegate is running.

**Your tasks when asked to “implement this system”:**

1. **Per-role profiles:** For each org role that receives delegation, ensure `~/.hermes/profiles/<slug>/` exists with:
   - `config.yaml` appropriate to the role (model, toolsets, `delegation` block if needed).
   - `.env` with **all tokens that role needs** for its tools (OpenRouter, Slack, Telegram, provider keys, etc.). Do not rely only on chief’s `.env` overlay — overlay is for *missing* keys, not a substitute for a proper role `.env`.
2. **Policies & memory paths:** If the chief references workspace policies under `${HERMES_HOME}/...`, either materialize the same tree in each delegate profile or document symlinks/copy steps so delegates resolve the same policy files under **their** `HERMES_HOME`.
3. **Operator + droplet parity:** Apply the same profile directories and `.env` patterns on both hosts (or document which secrets are host-specific).
4. **Verification:** After changes, run `hermes doctor`, `hermes -p <role> gateway watchdog-check` (if gateway per profile), and a smoke `delegate_task` with `hermes_profile=<role>` to confirm tools authenticate.

**Out of scope for code-only fixes:** Human approval workflows and secret rotation — document operator runbooks separately.

---

_End of template._
