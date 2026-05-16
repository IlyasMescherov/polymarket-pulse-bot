# AI Market Interpretation Layer

PulseMarket AI is an interpretation layer for Polymarket, not a prediction engine.

The product should answer one core question:

```text
What does this market activity mean?
```

## Role

AI acts as a calm market intelligence analyst. It explains:

- why a market is getting attention
- what changed around the market
- whether the read is weak, notable, or more convincing than usual
- whether attention is moving together with probability
- how YES and NO sides are balanced
- how the market changed compared with prior snapshots
- what behavior regime the market is currently in
- which related topics matter
- what to watch next

It does not tell users what to do.

## New Interpretation Fields

Market API objects can include:

- `what_this_means`
- `insight_strength`
- `main_tension`
- `confidence_level`
- `attention_vs_conviction`
- `related_topics`
- `market_memory_summary`
- `market_regime`
- `regime_reason`
- `memory_pattern`
- `changed_since_last_seen`
- `historical_context`
- `side_summary`
- `dominant_side`
- `yes_probability`
- `no_probability`
- `side_balance`
- `side_tension`
- `side_confidence`
- `side_verdict`

Daily briefing payloads can include:

- `interpretation`

## Insight Strength

Allowed labels:

- Weak confirmation
- Interest is present
- More noticeable than usual
- Strong attention
- More convincing than usual

Russian UI labels:

- Слабое подтверждение
- Есть интерес
- Рынок заметнее обычного
- Сильное внимание
- Движение выглядит убедительнее обычного

These labels describe public attention, not future outcomes.

## Attention vs Conviction

PulseMarket separates attention from conviction:

- Attention can rise while probability stays almost unchanged.
- Probability and attention moving together can make the market read stronger.
- Activity near resolution can rise even without a strong expectation change.

This is the main interpretation advantage over raw dashboards.

## YES / NO Side Balance

Polymarket markets usually have two sides. PulseMarket now interprets whether the market leans toward YES, NO, or remains balanced.

The side layer explains:

- current YES and NO probabilities
- which side is dominant
- whether side confidence is low, medium, or high
- whether the opposite side still has visible interest
- what the side balance means for understanding the market

This is interpretation only. It does not tell the user what to do.

## Market Memory

Market Memory compares the current market with stored `market_snapshots`.

It can explain whether:

- activity is holding across briefs
- interest cooled after an earlier active period
- probability barely moved over 24h
- attention grew faster than probability
- the market is close to resolution

If history is weak, the product says so directly instead of inventing context.

## Market Regime

Market Regime names the current behavior type:

- Quiet market
- Market became active
- Short-term attention
- Near resolution
- News-driven reaction
- Sustained interest
- Weak confirmation
- More confident move

These labels describe market behavior, not future outcomes.

## Safety Scope

The interpretation layer must not include:

- directional advice
- outcome certainty
- certainty language
- private information claims
- copy-trading instructions

Everything is based on public market data and optional AI summaries.

## Fallback

If `OPENAI_API_KEY` is missing or the API fails, deterministic fallback text still produces:

- context-aware market meaning
- insight strength
- attention vs conviction
- related topics
- daily interpretation
- market memory fallback
- market regime fallback
