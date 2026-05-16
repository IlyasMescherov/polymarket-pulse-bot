# YES / NO Side Analysis

PulseMarket AI does not just show market probability. It explains how the market distributes confidence between YES and NO.

## Available Data

Current Gamma market payloads include useful side-level fields:

- `outcomes`: usually `["Yes", "No"]`
- `outcomePrices`: current outcome prices as strings
- `lastTradePrice`
- `bestBid`
- `bestAsk`
- `spread`
- `clobTokenIds`
- `volume`, `volumeNum`, `volume24hr`
- `liquidity`, `liquidityNum`
- `enableOrderBook`

The current `PolymarketClient` already stores the full raw Gamma payload in `Market.raw`. Before this change the app only exposed `yes_probability`, which was derived from `outcomes` and `outcomePrices`.

## Current MVP

The MVP side engine uses:

- real YES / NO prices when `outcomes` and `outcomePrices` are available
- probability fallback when only `yes_probability` or `probability` is available
- volume and confirmation level to lower or raise side confidence

It returns:

- `side_summary`
- `dominant_side`
- `opposite_side`
- `yes_probability`
- `no_probability`
- `yes_price`
- `no_price`
- `side_balance`
- `side_tension`
- `side_confidence`
- `opposite_interest`
- `side_verdict`
- `side_risk_note`

## Fallback

If only probability is available:

- `yes_probability = probability`
- `no_probability = 100 - probability`
- `yes_price ~= probability / 100`
- `no_price ~= 1 - yes_price`
- side confidence is lowered because detailed side data is limited

If no usable side data is available:

- EN: `Not enough side data yet.`
- RU: `Данных по сторонам пока мало.`

The engine never invents side volume or order-book depth.

## Dominant Side Logic

- `YES` dominant: YES probability is at least 65%
- `NO` dominant: YES probability is at most 35%
- `BALANCED`: YES probability is between 40% and 60%
- `UNKNOWN`: side data is missing

Extreme reads:

- Extreme YES: YES probability is at least 85%
- Extreme NO: YES probability is at most 15%

## Confidence

Side confidence is:

- `high`: clear dominant side, strong confirmation, stronger volume
- `medium`: clear dominant side but mixed confirmation
- `low`: weak volume, probability-only fallback, balanced sides, or limited data

## API Coverage

Side fields are added to:

- `GET /api/today`
- `GET /api/markets/hot`
- `GET /api/markets/moves`
- `GET /api/search`
- `GET /api/smart-money/active`

## Mini App UX

Market cards now show a compact YES / NO strip:

- `YES 4% | NO 96%`
- horizontal split bar
- side read such as `Market leans NO`
- side and side confidence inside the score grid

The Analysis screen includes a dedicated `YES / NO balance` block.

## Telegram Bot UX

Market cards include:

- `YES`
- `NO`
- `Market leans`
- side read

The language stays interpretive. It describes what the market appears to price, without telling the user what to do.

## Limitations

Order-book depth, bid/ask spread interpretation, and side-specific volume are not fully modeled in this MVP. `bestBid`, `bestAsk`, `spread`, and `clobTokenIds` are available in Gamma payloads and can power a future depth layer.

## Safety Scope

Side analysis is research-only market interpretation.

It does not execute trades, connect wallets, accept funds, or provide financial advice.
