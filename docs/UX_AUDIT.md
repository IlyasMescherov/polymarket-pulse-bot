# UX Audit

PulseMarket AI should feel like a simple market intelligence assistant, not a trading terminal or raw data dashboard.

## Problem

Some screens exposed technical nouns before explaining user value:

- Smart Money sounded like a pro trading feature.
- Public Traders made wallets and ranks feel like the main point.
- Active Markets did not clearly say why the list mattered.
- Today’s Pulse showed useful metrics, but the reason to care was not always first.
- Pulse Score and Market Health appeared without enough plain-language meaning.
- Mini App cards repeated too many metrics before explaining the story.
- Empty states were correct, but not always actionable or calm.

## Why It Confuses Users

New Polymarket users usually need a simple answer first:

1. What is important today?
2. Why is this market here?
3. What should I watch next?
4. Is this bot trading for me?

Wallet hashes, ranks, raw volume, and unexplained scores can make the product feel like a professional trading terminal. That is the wrong first impression for PulseMarket AI.

## Fix

The UI now leads with meaning before data:

- `/start` explains the first three actions: Today’s Pulse, Activity Radar, and Search.
- Smart Money user-facing copy is reframed as Activity Radar.
- Active Markets became Markets getting attention.
- Public Traders became Active participants.
- Track Public Wallet became Follow public activity.
- Today’s Pulse cards now answer why the market matters and what to watch.
- Pulse Score and Market Health include short explanations where shown.
- Probability below 1% is shown as `<1%` or as unlikely instead of a confusing `0%`.
- Mini App first screen is anchored around Today’s Pulse.
- Mini App cards show title, probability, Pulse Score, and a short reason before secondary details.
- Landing page now uses the same message: understand what matters on Polymarket.

## Files Changed

- `bot/utils/i18n.py`
- `bot/keyboards/main.py`
- `bot/handlers/smart_money.py`
- `bot/services/smart_money_analyzer.py`
- `bot/services/today_pulse.py`
- `bot/services/movement_explainer.py`
- `bot/services/health_server.py`
- `bot/services/content_publisher.py`
- `bot/utils/formatting.py`
- `bot/main.py`
- `miniapp/index.html`
- `miniapp/app.js`
- `miniapp/styles.css`
- `landing/index.html`
- `landing/styles.css`
- `tests/`
