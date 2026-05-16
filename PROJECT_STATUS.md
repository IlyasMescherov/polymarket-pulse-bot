# PulseMarket Bot Project Status

## Current MVP Status

PulseMarket Bot is a live MVP available on Telegram as [@PulseMarketAIBot](https://t.me/PulseMarketAIBot).

The current version focuses on becoming a daily market intelligence companion for Polymarket: it selects what matters, explains why people care, and points users to public source market pages.

## Working Features

- Telegram `/start` onboarding flow
- Main menu with inline buttons
- Today's Pulse discovery screen and `/today` command
- Morning Briefing layer for a short daily read of what matters
- Market Mood labels for Quiet, Active, Heating up, Volatile, and Ending soon
- Activity Radar screen and `/smart` command
- Hot Markets view
- New Markets view
- Sharp Movement detection based on stored market snapshots
- Why it moved explanations for market movement context
- Pulse Score for market interest ranking
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
- Simple Read copy that explains what a market asks, why people care, and what to watch
- Resolution explainer for market rules and settlement context
- Share bot and share market cards
- Inline query handler in code and BotFather inline mode enabled
- Link click tracking for market opens
- Search query tracking for aggregate product stats
- Admin stats command gated by `ADMIN_TELEGRAM_IDS`
- Admin channel digest command gated by `ADMIN_TELEGRAM_IDS`
- User feedback command and admin feedback review
- Read-only Activity Radar using public Polymarket Data API fallback
- Public wallet address tracking without wallet connection
- `/whoami` command for safe admin id discovery
- User notification toggle and alert settings for sharp movement alerts
- PostgreSQL persistence for users and market snapshots
- Alembic migrations
- Docker Compose PostgreSQL service
- Optional OpenAI explanations when `OPENAI_API_KEY` is configured
- AI Context Engine for safe market reasoning, daily narratives, and category summaries
- AI Interpretation Layer for what-this-means, attention vs conviction, strength labels, and related topics
- Event categories for Politics, Crypto, AI, Sports, Esports, Global, and Culture
- Human probability interpretation for unlikely, possible, likely, and highly likely states
- Local Mini App interests for category prioritization
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
- Public landing page served from [https://pulsemarketai.com](https://pulsemarketai.com) and sourced from [landing/](landing/)
- Competitor analysis in [docs/COMPETITOR_ANALYSIS.md](docs/COMPETITOR_ANALYSIS.md)

## Phase 6 Read-only Activity Radar Completed

Phase 6 adds public market intelligence without trading or wallet connection:

- `/smart` command and Smart Money main menu button
- Unusual Activity from public Data API trades when available
- Public Traders from public leaderboard data when available
- Active Markets aggregation from public activity
- Track Public Wallet for public EVM addresses only
- Smart Money alerts setting
- Admin stats for Smart Money snapshots, tracked public wallets, alerts, and large public activity
- Optional Smart Money block in `/admin_digest`
- Public landing page Activity Radar section
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

## Telegram Mini App Dashboard Preview Completed

The project now includes a static Telegram Mini App preview:

- Mini App route: [https://app.pulsemarketai.com/app](https://app.pulsemarketai.com/app)
- Static source: [miniapp/](miniapp/)
- Setup docs: [docs/MINI_APP_SETUP.md](docs/MINI_APP_SETUP.md)
- Read-only API endpoints for Today's Pulse, hot markets, new markets, sharp moves, Activity Radar, public traders, and search
- Dashboard button in the Telegram main menu

## Daily Market Intelligence Companion Layer

The next product direction is now documented and partially implemented:

- Product strategy: [docs/PRODUCT_STRATEGY_NEXT.md](docs/PRODUCT_STRATEGY_NEXT.md)
- Morning Briefing: [docs/MORNING_BRIEFING.md](docs/MORNING_BRIEFING.md)
- Market Mood: [docs/MARKET_MOOD.md](docs/MARKET_MOOD.md)
- `/start` positions PulseMarket AI as a daily Polymarket intelligence companion.
- Mini App Today tab starts with Morning Briefing instead of a raw dashboard.
- Market cards now include Market Mood and a short why people care line.
- Activity Radar remains focused on public attention, not trade execution.

## AI Reasoning Layer Added

PulseMarket AI now has an optional reasoning layer on top of ranking and filtering:

- AI Context Engine: [docs/AI_REASONING_LAYER.md](docs/AI_REASONING_LAYER.md)
- AI Market Interpretation Layer: [docs/AI_INTERPRETATION_LAYER.md](docs/AI_INTERPRETATION_LAYER.md)
- Market Memory: [docs/MARKET_MEMORY.md](docs/MARKET_MEMORY.md)
- Market Regimes: [docs/MARKET_REGIMES.md](docs/MARKET_REGIMES.md)
- YES / NO Side Analysis: [docs/YES_NO_SIDE_ANALYSIS.md](docs/YES_NO_SIDE_ANALYSIS.md)
- Outcome Display Logic: [docs/OUTCOME_DISPLAY_LOGIC.md](docs/OUTCOME_DISPLAY_LOGIC.md)
- AI Market Briefing: [docs/AI_MARKET_BRIEFING.md](docs/AI_MARKET_BRIEFING.md)
- Event Category System: [docs/EVENT_CATEGORY_SYSTEM.md](docs/EVENT_CATEGORY_SYSTEM.md)
- Mini App Today tab includes Today’s Narrative and category-aware briefing copy.
- Mini App Explain sheet includes What this means, Attention vs conviction, strength labels, related topics, and what to watch.
- Mini App category selector filters Today, Radar, and search suggestions.
- Search API returns a short context summary.
- All AI behavior has deterministic fallback when `OPENAI_API_KEY` is missing.
- Market cards and APIs include real outcome labels for YES / NO, team-vs-team, moneyline, and custom markets.
- External News Intelligence matches public RSS and official sources to markets, with X, Telegram, and News API adapters prepared as disabled stubs.
- Mini App market cards and Analysis now show a compact outside-context read when relevant news is available.

Telegram requires HTTPS for a real Mini App URL in BotFather. The current HTTP route is a browser preview until a domain and HTTPS are configured.

## What is live on VPS

- Production VPS health endpoint: [https://pulsemarketai.com/health](https://pulsemarketai.com/health)
- Public landing page: [https://pulsemarketai.com](https://pulsemarketai.com)
- Mini App preview: [https://app.pulsemarketai.com/app](https://app.pulsemarketai.com/app)
- Telegram bot: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Public channel: [@PulseMarketAI](https://t.me/PulseMarketAI)
- Support: [@PulseMarketAISupport](https://t.me/PulseMarketAISupport)
- X/Twitter: [@PulseMarketBot](https://x.com/PulseMarketBot)
- Activity Radar is available from `/smart`
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
4. Keep the public landing page updated at [https://pulsemarketai.com](https://pulsemarketai.com).
5. Post the first manual digest in [@PulseMarketAI](https://t.me/PulseMarketAI).
6. Run `/admin_check_channel` before enabling channel autoposting.
7. Keep `AUTO_CHANNEL_POSTING_ENABLED=false` until preview publishing is manually verified.
8. Link `@PulseMarketAISupport` as the discussion group for channel comments if comments are desired.
9. Paste [BUILDER_SUBMISSION_TEXT.md](BUILDER_SUBMISSION_TEXT.md) into the application.
10. Attach GitHub repo.
11. Include Telegram bot handle.
12. Include admin stats screenshot.
13. Add `POLYMARKET_REFERRAL_URL` only if the project becomes eligible for Polymarket referrals.
14. Add a domain with HTTPS before enabling the Mini App in BotFather.

## Before First Users

- Set the bot avatar in BotFather.
- Set BotFather name, description, about text, commands, and inline placeholder.
- Create a public Telegram channel.
- Create a support contact or support group.
- Finish the X/Twitter profile and pin the launch post.
- Add `PROJECT_CHANNEL_URL`.
- Add `PROJECT_SUPPORT_URL`.
- Add `PROJECT_X_URL`.
- Add `MINI_APP_URL` after HTTPS is ready.
- Record a clean demo video.
- Invite the first 20 to 50 users.
- Run `/admin_digest` and publish the first channel digest manually.
- Use `/admin_publish_today` for preview-and-publish channel flow.
- Use `/admin_x_draft` for manual X/Twitter draft generation.
- Ask first users to send `/feedback`.
- Ask early users whether Activity Radar is understandable without trading terminology.

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
