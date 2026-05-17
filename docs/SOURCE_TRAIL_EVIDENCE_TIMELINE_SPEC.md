# Source Trail / Evidence Timeline Spec

Date: 2026-05-17

Current production verdict: GREEN

Live logic commit: `4ba6158 Fix source relevance and story outcome trust blockers`

Product principle: PulseMarket AI is an event intelligence desk for Polymarket. The product is research-only: no trading advice, no wallet, no deposits, no order execution, no copy trading, and no buy/sell/bet recommendations.

## 1. Product Goal

Source Trail explains why PulseMarket AI connects a source to a market.

The trust chain should be visible:

`source -> event/story -> market relevance -> market reaction -> what to verify next`

Today, PulseMarket can classify market-news relevance, but the user mostly sees the result: source badges, catalyst labels, Story Context, and related news. Source Trail makes the reasoning inspectable without turning the UI into a terminal.

The user should be able to answer:

- Which source is being used?
- Why is this source connected to this market?
- What entity, country, team, topic, or outcome matched?
- Did the market react after this source appeared?
- Is this confirmed, possible, background, weak, or unclear?
- What should I verify before drawing a stronger conclusion?

Source Trail improves trust because it makes the app show its work. It should not claim causality unless evidence is strong.

## 2. Current Payload Inspection

Existing backend fields already available:

- `related_news`: title, summary, url, source, source_type, published_at, category, relevance_score, match_reason, credibility_score.
- `NewsImpact`: impact type, label, confidence, source count, official source signal, catalyst type, catalyst label, evidence strength, movement explanation, what to verify next.
- `StoryCluster`: story title, linked markets, source count, official source signal, news urgency, market reaction score, what happened, affected markets, movement timing, likely catalyst, catalyst evidence, price/probability context, what to verify next.
- Mini App Analysis already renders Story Context and dedupes repeated rows with `uniqueAnalysisRows`.

Current gap:

- `match_reason` is present but not structured enough for users.
- Source credibility and relevance are separated in backend logic, but the user cannot inspect the separation.
- Analysis does not show source-level evidence trail.
- There is no timeline of source publication vs market reaction.

## 3. Data Model

Add a minimal source trail object. It should be generated during the same cached/background path that already builds news/story context.

Recommended object name:

`source_trail`

Shape:

```json
{
  "source_name": "White House",
  "source_type": "official",
  "source_url": "https://...",
  "published_at": "2026-05-17T09:00:00Z",
  "matched_entities": ["Iran", "Trump"],
  "matched_topics": ["diplomacy"],
  "match_reason": "Matched entities: Iran, Trump",
  "relevance_level": "strong",
  "catalyst_type": "confirmed_catalyst",
  "market_reaction_summary": "Market reaction became more visible after the source appeared.",
  "what_to_verify_next": ["Official source text", "Resolution rules", "Related markets"]
}
```

Minimal fields:

| Field | Type | Notes |
|---|---|---|
| `source_name` | string | Human source label. |
| `source_type` | string | `official`, `rss`, `news_api`, `x`, `telegram`, etc. |
| `source_url` | string | Public source URL. Empty only if source has no safe URL. |
| `published_at` | string/null | ISO timestamp when available. |
| `matched_entities` | list[string] | Meaningful entities only; no stopwords. |
| `matched_topics` | list[string] | Meaningful topics only. |
| `match_reason` | string | User-safe explanation, not raw debug text. |
| `relevance_level` | string | `strong`, `medium`, `weak`. |
| `catalyst_type` | string | `confirmed_catalyst`, `possible_catalyst`, `background_context`, `weak_signal`, `no_clear_signal`. |
| `market_reaction_summary` | string | Short editorial sentence. |
| `what_to_verify_next` | list[string] | 2-4 checks. |

Optional later fields:

- `relevance_score`
- `credibility_score`
- `reaction_lag_minutes`
- `source_quality_label`
- `is_official`
- `is_same_entity_match`
- `is_same_country_match`
- `matched_market_fields`

### Evidence Timeline Item

Recommended object name:

`evidence_timeline`

Shape:

