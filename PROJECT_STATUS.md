# PulseMarket Bot Project Status

## Current MVP Status

PulseMarket Bot is a live MVP available on Telegram as [@PulseMarketAIBot](https://t.me/PulseMarketAIBot).

The current version focuses on public Polymarket market discovery, market movement alerts, and beginner-friendly explanations. It uses public Polymarket Gamma API data and stores user settings plus market snapshots in PostgreSQL.

## Working Features

- Telegram `/start` onboarding flow
- Main menu with inline buttons
- Today's Pulse discovery screen and `/today` command
- Smart Money Radar screen and `/smart` command
- Hot Markets view
- New Markets view
- Sharp Movement detection based on stored market snapshots
- Why it moved explanations for market movement context
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
- Inline query handler in code and BotFather inline mode enabled
- Link click tracking for market opens
- Search query tracking for aggregate product stats
- Admin stats command gated by `ADMIN_TELEGRAM_IDS`
- Admin channel digest command gated by `ADMIN_TELEGRAM_IDS`
- User feedback command and admin feedback review
- Read-only Smart Money Radar using public Polymarket Data API fallback
- Public wallet address tracking without wallet connection
- `/whoami` command for safe admin id discovery
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
- Automated Smart Money alert delivery
- Webhook production mode
- Demo video and final screenshots

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

## Phase 4 Builder Submission Package Ready

The submission package is ready for final screenshots and demo recording:

- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md)
- [BUILDER_SUBMISSION_TEXT.md](BUILDER_SUBMISSION_TEXT.md)
- [BUILDER_APPLICATION.md](BUILDER_APPLICATION.md)
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- [docs/SCREENSHOT_GUIDE.md](docs/SCREENSHOT_GUIDE.md)
- [docs/screenshots/](docs/screenshots/)

## Phase 5 Traction Layer Completed

Phase 5 adds the public traction layer for first users and Builders Program review:

- Today's Pulse for daily-style discovery
- Why it moved explanations
- Channel digest text generation for `@PulseMarketAI`
- User feedback collection
- Admin feedback review
- Public landing page served from [http://2.26.80.27:8080](http://2.26.80.27:8080) and sourced from [landing/](landing/)
- Competitor analysis in [docs/COMPETITOR_ANALYSIS.md](docs/COMPETITOR_ANALYSIS.md)

## Phase 6 Read-only Smart Money Radar Completed

Phase 6 adds public market intelligence without trading or wallet connection:

- `/smart` command and Smart Money main menu button
- Unusual Activity from public Data API trades when available
- Public Traders from public leaderboard data when available
- Active Markets aggregation from public activity
- Track Public Wallet for public EVM addresses only
- Smart Money alerts setting
- Admin stats for Smart Money snapshots, tracked public wallets, alerts, and large public activity
- Optional Smart Money block in `/admin_digest`
- Public landing page Smart Money Radar section
- [docs/SMART_MONEY_ANALYTICS.md](docs/SMART_MONEY_ANALYTICS.md)

## Safe Publishing Layer Completed

The project now includes a conservative publishing workflow:

- `published_posts` table for post history, duplicate protection, and cooldown checks
- English-first Today's Pulse channel post generation
- Smart Money channel post generation when public activity data exists
- Telegram channel publish service with `AUTO_CHANNEL_POSTING_ENABLED=false` by default
- Admin preview flow with `/admin_publish_today`
- Channel access diagnostic with `/admin_check_channel`
- X/Twitter draft generation with `/admin_x_draft`
- X API credentials are future-ready, but automatic X posting is not implemented
- Documentation in [docs/AUTO_PUBLISHING.md](docs/AUTO_PUBLISHING.md)
- Comments and translation setup in [docs/TELEGRAM_COMMENTS_SETUP.md](docs/TELEGRAM_COMMENTS_SETUP.md)

## What is live on VPS

- Production VPS health endpoint: [http://2.26.80.27:8080/health](http://2.26.80.27:8080/health)
- Public landing page: [http://2.26.80.27:8080](http://2.26.80.27:8080)
- Telegram bot: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Public channel: [@PulseMarketAI](https://t.me/PulseMarketAI)
- Support: [@PulseMarketAISupport](https://t.me/PulseMarketAISupport)
- X/Twitter: [@PulseMarketBot](https://x.com/PulseMarketBot)
- Smart Money Radar is available from `/smart`
- Admin publishing preview is available from `/admin_publish_today`
- X draft generation is available from `/admin_x_draft`
- Inline search is enabled and manually verified with `@PulseMarketAIBot bitcoin`
- Docker Compose production deployment
- PostgreSQL-backed persistence
- Alembic migrations run on container startup

## What still requires manual setup

1. Switch bot UI to English for screenshots.
2. Take clean screenshots.
3. Record a 45-second demo video if the application form asks for one.
4. Keep the public landing page updated at [http://2.26.80.27:8080](http://2.26.80.27:8080).
5. Post the first manual digest in [@PulseMarketAI](https://t.me/PulseMarketAI).
6. Run `/admin_check_channel` before enabling channel autoposting.
7. Keep `AUTO_CHANNEL_POSTING_ENABLED=false` until preview publishing is manually verified.
8. Link `@PulseMarketAISupport` as the discussion group for channel comments if comments are desired.
9. Paste [BUILDER_SUBMISSION_TEXT.md](BUILDER_SUBMISSION_TEXT.md) into the application.
10. Attach GitHub repo.
11. Include Telegram bot handle.
12. Include admin stats screenshot.
13. Add `POLYMARKET_REFERRAL_URL` only if the project becomes eligible for Polymarket referrals.

## Before First Users

- Set the bot avatar in BotFather.
- Set BotFather name, description, about text, commands, and inline placeholder.
- Create a public Telegram channel.
- Create a support contact or support group.
- Finish the X/Twitter profile and pin the launch post.
- Add `PROJECT_CHANNEL_URL`.
- Add `PROJECT_SUPPORT_URL`.
- Add `PROJECT_X_URL`.
- Record a clean demo video.
- Invite the first 20 to 50 users.
- Run `/admin_digest` and publish the first channel digest manually.
- Use `/admin_publish_today` for preview-and-publish channel flow.
- Use `/admin_x_draft` for manual X/Twitter draft generation.
- Ask first users to send `/feedback`.
- Ask early users whether Smart Money Radar is understandable without trading terminology.

## Next Milestones

- Add screenshots under `docs/screenshots/`.
- Add a 45-second demo video under `docs/demo/`.
- Add monitoring for bot polling, database connectivity, and Polymarket API failures.
- Prepare a polished Builders Program submission package.

## Builder Badge Strategy

The project is intentionally scoped as a safe public-data MVP first.

Builder badge submission should emphasize:

- Live Telegram bot: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Public Polymarket Gamma API integration
- Beginner-friendly user experience
- Market discovery and sharp movement alerts
- PostgreSQL-backed snapshots and notification settings
- Clear safety scope: no trading, no wallet management, no deposits, no private keys, no custody, no financial advice

`POLYMARKET_BUILDER_CODE` is already present in configuration for future readiness. It is not used in the MVP because this version does not trade or connect wallets.
