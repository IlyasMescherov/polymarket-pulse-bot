# Smart Money Radar

Smart Money Radar is a read-only market intelligence layer for PulseMarket AI.

It highlights unusual public activity and active market attention using public Polymarket data only.

## Scope

Smart Money Radar is research-only.

- No trading
- No wallet connection
- No deposits
- No private keys
- No seed phrases
- No custody
- No order placement
- No trade execution
- No financial advice

## Data Sources

The feature is configured with:

```text
POLYMARKET_DATA_API_URL=https://data-api.polymarket.com
```

The client attempts to use public Data API endpoints for:

- Public trades
- Public leaderboard data
- Public positions for a public wallet address

If the Data API is unavailable, blocked, or returns a different shape, PulseMarket AI falls back gracefully and the rest of the bot keeps working.

## User Features

### Unusual Activity

Shows large public activity when public trade data is available.

The explanation is intentionally conservative:

- It says public activity may indicate attention.
- It asks users to check movement and resolution rules.
- It never tells users what action to take.

### Public Traders

Shows public leaderboard context when available.

The screen includes:

```text
Past performance does not guarantee future results.
Use this for research, not copy trading.
```

### Active Markets

Aggregates public activity by market and highlights markets with stronger attention.

### Track Public Wallet

Users can save a public EVM wallet address for read-only monitoring.

This is not wallet connection. The bot never asks for secrets.

## Database

Phase 6 adds:

- `smart_money_snapshots`
- `tracked_traders`
- `smart_money_alerts_log`
- `users.smart_money_alerts_enabled`

## Admin Metrics

`/admin_stats` includes:

- Smart Money snapshots count
- Tracked public wallets count
- Smart Money alerts sent today
- Large public activities detected today

`/admin_digest` may include a Smart Money Radar block when recent public activity snapshots exist.

## Builder Program Value

This feature makes PulseMarket AI more useful as a Polymarket discovery layer:

- It surfaces public attention shifts.
- It adds context before a user opens Polymarket.
- It does not replace Polymarket execution.
- It keeps the safety scope clear and research-only.
