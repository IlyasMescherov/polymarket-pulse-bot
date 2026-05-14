# Auto Publishing

PulseMarket AI supports a safe publishing workflow for the public Telegram channel and X/Twitter drafts.

The default production posture is conservative:

- Telegram channel autoposting is disabled by default.
- X/Twitter publishing is draft-only.
- No trading language is used.
- Duplicate content is tracked in PostgreSQL.
- Cooldown protection prevents frequent repeated channel posts.

## Telegram channel autoposting

Telegram channel publishing uses the existing aiogram bot and `Bot.send_message`.

Required environment variables:

```env
AUTO_CHANNEL_POSTING_ENABLED=false
PROJECT_CHANNEL_ID=@PulseMarketAI
AUTO_CHANNEL_POSTING_TIME=09:00
AUTO_CHANNEL_POSTING_TIMEZONE=UTC
AUTO_CHANNEL_POSTING_MIN_HOURS_BETWEEN_POSTS=20
```

`AUTO_CHANNEL_POSTING_ENABLED` should stay `false` until the admin preview flow is manually verified.

## Required bot permissions

The bot must be an admin of `@PulseMarketAI` with permission to post messages.

Use:

```text
/admin_check_channel
```

This checks channel access without publishing a test post.

## Daily Today’s Pulse

The scheduler can generate an English-first Today’s Pulse post once per day.

The post includes:

- 3 Polymarket markets worth watching
- Probability
- Pulse Score
- Why it matters
- Safety footer
- Bot handle

## Smart Money posts

Smart Money channel posts are generated only when public activity data exists.

If no data is available, no empty post is published.

## Admin preview flow

Use:

```text
/admin_publish_today
```

The bot sends an admin-only preview with buttons:

- Publish to channel
- Generate X draft
- Cancel

Manual publishing still respects duplicate protection and cooldown.

## X draft mode

Required environment variables:

```env
X_DRAFTS_ENABLED=true
X_POSTING_MODE=draft
X_HANDLE=
AUTO_X_POSTING_ENABLED=false
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
```

Use:

```text
/admin_x_draft
```

The bot creates a draft entry and sends the text to admins:

```text
🐦 X draft ready

<text>

Copy and publish manually.
```

## X API future setup

The code has a future-ready structure for X API credentials, but it does not publish through the X API yet.

If `AUTO_X_POSTING_ENABLED=true` and `X_POSTING_MODE=api`, the bot checks whether credentials exist and warns admins if they are incomplete. It does not publish automatically.

## Safety wording

Approved wording:

- Research only
- Market intelligence
- Public activity
- No trading
- No wallets
- No financial advice

Avoid any language that sounds like instructions to trade or promises outcomes.

## What is not automated

- No X API posting
- No channel posting unless explicitly enabled
- No paid promotion
- No trading actions
- No wallet access
- No order placement
