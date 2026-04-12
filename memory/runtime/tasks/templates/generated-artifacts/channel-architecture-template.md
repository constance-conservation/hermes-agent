# CHANNEL_ARCHITECTURE

## Channel to Role Map

| Channel | Role routing | Allowed toolsets | Notes |
|---------|--------------|------------------|-------|
| | | | |

## Allowlist Variables

- TELEGRAM_ALLOWED_CHATS:
- DISCORD_ALLOWED_CHANNELS:
- SLACK_ALLOWED_CHANNELS:
- WHATSAPP_ALLOWED_CHATS:

Two-host WhatsApp default: **`WHATSAPP_MODE=self-chat`**, own number in **`WHATSAPP_ALLOWED_USERS`**, **`WHATSAPP_ALLOW_NON_SELF_DM`** off until expanded — see **`policies/core/messaging/whatsapp-self-chat-default.md`**.
