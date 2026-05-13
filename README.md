# PulseMarket Bot

**Status:** Live MVP  
**Telegram bot:** [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)  
**GitHub repo:** [IlyasMescherov/polymarket-pulse-bot](https://github.com/IlyasMescherov/polymarket-pulse-bot)

PulseMarket Bot is a Telegram analytics bot for Polymarket discovery. It helps users find active prediction markets, understand market probabilities in plain language, and receive alerts when probabilities move sharply.

This project is prepared for a Polymarket Builders Program submission. The current MVP is intentionally scoped around analytics, notifications, and public market links.

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
- Sharp movements: compares stored market snapshots and surfaces probability changes above 10 percentage points.
- Notifications: users can enable or disable sharp movement alerts.
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
- No private keys
- No seed phrases
- No payments
- No custody
- No order signing
- Public Polymarket data only

The bot provides market discovery and notifications. It does not provide financial advice.

## Builder Program Notes

`POLYMARKET_BUILDER_CODE` is included in configuration for future readiness.

At this first stage, the bot uses public Polymarket data only. Builder code is prepared for a future version with a reviewed trading integration.

The MVP is useful for the Builders Program because it demonstrates:

- A live user-facing Polymarket experience
- Public data integration with the Gamma API
- Beginner-friendly market presentation
- User-level notification settings
- Snapshot-based market movement detection
- A clear safety boundary before any trading integration

## Roadmap

- Add category filters for politics, crypto, sports, culture, and macro.
- Add user watchlists for specific markets.
- Add saved keywords and topic alerts.
- Add richer market movement summaries.
- Add a public landing page with screenshots and demo video.
- Add production monitoring and health checks.
- Add webhook deployment mode for production Telegram hosting.
- Consider Builder Code usage only in a future trading version after safety review.

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
PROJECT_PUBLIC_URL=
PROJECT_TELEGRAM_HANDLE=@PulseMarketAIBot
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
- Hot Markets result
- New Markets result
- Sharp Movement result
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
- Enable notifications
- Open a Polymarket market link
- End on GitHub repository and [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)

Suggested path:

```text
docs/demo/pulsemarket-bot-demo.mp4
```
