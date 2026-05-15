# PulseMarket Bot

- **Status:** Live MVP
- **Telegram bot:** [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- **GitHub repo:** [IlyasMescherov/polymarket-pulse-bot](https://github.com/IlyasMescherov/polymarket-pulse-bot)
- **Landing page:** [https://pulsemarketai.com](https://pulsemarketai.com)
- **Mini App preview:** [https://app.pulsemarketai.com/app](https://app.pulsemarketai.com/app)
- **Production health:** [https://pulsemarketai.com/health](https://pulsemarketai.com/health)

PulseMarket AI is a daily market intelligence companion for Polymarket. It helps users understand what matters today, why people are watching a market, where public attention is rising, and what to inspect next.

This project is prepared for a Polymarket Builders Program submission. The current MVP is intentionally scoped around analytics, notifications, and public market links.

## Submission Ready

PulseMarket AI is live on Telegram as [@PulseMarketAIBot](https://t.me/PulseMarketAIBot) and deployed on a VPS with a health endpoint.

Public landing page: [https://pulsemarketai.com](https://pulsemarketai.com)

Builder submission package:

- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md)
- [BUILDER_SUBMISSION_TEXT.md](BUILDER_SUBMISSION_TEXT.md)
- [BUILDER_APPLICATION.md](BUILDER_APPLICATION.md)
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- [docs/SCREENSHOT_GUIDE.md](docs/SCREENSHOT_GUIDE.md)
- [docs/screenshots/](docs/screenshots/)
- [docs/MINI_APP_SETUP.md](docs/MINI_APP_SETUP.md)

## Public Telegram Setup

- Bot: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Channel: [@PulseMarketAI](https://t.me/PulseMarketAI)
- Support: [@PulseMarketAISupport](https://t.me/PulseMarketAISupport)
- X/Twitter: [@PulseMarketBot](https://x.com/PulseMarketBot)
- BotFather setup doc: [docs/BOTFATHER_SETUP.md](docs/BOTFATHER_SETUP.md)
- Public Telegram setup doc: [docs/TELEGRAM_PUBLIC_SETUP.md](docs/TELEGRAM_PUBLIC_SETUP.md)
- Auto publishing doc: [docs/AUTO_PUBLISHING.md](docs/AUTO_PUBLISHING.md)
- Telegram comments setup: [docs/TELEGRAM_COMMENTS_SETUP.md](docs/TELEGRAM_COMMENTS_SETUP.md)
- Telegram Mini App setup: [docs/MINI_APP_SETUP.md](docs/MINI_APP_SETUP.md)
- X/Twitter setup doc: [docs/X_PUBLIC_SETUP.md](docs/X_PUBLIC_SETUP.md)
- X/Twitter launch thread: [docs/X_LAUNCH_THREAD.md](docs/X_LAUNCH_THREAD.md)
- Competitor analysis: [docs/COMPETITOR_ANALYSIS.md](docs/COMPETITOR_ANALYSIS.md)
- Next product strategy: [docs/PRODUCT_STRATEGY_NEXT.md](docs/PRODUCT_STRATEGY_NEXT.md)
- Morning Briefing: [docs/MORNING_BRIEFING.md](docs/MORNING_BRIEFING.md)
- Market Mood: [docs/MARKET_MOOD.md](docs/MARKET_MOOD.md)
- AI reasoning layer: [docs/AI_REASONING_LAYER.md](docs/AI_REASONING_LAYER.md)
- AI market briefing: [docs/AI_MARKET_BRIEFING.md](docs/AI_MARKET_BRIEFING.md)
- Event category system: [docs/EVENT_CATEGORY_SYSTEM.md](docs/EVENT_CATEGORY_SYSTEM.md)
- Static landing page: [landing/](landing/)
- Telegram Mini App preview: [miniapp/](miniapp/)
- Avatar guide: [docs/brand/AVATAR_GUIDE.md](docs/brand/AVATAR_GUIDE.md)

Recommended public channel username: `@PulseMarketAI`. If unavailable, use `@PulseMarketNews`, `@PulseMarketAlerts`, `@PulseMarketSignal`, `@PulseMarketRadar`, or `@PulseMarketDigest`.

## What is PulseMarket Bot

PulseMarket Bot is a lightweight daily companion for Polymarket. It watches public Polymarket markets, highlights what matters, and turns market data into a short read of the day.

The bot is designed for users who want a simple way to follow Polymarket without opening multiple dashboards or learning advanced trading terminology.

## Live Demo

- Telegram: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Status: Live MVP
- Command to start: `/start`

The bot currently runs as a polling Telegram bot with PostgreSQL-backed user settings and market snapshots.

## Key Features

- Hot markets: shows 5 active Polymarket markets ranked by recent volume.
- New markets: shows 5 newly created active markets.
- Morning Briefing / Today's Pulse: shows a short daily selection of high-signal markets with why people care and what to watch.
- AI Context Engine: optionally adds short market context, topic narratives, and what-changed summaries when `OPENAI_API_KEY` is configured.
- Today’s Narrative: explains what public markets are reacting to today without making predictions.
- Event categories: All, Politics, Crypto, AI, Sports, Esports, Global, and Culture help users filter the daily briefing and Activity Radar.
- Human probability language: very low probability, possible, likely, and highly likely labels make raw percentages easier to read.
- Personal interests in the Mini App: users can prioritize categories locally for a more relevant daily read.
- Market Mood: adds a human-readable label such as Quiet, Active, Heating up, Volatile, or Ending soon.
- Activity Radar: read-only view of unusual public activity, public leaderboard data, active market attention, and user-tracked public wallet addresses.
- Sharp movements: compares stored market snapshots and surfaces probability changes above each user's selected threshold.
- Why it moved: explains probability movement using public market data, volume, time to resolution, and risk flags.
- Pulse Score: each market gets a 0-100 signal score based on movement, volume, time to close, and data quality.
- Market Health Score: each market gets a separate 0-100 quality/activity score based on volume, data completeness, time to resolution, and optional liquidity signals when available.
- Risk flags: market cards highlight low volume, missing data, ending soon, sharp move, and volatile-history risks.
- Market search: users can search public Polymarket markets by topic, such as `bitcoin`, `fed`, `election`, or `ai`.
- Watchlist 2.0: users can save markets, compare initial vs current probability, and remove markets later.
- Topic alerts: users can save topics like `bitcoin`, `trump`, `fed`, `openai`, or `ufc`.
- Smart alerts: sharp movement notifications respect user threshold, minimum volume, saved topics, and a 6-hour per-market cooldown.
- Market timeline: cards include a timeline button that shows recent stored probability snapshots.
- Beginner mode: every market can be explained in plain language without trading advice.
- Resolution explainer: users can ask how a market resolves and what rules should be checked.
- Categories: politics, crypto, AI / tech, sports, and economy filters are available from the main menu.
- Daily digest: users can opt into a daily digest of high-signal markets, personalized by topics when available.
- Admin channel digest: admins can generate a ready-to-copy daily post for `@PulseMarketAI` with `/admin_digest`.
- Safe channel publishing: admins can preview Today’s Pulse, publish to `@PulseMarketAI` only after approval, and rely on duplicate/cooldown protection.
- X draft generation: admins can generate short X/Twitter drafts without automatic X posting.
- English-first public posts: channel content is generated in English so Telegram translation works cleanly for international users.
- Feedback: users can send product feedback with `/feedback`; admins can review recent feedback with `/admin_feedback`.
- Quick start: a short guided onboarding screen explains how to use the bot.
- Settings: users can manage sharp move alerts, daily digest preference, language, and movement threshold.
- RU/EN language: core product screens support Russian and English through a simple internal dictionary.
- Share cards: users can share the bot or generate a clean text card for a specific market.
- Inline mode ready: the bot includes an inline query handler for quick market lookup from Telegram chats.
- Inline search: BotFather inline mode is enabled; `@PulseMarketAIBot bitcoin` returns market results.
- Link click tracking: Polymarket link opens are tracked as safe product analytics without storing secrets.
- Admin stats: project admins can view aggregate usage stats with `/admin_stats`.
- Smart Money admin metrics: admin stats include Smart Money snapshots, tracked public wallets, alerts sent today, and large public activity detected today.
- Admin diagnostics: `/whoami` shows a user's Telegram id for safe admin setup.
- Optional referral URL: an optional referral URL can be configured only if the project becomes eligible for Polymarket referrals.
- Optional AI explanations: when `OPENAI_API_KEY` is configured, the bot adds short plain-language explanations.
- No-AI fallback: when `OPENAI_API_KEY` is missing, the bot still works normally.
- Public market links: every market card links users back to Polymarket.
- Public landing page: a no-build page is served from [https://pulsemarketai.com](https://pulsemarketai.com) and kept in [landing/](landing/).
- Telegram Mini App Dashboard: a no-build mobile companion is served from [https://app.pulsemarketai.com/app](https://app.pulsemarketai.com/app), centered on Morning Briefing, Activity Radar, Search, Saved markets, and settings.

## How it works

PulseMarket Bot uses the public Polymarket Gamma API:

```text
https://gamma-api.polymarket.com
```

The bot reads public market fields such as `question`, `outcomePrices`, `volume`, `endDate`, and `slug`.

For Activity Radar, the bot also uses the public Polymarket Data API when available:

```text
https://data-api.polymarket.com
```

The current integration uses public trades, public leaderboard data, and public positions endpoints with graceful fallback. If the Data API is unavailable or returns an unexpected format, the bot keeps running and shows a friendly unavailable state.

The same lightweight web server exposes read-only JSON endpoints for the Mini App preview:

- `/api/today`
- `/api/markets/hot`
- `/api/markets/new`
- `/api/markets/moves`
- `/api/smart-money/active`
- `/api/smart-money/traders`
- `/api/search?q=bitcoin`

When `OPENAI_API_KEY` is configured, the web API enriches market objects with safe context fields:

- `why_people_care`
- `simple_read`
- `what_to_watch`
- `attention_summary`
- `topic_narrative`
- `probability_interpretation`
- `category`
- `category_label`

If the key is not configured, deterministic fallback copy is used.

For Yes/No markets, the Yes outcome price is displayed as the implied event probability. If the data is incomplete, the bot does not fail; it shows a friendly "data is not available yet" message.

Sharp movement detection works by saving market snapshots to PostgreSQL, then comparing the latest public probability against the previously stored probability for the same market.

Search and categories use public Gamma API market data. If a direct search field is not available, the bot loads active markets and filters locally by market title, question, category, and simple topic keywords.

Pulse Score is intentionally simple and transparent:

- Movement points reward large probability changes.
- Volume points reward higher public market volume.
- Ending points highlight markets near resolution.
- Data quality points reward complete public data.

Risk flags are guardrails for discovery. They are not trading advice.

Market Health is separate from Pulse Score. It is a quality and activity signal based on public data completeness, volume, time to resolution, and optional liquidity data when available. Market Health is not financial advice.

## Tech Stack

- Python 3.12
- aiogram 3
- PostgreSQL
- SQLAlchemy 2
- Alembic
- httpx
- Docker Compose
- python-dotenv
- Optional OpenAI API
- Public Polymarket Gamma API
- Public Polymarket Data API

## Safety and Scope

PulseMarket Bot is not a trading bot.

The current MVP has strict safety boundaries:

- No trading
- No copy trading
- No wallet connection
- No wallet management
- No deposits
- No private keys
- No seed phrases
- No payments
- No custody
- No order signing
- No financial advice
- Public Polymarket data only

The bot provides market discovery, watchlists, alerts, and links back to Polymarket. PulseMarket AI does not execute trades, manage wallets, hold funds, or provide financial advice.

## Why this helps Polymarket

PulseMarket AI gives new and casual users a low-friction way to discover Polymarket markets directly inside Telegram. It explains probabilities in plain language, highlights market movement, and sends users to the original Polymarket market pages instead of trying to replace the Polymarket experience.

The bot can also help identify which topics users search for and which markets they open, creating useful product signals for future builder work.

## Builder Program Alignment

PulseMarket AI is aligned with the Builders Program as a safe discovery and analytics layer:

- It uses public Polymarket market data.
- It drives users to Polymarket market pages.
- It improves market understanding for beginners.
- It tracks aggregate engagement such as searches and market opens.
- It prepares future builder-code integration without custody or private-key handling.

Builder code is prepared for future official trading integration, but the current MVP uses public Polymarket market data only.

## Analytics only safety scope

PulseMarket AI does not execute trades, manage wallets, hold funds, or provide financial advice.

The current MVP intentionally excludes wallets, balances, deposits, positions, order placement, order signing, seed phrases, private keys, and payments.

## Market Health Score

Market Health is a 0-100 score with three labels:

- `Risky`: 0-39
- `Medium`: 40-69
- `Healthy`: 70-100

It is based on public market quality signals such as volume, probability availability, end date availability, time to close, and optional liquidity fields if stable public CLOB data is available. If liquidity data is unavailable, the bot falls back to volume and data-completeness checks.

Market Health is not a recommendation to trade.

## Activity Radar

Activity Radar is a read-only market intelligence layer. It highlights unusual public activity, public leaderboard context, active market attention, and public wallet addresses that users choose to track.

It does not connect wallets, manage positions, place orders, or tell users what decision to make. The feature is for research only and uses public Polymarket data.

Current Activity Radar surfaces:

- Unusual Activity: large public activity detected from public trade data.
- Public Traders: public leaderboard context with a clear past-performance warning.
- Active Markets: markets receiving stronger public attention.
- Track Public Wallet: lets a user save a public EVM wallet address for read-only monitoring.

If the public Data API is unavailable, the bot falls back safely and does not interrupt the rest of the product.

## Resolution Explainer

Each market card includes a resolution explainer button. It summarizes:

- What the market means
- What must happen for it to resolve
- When the market is expected to end
- Which market rules or sources should be checked
- Why the displayed probability is not a guarantee

When `OPENAI_API_KEY` is configured, PulseMarket AI can add a short AI explanation. Without an API key, the template still works.

## Link click tracking

Market open buttons use an intermediate Telegram callback. When a user taps a market link, the bot records:

- Telegram user id
- Market id
- Market title
- Source screen, such as hot, search, watchlist, digest, or category
- Timestamp

The bot then sends the direct Polymarket URL. This gives the project safe engagement metrics for the Builders Program without handling funds or secrets.

## Safe public publishing

PulseMarket AI can generate public Today’s Pulse posts for the Telegram channel and X/Twitter drafts.

Telegram channel autoposting is disabled by default with `AUTO_CHANNEL_POSTING_ENABLED=false`. Admins can use `/admin_publish_today` to preview content, publish it to the channel, generate an X draft, or cancel. Published content is tracked in PostgreSQL to prevent duplicates and enforce a cooldown.

X/Twitter support is draft-only by default. The bot can prepare a short post and send it to admins for manual publishing, but it does not post to X automatically.

## Admin stats

Project admins can use `/admin_stats` when their Telegram ids are configured in `ADMIN_TELEGRAM_IDS`.

The command shows aggregate metrics such as total users, notification users, digest users, watchlist items, topic count, market opens, alerts sent today, Smart Money snapshots, tracked public wallets, top clicked markets, top search queries, and snapshot count.

## Optional referral URL

`POLYMARKET_REFERRAL_URL` is optional and only used if the project becomes eligible for Polymarket referrals.

The bot does not rewrite specific market URLs when doing so would break direct market opening. If the referral URL is not set, normal Polymarket links are used.

## Builder application doc

See [BUILDER_APPLICATION.md](BUILDER_APPLICATION.md) for the submission-oriented product summary, safety scope, user flow, ecosystem value, and demo checklist.

## Builder Program Notes

`POLYMARKET_BUILDER_CODE` is included in configuration for future readiness.

At this first stage, the bot uses public Polymarket data only. Builder code is prepared for a future version with a reviewed trading integration.

Builder code is prepared for future official trading integration, but the current MVP uses public Polymarket market data only.

The MVP is useful for the Builders Program because it demonstrates:

- A live user-facing Polymarket experience
- Public data integration with the Gamma API
- Beginner-friendly market presentation
- User-level notification settings
- Market search, categories, and user watchlists
- Pulse Score, risk flags, market timeline, and topic-based smart alerts
- Snapshot-based market movement detection
- A clear safety boundary before any trading integration

## Traction Layer

Phase 5 adds a lightweight traction layer for public launch:

- Today's Pulse gives users a simple daily discovery surface.
- Why it moved explains market movement without giving directional financial advice.
- Activity Radar highlights unusual public activity as research-only market intelligence.
- `/admin_digest` generates a channel-ready post for [@PulseMarketAI](https://t.me/PulseMarketAI).
- `/feedback` gives early users a direct product feedback loop.
- The static landing page in [landing/](landing/) gives the project a public website, currently served at [https://pulsemarketai.com](https://pulsemarketai.com).
- [docs/COMPETITOR_ANALYSIS.md](docs/COMPETITOR_ANALYSIS.md) explains how PulseMarket AI differs from trading terminals and copy-trading tools.
- [docs/SMART_MONEY_ANALYTICS.md](docs/SMART_MONEY_ANALYTICS.md) explains the read-only Activity Radar scope.

## Daily Market Intelligence Companion

PulseMarket AI's next product direction is:

> Understand what matters on Polymarket today.

The Mini App and bot now prioritize meaning before metrics:

- Morning Briefing gives users one main story and a few secondary markets.
- Market Mood explains whether a market feels Quiet, Active, Heating up, Volatile, or Ending soon.
- Simple Read turns a market into plain language: what it asks, why people care, what to watch, and where to inspect rules.
- Activity Radar focuses on where public attention is rising instead of leading with raw wallet data.

See [docs/PRODUCT_STRATEGY_NEXT.md](docs/PRODUCT_STRATEGY_NEXT.md), [docs/MORNING_BRIEFING.md](docs/MORNING_BRIEFING.md), and [docs/MARKET_MOOD.md](docs/MARKET_MOOD.md).

## Roadmap

- Add richer market movement summaries.
- Publish the static landing page and add screenshots plus demo video.
- Add production monitoring and health checks.
- Add webhook deployment mode for production Telegram hosting.
- Consider Builder Code usage only in a future trading version after safety review.

## Inline Mode

PulseMarket AI includes inline query support in code, and inline mode is enabled for the live bot. If it ever needs to be re-enabled in BotFather, run:

```text
/setinline
```

Choose `@PulseMarketAIBot`, then set a placeholder such as:

```text
Search Polymarket markets
```

After BotFather enables inline mode, users can type:

```text
@PulseMarketAIBot bitcoin
```

Telegram will show up to 5 matching market cards.

## Local Development

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Required:

```env
BOT_TOKEN=
```

Optional:

```env
OPENAI_API_KEY=
POLYMARKET_DATA_API_URL=https://data-api.polymarket.com
POLYMARKET_BUILDER_CODE=
POLYMARKET_REFERRAL_URL=
PROJECT_PUBLIC_URL=
PROJECT_TELEGRAM_HANDLE=@PulseMarketAIBot
PROJECT_CHANNEL_URL=
PROJECT_SUPPORT_URL=
PROJECT_X_URL=
ADMIN_TELEGRAM_IDS=
```

Start PostgreSQL:

```bash
docker compose up -d db
```

Run migrations:

```bash
PATH=.venv/bin:$PATH alembic upgrade head
```

Run the bot locally:

```bash
PATH=.venv/bin:$PATH python -m bot.main
```

Run checks:

```bash
PATH=.venv/bin:$PATH python -m compileall bot
PATH=.venv/bin:$PATH pytest -q
docker compose config
PATH=.venv/bin:$PATH alembic upgrade head --sql
```

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full VPS deployment guide.

Recommended production setup:

- A small VPS or managed app host
- Managed PostgreSQL or a backed-up PostgreSQL instance
- Telegram bot token stored as a secret
- `OPENAI_API_KEY` stored as an optional secret
- Process manager such as systemd, Docker Compose, or a platform-native worker
- Health checks for the bot process and database
- Log aggregation for callback actions and API failures

For a simple Docker-based deployment:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

The bot container runs Alembic migrations before starting the Telegram polling process.

## Screenshots placeholders

Add screenshots before submitting:

- `/start` welcome screen
- Main menu
- Quick Start screen
- Hot Markets result
- New Markets result
- Sharp Movement result
- Pulse Score and risk flags
- Market Search result
- Watchlist view
- Topic alerts settings
- Market timeline
- Beginner explanation
- Categories view
- Notification settings
- Polymarket market link opened from Telegram

Suggested path:

```text
docs/screenshots/
```

## Demo video placeholder

Add a 45-second demo video showing the live Telegram bot flow:

- Open Telegram
- Send `/start`
- Open Hot Markets
- Open New Markets
- Open Sharp Moves
- Search for a market
- Add a market to Watchlist
- Open Market Timeline
- Tap Explain Simply
- Add a topic alert
- Enable notifications
- Share a market card
- Open a Polymarket market link
- End on GitHub repository and [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)

Suggested path:

```text
docs/demo/pulsemarket-bot-demo.mp4
```
