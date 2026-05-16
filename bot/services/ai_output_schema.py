from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class AIOutputSchema:
    name: str
    required_fields: tuple[str, ...]
    text_fields: tuple[str, ...]
    list_fields: tuple[str, ...] = ()
    dict_fields: tuple[str, ...] = ()
    critical_fields: tuple[str, ...] = ()
    max_lengths: Mapping[str, int] = field(default_factory=dict)
    fallback: Mapping[str, Any] = field(default_factory=dict)


MARKET_INSIGHT_FIELDS: tuple[str, ...] = (
    "why_people_care",
    "simple_read",
    "what_to_watch",
    "attention_summary",
    "topic_narrative",
    "market_mood_reasoning",
    "quick_take",
    "what_happened",
    "main_tension",
    "what_this_means",
    "attention_vs_conviction",
    "insight_strength",
    "confidence_level",
    "resolution_note",
    "category_voice",
    "related_topics",
    "market_memory_summary",
    "market_regime",
    "regime_reason",
    "memory_pattern",
    "changed_since_last_seen",
    "historical_context",
    "side_summary",
    "side_tension",
    "side_verdict",
    "side_risk_note",
)


def _market_fallback(lang: str = "en") -> dict[str, Any]:
    normalized = normalize_language(lang)
    if normalized == "ru":
        return {
            "why_people_care": "Рынок заметен, но вывод требует проверки источников и правил разрешения.",
            "simple_read": "Смысл рынка зависит от исхода, указанного в названии.",
            "what_to_watch": "Проверь правила разрешения; объём; время до завершения; связанные рынки.",
            "attention_summary": "Данных достаточно для осторожного чтения, но не для сильного вывода.",
            "topic_narrative": "Тема заметна в текущей картине рынка.",
            "market_mood_reasoning": "Поведение рынка требует короткой проверки перед выводом.",
            "quick_take": "Рынок заметен, но сильного подтверждения пока нет.",
            "what_happened": "Рынок выделился в текущем обзоре.",
            "main_tension": "Главное противоречие: видимость рынка выше, чем сила подтверждения.",
            "what_this_means": "Пока это лучше читать как повод проверить контекст, а не как уверенную переоценку.",
            "attention_vs_conviction": "Видимость выше, но ожидания не выглядят резко пересмотренными.",
            "insight_strength": "Слабое подтверждение",
            "confidence_level": "Осторожное чтение",
            "resolution_note": "Ключевая проверка — правила разрешения и последние официальные источники.",
            "category_voice": "Категория требует отдельного чтения по источникам и времени до завершения.",
            "related_topics": ["Polymarket", "Market context"],
            "market_memory_summary": "Пока мало истории для сравнения.",
            "market_regime": "Спокойный рынок",
            "regime_reason": "Данных недостаточно для более сильного режима поведения.",
            "memory_pattern": "Пока мало истории для сравнения.",
            "changed_since_last_seen": "Пока мало истории для сравнения.",
            "historical_context": "История рынка ещё недостаточна для сильного вывода.",
            "side_summary": "Данных по сторонам пока мало.",
            "side_tension": "Баланс исходов требует проверки на странице рынка.",
            "side_verdict": "Рынок требует осторожного чтения по исходам.",
            "side_risk_note": "Проверь ликвидность, дедлайн и правила разрешения.",
        }
    return {
        "why_people_care": "The market stands out, but sources and resolution rules still need a check.",
        "simple_read": "The market meaning depends on the outcome named in the title.",
        "what_to_watch": "Check resolution rules; volume; time left; related markets.",
        "attention_summary": "There is enough data for a cautious read, not a strong conclusion.",
        "topic_narrative": "This topic is visible in the current market picture.",
        "market_mood_reasoning": "The market needs a quick context check before drawing a conclusion.",
        "quick_take": "The market stands out, but the read is not strongly confirmed yet.",
        "what_happened": "The market stood out in the current briefing.",
        "main_tension": "The main tension is higher visibility than confirmation strength.",
        "what_this_means": "For now, this is better read as context to verify than a firm repricing.",
        "attention_vs_conviction": "Visibility is higher, but expectations do not look sharply revised.",
        "insight_strength": "Weak confirmation",
        "confidence_level": "Cautious read",
        "resolution_note": "The key check is the rule set and the latest official sources.",
        "category_voice": "This category needs a separate read across sources and time left.",
        "related_topics": ["Polymarket", "Market context"],
        "market_memory_summary": "Not enough history for comparison yet.",
        "market_regime": "Quiet market",
        "regime_reason": "There is not enough data for a stronger behavior label.",
        "memory_pattern": "Not enough history for comparison yet.",
        "changed_since_last_seen": "Not enough history for comparison yet.",
        "historical_context": "Market history is still too limited for a strong comparison.",
        "side_summary": "Not enough side data yet.",
        "side_tension": "Outcome balance should be checked on the market page.",
        "side_verdict": "The outcome read needs caution.",
        "side_risk_note": "Check liquidity, deadline, and resolution rules.",
    }


