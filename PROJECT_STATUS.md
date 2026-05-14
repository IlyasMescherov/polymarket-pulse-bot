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
- Risk flags for low volume, missing data, ending soon, sharp move, and volatile history
- Market search with local fallback filtering
- Category filters for politics, crypto, AI / tech, sports, and economy
- Watchlist 2.0 with initial/current probability tracking
- Topic alerts for personalized smart alerts
- Alert cooldown log to reduce repeated notifications
- Daily digest opt-in with topic personalization
- Market timeline from stored snapshots
- Beginner explanation mode
- Share bot and share market cards
- Inline query handler in code
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
