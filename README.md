# PulseMarket Bot

- **Status:** Live MVP
- **Telegram bot:** [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- **GitHub repo:** [IlyasMescherov/polymarket-pulse-bot](https://github.com/IlyasMescherov/polymarket-pulse-bot)
- **Production health:** [http://2.26.80.27:8080/health](http://2.26.80.27:8080/health)

PulseMarket AI is a Telegram analytics bot for Polymarket discovery. It helps users find active prediction markets, understand market probabilities in plain language, save markets to a watchlist, and receive alerts when probabilities move sharply.

This project is prepared for a Polymarket Builders Program submission. The current MVP is intentionally scoped around analytics, notifications, and public market links.

## Submission Ready

PulseMarket AI is live on Telegram as [@PulseMarketAIBot](https://t.me/PulseMarketAIBot) and deployed on a VPS with a health endpoint.

Builder submission package:

- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md)
- [BUILDER_SUBMISSION_TEXT.md](BUILDER_SUBMISSION_TEXT.md)
- [BUILDER_APPLICATION.md](BUILDER_APPLICATION.md)
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- [docs/SCREENSHOT_GUIDE.md](docs/SCREENSHOT_GUIDE.md)
- [docs/screenshots/](docs/screenshots/)

## What is PulseMarket Bot

PulseMarket Bot is a lightweight Telegram companion for Polymarket. It watches public Polymarket markets, highlights interesting activity, and presents market data in a beginner-friendly format.

The bot is designed for users who want a simple way to follow Polymarket without opening multiple dashboards or learning advanced trading terminology.

## Live Demo

- Telegram: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- Status: Live MVP
- Command to start: `/start`

The bot currently runs as a polling Telegram bot with PostgreSQL-backed user settings and market snapshots.

## Key Features

- Hot markets: shows 5 active Polymarket markets ranked by recent volume.
- New markets: shows 5 newly created active markets.
- Sharp movements: compares stored market snapshots and surfaces probability changes above each user's selected threshold.
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
- Quick start: a short guided onboarding screen explains how to use the bot.
- Settings: users can manage sharp move alerts, daily digest preference, language, and movement threshold.
- RU/EN language: core product screens support Russian and English through a simple internal dictionary.
- Share cards: users can share the bot or generate a clean text card for a specific market.
- Inline mode ready: the bot includes an inline query handler for quick market lookup from Telegram chats.
- Inline search: BotFather inline mode is enabled; `@PulseMarketAIBot bitcoin` returns market results.
- Link click tracking: Polymarket link opens are tracked as safe product analytics without storing secrets.
- Admin stats: project admins can view aggregate usage stats with `/admin_stats`.
- Admin diagnostics: `/whoami` shows a user's Telegram id for safe admin setup.
- Optional referral URL: an optional referral URL can be configured only if the project becomes eligible for Polymarket referrals.
- Optional AI explanations: when `OPENAI_API_KEY` is configured, the bot adds short plain-language explanations.
- No-AI fallback: when `OPENAI_API_KEY` is missing, the bot still works normally.
- Public market links: every market card links users back to Polymarket.

## How it works

PulseMarket Bot uses the public Polymarket Gamma API:

```text
https://gamma-api.polymarket.com
```

The bot reads public market fields such as `question`, `outcomePrices`, `volume`, `endDate`, and `slug`.

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

## Safety and Scope

PulseMarket Bot is not a trading bot.

The current MVP has strict safety boundaries:

- No trading
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

## Admin stats

Project admins can use `/admin_stats` when their Telegram ids are configured in `ADMIN_TELEGRAM_IDS`.

The command shows aggregate metrics such as total users, notification users, digest users, watchlist items, topic count, market opens, alerts sent today, top clicked markets, top search queries, and snapshot count.

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

## Roadmap

- Add richer market movement summaries.
- Add a public landing page with screenshots and demo video.
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
POLYMARKET_BUILDER_CODE=
POLYMARKET_REFERRAL_URL=
PROJECT_PUBLIC_URL=
PROJECT_TELEGRAM_HANDLE=@PulseMarketAIBot
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
