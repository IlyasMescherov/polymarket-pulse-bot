# Production Deployment

This guide describes a simple VPS deployment for PulseMarket Bot using Docker Compose.

The production deployment keeps the current MVP scope:

- No trading
- No wallet connection
- No wallet management
- No deposits
- No private keys
- No custody
- No payments
- No financial advice
- Public Polymarket data only

Live project references:

- Telegram handle: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- GitHub repo: [https://github.com/IlyasMescherov/polymarket-pulse-bot](https://github.com/IlyasMescherov/polymarket-pulse-bot)
- Production health: [https://pulsemarketai.com/health](https://pulsemarketai.com/health)

## Requirements

- Ubuntu 22.04+ or another modern Linux VPS
- Docker Engine
- Docker Compose plugin
- Git
- A Telegram bot token from BotFather
- Optional OpenAI API key
- Open inbound TCP port for the health endpoint, usually `8080`

## Server setup

Install Docker and Git using your server provider's recommended Docker installation path.

Verify installation:

```bash
docker --version
docker compose version
git --version
```

Clone the repository:

```bash
git clone https://github.com/IlyasMescherov/polymarket-pulse-bot.git
cd polymarket-pulse-bot
```

## Environment variables

Create the production environment file:

```bash
cp .env.production.example .env
nano .env
```

Set at minimum:

```env
BOT_TOKEN=
POSTGRES_PASSWORD=
DATABASE_URL=postgresql+asyncpg://pulse:<same_password>@db:5432/pulsemarket
PROJECT_TELEGRAM_HANDLE=@PulseMarketAIBot
ADMIN_TELEGRAM_IDS=
APP_HOST=0.0.0.0
APP_PORT=8080
```

Important:

- Change `POSTGRES_PASSWORD` before production.
- Keep `DATABASE_URL` password in sync with `POSTGRES_PASSWORD`.
- Keep `.env` private. It is ignored by git.
- `OPENAI_API_KEY` is optional.
- Use `/whoami` in Telegram to find your Telegram id, then set `ADMIN_TELEGRAM_IDS` if you need `/admin_stats`.

## Docker Compose production launch

Start the production stack:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check service status:

```bash
docker compose -f docker-compose.prod.yml ps
```

Check the bot logs:

```bash
docker compose -f docker-compose.prod.yml logs -f bot
```

Check the health endpoint:

```bash
curl http://localhost:8080/health
```

PostgreSQL is not exposed publicly in `docker-compose.prod.yml`.

## Migrations

The bot startup script waits for PostgreSQL and runs:

```bash
alembic upgrade head
```

To run migrations manually:

```bash
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head
```

## Logs

Follow bot logs:

```bash
docker compose -f docker-compose.prod.yml logs -f bot
```

Follow database logs:

```bash
docker compose -f docker-compose.prod.yml logs -f db
```

Show recent logs:

```bash
docker compose -f docker-compose.prod.yml logs --tail=200 bot
```

## Restarting

Restart only the bot:

```bash
docker compose -f docker-compose.prod.yml restart bot
```

Restart the full stack:

```bash
docker compose -f docker-compose.prod.yml restart
```

Stop the stack:

```bash
docker compose -f docker-compose.prod.yml down
```

Do not remove volumes unless you intentionally want to remove PostgreSQL data.

## Updating from GitHub

Pull the latest code:

```bash
git pull origin main
```

Rebuild and restart:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check logs:

```bash
docker compose -f docker-compose.prod.yml logs -f bot
```

## Security checklist

- `.env` is not committed to git.
- `POSTGRES_PASSWORD` is changed from the example value.
- `DATABASE_URL` uses the same strong database password.
- PostgreSQL port is not exposed publicly.
- Only the health endpoint port is exposed.
- Telegram token is stored only in `.env`.
- OpenAI API key is optional and stored only in `.env`.
- The bot does not trade.
- The bot does not connect wallets.
- The bot does not request private keys or seed phrases.
- The bot does not accept payments.

## Troubleshooting

Docker daemon is not running:

```bash
docker info
```

If Docker is not available, restart Docker and check again.

Database is not healthy:

```bash
docker compose -f docker-compose.prod.yml ps db
docker compose -f docker-compose.prod.yml logs --tail=200 db
```

Bot is not healthy:

```bash
docker compose -f docker-compose.prod.yml ps bot
docker compose -f docker-compose.prod.yml logs --tail=200 bot
curl http://localhost:8080/health
```

Telegram polling conflict:

Make sure only one bot instance is running with the same `BOT_TOKEN`.

```bash
docker compose -f docker-compose.prod.yml ps
```

Polymarket API errors:

Check network connectivity from the server and inspect bot logs.
