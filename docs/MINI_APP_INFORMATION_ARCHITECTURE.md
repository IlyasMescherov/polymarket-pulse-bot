# Mini App Information Architecture

PulseMarket AI Mini App should feel like an event intelligence front page, not a raw market feed.

## Today

Today is the primary daily ritual.

Order:

1. Header
2. Category chips
3. Daily narrative
4. Top Story, if quality threshold is met
5. Story cards, if quality threshold is met
6. Market fallback, if stories are weak
7. Hot Markets
8. Sharp Moves, only when real movement exists

## Top Story Rules

Top Story is shown only when:

- at least 2 related markets exist, or
- strong news impact exists, or
- official-source context exists.

If not, the UI keeps the existing market-based Today card.

## Story Card

Story card shows:

- story title
- category visual
- source badge
- linked market count
- short why it matters
- 2-3 linked markets
- Open story

It should feel like an intelligence brief.

## Market Card

Market cards remain outcome-first:

- real outcomes from Polymarket
- outcome split bar
- short human read
- news context when relevant
- Open
- Analysis

The event layer is additive. It must not break Hot Markets, Search, Saved, or existing outcome rendering.

## Analysis / Разбор

Analysis shows Story context only when the market is part of a qualified story.

Story context includes:

- story title
- what changed
- news backdrop
- official-source status
- linked market count

If story data is weak, Analysis hides this block and keeps the regular market analysis.

## Empty And Quiet Days

If no strong stories exist, PulseMarket should not invent one.

The app should say the market is quiet or continue with selected markets.
