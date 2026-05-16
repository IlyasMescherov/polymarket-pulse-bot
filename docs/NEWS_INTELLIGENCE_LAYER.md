# News Intelligence Layer

PulseMarket AI now has an external information layer for matching public market movement with outside context.

The goal is not to predict outcomes or tell users what to do. The goal is to answer: what outside information may explain why this market became more visible?

## MVP Sources

Implemented now:

- Public RSS feeds from mainstream and category-specific sources.
- Public official RSS feeds from government, regulator, central bank, and AI company sources.

Stubs prepared for later:

- X public posts through an approved API/provider.
- Telegram public channels.
- News API provider.

The app does not parse closed sources, bypass paywalls, or scrape private channels.

## Data Model

New tables:

- `external_sources`: source type, name, URL, credibility score, category, active flag.
- `external_events`: title, summary, URL, publish time, category, entities/topics, urgency, credibility, raw payload.
- `market_event_links`: market to event relevance score and match reason.

If the tables are not migrated yet, production falls back to in-memory events and keeps serving market data.

## Matching Logic

Markets are matched to external events through:

- title and slug keywords
- entities such as Trump, Iran, Bitcoin, OpenAI, Fed
- category overlap
- event urgency
- source credibility

Each market receives:

- `news_context`
- `latest_relevant_news`
- `source_count`
- `credible_source_count`
- `social_heat`
- `telegram_heat`
- `x_heat`
- `official_source_signal`
- `news_urgency`
- `why_moving_now`
- `what_changed_outside_market`
- `confidence_from_news`
- `news_risk_note`

## Product Language

Good language:

- “External coverage adds context, but official confirmation is still limited.”
- “An official source is part of the backdrop.”
- “Check official sources before drawing a strong conclusion.”

Avoid:

- trading direction
- certainty claims
- private-source claims
- paywalled or closed-source assumptions

## Mini App UX

Market cards now show:

- a small news intensity badge
- an official/source-context badge
- one short line about why the outside backdrop matters

Analysis / Разбор now includes:

- why the market may be moving now
- latest outside context
- source status
- what to verify

Today includes a compact `news_themes` layer so the daily view can explain which themes the market is reacting to.
