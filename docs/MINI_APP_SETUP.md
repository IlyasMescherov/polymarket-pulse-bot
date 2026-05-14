# Telegram Mini App Setup

## What Is The Mini App?

PulseMarket AI Mini App is a Telegram-friendly dashboard for Polymarket
discovery and market intelligence.

It shows:

- Today's Pulse
- Smart Money Radar
- Hot markets
- Sharp moves
- Market search
- Safety scope

Current preview URL:

```text
http://2.26.80.27:8080/app
```

## Production Requirement

Telegram Mini App URLs must use HTTPS.

Recommended final URL:

```text
https://app.YOUR_DOMAIN/app
```

or:

```text
https://YOUR_DOMAIN/app
```

## BotFather Setup

Manual setup in BotFather:

1. Open `@BotFather`.
2. Send `/mybots`.
3. Choose `@PulseMarketAIBot`.
4. Open `Bot Settings`.
5. Choose `Configure Mini App`.
6. Enable Mini App.
7. Set the HTTPS Mini App URL.

Optional menu button setup:

1. Send `/setmenubutton`.
2. Choose `@PulseMarketAIBot`.
3. Choose Web App.
4. Set button text: `Dashboard`.
5. Set the same HTTPS URL.

## HTTPS Options

Option A: real domain with Caddy

- Buy a domain.
- Point DNS `A` record to VPS IP: `2.26.80.27`.
- Use Caddy on the VPS for automatic HTTPS.

Option B: Cloudflare Tunnel

- Keep the VPS private.
- Expose the Mini App through a Cloudflare-managed HTTPS URL.

Option C: ngrok for testing only

- Useful for temporary experiments.
- Not recommended for production or Builders Program submission.

Recommendation: for production and Builders Program review, use a real domain
with HTTPS.

## Safety Scope

PulseMarket AI Mini App is analytics-only:

- No trading
- No wallets
- No deposits
- No private keys
- No financial advice

---

# Настройка Telegram Mini App

## Что это?

PulseMarket AI Mini App — это дашборд внутри Telegram для поиска рынков
Polymarket и просмотра рыночной аналитики.

Он показывает:

- Пульс дня
- Smart Money Radar
- Горячие рынки
- Резкие движения
- Поиск рынков
- Безопасный scope проекта

Текущий preview:

```text
http://2.26.80.27:8080/app
```

## Важное требование

Telegram Mini App URL должен быть HTTPS.

Рекомендуемый финальный URL:

```text
https://app.YOUR_DOMAIN/app
```

или:

```text
https://YOUR_DOMAIN/app
```

## Настройка в BotFather

Делается вручную:

1. Открой `@BotFather`.
2. Отправь `/mybots`.
3. Выбери `@PulseMarketAIBot`.
4. Открой `Bot Settings`.
5. Выбери `Configure Mini App`.
6. Включи Mini App.
7. Укажи HTTPS URL Mini App.

Опционально можно настроить кнопку меню:

1. Отправь `/setmenubutton`.
2. Выбери `@PulseMarketAIBot`.
3. Выбери Web App.
4. Текст кнопки: `Dashboard`.
5. Укажи тот же HTTPS URL.

## Варианты HTTPS

Вариант A: домен и Caddy

- Купить домен.
- Направить DNS `A` record на VPS IP: `2.26.80.27`.
- Использовать Caddy на VPS для автоматического HTTPS.

Вариант B: Cloudflare Tunnel

- Не открывать VPS напрямую.
- Отдать Mini App через HTTPS URL от Cloudflare.

Вариант C: ngrok только для теста

- Подходит для временной проверки.
- Не лучший вариант для production и Builders Program.

Рекомендация: для production и Builders Program лучше использовать настоящий
домен с HTTPS.

## Safety Scope

PulseMarket AI Mini App работает только как аналитика:

- без торговли
- без кошельков
- без пополнений
- без приватных ключей
- без финансовых советов
