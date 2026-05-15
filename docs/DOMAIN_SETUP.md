# Production Domain And HTTPS Setup

PulseMarket AI uses a production domain with Caddy-managed HTTPS.

## Domains

- Landing page: `https://pulsemarketai.com`
- Health endpoint: `https://pulsemarketai.com/health`
- Telegram Mini App: `https://app.pulsemarketai.com/app`
- Mini App APIs: `https://app.pulsemarketai.com/api/*`

## DNS Records

Create these DNS records:

```text
Type  Name  Value
A     @     2.26.80.27
A     app   2.26.80.27
```

Both `pulsemarketai.com` and `app.pulsemarketai.com` must resolve to the VPS IP
before Let's Encrypt can issue certificates.

## Caddy

Production HTTPS is handled by the `caddy` service in
`docker-compose.prod.yml`.

The Caddy config lives in `Caddyfile`:

```text
pulsemarketai.com {
    reverse_proxy bot:8080
}

app.pulsemarketai.com {
    reverse_proxy bot:8080
}
```

Caddy automatically requests and renews HTTPS certificates. Certificate state is
stored in Docker volumes:

- `caddy_data`
- `caddy_config`

## Production Flow

1. DNS points both domains to `2.26.80.27`.
2. Caddy listens on ports `80` and `443`.
3. Caddy proxies requests to the existing bot web server on Docker network
   address `bot:8080`.
4. The existing bot web server continues to serve:
   - `/`
   - `/health`
   - `/app`
   - `/api/*`

## Environment

Production `.env` should contain:

```text
PROJECT_PUBLIC_URL=https://pulsemarketai.com
MINI_APP_URL=https://app.pulsemarketai.com/app
```

Do not commit `.env`.

## Verification

Run on the VPS:

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS https://pulsemarketai.com
curl -fsS https://pulsemarketai.com/health
curl -fsS https://app.pulsemarketai.com/app
curl -fsS https://app.pulsemarketai.com/api/today
```

## Troubleshooting

- If HTTPS fails, confirm both DNS records resolve to `2.26.80.27`.
- If Caddy cannot issue certificates, check that ports `80` and `443` are open.
- If the Mini App button opens a normal link, confirm `MINI_APP_URL` starts with
  `https://` and restart the bot container.
- If BotFather rejects the URL, verify the URL is exactly:
  `https://app.pulsemarketai.com/app`.
