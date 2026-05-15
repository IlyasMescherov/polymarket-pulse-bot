# AI Reasoning Layer

PulseMarket AI uses an optional AI Context Engine on top of the existing discovery and intelligence layer.

The role of AI is not to predict outcomes. It acts as a calm market intelligence analyst that helps users understand public market context.

## What It Does

- Explains why people may care about a market.
- Summarizes market meaning in plain language.
- Highlights what to watch next: probability changes, activity, time left, and resolution rules.
- Groups markets into event categories.
- Creates short daily narratives for the Mini App.
- Interprets what market activity means through `what_this_means`.
- Separates attention from conviction so users can see whether activity changed expectations or only visibility.
- Labels public activity as Noise, Moderate attention, Strong interest, or Meaningful attention shift.
- Produces a safe fallback when no AI key is configured.

## What It Does Not Do

- No trade execution
- No financial advice
- No outcome certainty
- No order routing
- No wallet access
- No private-key handling
- No seed-phrase handling

## AI Context Engine

Service:

```text
bot/services/ai_context_engine.py
```

Inputs:

- market title
- market description when available
- probability
- probability movement
- volume
- Pulse Score
- Market Mood
- time left
- event category

Outputs:

- `why_people_care`
- `simple_read`
- `what_to_watch`
- `attention_summary`
- `topic_narrative`
- `market_mood_reasoning`
- `what_this_means`
- `attention_signal`
- `attention_vs_conviction`
- `related_topics`
- human probability interpretation

See [AI_INTERPRETATION_LAYER.md](AI_INTERPRETATION_LAYER.md) for the product rules around interpretation.

## Fallback Mode

If `OPENAI_API_KEY` is missing, PulseMarket AI still works with deterministic templates. The fallback keeps explanations short, safe, and meaning-first.

## Environment

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

Secrets must never be logged or committed.
