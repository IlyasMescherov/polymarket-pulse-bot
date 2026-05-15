# Event Category System

PulseMarket AI uses event categories to make Polymarket easier to scan.

Instead of showing raw markets as one long list, the Mini App lets users filter the briefing by the kind of event they care about.

## Categories

English:

- All
- Politics
- Crypto
- AI
- Sports
- Esports
- Global
- Culture

Russian:

- Все
- Политика
- Крипто
- AI
- Спорт
- Киберспорт
- Мировые
- Культура

## Where Categories Are Used

- Mini App category selector
- Today tab filtering
- Activity Radar filtering
- Search suggestions
- Daily narrative summaries
- User interest preferences

## How Classification Works

Service:

```text
bot/services/event_categories.py
```

The classifier reads public market text:

- title
- description
- tags
- category fields

It then matches lightweight keyword groups. If a market cannot be classified confidently, it falls back to a broad global category.

## Product Goal

Categories help users answer:

```text
What part of the world or culture is this market about?
```

This keeps the product approachable for new users and avoids a dense terminal-style experience.
