# Channel architecture (Session 10 — production allowlists)

> **Canonical policy concepts:** `POLICY_ROOT/core/governance/standards/channel-architecture-policy.md`  
> **This file:** operational **IDs + env vars** for the **chief-orchestrator** gateway host.  
> **Rule:** Non-DM / non-private surfaces must be allowlisted via env (see `gateway/run.py`). Fill tables below and export vars in the profile **`.env`** or systemd unit.

## Environment variables (reference)

| Variable | Platform | Format hint |
|----------|----------|-------------|
| `TELEGRAM_ALLOWED_CHATS` | Telegram | Comma-separated numeric chat IDs |
| `DISCORD_ALLOWED_CHANNELS` | Discord | Comma-separated channel snowflakes |
| `DISCORD_ALLOWED_GUILDS` | Discord | Comma-separated guild snowflakes |
| `SLACK_ALLOWED_CHANNELS` | Slack | Comma-separated channel IDs |
| `SLACK_ALLOWED_WORKSPACE_TEAMS` | Slack | Comma-separated team/workspace IDs |
| `WHATSAPP_ALLOWED_CHATS` | WhatsApp | Comma-separated chat identifiers |

---

## Slack

| Logical channel (policy name) | Slack workspace / team ID | Channel ID | Notes |
|------------------------------|---------------------------|------------|--------|
| *(example)* operator-direct-line | `T________` | `C________` | |
| *(example)* engineering | `T________` | `C________` | |
| | | | |

**Env line (paste into `.env`):**
```bash
# SLACK_ALLOWED_WORKSPACE_TEAMS=T12345678
# SLACK_ALLOWED_CHANNELS=C11111111,C22222222
```

---

## Telegram

| Logical channel | Chat ID | Notes |
|-----------------|---------|--------|
| | | |

```bash
# TELEGRAM_ALLOWED_CHATS=-1001234567890
```

---

## Discord

| Logical channel | Guild ID | Channel ID | Notes |
|-----------------|----------|------------|--------|
| | | | |

```bash
# DISCORD_ALLOWED_GUILDS=...
# DISCORD_ALLOWED_CHANNELS=...
```

---

## WhatsApp

| Logical channel | Chat ID | Notes |
|-----------------|---------|--------|
| | | |

```bash
# WHATSAPP_ALLOWED_CHATS=...
```

---

## Browser strategy (W002)

| Mode | When to use | Config |
|------|-------------|--------|
| **Browserbase** (or remote) | Default production automation | Set provider keys per Hermes docs |
| **Camofox / local** | Dev or approved internal only | Isolated profile; `browser.allow_private_urls: false` unless exception recorded here |

**Exception log (operator-approved only):**

| Date | Scope | Approver | Expiry |
|------|-------|----------|--------|
| | | | |

---

## Review cadence

- **Monthly:** AG-009 or operator verifies table matches live Slack/Telegram/Discord/WhatsApp invites and env on disk.
- After **any** new public channel or bot install: update this file and restart gateway.
