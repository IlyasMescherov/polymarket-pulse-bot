# PulseMarket AI Builder Application

## 1. Product name

PulseMarket AI

## 2. Telegram handle

[@PulseMarketAIBot](https://t.me/PulseMarketAIBot)

## 3. GitHub repo

[github.com/IlyasMescherov/polymarket-pulse-bot](https://github.com/IlyasMescherov/polymarket-pulse-bot)

## 4. Live health endpoint

[http://2.26.80.27:8080/health](http://2.26.80.27:8080/health)

## 5. Problem

New users struggle to discover relevant Polymarket markets and understand probabilities, market movement, and resolution rules. Many prediction-market interfaces assume users already know what a probability means, why market movement matters, and how resolution should be checked.

## 6. Solution

PulseMarket AI is a Telegram discovery and analytics assistant for Polymarket. It helps users find active markets, understand probability changes in plain language, save markets to a watchlist, follow topics, and open the original Polymarket pages for deeper review.

## 7. Current MVP

The live MVP includes:

- Hot markets
- New markets
- Sharp movement detection
- Pulse Score
- Market Health Score
- Risk flags
- Market search
- Category filters
- Watchlist 2.0
- Topic alerts
- Smart alerts with cooldown
- Daily digest
- Beginner mode
- Resolution explainer
- Share cards
- Inline search enabled and manually verified with `@PulseMarketAIBot bitcoin`
- Link click tracking for product engagement metrics
- Admin stats for usage overview
- `/whoami` for safe admin id discovery

## 8. User flow

1. User opens Telegram and starts `@PulseMarketAIBot`.
2. User taps Hot Markets, New Markets, or Search.
3. Bot shows market cards with probability, volume, movement, Pulse Score, Market Health, and risk flags.
4. User can add a market to Watchlist or ask for a simple explanation.
5. User can enable alerts, save topics, and receive smart movement notifications.
6. User opens the original Polymarket market page from Telegram.

## 9. Safety scope

PulseMarket AI is analytics only:

- No trading
- No wallet management
- No deposits
- No private keys
- No seed phrases
- No custody
- No payments
- No financial advice

PulseMarket AI does not execute trades, manage wallets, hold funds, or provide financial advice.

## 10. Polymarket ecosystem value

PulseMarket AI helps the Polymarket ecosystem by:

- Helping users discover active and relevant markets
- Explaining probabilities in simple language
- Surfacing market movement and resolution considerations
- Driving users to original Polymarket market pages
- Tracking engagement metrics such as market opens and search topics
- Preparing a safe path for future official builder-code integration

## 11. Future builder code integration

`POLYMARKET_BUILDER_CODE` is already prepared in configuration. Builder code is prepared for future official trading integration, but the current MVP uses public Polymarket market data only.

A future version can add official order routing and builder code attribution without custody, without private-key handling, and only after a dedicated safety review.

## 12. Demo checklist

- Telegram bot live: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- GitHub repo public
- Health endpoint responding
- `/start` screen screenshot
- Hot Markets screenshot
- Search screenshot
- Watchlist screenshot
- Market Health and Pulse Score screenshot
- Resolution Explainer screenshot
- Admin stats screenshot
- 45-second demo video