```json
{
  "timestamp": "2026-05-17T09:00:00Z",
  "type": "source_published",
  "title": "Official statement published",
  "source_name": "White House",
  "summary": "Official source matched Iran and Trump.",
  "confidence": "high"
}
```

Allowed timeline item types:

- `source_published`
- `market_reaction`
- `story_clustered`
- `official_confirmation`
- `verification_needed`

Timeline should only appear when there is enough evidence to order events meaningfully.

## 4. API Changes

Expose Source Trail in existing cached payloads. Do not add heavy AI or external fetches to request paths.

### `/api/today`

Add to market objects only when reliable:

- `source_trail`
- `evidence_timeline`
- `has_source_trail`
- `source_trail_summary`

Add to story clusters:

- `source_trail`
- `evidence_timeline`
- `source_trail_summary`

Keep `/api/today` fast:

- Build these fields in background refresh.
- Store them inside the cached Today payload.
- Warm request path reads cache only.
- If trail generation fails, return existing market/story fallback.

### Market Analysis Payload

Analysis should read the fields from already-loaded Today state where possible:

- `source_trail`
- `evidence_timeline`
- `source_trail_summary`
- existing Story Context fields.

If an endpoint later serves per-market Analysis, it should reuse cached source trail artifacts or precomputed DB records. It should not call OpenAI or refetch news on open.

### Story Cluster Payload

Add source trail to qualified stories:

```json
{
  "story_title": "Iran / US diplomacy",
  "source_trail": [...],
  "evidence_timeline": [...],
  "source_trail_summary": "Official context matched Iran and Trump; market reaction became more visible after the update."
}
```

### `related_news` Objects

Keep `related_news` as the lightweight source list, but add structured match fields:

- `matched_entities`
- `matched_topics`
- `relevance_level`
- `catalyst_type`

Do not expose raw stopword-heavy match reasons. User-facing `match_reason` should be clean and short.

## 5. Mini App UI

Do not overload Today cards. Today can show one compact badge or line:

- `Источник: официальный`
- `Связь: сильная`
- `Проверить: правила расчёта`

Primary UI surface: Analysis / Разбор.

Recommended Analysis section:

`Источник и доказательства`

Rows:

- `Источник`
- `Почему связан`
- `Что изменилось`
- `Сила связи`
- `Что проверить`

RU copy:

- `Источник`
- `Почему связан`
- `Что изменилось`
- `Сила связи`
- `Что проверить`

EN copy:

- `Source`
- `Why connected`
- `What changed`
- `Evidence strength`
- `What to verify`

Compact rendering:

```text
Источник
White House · официальный

Почему связан
Совпали сущности: Iran, Trump.

Что изменилось
После публикации рынок стал заметнее, но проверка правил расчёта всё ещё важна.

Сила связи
Сильная

Что проверить
Официальный текст · правила расчёта · связанные рынки
```

Evidence Timeline should be a small vertical list below Source Trail:

- timestamp
- source / market event label
- one-sentence summary
- confidence chip

Hide timeline on Today cards.

## 6. Classification Rules

Keep conservative classification.

### Confirmed

Use confirmed only when all are true:

- strong entity/topic match;
- source is official or high-quality primary source;
- source is fresh enough for the market context;
- market reaction exists after or near the source time;
- not based on stopwords or broad category-only match.

### Possible

Use possible when:

- entity/topic match is plausible;
- multiple sources or one strong specialist source exists;
- market reaction is visible but timing/causality is not fully proven.

### Background

Use background when:

- source is relevant to the broader topic;
- market reaction is weak or not clearly timed to the source.

### Weak / Hidden

Weak source matches should remain weak or hidden.

Hide the source trail when:

- only stopwords/common terms matched;
- source is official but does not directly match market entities/topics;
- source is stale and market reaction is not clear;
- relevance is broad category-only;
- source would imply false authority.

Official source does not imply relevance by itself.

## 7. Fallback Behavior

If no reliable source trail exists:

RU:

`Надёжной связи с внешним источником пока нет.`

EN:

`No reliable external source link yet.`

If there is news but it is weak:

RU:

`Фон по теме есть, но он пока не объясняет движение рынка.`

EN:

`Related coverage exists, but it does not explain the market move yet.`

