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
- whether activity looks like background noise or a stronger attention shift
- whether attention is moving together with probability
- which related topics matter
- what to watch next

It does not tell users what to do.

## New Interpretation Fields

Market API objects can include:

- `what_this_means`
- `attention_signal`
- `attention_vs_conviction`
- `related_topics`

Daily briefing payloads can include:

- `interpretation`

## Attention Signal

Allowed labels:

- Noise
- Moderate attention
- Strong interest
- Meaningful attention shift

Russian UI labels:

- Шум
- Умеренное внимание
- Сильный интерес
- Значимое движение внимания

These labels describe public attention, not future outcomes.

## Attention vs Conviction

PulseMarket separates attention from conviction:

- Attention can rise while probability stays almost unchanged.
- Probability and attention moving together can make the market read stronger.
- Activity near resolution can rise even without a strong expectation change.

This is the main interpretation advantage over raw dashboards.

## Safety Scope

The interpretation layer must not include:

- buy/sell advice
- outcome certainty
- certainty language
- private information claims
- copy-trading instructions

Everything is based on public market data and optional AI summaries.

## Fallback

If `OPENAI_API_KEY` is missing or the API fails, deterministic fallback text still produces:

- context-aware market meaning
- attention signal
- attention vs conviction
- related topics
- daily interpretation
