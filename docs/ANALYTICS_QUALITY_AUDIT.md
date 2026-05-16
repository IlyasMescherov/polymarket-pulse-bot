# Analytics Quality Audit

Mini App / Today | DATA_RETELLING | Cards often repeat probability, mood, and score without a decisive reader takeaway.
Mini App / Today | NO_INTERPRETATION | Main story needs a stronger "what this means" layer before secondary metrics.
Mini App / Today | VISUAL_NOISE | Multiple pills and repeated containers slow down scanning.
Mini App / Radar | NO_CROSS_MARKET | Related attention clusters are not surfaced as a shared narrative.
Mini App / Radar | DATA_RETELLING | Public activity appears before explaining whether expectations changed.
Mini App / Search | NO_INTERPRETATION | Search results show market cards but do not synthesize the query context enough.
Mini App / Saved | NO_INTERPRETATION | Saved markets behave like storage, not a personal briefing feed.
Mini App / More | DUPLICATE_SUMMARY | Learning cards use similar explanatory rhythm across product concepts.
Mini App / Analysis Sheet | NO_CONFIDENCE | The sheet needs a clear attention-vs-conviction read.
Telegram / start | NO_INTERPRETATION | Onboarding explains features more than the product habit.
Telegram / today | DATA_RETELLING | Cards still lean on score and probability before the market read.
Telegram / smart | GPT_PHRASING | Public activity language can feel template-driven instead of editorial.
Telegram / search | NO_INTERPRETATION | Search flow should explain why returned markets match the query.
Telegram / market cards | VISUAL_NOISE | Buttons and metrics can crowd the core interpretation.
Telegram / share | DUPLICATE_SUMMARY | Share text should carry one concise takeaway instead of repeating generic feature copy.
API / api/today | NO_CROSS_MARKET | Response supports per-market context but needs grouped narrative analysis.
API / api/search | NO_INTERPRETATION | Query summary should distinguish topic relevance from market conviction.
API / api/markets/hot | DATA_RETELLING | Hot markets need a human verdict, not only hotness metrics.
API / api/smart-money/active | NO_CONFIDENCE | Public activity requires a caution/conviction distinction.
Product-wide | BANNED_LANGUAGE | Legacy market-jargon terms should be filtered before any generated text is shown.
Product-wide | MIXED_LANGUAGE | Generated context must validate language consistency before display.

## Post AIInsightEngine audit

Market: LoL: Gen.G vs T1 (BO3) - LCK Rounds 1-2
Old output: "Probability moved enough to make this market stand out."
Why weak: It describes selection logic, not the market tension. It does not explain why event timing matters.
Better version: "Probability moved together with volume, which makes the reaction stronger than usual."
Fix: Added `quick_take`, `main_tension`, and resolution-aware wording in `AIInsightEngine`.

Market: Will Bulgaria win Eurovision 2026?
Old output: "As the event nears, fluctuations in Bulgaria's candidate performance or public reception could impact market dynamics."
Why weak: Generic GPT-style explanation; it could apply to almost any Eurovision market.
Better version: "The topic is visible, but the market still lacks enough confirmation for a strong read."
Fix: Added weak-data fallback and category-specific culture voice.

Market: Will Trump say "Nuclear" during events with Xi Jinping?
Old output: "While there is moderate attention, conviction in the outcome appears low given the current probability."
Why weak: Too abstract. It does not name the contradiction between a watched diplomatic event and a low-probability term.
Better version: "The event is visible, but the probability line says participants have not repriced the wording risk."
Fix: Added `main_tension` and attention-vs-conviction separation.

Market: Strait of Hormuz traffic returns to normal by May 15?
Old output: "The outcome will provide insights into shipping trends in a vital region..."
Why weak: Describes the subject area rather than the market read.
Better version: "The market is near resolution, so the exact criteria matter more than the headline."
Fix: Added resolution proximity logic and `resolution_note`.

Market: Will Bitcoin hit $150k by June 30, 2026?
Old output: "Investors are interested in Bitcoin's price movements due to its historical volatility..."
Why weak: Generic crypto boilerplate and too close to investment framing.
Better version: "Volume is present, but the market still treats the outcome as unlikely."
Fix: Added contradiction detection for strong volume with low probability.

Market: Internazionali BNL d'Italia: Jannik Sinner vs Daniil Medvedev
Old output: "Fans and analysts are interested in the match..."
Why weak: Reads like a sports preview, not market interpretation.
Better version: "Event timing made this market more visible; late information can matter more than long-term context."
Fix: Added sports category voice and resolution-window language.

Market: Israel x Syria security agreement by June 30?
Old output: "The low probability suggests skepticism..."
Why weak: Retells probability without explaining the geopolitics/expectations tension.
Better version: "The market reflects cautious diplomatic expectations rather than a firm repricing."
Fix: Tuned politics category voice around diplomacy and repricing.

Market: /api/search?q=bitcoin results
Old output: Multiple Bitcoin cards reused the same "price movements / potential returns" explanation.
Why weak: Duplicate phrasing made different expiries feel identical.
Better version: "Short-term crypto markets can move faster than longer-term expectations; volume decides how strong the read is."
Fix: Added category voice plus `main_tension` and `confidence_level` fields for every API market object.
