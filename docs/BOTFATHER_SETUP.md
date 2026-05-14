# BotFather Setup / Настройка BotFather

This setup is manual. Do not paste tokens, `.env` values, or server logs into BotFather.

Настройка выполняется вручную. Не вставляйте токены, значения `.env` или server logs в BotFather.

## Profile Values

### Bot name

```text
PulseMarket AI
```

### Short description

```text
AI-powered Polymarket market discovery, alerts, and simple explanations.
```

### About text

```text
PulseMarket AI helps you discover interesting Polymarket markets, track sharp movements, understand probabilities, and open markets directly on Polymarket.

Analytics only.
No trading.
No wallets.
No deposits.
No private keys.
No financial advice.
```

### Description EN

```text
PulseMarket AI is a Telegram discovery and analytics assistant for Polymarket.

It helps users:
- discover hot and new markets
- track sharp probability movements
- search markets by topic
- understand probabilities in simple language
- save markets to a watchlist
- receive smart alerts
- open markets directly on Polymarket

PulseMarket AI does not execute trades, manage wallets, hold funds, accept deposits, request private keys, or provide financial advice.
```

### Description RU

```text
PulseMarket AI помогает находить интересные рынки Polymarket, отслеживать резкие движения, понимать вероятность простым языком и открывать рынки прямо на Polymarket.

Бот работает только в аналитическом режиме:
без торговли
без кошельков
без пополнений
без приватных ключей
без финансовых советов
```

### Commands

Paste this into `/setcommands`:

```text
start - Main menu
hot - Hot markets
new - New markets
moves - Sharp movements
search - Search markets
watchlist - My watchlist
settings - Settings
whoami - Show my Telegram ID
about - About PulseMarket AI
```

## Manual BotFather Steps

### 1. Set bot name

1. Open `@BotFather`.
2. Send `/setname`.
3. Choose `@PulseMarketAIBot`.
4. Paste:

```text
PulseMarket AI
```

### 2. Set short description

1. Send `/setdescription`.
2. Choose `@PulseMarketAIBot`.
3. Paste the short description:

```text
AI-powered Polymarket market discovery, alerts, and simple explanations.
```

### 3. Set about text

1. Send `/setabouttext`.
2. Choose `@PulseMarketAIBot`.
3. Paste the About text from this document.

### 4. Set command menu

1. Send `/setcommands`.
2. Choose `@PulseMarketAIBot`.
3. Paste the commands block from this document.

### 5. Set userpic

1. Send `/setuserpic`.
2. Choose `@PulseMarketAIBot`.
3. Upload a 1024x1024 PNG avatar prepared using [brand/AVATAR_GUIDE.md](brand/AVATAR_GUIDE.md).

### 6. Enable inline mode

1. Send `/setinline`.
2. Choose `@PulseMarketAIBot`.
3. Set placeholder:

```text
Search Polymarket markets
```

## Ручная настройка BotFather

1. Откройте `@BotFather`.
2. Используйте `/setname`, `/setdescription`, `/setabouttext`, `/setcommands`, `/setuserpic`, `/setinline`.
3. Каждый раз выбирайте `@PulseMarketAIBot`.
4. Вставляйте готовые тексты из этого файла.
5. Для `/setuserpic` используйте отдельную аватарку 1024x1024 PNG.
6. Inline placeholder:

```text
Search Polymarket markets
```
