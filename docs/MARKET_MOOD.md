# Market Mood

Market Mood is a simple human-readable layer for Polymarket markets.

It helps users understand how a market feels today without reading raw metrics first.

## Labels

| EN | RU | Meaning |
| --- | --- | --- |
| Quiet | Тихо | No strong movement yet. |
| Active | Активно | People are already paying attention. |
| Heating up | Разогревается | Attention is rising. |
| Volatile | Волатильно | Probability moved enough to stand out. |
| Ending soon | Скоро завершение | The market is close to resolution. |

## Why It Exists

Raw numbers are useful, but they are not the first thing a new user needs.

Market Mood answers:

- Is this market calm or active?
- Is attention rising?
- Is the market close to resolution?
- Should I inspect the rules and probability more closely?

## Formula

The MVP version uses public market data only:

- Time to market end
- Probability movement when snapshots are available
- Public volume/activity

Rules:

- Ending soon: less than 24 hours to close
- Volatile: probability movement is at least 10 percentage points
- Heating up: movement is at least 5 percentage points or volume is high
- Active: volume or public activity is noticeable
- Quiet: no stronger signal yet

## Safety Scope

Market Mood is not financial advice.

It does not tell users to trade. It only helps users read public market context faster.
