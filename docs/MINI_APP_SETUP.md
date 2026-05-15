# Telegram Mini App Setup

## What Is The Mini App?

PulseMarket AI Mini App is a Telegram-friendly dashboard for Polymarket
discovery and market intelligence.

It shows:

- Today's Pulse
- Activity Radar
- Hot markets
- Sharp moves
- Market search
- Safety scope

Production Mini App URL:

```text
https://app.pulsemarketai.com/app
```

## Production Requirement

Telegram Mini App URLs must use HTTPS.

Production URL for `@PulseMarketAIBot`:

```text
https://app.pulsemarketai.com/app
```

Generic format for future projects:

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
7. Set the HTTPS Mini App URL:

```text
https://app.pulsemarketai.com/app
```

Successful setup means Telegram accepts the URL and the Dashboard button opens
inside the Telegram Mini App browser, not as a plain external HTTP preview.

Optional menu button setup:

1. Send `/setmenubutton`.
2. Choose `@PulseMarketAIBot`.
3. Choose Web App.
4. Set button text: `Dashboard`.
5. Set the same HTTPS URL.

## How To Check

- Open a private chat with `@PulseMarketAIBot`.
- Send `/start`.
- Press `Dashboard`.
- The Mini App should open inside Telegram.
- The first screen should show Today's Pulse and the `Research only · No trade execution` label.

Troubleshooting:

- If Telegram opens a normal message instead of the Mini App, confirm
  `MINI_APP_URL=https://app.pulsemarketai.com/app` is set on production and
  restart the bot container.
- If BotFather rejects the URL, confirm the URL starts with `https://`.
- If the page does not load, check `https://app.pulsemarketai.com/app` in a
  browser and confirm Caddy is healthy.

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

## UX Philosophy

PulseMarket AI Mini App is designed as a market intelligence product, not a
trading terminal.

The first screen answers one question:

```text
What matters today?
```

The dashboard prioritizes:

- Today's Pulse as the main editorial story.
- Activity Radar as public activity context.
- Hot markets and sharp moves as secondary discovery.
- Search as a fast way to explore a topic.
- Safety scope as a visible product boundary.

## Market Intelligence Positioning

Competitors help users trade faster. PulseMarket AI helps users understand
markets faster.

The Mini App avoids exchange-style tables, dense order screens, balance panels,
and execution language. It uses larger cards, short explanations, calm
typography, and direct links back to Polymarket.

## Design References

The visual direction is inspired by:

- Bloomberg-style information hierarchy.
- Apple Weather-style overview cards.
- Arc Browser cleanliness.
- Linear and Notion spacing.
- Premium fintech dashboards.

## Mobile-First Principles

- One-hand scrolling.
- Large tap targets.
- Readable cards without zoom.
- Dark mode by default.
- Lightweight static files with no frontend build step.

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
- Activity Radar
- Горячие рынки
- Резкие движения
- Поиск рынков
- Безопасный scope проекта

Production Mini App URL:

```text
https://app.pulsemarketai.com/app
```

## Важное требование

Telegram Mini App URL должен быть HTTPS.

Production URL для `@PulseMarketAIBot`:

```text
https://app.pulsemarketai.com/app
```

Общий формат для будущих проектов:

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
7. Укажи HTTPS URL Mini App:

```text
https://app.pulsemarketai.com/app
```

Успешная настройка означает, что Telegram принимает URL, а кнопка Dashboard
открывает Mini App внутри Telegram, а не обычную HTTP preview-ссылку.

Опционально можно настроить кнопку меню:

1. Отправь `/setmenubutton`.
2. Выбери `@PulseMarketAIBot`.
3. Выбери Web App.
4. Текст кнопки: `Dashboard`.
5. Укажи тот же HTTPS URL.

## Как проверить

- Открой private chat с `@PulseMarketAIBot`.
- Отправь `/start`.
- Нажми `Dashboard`.
- Mini App должен открыться внутри Telegram.
- Первый экран должен показать Today's Pulse и метку `Research only · No trade execution`.

Troubleshooting:

- Если Telegram показывает обычное сообщение вместо Mini App, проверь, что на
  production установлено `MINI_APP_URL=https://app.pulsemarketai.com/app`, и
  перезапусти bot container.
- Если BotFather не принимает URL, проверь, что URL начинается с `https://`.
- Если страница не открывается, проверь `https://app.pulsemarketai.com/app` в
  браузере и Caddy container.

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

## UX-философия

PulseMarket AI Mini App — это продукт для рыночной аналитики, а не торговый
терминал.

Первый экран отвечает на один вопрос:

```text
Что сегодня действительно важно?
```

Дашборд делает акцент на:

- Пульсе дня как главной истории.
- Activity Radar как контексте публичной активности.
- Горячих рынках и резких движениях как discovery-слое.
- Поиске по теме.
- Видимом safety scope.

## Позиционирование

Конкуренты помогают пользователям быстрее торговать. PulseMarket AI помогает
быстрее понимать рынки.

Mini App избегает биржевых таблиц, экранов исполнения, блоков баланса и языка
сделок. Вместо этого используются крупные карточки, короткие объяснения,
спокойная типографика и прямые ссылки на Polymarket.

## Дизайн-ориентиры

Визуальное направление:

- информационная иерархия в духе Bloomberg;
- overview-карточки как в Apple Weather;
- чистота интерфейса Arc Browser;
- spacing Linear и Notion;
- premium fintech dashboard.

## Mobile-first принципы

- прокрутка одной рукой;
- крупные зоны нажатия;
- карточки читаются без zoom;
- dark mode по умолчанию;
- лёгкие static files без frontend build step.

## Safety Scope

PulseMarket AI Mini App работает только как аналитика:

- без торговли
- без кошельков
- без пополнений
- без приватных ключей
- без финансовых советов
