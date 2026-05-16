# Prompt Eval V4

Goal: verify that the AI interpretation layer sounds like a market editor, not a generic summary tool.

Scale: 1 = weak, 5 = strong.

| Market title | Category | Probability | Volume | Old quick_take | New quick_take | Old what_this_means | New what_this_means | Score | Why better / worse |
|---|---:|---:|---:|---|---|---|---|---:|---|
| LoL: Gen.G vs T1 (BO3) - LCK Rounds 1-2 | esports | 57% | high | Probability moved enough to make this market stand out. | Probability moved together with volume, which makes the reaction stronger than usual. | Close to resolution, so attention can rise. | Near resolution, exact rules and timing matter more than usual. | 5 | Names why the move reads stronger and why timing matters. |
| Will Bulgaria win Eurovision 2026? | culture | low | medium | Public reception could impact market dynamics. | The topic is visible, but the read is still weak. | Candidate performance may affect sentiment. | The market needs stronger confirmation before drawing much from it. | 4 | Removes generic event copy and gives a confidence read. |
| Will Trump say "Nuclear" during events with Xi Jinping? | politics | low | medium | Moderate attention with low conviction. | The event is visible, but expectations barely moved. | The wording outcome could change later. | Participants have not repriced the wording risk yet. | 5 | Explains the tension between attention and probability. |
| Strait of Hormuz traffic returns to normal by May 15? | global | low | medium | Shipping trends may influence economic discussions. | The deadline makes the criteria more important than the headline. | Outcome provides insight into a route. | Near resolution, the official measurement method matters most. | 5 | Moves from subject summary to resolution-aware interpretation. |
| Will Trump say "Iran" during events with Xi Jinping? | politics | low | high | Attention around political headlines. | Interest is present, but expectations did not move. | Close to resolution. | More interest than conviction; check exact wording criteria. | 5 | Adds contradiction and practical verification target. |
| Will Bitcoin hit $150k by June 30, 2026? | crypto | low | high | Investors care about Bitcoin volatility. | Volume is present, but the market still treats the outcome as unlikely. | Higher attention may affect dynamics. | This is interest around volatility, not a broad repricing yet. | 5 | Avoids investment framing and separates attention from conviction. |
| Will Bitcoin hit $150k by September 30? | crypto | low | high | Digital asset followers track the target. | The short-term expiry makes confirmation fragile. | Exchange-specific data matters. | Price movement and Binance rules matter more than broad crypto sentiment. | 4 | More concrete, though still depends on available market data. |
| Will Bitcoin hit $150k by December 31? | crypto | low | medium | Bitcoin could move on sentiment. | Longer expiry keeps the read calmer than short-term Bitcoin markets. | Outcome depends on Binance price data. | The market is about long-horizon conviction, not a single daily move. | 4 | Distinguishes short-term volatility from long-horizon expectations. |
| Internazionali BNL d'Italia: Jannik Sinner vs Daniil Medvedev | sports | medium | high | Fans and analysts are interested in the match. | Event timing made this market more visible. | Stakeholders monitor health and form. | Short resolution window means late news can matter more than broad form. | 5 | Turns sports preview text into market timing logic. |
| Will Trump say "Strait" or "Hormuz" during events with Xi Jinping? | politics | low | medium | Language matters in diplomacy. | The diplomatic event is visible, but the wording market remains cautious. | The market reflects U.S.-China context. | Probability stability suggests the specific phrase has not been repriced. | 5 | Adds narrow wording-market interpretation. |
| Israel x Syria security agreement by June 30? | politics | low | medium | Low probability suggests skepticism. | The market reflects cautious diplomacy, not a firm repricing. | Discussions could shift perceptions. | Participants are not treating an agreement as the base case yet. | 5 | Stronger editorial conclusion with no advice. |
| AI-related announcement market | ai | unknown | low | AI attention increased today. | The news cycle is visible, but conviction remains limited. | Announcement-driven interest may matter. | Discussion is ahead of market confirmation. | 4 | Category voice is distinct and avoids template repetition. |
| Sports playoff market | sports | medium | medium | Market is active near the event. | The short event window is doing most of the work here. | Probability may change before the match. | Late information can change the read faster than usual. | 4 | Better timing logic; still needs live team/news data for more context. |
| Culture release market | culture | low | low | Users started watching this topic. | The topic is visible, but the market read is still thin. | Public discussion could influence it. | Audience attention exists, but confirmation is weak. | 4 | Human and concise; keeps confidence low. |
| Global macro event market | global | medium | medium | Global events are shaping the read. | The broader event cycle is visible, but no single theme dominates. | Related headlines matter. | Cross-market grouping is needed before treating this as a theme. | 4 | Better framing, with a clear next analytical need. |

## Summary

Average score: 4.6 / 5.

Main improvements:
- The new layer names the contradiction instead of repeating metrics.
- `insight_strength` tells the user how much confidence to place in the read.
- Category voice is more distinct across politics, crypto, sports, AI, culture, and global markets.
- The Explain / Analysis layer now has a market-editor structure: quick take, what happened, main tension, interpretation, attention vs conviction, strength, checks, related topics, and resolution rules.
