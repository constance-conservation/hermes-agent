---
sidebar_position: 8
title: "Operator + droplet: two isolated gateways"
description: "Run Hermes on a VPS and a Mac without cross-talk: WhatsApp sessions, lock instances, watchdogs, and Telegram/Slack"
---

# Two isolated gateways (operator Mac + droplet VPS)

This guide is for running **two Hermes deployments** that must **never** share live messaging sessions: one on a **Linux VPS** (droplet) and one on a **Mac** (operator workstation).

## Non-negotiable rules

1. **One Baileys (WhatsApp Web) session per phone number**  
   You cannot scan the same WhatsApp account on two servers. If both gateways used the **same** WhatsApp login, the second would kick the first offline.

2. **One Telegram bot token / one Slack app per live gateway**  
   Duplicate processes with the **same** `TELEGRAM_BOT_TOKEN` or `SLACK_BOT_TOKEN` will fight for a single connection (token lock / missed events).  
   **Options:** use **different** Telegram bots and Slack apps per host, **or** run Telegram/Slack only on the droplet and **disable** them on the operator profile.

3. **`HERMES_GATEWAY_LOCK_INSTANCE` is not a substitute for (1) and (2)**  
   It only separates **filesystem** lock paths under `$XDG_STATE_HOME/hermes/gateway-locks/` when you copy `HERMES_HOME` between machines. It does **not** split WhatsApp/Telegram/Slack provider sessions.

## Recommended WhatsApp split (operator Mac + droplet VPS)

Use **two different WhatsApp logins** (one phone number per host). On **each** host, Hermes should only **receive and send** in the **self-chat** thread — the “message yourself” / chat-with-your-own-number conversation — **not** in DMs with other contacts and **not** in groups, unless you explicitly opt in (see below).

**Do not use the old pattern:** operator logged in as **personal** with `WHATSAPP_MODE=bot` and `WHATSAPP_ALLOWED_USERS` set to the **business** number so you DM personal ↔ business. That cross-number setup is deprecated; both hosts use **`WHATSAPP_MODE=self-chat`** on their respective accounts.

| Host | WhatsApp account (QR session) | Mode | `WHATSAPP_ALLOWED_USERS` |
|------|------------------------------|------|--------------------------|
| **Droplet** | **Business** number (e.g. `61483757391`) | `self-chat` | That **same** business number (E.164, no `+`) |
| **Operator Mac** | **Personal** number (e.g. `61419933874`) | `self-chat` | That **same** personal number (E.164, no `+`) |

The bridge drops traffic that is **not** the self-chat thread when `WHATSAPP_MODE=self-chat` and **`WHATSAPP_ALLOW_NON_SELF_DM`** is unset/false (default). Optional: `whatsapp.unauthorized_dm_behavior: ignore` in **`config.yaml`** so unauthorized surfaces stay silent.

### Droplet (`chief-orchestrator` profile) — business line

In **`HERMES_HOME/.env`**:

```bash
WHATSAPP_ENABLED=true
WHATSAPP_MODE=self-chat
WHATSAPP_ALLOWED_USERS=61483757391
# Default: omit or false — do not handle non-self-chat DMs until you expand allowlists deliberately:
# WHATSAPP_ALLOW_NON_SELF_DM=false
```

Pair the bridge with the **WhatsApp Business** app for that number (`hermes whatsapp` on the server).

### Operator Mac — personal line

Use a **separate** `HERMES_HOME` (e.g. `~/.hermes/profiles/operator` or default `~/.hermes`).

```bash
WHATSAPP_ENABLED=true
WHATSAPP_MODE=self-chat
WHATSAPP_ALLOWED_USERS=61419933874
```

Pair with the **personal** WhatsApp app for that number. Interact with Hermes only in **self-chat** on that device.

### LID mapping and replies

If the gateway sends **DM pairing codes** even though allowlists look correct, ensure `lid-mapping-*.json` under `HERMES_HOME/whatsapp/session` (or `platforms/whatsapp/session`) exists after pairing. If **outbound** replies never appear, the session may be using **LID** JIDs — the bridge maps `@lid` → `...@s.whatsapp.net` using those files.

### Extending beyond self-chat later

When you intentionally add more numbers, groups, or non-self DMs, set **`WHATSAPP_ALLOW_NON_SELF_DM=true`**, tune **`WHATSAPP_ALLOWED_USERS`** / **`WHATSAPP_ALLOWED_CHATS`**, and follow [WhatsApp setup](./whatsapp.md).

## Lock instance + service install (both hosts)

Set a **stable** label **before** `gateway install` and `gateway watchdog-install` so generated **systemd** units and **LaunchAgent** plists embed the variable:

```bash
# Droplet (example)
export HERMES_GATEWAY_LOCK_INSTANCE=droplet

# Operator Mac (example)
export HERMES_GATEWAY_LOCK_INSTANCE=operator
```

Then reinstall services so definitions refresh:

```bash
hermes -p <profile> gateway install --force
hermes -p <profile> gateway watchdog-install --force
```

Linux user units pick up `Environment=HERMES_GATEWAY_LOCK_INSTANCE=…` from the generator. macOS LaunchAgents include the same key under `EnvironmentVariables`.

## Watchdog (each host)

- **Droplet:** `hermes gateway watchdog-install` (or `scripts/core/install_and_restart_gateway_watchdog.sh`) + optional systemd user unit from `scripts/core/hermes-gateway-watchdog.user.service.example`. Ensure **one** watchdog per `HERMES_HOME`.
- **Operator:** `hermes gateway watchdog-install` on the Mac; use `hermes gateway audit-singleton` if anything looks duplicated.

## Verification

On each machine, with the correct profile:

```bash
hermes gateway audit-singleton
hermes gateway watchdog-check
```

Strict all-platform health (when enabled) requires every configured adapter connected — if the operator disables Telegram/Slack, ensure they are **disabled** in config so the watchdog does not expect them.

## Checklist summary

- [ ] Different **WhatsApp** QR logins (business on droplet, personal on operator).
- [ ] Both hosts: **`WHATSAPP_MODE=self-chat`**, **`WHATSAPP_ALLOWED_USERS`** = that host’s **own** number only (unless you have deliberately widened access).
- [ ] **`WHATSAPP_ALLOW_NON_SELF_DM`** left unset/false until you explicitly allow non-self-chat DMs.
- [ ] Telegram/Slack: **disjoint tokens** or **disabled** on one host.
- [ ] `HERMES_GATEWAY_LOCK_INSTANCE` set and services reinstalled on **both** hosts.
- [ ] One gateway + one external watchdog per `HERMES_HOME` per machine.