If there is no market movement:

RU:

`Таймлайн не показан: рынок пока не дал заметной реакции.`

EN:

`Timeline hidden: the market has not shown a visible reaction yet.`

Do not invent a timeline.

Do not show source trail just because a source is credible.

## 8. Tests Needed

Backend tests:

- strong source trail is generated for official source + strong entity/topic match + market reaction;
- weak source is hidden from source trail;
- official source without entity match is not shown as strong;
- source credibility alone does not produce `relevance_level=strong`;
- stopword-only matches do not create source trail;
- source trail uses clean `matched_entities` and `matched_topics`;
- `evidence_timeline` does not appear without market movement;
- no trading advice wording in source trail or timeline copy;
- RU localization for source trail labels and fallback copy.

API tests:

- `/api/today` includes source trail only for reliable matches;
- `/api/today` remains cache-friendly and does not call adapters/OpenAI in warm request path;
- story cluster payload can include source trail;
- related news objects expose clean structured match fields;
- fallback payload does not include fake timeline.

Mini App static tests:

- Analysis includes `Источник`, `Почему связан`, `Что изменилось`, `Сила связи`, `Что проверить`;
- Today cards do not render full timeline;
- no source trail block appears for weak/no-news markets;
- RU mode does not show English Source Trail labels;
- no buy/sell/bet wording.

## 9. Recommended Files To Change

Backend:

- `bot/services/event_matching_engine.py`
- `bot/services/news_impact_engine.py`
- `bot/services/news_intelligence_engine.py`
- `bot/services/event_story_engine.py`
- `bot/services/health_server.py`

Optional new backend module:

- `bot/services/source_trail_engine.py`

Mini App:

- `miniapp/app.js`
- `miniapp/styles.css` only if timeline needs new compact styling.

Tests:

- `tests/test_news_impact_engine.py`
- `tests/test_news_intelligence.py`
- `tests/test_event_story_engine.py`
- `tests/test_miniapp_api.py`
- `tests/test_miniapp_static.py`
- optional new `tests/test_source_trail_engine.py`

Docs:

- `docs/SOURCE_TRAIL_EVIDENCE_TIMELINE_SPEC.md`
- update `docs/NEWS_IMPACT_ENGINE.md`
- update `docs/EVENT_GRAPH_MODEL.md`
- update `PROJECT_STATUS.md` after implementation.

## 10. Risk Points

- False authority: official sources can look authoritative even when relevance is weak.
- UI overload: Today cards can become too dense if full trail is shown outside Analysis.
- Request latency: source trail must be generated in cached/background paths.
- Mixed language: source names can be English, but labels and explanatory copy must follow user language.
- Timeline causality: publication time near market movement is not proof of causality.
- Duplicate content: Source Trail should not repeat Story Context row-for-row.
- Raw debug leakage: `match_reason` must be user-safe, not internal scoring text.

## 11. Implementation Order

### Commit A: Backend Source Trail Payload

- Add `source_trail_engine.py` or equivalent helper functions.
- Convert conservative `MarketEventMatch` objects into source trail items.
- Add structured match fields to `related_news`.
- Add `source_trail`, `has_source_trail`, and `source_trail_summary` to market/story payloads.
- Ensure fields are generated during Today build/background refresh.

### Commit B: Tests

- Add backend/API tests for strong, weak, official-without-entity, stopword-only, and no-movement cases.
- Add safety language tests.
- Add cache-friendly warm path test/mocks if available.

### Commit C: Mini App Rendering

- Add compact Analysis source trail section.
- Add optional evidence timeline below Source Trail.
- Keep Today cards compact.
- Add RU/EN labels and static tests.

### Commit D: Production Audit

- Deploy after review.
- Verify timings, source trail visibility, false-source cases, and RU localization.
- Document production audit results.

## 12. Commit Strategy

Split this into multiple commits.

Recommended:

1. `Add source trail payload for market evidence`
2. `Add source trail and evidence timeline tests`
3. `Render source trail in Mini App Analysis`
4. `Document Source Trail production audit`

Reason: this touches trust logic, cached API payloads, UI, and tests. Keeping backend and UI separate makes review safer and rollback easier.
