# PulseMarket AI Mini App

Static Telegram Mini App preview for PulseMarket AI.

## Product Direction

PulseMarket AI is a market intelligence assistant for Polymarket. The Mini App is intentionally not a terminal: it is built around curated screens that help a user understand what matters today.

## App Structure

- **Today**: daily market story, secondary picks, compact hot markets, and sharp-move summary.
- **Radar**: public-attention insight cards, focused on markets rather than technical account data.
- **Search**: Spotlight-like market search with trending and recent searches.
- **Saved**: local saved markets and recently opened markets.
- **More**: language, theme, notification preferences, compact mode, reduced animations, links, and short explanations.

## UX Principles

- Bottom navigation is the primary navigation layer.
- The sticky top area is contextual, not duplicated navigation.
- Cards are compact and meaning-first.
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
