# Market Memory

PulseMarket AI does not just read the market. It remembers how markets change over time.

Market Memory reuses the existing `market_snapshots` table. No new trading, wallet, balance, or order logic is added.

## What It Compares

- previous probability versus current probability
- previous volume versus current volume
- recent volume growth between snapshots
- time left before resolution
- whether attention is holding, cooling, or appearing for the first time

## User-Facing Outputs

- `market_memory_summary`
- `memory_pattern`
- `changed_since_last_seen`
- `historical_context`

When history is weak, PulseMarket says:

`Not enough history for comparison yet.`

Russian:

`Пока мало истории для сравнения.`

## Example Reads

- Activity is holding, but probability barely changed.
- Compared with the previous brief, this market stands out more.
- The market is close to resolution.
- Активность держится, но вероятность почти не изменилась.
- По сравнению с прошлым обзором рынок стал заметнее.

## Safety Scope

Market Memory is interpretation only. It does not tell users what to do and does not execute anything.
