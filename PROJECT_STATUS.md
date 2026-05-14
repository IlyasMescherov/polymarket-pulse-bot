# PulseMarket Bot Project Status

## Current MVP Status

PulseMarket Bot is a live MVP available on Telegram as [@PulseMarketAIBot](https://t.me/PulseMarketAIBot).

The current version focuses on public Polymarket market discovery, market movement alerts, and beginner-friendly explanations. It uses public Polymarket Gamma API data and stores user settings plus market snapshots in PostgreSQL.

## Working Features

- Telegram `/start` onboarding flow
- Main menu with inline buttons
- Hot Markets view
- New Markets view
- Sharp Movement detection based on stored market snapshots
- Pulse Score for market signal ranking
- Market Health Score for public-data quality and activity context
- Risk flags for low volume, missing data, ending soon, sharp move, and volatile history
- Market search with local fallback filtering
- Category filters for politics, crypto, AI / tech, sports, and economy
- Watchlist 2.0 with initial/current probability tracking
- Topic alerts for personalized smart alerts
- Alert cooldown log to reduce repeated notifications
- Daily digest opt-in with topic personalization
- Market timeline from stored snapshots
- Beginner explanation mode
- Resolution explainer for market rules and settlement context
- Share bot and share market cards
- Inline query handler in code
- Link click tracking for market opens
- Search query tracking for aggregate product stats
- Admin stats command gated by `ADMIN_TELEGRAM_IDS`
- User notification toggle and alert settings for sharp movement alerts
- PostgreSQL persistence for users and market snapshots
- Alembic migrations
- Docker Compose PostgreSQL service
- Optional OpenAI explanations when `OPENAI_API_KEY` is configured
- Full no-AI fallback when `OPENAI_API_KEY` is missing
- Public Polymarket market links
- Callback action logging with user id, username, action, and timestamp

## Not Implemented Yet

- Trading
- Wallet connection
- Private key handling
- Seed phrase handling
- Payments
- Order signing
- Webhook production mode
- Public landing page
- Demo video and final screenshots
- BotFather inline mode activation may still need to be enabled manually with `/setinline`
- `ADMIN_TELEGRAM_IDS` must be set manually in production before `/admin_stats` is usable by the owner

## Phase 3 Completed

Phase 3 added the intelligence and product-discovery layer:

- Pulse Score
- Risk flags
- Better market cards
- Watchlist 2.0
- Topic alerts
- Smart alert cooldowns
- Market timeline
- Beginner mode
- Share cards
- Daily digest
- Inline query handler in code

## Phase 4 Builder Readiness Completed

Phase 4 adds Builder Program readiness:

- Market Health Score
- Resolution Explainer
- Improved discovery fallback for public search, tags, series, sports, and local filtering
- Link click tracking for market opens
- Search query tracking
- Admin stats command
- Optional `POLYMARKET_REFERRAL_URL`
- `BUILDER_APPLICATION.md`
- README sections for Builders Program alignment and safety scope

## What is live on VPS

- Production VPS health endpoint: [http://2.26.80.27:8080/health](http://2.26.80.27:8080/health)
- Telegram bot: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Docker Compose production deployment
- PostgreSQL-backed persistence
- Alembic migrations run on container startup

## What still requires manual setup

1. Enable inline mode in BotFather with `/setinline`.
2. Choose `@PulseMarketAIBot`.
3. Set inline placeholder to `Search Polymarket markets`.
4. Add screenshots to the repository.
5. Record a 45-second demo video.
6. Set `ADMIN_TELEGRAM_IDS` in production `.env` and restart the bot before using `/admin_stats`.
7. Submit the builder application.
8. Add `POLYMARKET_REFERRAL_URL` only if the project becomes eligible for Polymarket referrals.

## Next Milestones

- Publish the repository on GitHub.
- Add screenshots under `docs/screenshots/`.
- Add a 45-second demo video under `docs/demo/`.
- Deploy the bot on a production host with persistent PostgreSQL.
- Add monitoring for bot polling, database connectivity, and Polymarket API failures.
- Enable inline mode in BotFather if it is not already enabled.
- Prepare a polished Builders Program submission package.

## Builder Badge Strategy

The project is intentionally scoped as a safe public-data MVP first.

Builder badge submission should emphasize:

- Live Telegram bot: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Public Polymarket Gamma API integration
- Beginner-friendly user experience
- Market discovery and sharp movement alerts
- PostgreSQL-backed snapshots and notification settings
- Clear safety scope: no trading, no wallet connection, no private keys, no payments

`POLYMARKET_BUILDER_CODE` is already present in configuration for future readiness. It is not used in the MVP because this version does not trade or connect wallets.
