# AI Output Reliability

PulseMarket AI uses OpenAI as an interpretation layer, not as a source of trading instructions. The product must keep working when a model returns malformed JSON, generic prose, or unsafe wording.

## OpenAI Call Sites

| Surface | File | Expected Format | Parser | Fallback |
|---|---|---|---|---|
| Market context for Mini App cards and Analysis | `bot/services/ai_context_engine.py` | Strict JSON object matching `market_insight_schema` | `parse_ai_json_response` | `fallback_market_context` |
| Today narrative in cached briefing refresh | `bot/services/ai_context_engine.py` | Strict JSON object matching `today_narrative_schema` | `parse_ai_json_response` | `fallback_daily_narrative` |
| Telegram beginner market explanation | `bot/services/ai_explainer.py` | Plain text | Safety/generic phrase filter | No AI explanation shown |
| Telegram resolution explanation | `bot/services/ai_explainer.py` | Plain text | Safety/generic phrase filter | No AI explanation shown |
| Event story and news context | `bot/services/event_story_engine.py`, `bot/services/news_impact_engine.py` | Deterministic for now | No OpenAI parser required | Deterministic labels |
| X drafts | `bot/services/x_publisher.py` | Deterministic stored drafts | No OpenAI parser required | Draft is skipped or shortened by publisher rules |

## JSON Risks Found

- `_complete_json` previously depended on a single `json.loads(content)` call.
- A response wrapped in markdown, prose, or truncated JSON could trigger deterministic fallback.
- There was no repair retry, so one malformed response could reduce briefing quality.
- There was no structured quality score to show how often fallback text was used.
- Today background refresh could still save a valid market fallback, but logs did not separate parse errors from normal deterministic fallback.

## Schemas Added

`bot/services/ai_output_schema.py` defines:

- `market_insight_schema`
- `today_narrative_schema`
- `story_context_schema`
- `news_impact_schema`
- `x_draft_schema`

Each schema defines required fields, critical non-empty fields, text/list/object fields, max text lengths, and safe fallback payloads.

## Parser Behavior

`bot/services/ai_output_parser.py` now handles:

- clean JSON;
- JSON inside markdown code fences;
- prose before or after a JSON object;
- safe trailing comma repair;
- required field validation;
- critical field validation;
- phrase-level generic wording detection;
- unsafe language detection.

If parsing or validation fails, `AIContextEngine` logs:

- `ai_parse_error=true`
- `ai_response_type`
- `error_message`
- `raw_preview` limited to the first 300 characters

Then it performs one repair retry with a strict instruction to return only valid JSON. If the retry fails, the engine uses deterministic fallback and logs `ai_fallback_reason=parse_error_after_retry`.

## Quality Scoring

`bot/services/ai_quality_engine.py` scores generated AI payloads from 0 to 100.

Quality flags include:

- `empty_output`
- `generic_phrase`
- `banned_language`
- `too_long`
- `repetitive`
- `missing_concrete_context`
- `missing_what_changed`
- `missing_what_to_verify`

`/api/today` may include per-market `ai_quality_score` and `ai_quality_flags`. Mini App does not display these fields. They are for monitoring and tests.

## Generic Phrase Control

The parser treats the following as low-quality generated language:

- `people are watching`
- `activity increased`
- `worth watching`
- `market is active`
- `this market asks whether`
- `uncertainty remains`
- `interest is there`
- `confidence is limited`
- `monitor this market`
- `could be important`
- `люди следят`
- `активность выросла`
- `стоит смотреть`
- `рынок активен`
- `этот рынок спрашивает`
- `неопределённость сохраняется`
- `интерес есть`
- `уверенности мало`
- `стоит наблюдать`
- `может быть важно`

These are phrase-level checks, not broad word bans.

## Today Refresh Protection

The cached Today briefing path now logs:

- `today.ai_quality_avg`
- `today.ai_fallback_count`
- `today.ai_parse_error_count`

Rules:

- Fresh cache still returns immediately.
- Stale cache still returns last good briefing while refresh runs in the background.
- Broken AI JSON is not saved as raw model text.
- If AI parsing fails, deterministic market fallback can still be saved as a valid briefing.
- If the whole build fails, previous last-good cache remains the user-facing response.

## Common Empty Field Risks

Fields that must not be empty:

- `quick_take`
- `main_tension`
- `what_this_means`
- `attention_vs_conviction`
- `insight_strength`
- `headline`
- `interpretation`

If any critical field is empty, validation fails and the retry/fallback path is used.
