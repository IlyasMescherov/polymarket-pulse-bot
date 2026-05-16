# Market Regimes

Market Regime describes the current behavior type of a Polymarket market.

It helps users understand whether a market is quiet, close to resolution, short-term active, or showing stronger confirmation through both probability and volume.

## Regime Labels

English:

- Quiet market
- Market became active
- Short-term attention
- Near resolution
- News-driven reaction
- Emotional reaction
- Sustained interest
- Weak confirmation
- More confident move

Russian:

- Спокойный рынок
- Рынок оживился
- Краткосрочное внимание
- Перед завершением
- Новостная реакция
- Эмоциональная реакция
- Устойчивый интерес
- Слабое подтверждение
- Более уверенное движение

## Classification Rules

- ending soon + public activity: Near resolution
- activity up + flat probability: Short-term attention
- probability moved + weak volume: Weak confirmation
- probability moved + strong volume: More confident move
- related markets moving together: News-driven reaction
- low movement + low volume: Quiet market

## API Fields

- `market_regime_key`
- `market_regime`
- `regime_reason`

## Product Role

Regimes are not predictions. They are plain-language behavior labels for reading market dynamics.
