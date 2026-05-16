# Outcome Display Logic

PulseMarket AI must not force every Polymarket market into a YES / NO view.
Gamma markets can appear as standalone binary markets, grouped sports markets, or multi-outcome events.

## Gamma Fields

Current Gamma payloads expose:

- `outcomes`: outcome labels, often JSON strings such as `["Yes", "No"]`
- `outcomePrices`: current prices aligned by outcome index
- `clobTokenIds`: token ids aligned by outcome index
- `groupItemTitle`: event-level label for grouped markets, for example `Manchester City FC`
- `question`, `title`, `slug`
- `events`: parent event metadata; `/events?slug=...` can return sibling `markets`
- `sportsMarketType`, `enableOrderBook`, `bestBid`, `bestAsk`, `spread`

The market endpoint often returns sports event children as binary markets:
`Will Manchester City FC win...?` with `["Yes", "No"]`.
The parent event can still be a moneyline-style display with `Chelsea / Draw / Manchester City`.
For that reason PulseMarket enriches grouped markets from `/events?slug=...` when available.

## Supported Outcome Types

- `binary_yes_no`: real `Yes` / `No` outcomes.
- `binary_custom`: exactly two custom outcomes, such as `Over / Under`.
- `sports_moneyline`: event-level sports outcomes, such as `Frankfurt / Draw / Stuttgart`.
- `multi_outcome`: three or more custom outcomes.
- `unknown`: outcome data is missing.

## Detection Rules

1. If event sibling markets are available, use `groupItemTitle` plus each sibling YES price as the displayed outcome list.
2. If outcomes are exactly `Yes` and `No`, use YES / NO.
3. If there are two outcomes and they are not `Yes` / `No`, use the real labels.
4. If there are three sports/event outcomes, show all three.
5. If there are more than three outcomes, cards show the top options and Analysis can show the full list.
6. If outcomes are missing and the question starts with `Will`, use a YES / NO fallback.
7. If data is missing and the title is not clearly binary, show an unavailable outcome state.

## UI Rules

- Use green/red YES / NO only for `binary_yes_no`.
- For custom outcomes, show real outcome labels.
- For sports moneyline, show team/draw labels.
- Do not display YES / NO when `should_use_yes_no = false`.
- Analysis starts with the correct balance title:
  - `YES / NO balance`
  - `Outcome balance`
  - `Market outcomes`

## Limitations

Order-book depth, side-specific volume, and bid/ask spread are not fully modeled in this layer.
Those fields are available in Gamma for future depth analysis, but this MVP focuses on honest outcome display.
