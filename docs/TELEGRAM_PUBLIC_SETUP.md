# Telegram Public Setup / Публичная настройка Telegram

This document prepares the public Telegram presence for PulseMarket AI before inviting first users and submitting to the Polymarket Builders Program.

Этот документ помогает подготовить публичное присутствие PulseMarket AI перед первыми пользователями и заявкой в Polymarket Builders Program.

## Public Channel

Preferred username:

```text
@PulseMarketAI
```

If it is taken, try:

```text
@PulseMarketNews
@PulseMarketAlerts
@PulseMarketSignal
@PulseMarketRadar
@PulseMarketDigest
```

Channel purpose:

- product updates
- daily digest
- interesting markets
- bot news
- changelog
- first-user acquisition

## Support

Preferred support usernames:

```text
@PulseMarketSupport
@PulseMarketHelp
@PulseMarketAIHelp
```

If a separate support account is not needed, create a support group:

```text
PulseMarket AI Support
```

## Channel Description EN

```text
PulseMarket AI updates, Polymarket market highlights, product news, and discovery alerts.

Analytics only.
No trading.
No wallets.
No financial advice.

Bot: @PulseMarketAIBot
```

## First Channel Post EN

```text
🚀 PulseMarket AI is live

PulseMarket AI is a Telegram assistant for discovering Polymarket markets, tracking sharp movements, and understanding probabilities in simple language.

What it does:
- Hot markets
- New markets
- Sharp movements
- Market search
- Watchlist
- Topic alerts
- Beginner explanations
- Direct Polymarket links

Analytics only:
No trading.
No wallets.
No deposits.
No private keys.
No financial advice.

Try the bot:
@PulseMarketAIBot
```

## Текст первого поста RU

```text
🚀 PulseMarket AI запущен

Это Telegram бот для поиска интересных рынков Polymarket, отслеживания резких движений и простого объяснения вероятностей.

Что умеет:
- горячие рынки
- новые рынки
- резкие движения
- поиск рынков
- watchlist
- уведомления по темам
- объяснение простым языком
- ссылки на Polymarket

Только аналитика:
без торговли
без кошельков
без пополнений
без приватных ключей
без финансовых советов

Бот:
@PulseMarketAIBot
```

## Manual Steps / Ручные шаги

1. Create the public channel.
2. Set the channel description.
3. Publish the first post.
4. Create a support account or support group.
5. Add the final URLs to `.env` on production:

```env
PROJECT_CHANNEL_URL=
PROJECT_SUPPORT_URL=
```

Do not print `.env` values in chat, logs, screenshots, or public docs.
