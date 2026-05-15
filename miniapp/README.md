# PulseMarket AI Mini App

Static Telegram Mini App preview for PulseMarket AI.

## Product Direction

PulseMarket AI is a daily market intelligence companion for Polymarket. The Mini App is intentionally not a terminal: it is built around curated screens that help a user understand what matters today.

## App Structure

- **Today**: Morning Briefing, one main story, secondary picks, attention shift, and Market Mood badges.
- **Radar**: public-attention insight cards, focused on markets rather than technical account data.
- **Search**: Spotlight-like market search with category-aware suggestions and a short context summary.
- **Saved**: local saved markets and recently opened markets.
- **More**: language, theme, interests, notification preferences, compact mode, reduced animations, links, and short explanations.

## UX Principles

- Bottom navigation is the primary navigation layer.
- The sticky top area is contextual, not duplicated navigation.
- Cards are compact and meaning-first.
- Market Mood turns activity into a plain-language read: Quiet, Active, Heating up, Volatile, or Ending soon.
- Event categories help users filter the briefing by Politics, Crypto, AI, Sports, Esports, Global, and Culture.
- Optional AI context explains why people may care, what to watch, and what public markets are reacting to today.
- Metrics are secondary to the reason a market is shown.
- Settings are local-only and stored in the browser.
- Light and dark themes are supported without a build step.

## Safety Scope

- Research only
- No trading
- No wallets
- No deposits
- No private keys
- No financial advice

## Preview

Local/prod route:

```text
/app
```

Telegram Mini App production requires HTTPS.
