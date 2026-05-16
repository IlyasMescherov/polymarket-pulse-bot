# Event Graph Model

PulseMarket AI is evolving into an event intelligence desk for Polymarket.

The product should not only show individual markets. It should explain the story behind a group of related markets.

## Core Objects

### Market

A single Polymarket market with outcomes, probability, volume, memory, regime, and news context.

### Story Cluster

A story cluster is a research-only object that groups related markets around one event or narrative.

Fields:

- `story_cluster_id`
- `story_title`
- `story_summary`
- `primary_category`
- `linked_markets`
- `related_market_ids`
- `main_market_id`
- `dominant_outcome`
- `runner_up_outcome`
- `source_count`
- `official_source_signal`
- `news_urgency`
- `market_reaction_score`
- `what_changed`
- `why_it_matters`
- `what_to_verify`
- `confidence_level`

## Grouping Rules

Primary grouping:

- `eventSlug`
- `eventTitle`
- Gamma event markets

Fallback grouping:

- shared entities
- shared country, team, person, or topic
- shared category
- matched external news entities
- related source matches

## Story Quality Threshold

A story is shown only when it is strong enough:

- at least 2 linked markets, or
- 1 market with strong news impact, or
- 1 market with official-source context.

Weak single-market stories are not shown as Top Story. The Mini App falls back to the market-based Today layout.

## Ranking

Top Story ranking uses:

- news urgency
- market reaction score
- source count
- official-source context
- linked markets count
- freshness

## Safety

Story clusters explain context. They do not tell users what action to take.
