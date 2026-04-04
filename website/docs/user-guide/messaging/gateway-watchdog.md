---
sidebar_position: 2
title: "Gateway watchdog"
description: "Keep the messaging gateway and platform connections healthy with watchdog-check, scripts/gateway-watchdog.sh, doctor --fix, and recovery backoff"
---

# Gateway watchdog (uptime & recovery)

The messaging gateway is a long-lived process that should stay up and keep **at least one** platform adapter **connected** (Telegram, Slack, Discord, etc.). For servers or VPS deployments, run an **external watchdog** that periodically verifies health and recovers when something breaks.

## What “healthy” means

`hermes gateway watchdog-check` exits **0** only when all of the following are true:

| Check | Meaning |
|--------|--------|
| **Gateway process** | `gateway.pid` in `$HERMES_HOME` references a **live** Hermes gateway process. This avoids treating a crashed process as healthy when `gateway_state.json` is stale. |
| **Gateway state** | `gateway_state.json` has `gateway_state: running`. |
| **Messaging uptime** | Under `platforms`, **at least one** adapter has `state: connected`. |

Hermes **does not** require every platform to be connected. For example, Slack can be healthy while WhatsApp is `reconnecting` or `fatal`; restarting the whole gateway would drop good connections unnecessarily.

Run manually (from the repo with venv activated, `HERMES_HOME` set):

```bash
hermes gateway watchdog-check && echo OK
```

## Official shell watchdog

The repo ships `scripts/gateway-watchdog.sh`: a loop that:

1. Polls `watchdog-check` on a fixed interval while healthy.
2. On failure: applies **exponential backoff + jitter**, then runs `hermes gateway run --replace`.
3. If still unhealthy: runs **`hermes doctor --fix`** (append output to `$HERMES_HOME/logs/gateway-watchdog.log`), then replaces the gateway again.
4. Enforces a **rolling cap** on recovery attempts and a **cooldown** so a broken config does not spin forever.

Copy it to `$HERMES_HOME/bin/gateway-watchdog.sh`, `chmod +x`, and run it under **systemd**, **tmux**, or a **cron** `@reboot` job as the **same user** that owns the gateway (so `HERMES_HOME` and `gateway.pid` match).

### Environment variables

All variables are optional; defaults are in the script header.

- **`HERMES_HOME`** — Profile / instance directory (default `~/.hermes`).
- **`HERMES_AGENT_DIR`** — Path to the `hermes-agent` checkout containing `venv` (default `~/hermes-agent`).
- **`WATCHDOG_INTERVAL_SECONDS`** — Seconds between checks when healthy (default `60`).
- **`WATCHDOG_MAX_BACKOFF_SECONDS`**, **`WATCHDOG_JITTER_MAX_SECONDS`** — Backoff behavior between recovery attempts.
- **`WATCHDOG_MAX_ATTEMPTS_IN_WINDOW`**, **`WATCHDOG_ATTEMPT_WINDOW_SECONDS`**, **`WATCHDOG_COOLDOWN_SECONDS`** — Rate limiting after repeated failures.

### Logs

The watchdog appends to:

```text
$HERMES_HOME/logs/gateway-watchdog.log
```

Inspect this file when diagnosing restart loops or `doctor --fix` output.

## Relation to systemd / `gateway install`

`hermes gateway install` sets up a service that starts the gateway at boot. The **shell watchdog** is an extra layer: it watches **runtime health** (process + `gateway_state.json` + at least one connected platform) and triggers **replace + doctor** when the service alone is not enough (e.g. wedged adapters, missing deps).

Use both if you need automatic recovery without manual SSH.

## See also

- **Policy layer (repository):** `policies/core/gateway-watchdog.md` — governance requirements for production messaging gateway uptime and recovery (read with the rest of `policies/`).
- [Messaging Gateway overview](/docs/user-guide/messaging) — architecture and setup
- [`hermes doctor`](/docs/reference/cli-commands#hermes-doctor) — diagnostics and `--fix`
- [Gateway internals](/docs/developer-guide/gateway-internals) — code layout
