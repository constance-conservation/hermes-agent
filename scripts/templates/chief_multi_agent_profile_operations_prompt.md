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
2. **Policies paths (canonical):** Org policy markdown is read from **`${HERMES_HOME}/policies/`** on each profile — typically a **symlink** to **`~/.hermes/profiles/chief-orchestrator/policies`**. The pipeline (`start_pipeline.py` with `--policy-root`) materializes generated and runtime subtrees into that same root — **not** under `workspace/policies/`.
3. **Single gateway per physical host:** Use **one** long-lived `gateway run` **per machine**, each with its **own** `HERMES_HOME` profile — **not** the same orchestrator profile name on two hosts (that duplicates cron + token locks). Recommended: **`chief-orchestrator`** on the **operator** Mac (Slack role-cron leader + primary messaging), **`chief-orchestrator-droplet`** on the **VPS** (isolated copy; see `scripts/core/isolate_droplet_orchestrator.py`). Delegate profiles are for **`delegate_task(..., hermes_profile=…)`** subprocesses only — they **do not** get their own gateway. Health: **`hermes -p <orchestrator-profile-for-this-host> gateway watchdog-check`**.
4. **Operator vs droplet:** Do **not** rsync the same `~/.hermes/profiles/chief-orchestrator/` tree to both — clone once, then run **`isolate_droplet_orchestrator.py`** on the VPS profile. Set **`AGENT_DROPLET_PROFILE=chief-orchestrator-droplet`** on the workstation when using **`hermes … droplet`** so the SSH hop targets the VPS profile.
5. **Verification:** **`hermes doctor`**, **`hermes -p <profile> gateway watchdog-check`** on **each** host with its own orchestrator profile, and a smoke **`delegate_task`** with `hermes_profile=<role>`.

**Out of scope for code-only fixes:** Human approval workflows and secret rotation — document operator runbooks separately.

---

_End of template._
