# News Impact Engine

The News Impact Engine classifies how external information relates to a market or story.

It does not decide outcomes. It helps users understand whether market movement is supported by external context.

## Impact Types

| Type | Meaning |
|---|---|
| `official_confirmed` | A primary or official source matched the market story. |
| `multiple_sources` | Several sources cover the same theme. |
| `social_only` | Context comes mainly from social discussion. |
| `stale_context` | Matched coverage is older. |
| `market_moved_without_news` | Market reaction is stronger than matched outside context. |
| `news_without_market_reaction` | Coverage exists, but the market reaction is limited. |
| `weak_external_context` | Outside context is present but not strong enough. |

## Labels

EN:

- Official source confirmed
- Multiple sources cover this
- Social-only context
- Stale context
- Market moved without strong news
- News present, market barely reacted
- Weak external context

RU:

- Есть официальное подтверждение
- Несколько источников по теме
- Только социальный фон
- Новость уже старая
- Рынок двинулся без сильного новостного фона
- Новость есть, но рынок почти не отреагировал
- Внешний контекст слабый

## Confidence

Confidence is based on:

- official-source presence
- number of distinct sources
- source credibility
- freshness
- market reaction strength

## Product Use

The impact label appears in:

- Today Top Story
- Story cards
- market cards when relevant
- Analysis / Разбор

The goal is to answer:

> Why might this market be moving now?

If external context is weak, PulseMarket says that directly.
