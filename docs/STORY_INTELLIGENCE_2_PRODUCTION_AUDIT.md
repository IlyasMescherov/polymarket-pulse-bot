# Story Intelligence 2.0 Production Audit

Date: 2026-05-17

Live commit: `4ba6158 Fix source relevance and story outcome trust blockers`

Production verdict: GREEN

PulseMarket AI is an event intelligence desk for Polymarket. This release keeps the product research-only: no trading, no wallet, no deposits, no order execution, no copy trading, and no buy/sell/bet recommendations.

## What Was Deployed

- Story Intelligence 2.0 for event-level market interpretation.
- Story Context visibility in Analysis / Разбор from Today story cards, Hot Markets, and matching loaded Today state.
- Source relevance hardening for market-level related news.
- Outcome label trust fix for story-linked market previews.
- Hot/Search fallback protection so slow upstream behavior does not leave the Mini App hanging.
- RU localization polish, including the Russian kicker `СОБЫТИЙНЫЙ РАДАР`.

## Production Timings

Warm production timings after deploy:

| Endpoint | Warm timing |
|---|---:|
| `/api/today` | ~0.39s |
| `/api/markets/hot` | ~0.56s |
| `/api/search?q=bitcoin` | ~0.56s |

The cached Today path remained fast after Story Intelligence 2.0. Heavy market/news/story work stays outside the normal warm request path.

## Trust Checks Passed

- Peru presidential markets no longer receive unrelated White House/Fed items as strong related news.
- `official_source_signal` stays `false` when official-source relevance is weak.
- `confidence_from_news` stays low when source-market relevance is weak.
- Stopword-heavy `matched_terms` such as `and`, `the`, `who`, and `known` are filtered out.
- The unrelated `Peng` outcome leak in Trump/Iran/Strait story cards was fixed.
- `Strait or Hormuz` safely matches the same-market outcome label `Strait / Hormuz`.
- Russian UI uses `СОБЫТИЙНЫЙ РАДАР` instead of `EVENT INTELLIGENCE DESK`.
- No trading advice wording appeared in checked user-facing output.

## Source Relevance Standard

Source credibility is not enough to make a source relevant to a market.

Official sources only affect market-level confidence when the source has strong entity/topic relevance to that market. A trusted source with a weak or generic match is either omitted from `related_news` or treated as weak/background context.

High `confidence_from_news` requires conservative evidence, not source quality alone:

- confirmed catalyst-level relevance, or
- strong possible catalyst relevance, and
- meaningful entity/topic match, and
- no stopword-only match.

## Outcome Trust Standard

Story cards must only show a specific outcome when that outcome belongs to the exact market being previewed.

If mapping is uncertain, the Mini App uses neutral copy instead of reusing another market's dominant outcome from the same story cluster.

Safe neutral copy examples:

- `Рынок связан с одним из вариантов.`
- `Рынок сместился к одному из вариантов.`

## Remaining Future Improvements

- Source trail: explain why a source matched a market or story.
- Evidence timeline: show what changed, when it changed, and how the market reacted.
- Telegram bot product polish so `/today` feels like an event intelligence brief rather than an old market list.
- Playwright Mini App tests for Story Context, Analysis, Search fallback, and RU localization.
- Personal briefing and retention loop for saved markets, topics, and recurring briefings.