market_insight_schema = AIOutputSchema(
    name="market_insight",
    required_fields=MARKET_INSIGHT_FIELDS,
    text_fields=tuple(field for field in MARKET_INSIGHT_FIELDS if field != "related_topics"),
    list_fields=("related_topics",),
    critical_fields=(
        "quick_take",
        "main_tension",
        "what_this_means",
        "attention_vs_conviction",
        "insight_strength",
    ),
    max_lengths={
        "why_people_care": 140,
        "simple_read": 180,
        "what_to_watch": 160,
        "attention_summary": 140,
        "topic_narrative": 180,
        "market_mood_reasoning": 140,
        "quick_take": 160,
        "what_happened": 180,
        "main_tension": 180,
        "what_this_means": 190,
        "attention_vs_conviction": 190,
        "insight_strength": 70,
        "confidence_level": 80,
        "resolution_note": 180,
        "category_voice": 180,
        "market_memory_summary": 190,
        "market_regime": 80,
        "regime_reason": 190,
        "memory_pattern": 160,
        "changed_since_last_seen": 160,
        "historical_context": 190,
        "side_summary": 160,
        "side_tension": 180,
        "side_verdict": 180,
        "side_risk_note": 160,
    },
    fallback=_market_fallback("en"),
)


today_narrative_schema = AIOutputSchema(
    name="today_narrative",
    required_fields=("headline", "what_changed", "category_summaries", "interpretation"),
    text_fields=("headline", "interpretation"),
    list_fields=("what_changed",),
    dict_fields=("category_summaries",),
    critical_fields=("headline", "interpretation"),
    max_lengths={"headline": 180, "interpretation": 220},
    fallback={
        "headline": "There is no dominant market narrative today.",
        "what_changed": ["No clear theme yet."],
        "category_summaries": {},
        "interpretation": "There is not enough fresh market activity to build a clear read yet.",
    },
)


story_context_schema = AIOutputSchema(
    name="story_context",
    required_fields=(
        "story_title",
        "story_summary",
        "why_it_matters",
        "what_changed",
        "what_to_verify",
        "confidence_level",
    ),
    text_fields=(
        "story_title",
        "story_summary",
        "why_it_matters",
        "what_changed",
        "confidence_level",
    ),
    list_fields=("what_to_verify",),
    critical_fields=("story_title", "why_it_matters", "confidence_level"),
    max_lengths={
        "story_title": 80,
        "story_summary": 220,
        "why_it_matters": 220,
        "what_changed": 180,
        "confidence_level": 80,
    },
    fallback={
        "story_title": "Market story",
        "story_summary": "Not enough story evidence for a strong read yet.",
        "why_it_matters": "The story needs more source confirmation before it becomes a stronger market read.",
        "what_changed": "No clear change yet.",
        "what_to_verify": ["Official sources", "Related markets", "Resolution rules"],
        "confidence_level": "Cautious read",
    },
)


news_impact_schema = AIOutputSchema(
    name="news_impact",
    required_fields=(
        "impact_type",
        "impact_label",
        "why_moving_now",
        "what_changed_outside_market",
        "news_risk_note",
        "confidence_from_news",
    ),
    text_fields=(
        "impact_type",
        "impact_label",
        "why_moving_now",
        "what_changed_outside_market",
        "news_risk_note",
        "confidence_from_news",
    ),
    critical_fields=("impact_type", "impact_label", "why_moving_now"),
    max_lengths={
        "impact_type": 60,
        "impact_label": 100,
        "why_moving_now": 220,
        "what_changed_outside_market": 180,
        "news_risk_note": 180,
        "confidence_from_news": 80,
    },
    fallback={
        "impact_type": "weak_external_context",
        "impact_label": "Weak external context",
        "why_moving_now": "There is not enough external confirmation for a strong market read.",
        "what_changed_outside_market": "No clear external change yet.",
        "news_risk_note": "Check official sources before drawing a conclusion.",
        "confidence_from_news": "Cautious read",
    },
)


x_draft_schema = AIOutputSchema(
    name="x_draft",
    required_fields=("posts",),
    text_fields=(),
    list_fields=("posts",),
    critical_fields=("posts",),
    fallback={
        "posts": [
            "Today’s Pulse: market context is still forming. Research only.",
        ],
    },
)


def fallback_for_language(schema: AIOutputSchema, lang: str | None = None) -> dict[str, Any]:
    normalized = normalize_language(lang)
    if schema.name == "market_insight":
        return _market_fallback(normalized)
    if normalized == "ru" and schema.name == "today_narrative":
        return {
            "headline": "Сегодня сильного доминирующего нарратива нет.",
            "what_changed": ["Ясной темы пока нет."],
            "category_summaries": {},
            "interpretation": "Пока мало свежей активности, чтобы собрать ясную картину дня.",
        }
    return dict(schema.fallback)


def schema_prompt(schema: AIOutputSchema) -> str:
    shape: dict[str, str] = {}
    for field_name in schema.required_fields:
        if field_name in schema.list_fields:
            shape[field_name] = "array"
        elif field_name in schema.dict_fields:
            shape[field_name] = "object"
        else:
            shape[field_name] = "string"
    max_lengths = {
        key: value for key, value in schema.max_lengths.items() if key in schema.required_fields
    }
    return (
        f"name={schema.name}\n"
        f"required={list(schema.required_fields)}\n"
        f"types={shape}\n"
        f"critical_non_empty={list(schema.critical_fields)}\n"
        f"max_lengths={max_lengths}"
    )
