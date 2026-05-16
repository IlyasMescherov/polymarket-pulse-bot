from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import httpx

from bot.services.event_categories import category_label, classify_market_category
from bot.services.ai_insight_engine import generate_market_briefing
from bot.services.ai_output_parser import AIParseResult, parse_ai_json_response
from bot.services.ai_output_schema import (
    AIOutputSchema,
    fallback_for_language,
    market_insight_schema,
    schema_prompt,
    today_narrative_schema,
)
from bot.services.ai_prompts import market_analyst_system_prompt
from bot.services.ai_quality_engine import score_ai_output
from bot.services.market_mood import MarketMood
from bot.services.market_memory_engine import MarketMemoryResult, compare_current_to_previous
from bot.services.market_regime_engine import MarketRegimeResult, classify_market_regime
from bot.services.market_side_engine import analyze_market_side
from bot.services.polymarket_client import Market
from bot.services.pulse_score import PulseScore
from bot.utils.i18n import normalize_language

logger = logging.getLogger(__name__)

_BANNED_FRAGMENTS = (
    "buy " + "now",
    "sell " + "now",
    "guaran" + "teed",
    "insi" + "der",
    "copy this " + "trader",
    "trade " + "signal",
    "alpha " + "leak",
    "pro" + "fit",
    "зара" + "ботай",
    "точный " + "прогноз",
    "ставь " + "сюда",
)

_GENERIC_FRAGMENTS = (
    "people are watching because activity " + "increased",
    "people are " + "watching",
    "activity " + "increased",
    "worth " + "watching",
    "this market is " + "active today",
    "market is " + "active",
    "public activity is above threshold",
    "public activity is above the visibility threshold",
    "this market asks " + "whether",
    "uncertainty " + "remains",
    "interest is " + "there",
    "confidence is " + "limited",
    "monitor this " + "market",
    "could be " + "important",
    "люди " + "следят",
    "активность выросла",
    "стоит " + "смотреть",
    "рынок активен сегодня",
    "рынок " + "активен",
    "этот рынок " + "спрашивает",
    "неопределённость " + "сохраняется",
    "интерес " + "есть",
    "уверенности " + "мало",
    "стоит " + "наблюдать",
    "может быть " + "важно",
)


@dataclass(frozen=True, slots=True)
class MarketContext:
    category: str
    category_label: str
    probability_interpretation: str
    why_people_care: str
    simple_read: str
    what_to_watch: str
    attention_summary: str
    topic_narrative: str
    market_mood_reasoning: str
    what_this_means: str
    attention_signal: str
    attention_vs_conviction: str
    quick_take: str
    what_happened: str
    main_tension: str
    insight_strength: str
    confidence_level: str
    resolution_note: str
    category_voice: str
    related_topics: tuple[str, ...]
    market_memory_summary: str
    market_regime_key: str
    market_regime: str
    regime_reason: str
    memory_pattern: str
    changed_since_last_seen: str
    historical_context: str
    side_summary: str
    dominant_side: str
    opposite_side: str
    side_balance: str
    side_tension: str
    side_confidence: str
    opposite_interest: str
    side_verdict: str
    side_risk_note: str


@dataclass(frozen=True, slots=True)
class DailyNarrative:
    headline: str
    what_changed: tuple[str, ...]
    category_summaries: dict[str, str]
    interpretation: str


class AIContextEngine:
    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o-mini",
        timeout: float = 8.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._cache: dict[str, Any] = {}
        self._parse_error_count = 0
        self._fallback_count = 0
        self._quality_scores: list[int] = []

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    def reset_quality_stats(self) -> None:
        self._parse_error_count = 0
        self._fallback_count = 0
        self._quality_scores = []

    def quality_stats(self) -> dict[str, int]:
        average = (
            round(sum(self._quality_scores) / len(self._quality_scores))
            if self._quality_scores
            else 0
        )
        return {
            "ai_quality_avg": average,
            "ai_fallback_count": self._fallback_count,
            "ai_parse_error_count": self._parse_error_count,
        }

    def probability_interpretation(
        self,
        probability: float | None,
        language: str | None = None,
    ) -> str:
        normalized = normalize_language(language)
        if probability is None:
            return "Unknown" if normalized == "en" else "Пока нет данных"
        value = probability * 100
        if value < 15:
            return "Unlikely" if normalized == "en" else "Маловероятно"
        if value < 45:
            return "Possible" if normalized == "en" else "Возможно"
        if value < 75:
            return "Likely" if normalized == "en" else "Вероятно"
        return "Highly likely" if normalized == "en" else "Очень вероятно"

    async def market_context(
        self,
        market: Market,
        pulse_score: PulseScore,
        mood: MarketMood,
        delta: float | None = None,
        language: str | None = None,
        history: Sequence[Any] | None = None,
        related_count: int = 0,
    ) -> MarketContext:
        fallback = self.fallback_market_context(
            market,
            pulse_score,
            mood,
            delta=delta,
            language=language,
            history=history,
            related_count=related_count,
        )
        if not self._api_key:
            return fallback

        cache_key = self._cache_key(
            "market",
            market.id,
            market.question,
            market.yes_probability,
            delta,
            language,
            fallback.market_memory_summary,
            fallback.market_regime,
        )
        cached = self._cache.get(cache_key)
        if isinstance(cached, MarketContext):
            return cached

        prompt = self._market_prompt(market, pulse_score, mood, delta, language, fallback)
        result = await self._complete_json(
            prompt,
            language=language,
            schema=market_insight_schema,
            response_type="market_insight",
            context={
                "title": market.question,
                "category": fallback.category,
                "dominant_outcome": fallback.dominant_side,
            },
        )
        if not result:
            return fallback

        context = MarketContext(
            category=fallback.category,
            category_label=fallback.category_label,
            probability_interpretation=fallback.probability_interpretation,
            why_people_care=self._safe_short(
                result.get("why_people_care"),
                fallback.why_people_care,
            ),
            simple_read=self._safe_short(
                result.get("simple_read"),
                fallback.simple_read,
                max_chars=180,
            ),
            what_to_watch=self._safe_short(
                result.get("what_to_watch"),
                fallback.what_to_watch,
                max_chars=160,
            ),
            attention_summary=self._safe_short(
                result.get("attention_summary"),
                fallback.attention_summary,
            ),
            topic_narrative=self._safe_short(
                result.get("topic_narrative"),
                fallback.topic_narrative,
                max_chars=180,
            ),
            market_mood_reasoning=self._safe_short(
                result.get("market_mood_reasoning"),
                fallback.market_mood_reasoning,
            ),
            what_this_means=self._safe_short(
                result.get("what_this_means"),
                fallback.what_this_means,
                max_chars=190,
            ),
            attention_signal=self._safe_signal(
                result.get("insight_strength") or result.get("attention_signal"),
                fallback.attention_signal,
                normalize_language(language),
            ),
            attention_vs_conviction=self._safe_short(
                result.get("attention_vs_conviction"),
                fallback.attention_vs_conviction,
                max_chars=190,
            ),
            related_topics=self._safe_topics(
                result.get("related_topics"),
                fallback.related_topics,
            ),
            quick_take=self._safe_short(
                result.get("quick_take"),
                fallback.quick_take,
                max_chars=160,
            ),
            what_happened=self._safe_short(
                result.get("what_happened"),
                fallback.what_happened,
                max_chars=180,
            ),
            main_tension=self._safe_short(
                result.get("main_tension"),
                fallback.main_tension,
                max_chars=180,
            ),
            insight_strength=self._safe_signal(
                result.get("insight_strength"),
                fallback.insight_strength,
                normalize_language(language),
            ),
            confidence_level=self._safe_short(
                result.get("confidence_level"),
                fallback.confidence_level,
                max_chars=80,
            ),
            resolution_note=self._safe_short(
                result.get("resolution_note"),
                fallback.resolution_note,
                max_chars=180,
            ),
            category_voice=self._safe_short(
                result.get("category_voice"),
                fallback.category_voice,
                max_chars=180,
            ),
            market_memory_summary=self._safe_short(
                result.get("market_memory_summary"),
                fallback.market_memory_summary,
                max_chars=190,
            ),
            market_regime=self._safe_short(
                result.get("market_regime"),
                fallback.market_regime,
                max_chars=80,
            ),
            market_regime_key=fallback.market_regime_key,
            regime_reason=self._safe_short(
                result.get("regime_reason"),
                fallback.regime_reason,
                max_chars=190,
            ),
            memory_pattern=self._safe_short(
                result.get("memory_pattern"),
                fallback.memory_pattern,
                max_chars=160,
            ),
            changed_since_last_seen=self._safe_short(
                result.get("changed_since_last_seen"),
                fallback.changed_since_last_seen,
                max_chars=160,
            ),
            historical_context=self._safe_short(
                result.get("historical_context"),
                fallback.historical_context,
                max_chars=190,
            ),
            side_summary=fallback.side_summary,
            dominant_side=fallback.dominant_side,
            opposite_side=fallback.opposite_side,
            side_balance=fallback.side_balance,
            side_tension=fallback.side_tension,
            side_confidence=fallback.side_confidence,
            opposite_interest=fallback.opposite_interest,
            side_verdict=fallback.side_verdict,
            side_risk_note=fallback.side_risk_note,
        )
        self._cache[cache_key] = context
        return context

    def fallback_market_context(
        self,
        market: Market,
        pulse_score: PulseScore,
        mood: MarketMood,
        delta: float | None = None,
        language: str | None = None,
        history: Sequence[Any] | None = None,
        related_count: int = 0,
    ) -> MarketContext:
        normalized = normalize_language(language)
        category = classify_market_category(market)
        probability_label = self.probability_interpretation(market.yes_probability, normalized)
        abs_delta = abs(delta or 0)
        high_volume = (market.volume or 0) >= 100_000
        memory = compare_current_to_previous(
            self._market_payload(market, pulse_score, delta),
            history,
            lang=normalized,
        )
        regime = classify_market_regime(
            self._market_payload(market, pulse_score, delta),
            history,
            related_count=related_count,
            lang=normalized,
        )
        payload = self._market_payload(market, pulse_score, delta, memory=memory, regime=regime)
        briefing = generate_market_briefing(
            payload,
            normalized,
            related_count=related_count,
        )
        topic_reason = self._topic_reason(market.question, normalized)
        signal = str(briefing["insight_strength"])
        attention_vs_conviction = str(briefing["attention_vs_conviction"])
        what_this_means = str(briefing["what_this_means"])
        related_topics = tuple(str(item) for item in briefing["related_topics"])  # type: ignore[index]

        if normalized == "en":
            if abs_delta >= 0.05:
                why = str(briefing["quick_take"])
                attention = str(briefing["what_happened"])
            elif high_volume:
                why = topic_reason
                attention = str(briefing["what_happened"])
            elif pulse_score.value >= 70:
                why = topic_reason
                attention = str(briefing["what_happened"])
            else:
                why = str(briefing["quick_take"])
                attention = str(briefing["what_happened"])

            simple = "Plain read: the outcome depends on the event named in the title."
            watch = "; ".join(str(item) for item in briefing["what_to_check"])  # type: ignore[index]
            narrative = str(briefing["category_voice"])
        else:
            if abs_delta >= 0.05:
                why = str(briefing["quick_take"])
                attention = str(briefing["what_happened"])
            elif high_volume:
                why = topic_reason
                attention = str(briefing["what_happened"])
            elif pulse_score.value >= 70:
                why = topic_reason
                attention = str(briefing["what_happened"])
            else:
                why = str(briefing["quick_take"])
                attention = str(briefing["what_happened"])

            simple = "Простой смысл: исход зависит от события, указанного в названии."
            watch = "; ".join(str(item) for item in briefing["what_to_check"])  # type: ignore[index]
            narrative = str(briefing["category_voice"])

        return MarketContext(
            category=category,
            category_label=category_label(category, normalized),
            probability_interpretation=probability_label,
            why_people_care=why,
            simple_read=simple,
            what_to_watch=watch,
            attention_summary=attention,
            topic_narrative=narrative,
            market_mood_reasoning=mood.reason,
            what_this_means=what_this_means,
            attention_signal=signal,
            attention_vs_conviction=attention_vs_conviction,
            quick_take=str(briefing["quick_take"]),
            what_happened=str(briefing["what_happened"]),
            main_tension=str(briefing["main_tension"]),
            insight_strength=str(briefing["insight_strength"]),
            confidence_level=str(briefing["confidence_level"]),
            resolution_note=str(briefing["resolution_note"]),
            category_voice=str(briefing["category_voice"]),
            related_topics=related_topics,
            market_memory_summary=str(briefing["market_memory_summary"]),
            market_regime_key=regime.key,
            market_regime=str(briefing["market_regime"]),
            regime_reason=str(briefing["regime_reason"]),
            memory_pattern=str(briefing["memory_pattern"]),
            changed_since_last_seen=str(briefing["changed_since_last_seen"]),
            historical_context=str(briefing["historical_context"]),
            side_summary=str(briefing["side_summary"]),
            dominant_side=str(briefing["dominant_side"]),
            opposite_side=str(briefing["opposite_side"]),
            side_balance=str(briefing["side_balance"]),
            side_tension=str(briefing["side_tension"]),
            side_confidence=str(briefing["side_confidence"]),
            opposite_interest=str(briefing["opposite_interest"]),
            side_verdict=str(briefing["side_verdict"]),
            side_risk_note=str(briefing["side_risk_note"]),
        )

    async def daily_narrative(
        self,
        markets: Sequence[Market],
        contexts: Sequence[MarketContext],
        language: str | None = None,
    ) -> DailyNarrative:
        fallback = self.fallback_daily_narrative(markets, contexts, language=language)
        if not self._api_key:
            return fallback

        cache_key = self._cache_key(
            "daily",
            [market.id for market in markets[:5]],
            [context.category for context in contexts[:5]],
            language,
        )
        cached = self._cache.get(cache_key)
        if isinstance(cached, DailyNarrative):
            return cached

        prompt = self._daily_prompt(markets, contexts, language)
        result = await self._complete_json(
            prompt,
            language=language,
            schema=today_narrative_schema,
            response_type="today_narrative",
            context={
                "title": markets[0].question if markets else "",
                "category": contexts[0].category if contexts else "",
                "has_changes": bool(markets),
            },
        )
        if not result:
            return fallback

        headline = self._safe_short(result.get("headline"), fallback.headline, max_chars=180)
        interpretation = self._safe_short(
            result.get("interpretation"),
            fallback.interpretation,
            max_chars=220,
        )
        raw_changes = result.get("what_changed")
        what_changed = tuple(
            self._safe_short(item, fallback.what_changed[0] if fallback.what_changed else "", max_chars=120)
            for item in raw_changes[:3]
        ) if isinstance(raw_changes, list) else fallback.what_changed
        raw_summaries = result.get("category_summaries")
        category_summaries = fallback.category_summaries.copy()
        if isinstance(raw_summaries, Mapping):
            for key, value in raw_summaries.items():
                category_summaries[str(key)] = self._safe_short(value, category_summaries.get(str(key), ""), max_chars=160)

        narrative = DailyNarrative(
            headline=headline,
            what_changed=what_changed or fallback.what_changed,
            category_summaries=category_summaries,
            interpretation=interpretation,
        )
        self._cache[cache_key] = narrative
        return narrative

    def fallback_daily_narrative(
        self,
        markets: Sequence[Market],
        contexts: Sequence[MarketContext],
        language: str | None = None,
    ) -> DailyNarrative:
        normalized = normalize_language(language)
        categories = [context.category for context in contexts]
        top_category = categories[0] if categories else "global"
        grouped: dict[str, int] = {}
        for category in categories:
            grouped[category] = grouped.get(category, 0) + 1

        if normalized == "en":
            headline = f"{category_label(top_category, 'en')} is the main market story today."
            changes = self._editorial_changes(grouped, normalized)
            summaries = {
                key: self._category_summary(key, normalized)
                for key in grouped
            }
        else:
            headline = f"{category_label(top_category, 'ru')} — главная история рынка сегодня."
            changes = self._editorial_changes(grouped, normalized)
            summaries = {
                key: self._category_summary(key, normalized)
                for key in grouped
            }

        if not markets:
            if normalized == "en":
                headline = "There is no dominant market narrative today."
                changes = ["No clear theme yet."]
                interpretation = "There is not enough fresh market activity to build a clear read yet."
            else:
                headline = "Сегодня сильного доминирующего нарратива нет."
                changes = ["Ясной темы пока нет."]
                interpretation = "Пока мало свежей активности, чтобы собрать ясную картину дня."
        else:
            interpretation = self._daily_interpretation(grouped, contexts, normalized)

        return DailyNarrative(
            headline=headline,
            what_changed=tuple(changes[:3]),
            category_summaries=summaries,
            interpretation=interpretation,
        )

    def _topic_reason(self, title: str, language: str) -> str:
        text = title.lower()
        if any(word in text for word in ("bitcoin", "btc", "ethereum", "crypto", "binance")):
            return (
                "Crypto volatility made this market more visible."
                if language == "en"
                else "Активность усилилась после движения крипторынка."
            )
        if any(word in text for word in ("iran", "israel", "trump", "election", "president", "war", "diplomacy")):
            return (
                "Political headlines made this market more visible."
                if language == "en"
                else "Политическая повестка сделала рынок заметнее."
            )
        if any(word in text for word in ("nba", "nfl", "ufc", "soccer", "football", "tennis", "match", "playoff")):
            return (
                "Event timing made this market more visible."
                if language == "en"
                else "Рынок оживился перед спортивным событием."
            )
        if any(word in text for word in ("openai", "nvidia", "anthropic", " ai ")):
            return (
                "AI news flow made this topic more visible today."
                if language == "en"
                else "Внимание к AI-теме усилилось."
            )
        return (
            "The topic became more visible in today’s market read."
            if language == "en"
            else "Тема стала заметнее в сегодняшнем чтении рынка."
        )

    def _topic_attention(self, title: str, language: str) -> str:
        reason = self._topic_reason(title, language)
        if language == "en":
            return reason.replace("made this market more visible", "is shaping today’s read").replace("increased today", "is rising")
        return reason.replace("усилилась после движения крипторынка", "выделяет этот рынок сегодня").replace("усилилось", "растёт")

    def _editorial_changes(self, grouped: Mapping[str, int], language: str) -> list[str]:
        ranked = sorted(grouped, key=lambda key: grouped[key], reverse=True)
        if language == "en":
            labels = {
                "politics": "🔥 Political markets became more active",
                "crypto": "📈 Crypto activity returned",
                "ai": "👀 AI attention increased",
                "sports": "🔥 Sports markets heated up",
                "esports": "🔥 Esports markets heated up",
                "culture": "👀 Culture markets drew attention",
                "global": "🔥 Global events became more active",
            }
            fallback = "👀 A market theme became more visible"
        else:
            labels = {
                "politics": "🔥 Политические рынки оживились",
                "crypto": "📈 Крипта снова активна",
                "ai": "👀 Внимание к AI усилилось",
                "sports": "🔥 Спорт разогревается",
                "esports": "🔥 Киберспорт разогревается",
                "culture": "👀 Культурные рынки заметнее",
                "global": "🔥 Мировые события активнее",
            }
            fallback = "👀 Тема стала заметнее"
        return [labels.get(key, fallback) for key in ranked[:3]] or [fallback]

    def _category_summary(self, category: str, language: str) -> str:
        if language == "en":
            return {
                "politics": "Political markets are more active in today’s briefing.",
                "crypto": "Crypto markets are drawing fresh attention.",
                "ai": "AI-related markets are getting more attention.",
                "sports": "Sports markets are heating up around upcoming events.",
                "esports": "Esports markets are active around match narratives.",
                "culture": "Culture markets are showing fresh interest.",
                "global": "Global-event markets are shaping the day’s read.",
            }.get(category, "This category is noticeable in today’s briefing.")
        return {
            "politics": "Политические рынки активнее в сегодняшнем обзоре.",
            "crypto": "Крипторынки снова привлекают внимание.",
            "ai": "AI-рынки получают больше внимания.",
            "sports": "Спортивные рынки разогреваются вокруг ближайших событий.",
            "esports": "Киберспорт активен вокруг матчевых сюжетов.",
            "culture": "Культурные рынки стали заметнее.",
            "global": "Мировые события формируют картину дня.",
        }.get(category, "Эта категория заметна в сегодняшнем обзоре.")

    def _attention_signal(
        self,
        market: Market,
        pulse_score: PulseScore,
        mood: MarketMood,
        delta: float | None = None,
        language: str = "en",
    ) -> str:
        abs_delta = abs(delta or 0)
        volume = market.volume or 0
        meaningful = abs_delta >= 0.05 and (volume >= 100_000 or pulse_score.value >= 60)
        strong = mood.key in {"heating_up", "volatile", "ending_soon"} or volume >= 500_000
        moderate = abs_delta >= 0.02 or volume >= 100_000 or pulse_score.value >= 50
        if language == "en":
            if meaningful:
                return "More convincing than usual"
            if strong:
                return "Strong attention"
            if moderate:
                return "More noticeable than usual"
            return "Weak confirmation"
        if meaningful:
            return "Движение выглядит убедительнее обычного"
        if strong:
            return "Сильное внимание"
        if moderate:
            return "Рынок заметнее обычного"
        return "Слабое подтверждение"

    def _attention_vs_conviction(
        self,
        market: Market,
        mood: MarketMood,
        delta: float | None = None,
        language: str = "en",
    ) -> str:
        abs_delta = abs(delta or 0)
        volume = market.volume or 0
        if language == "en":
            if abs_delta >= 0.05 and volume >= 100_000:
                return "Probability moved together with volume, which makes the reaction stronger than usual."
            if volume >= 100_000 and abs_delta < 0.02:
                return "The market is getting more attention, but expectations barely moved."
            if mood.key == "ending_soon":
                return "Attention is higher near resolution, but that does not always mean expectations changed."
            if abs_delta < 0.02:
                return "So far this looks more like interest than conviction."
            return "Probability moved, but more public attention would make the expectations read stronger."
        if abs_delta >= 0.05 and volume >= 100_000:
            return "Вероятность сдвинулась вместе с объёмом, поэтому реакция выглядит сильнее обычной."
        if volume >= 100_000 and abs_delta < 0.02:
            return "Интерес вырос, но ожидания участников почти не изменились."
        if mood.key == "ending_soon":
            return "Перед завершением внимание выше, но это не всегда означает смену ожиданий."
        if abs_delta < 0.02:
            return "Пока здесь больше интереса, чем уверенности."
        return "Вероятность изменилась, но для сильного вывода нужна более заметная активность."

    def _what_this_means(
        self,
        market: Market,
        mood: MarketMood,
        delta: float | None = None,
        language: str = "en",
    ) -> str:
        category = classify_market_category(market)
        abs_delta = abs(delta or 0)
        volume = market.volume or 0
        if language == "en":
            if mood.key == "ending_soon":
                return "The market is close to resolution, so attention can rise even without a major expectation change."
            if abs_delta >= 0.05:
                return "This is more than passive attention because probability moved enough to change the market read."
            if volume >= 100_000 and abs_delta < 0.02:
                return "The topic is drawing interest, but expectations have barely moved."
            return {
                "crypto": "This is mostly a read on whether short-term crypto volatility is changing expectations.",
                "politics": "This market helps show whether political headlines are changing expectations.",
                "sports": "This looks tied to event timing, where attention often rises before the result window.",
                "esports": "This looks tied to match timing, where attention can rise quickly before play starts.",
                "ai": "This shows whether AI-related news is turning into measurable market attention.",
                "culture": "This shows whether a culture topic is getting enough attention to become a market story.",
                "global": "This market helps read whether global-event attention is becoming more serious.",
            }.get(category, "This market is a small clue in today’s attention picture.")
        if mood.key == "ending_soon":
            return "Рынок близок к завершению, поэтому внимание может расти даже без сильной смены ожиданий."
        if abs_delta >= 0.05:
            return "Это больше, чем пассивный интерес: вероятность изменилась достаточно, чтобы изменить чтение рынка."
        if volume >= 100_000 and abs_delta < 0.02:
            return "Темой интересуются, но сам рынок пока почти не изменил ожидания."
        return {
            "crypto": "Это в первую очередь чтение того, меняет ли краткосрочная волатильность крипты ожидания.",
            "politics": "Рынок помогает понять, меняет ли политическая повестка ожидания участников.",
            "sports": "Похоже, внимание связано с близостью события, когда рынки часто оживают перед результатом.",
            "esports": "Похоже, внимание связано с матчем, где интерес может быстро расти перед началом.",
            "ai": "Рынок показывает, превращается ли AI-повестка в заметное рыночное внимание.",
            "culture": "Рынок показывает, стала ли культурная тема достаточно заметной для участников.",
            "global": "Рынок помогает понять, становится ли внимание к мировому событию серьёзнее.",
        }.get(category, "Это небольшой фрагмент сегодняшней картины внимания.")

    def _related_topics(self, market: Market) -> tuple[str, ...]:
        text = f"{market.question} {market.raw.get('description') or ''}".lower()
        topics: list[str] = []
        checks = (
            ("Bitcoin", ("bitcoin", "btc")),
            ("Crypto volatility", ("crypto", "ethereum", "eth", "binance", "coinbase")),
            ("US politics", ("trump", "president", "senate", "election")),
            ("Geopolitics", ("iran", "israel", "war", "diplomacy", "russia", "ukraine", "china")),
            ("AI", ("openai", "nvidia", "anthropic", " ai ")),
            ("Sports", ("nba", "nfl", "ufc", "soccer", "football", "tennis", "playoff", "match")),
            ("Esports", ("cs2", "league of legends", "valorant", "esports")),
            ("Culture", ("movie", "album", "grammy", "oscar", "celebrity")),
        )
        padded = f" {text} "
        for label, words in checks:
            if any(word in padded for word in words):
                topics.append(label)
        if not topics:
            topics.append(category_label(classify_market_category(market), "en"))
        return tuple(dict.fromkeys(topics))[:4]

    def _daily_interpretation(
        self,
        grouped: Mapping[str, int],
        contexts: Sequence[MarketContext],
        language: str,
    ) -> str:
        meaningful = sum(
            context.insight_strength
            in {"More convincing than usual", "Движение выглядит убедительнее обычного"}
            for context in contexts
        )
        attention_without_conviction = sum(
            "barely changed" in context.attention_vs_conviction.lower()
            or "почти не измен" in context.attention_vs_conviction.lower()
            for context in contexts
        )
        top_category = max(grouped, key=grouped.get) if grouped else "global"
        if language == "en":
            if meaningful:
                return f"{category_label(top_category, 'en')} has the clearest mix of volume and probability movement today."
            if attention_without_conviction:
                return "Several markets look busier, but expectations have mostly stayed stable."
            return "Today looks more like interest building than a broad shift in expectations."
        if meaningful:
            return f"{category_label(top_category, 'ru')} сегодня заметнее: объём и вероятность меняются вместе."
        if attention_without_conviction:
            return "Несколько рынков стали заметнее, но ожидания в основном остаются стабильными."
        return "Сегодня это больше похоже на накопление внимания, а не на широкий сдвиг ожиданий."

    def search_summary(
        self,
        query: str,
        markets: Sequence[Market],
        language: str | None = None,
    ) -> str:
        normalized = normalize_language(language)
        if not markets:
            return (
                "No close market match yet. Try a broader topic."
                if normalized == "en"
                else "Точного совпадения пока нет. Попробуй более широкую тему."
            )
        category = classify_market_category(markets[0])
        if normalized == "en":
            return f"{query.strip()} is closest to {category_label(category, 'en').lower()} markets right now."
        return f"{query.strip()} сейчас ближе всего к категории: {category_label(category, 'ru').lower()}."

    def share_snapshot(
        self,
        markets: Sequence[Market],
        contexts: Sequence[MarketContext],
        language: str | None = None,
    ) -> str:
        normalized = normalize_language(language)
        pairs = list(zip(markets[:3], contexts[:3], strict=False))
        if normalized == "en":
            lines = ["Today’s Pulse:", "3 Polymarket markets worth watching today."]
            for index, (market, context) in enumerate(pairs, start=1):
                lines.extend(["", f"{index}. {market.question}", f"Why it matters: {context.why_people_care}"])
            lines.extend(["", "Open PulseMarket AI:", "https://app.pulsemarketai.com/app"])
            return "\n".join(lines)

        lines = ["Пульс дня:", "3 рынка Polymarket, за которыми сегодня стоит следить."]
        for index, (market, context) in enumerate(pairs, start=1):
            lines.extend(["", f"{index}. {market.question}", f"Почему важно: {context.why_people_care}"])
        lines.extend(["", "Открыть PulseMarket AI:", "https://app.pulsemarketai.com/app"])
        return "\n".join(lines)

    async def _openai_chat_content(self, payload: Mapping[str, Any]) -> str:
        if not self._api_key:
            return ""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=dict(payload),
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return str(content or "")

    def _record_quality(
        self,
        payload: Mapping[str, Any],
        schema: AIOutputSchema,
        context: Mapping[str, Any] | None,
    ) -> None:
        result = score_ai_output(payload, schema=schema, context=context)
        self._quality_scores.append(result.score)
        if result.flags:
            logger.info(
                "ai_quality ai_response_type=%s ai_quality_score=%s ai_quality_flags=%s",
                schema.name,
                result.score,
                ",".join(result.flags),
            )

    def _log_parse_failure(
        self,
        *,
        response_type: str,
        result: AIParseResult,
    ) -> None:
        logger.warning(
            "AI JSON parse failed ai_parse_error=true ai_response_type=%s "
            "error_message=%s raw_preview=%s",
            response_type,
            ";".join(result.errors) or "validation_failed",
            result.raw_preview,
        )

    async def _complete_json(
        self,
        prompt: str,
        language: str | None = None,
        schema: AIOutputSchema | None = None,
        response_type: str = "unknown",
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any] | None:
        if not self._api_key:
            return None
        active_schema = schema or market_insight_schema
        fallback = fallback_for_language(active_schema, language)
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        market_analyst_system_prompt()
                        + " Return compact JSON only. No markdown. No prose outside JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 620,
            "response_format": {"type": "json_object"},
        }
        try:
            content = await self._openai_chat_content(payload)
            parsed = parse_ai_json_response(
                content,
                active_schema,
                fallback=fallback,
                lang=language,
            )
            if parsed.ok:
                self._record_quality(parsed.payload, active_schema, context)
                return parsed.payload

            self._parse_error_count += 1
            self._log_parse_failure(response_type=response_type, result=parsed)
            repair_payload = {
                **payload,
                "messages": [
                    payload["messages"][0],
                    {
                        "role": "user",
                        "content": (
                            "Return ONLY valid JSON matching this schema. "
                            "No markdown. No prose.\n"
                            f"{schema_prompt(active_schema)}\n\n"
                            f"Original task:\n{prompt}\n\n"
                            f"Previous invalid output:\n{content[:1500]}"
                        ),
                    },
                ],
                "temperature": 0,
            }
            repaired_content = await self._openai_chat_content(repair_payload)
            repaired = parse_ai_json_response(
                repaired_content,
                active_schema,
                fallback=fallback,
                lang=language,
            )
            if repaired.ok:
                self._record_quality(repaired.payload, active_schema, context)
                return repaired.payload

            self._parse_error_count += 1
            self._fallback_count += 1
            self._log_parse_failure(response_type=response_type, result=repaired)
            logger.warning(
                "AI JSON fallback ai_fallback_reason=parse_error_after_retry "
                "ai_response_type=%s",
                response_type,
            )
            return None
        except httpx.TimeoutException as exc:
            self._fallback_count += 1
            logger.warning("AI context generation failed ai_timeout=true: %s", exc)
            return None
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            self._fallback_count += 1
            logger.warning("AI context generation failed: %s", exc)
            return None

    def _market_prompt(
        self,
        market: Market,
        pulse_score: PulseScore,
        mood: MarketMood,
        delta: float | None,
        language: str | None,
        fallback: MarketContext,
    ) -> str:
        normalized = normalize_language(language)
        language_name = "English" if normalized == "en" else "Russian"
        return (
            f"Language: {language_name}\n"
            "Return JSON with keys: why_people_care, simple_read, what_to_watch, "
            "attention_summary, topic_narrative, market_mood_reasoning, "
            "quick_take, what_happened, main_tension, what_this_means, "
            "attention_vs_conviction, insight_strength, confidence_level, "
            "resolution_note, category_voice, related_topics, "
            "market_memory_summary, market_regime, regime_reason, memory_pattern, "
            "changed_since_last_seen, historical_context, side_summary, side_tension, "
            "side_verdict, side_risk_note.\n"
            "insight_strength must be exactly one of: Weak confirmation, Interest is present, "
            "More noticeable than usual, Strong attention, More convincing than usual.\n"
            "related_topics must be an array of 2-4 short topic labels.\n"
            "Each sentence must explain the reader takeaway, not market outcomes. "
            "Name the main tension between probability, volume, time left, and related markets. "
            "Use the visible outcome balance to explain which option the market leans toward. "
            "Use market memory to compare the current market with previous snapshots. "
            "Use market regime to name the current behavior type. "
            "No directional advice.\n\n"
            f"Market title: {market.question}\n"
            f"Probability: {market.yes_probability}\n"
            f"Volume: {market.volume}\n"
            f"Probability delta: {delta}\n"
            f"Pulse score: {pulse_score.value}/100 {pulse_score.label}\n"
            f"Market mood: {mood.label} - {mood.reason}\n"
            f"Market memory: {fallback.market_memory_summary}\n"
            f"Memory pattern: {fallback.memory_pattern}\n"
            f"Changed since last brief: {fallback.changed_since_last_seen}\n"
            f"Historical context: {fallback.historical_context}\n"
            f"Market regime: {fallback.market_regime} - {fallback.regime_reason}\n"
            f"Outcome balance: {fallback.side_balance}\n"
            f"Dominant outcome: {fallback.dominant_side}\n"
            f"Outcome tension: {fallback.side_tension}\n"
            f"Outcome confidence: {fallback.side_confidence}\n"
            f"Ends: {market.end_date}\n"
            f"Description: {market.raw.get('description') or ''}\n"
        )

    def _daily_prompt(
        self,
        markets: Sequence[Market],
        contexts: Sequence[MarketContext],
        language: str | None,
    ) -> str:
        normalized = normalize_language(language)
        language_name = "English" if normalized == "en" else "Russian"
        items = [
            {
                "title": market.question,
                "category": context.category,
                "why": context.why_people_care,
                "probability": market.yes_probability,
                "volume": market.volume,
                "market_memory": context.market_memory_summary,
                "market_regime": context.market_regime,
                "changed_since_last_brief": context.changed_since_last_seen,
                "dominant_side": context.dominant_side,
                "side_balance": context.side_balance,
                "side_tension": context.side_tension,
            }
            for market, context in zip(markets[:5], contexts[:5], strict=False)
        ]
        return (
            f"Language: {language_name}\n"
            "Return JSON with keys: headline, what_changed, category_summaries, interpretation.\n"
            "headline: one calm sentence about what markets are reacting to today.\n"
            "what_changed: array of 2-3 very short bullets.\n"
            "category_summaries: object keyed by category with one short sentence.\n"
            "interpretation: one short sentence connecting attention and expectations across markets.\n"
            "Use market_memory and market_regime to explain whether today differs from the previous brief.\n"
            "No predictions, no advice, no hype.\n\n"
            f"Markets: {json.dumps(items, ensure_ascii=False)}"
        )

    @staticmethod
    def _cache_key(*parts: object) -> str:
        raw = json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _safe_short(
        self,
        value: object,
        fallback: str,
        max_chars: int = 140,
    ) -> str:
        text = str(value or "").strip().replace("\n", " ")
        if not text:
            return fallback
        lower = text.lower()
        if any(fragment in lower for fragment in _BANNED_FRAGMENTS):
            return fallback
        if any(fragment in lower for fragment in _GENERIC_FRAGMENTS):
            return fallback
        if len(text) > max_chars:
            text = text[: max_chars - 1].rstrip(" ,.;:") + "."
        return text

    def _safe_signal(self, value: object, fallback: str, language: str) -> str:
        text = str(value or "").strip()
        allowed_en = {
            "Weak confirmation",
            "Interest is present",
            "More noticeable than usual",
            "Strong interest",
            "Strong attention",
            "More convincing than usual",
        }
        allowed_ru = {
            "Слабое подтверждение",
            "Есть интерес",
            "Рынок заметнее обычного",
            "Сильный интерес",
            "Сильное внимание",
            "Движение выглядит убедительнее обычного",
        }
        if language == "en":
            return text if text in allowed_en else fallback
        return text if text in allowed_ru else fallback

    @staticmethod
    def _market_payload(
        market: Market,
        pulse_score: PulseScore,
        delta: float | None,
        memory: MarketMemoryResult | None = None,
        regime: MarketRegimeResult | None = None,
    ) -> dict[str, Any]:
        payload = {
            "id": market.id,
            "title": market.question,
            "question": market.question,
            "category": classify_market_category(market),
            "probability": market.yes_probability,
            "probability_delta": delta or 0,
            "volume": market.volume or 0,
            "end_date": market.end_date,
            "pulse_score": pulse_score.value,
            "description": market.raw.get("description") or "",
            "raw": market.raw,
        }
        payload.update(analyze_market_side(market, delta=delta, language="en").as_dict())
        if memory is not None:
            payload.update(memory.as_dict())
        if regime is not None:
            payload.update(regime.as_dict())
        return payload

    def _safe_topics(self, value: object, fallback: tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            return fallback
        topics: list[str] = []
        for raw in value:
            topic = self._safe_short(raw, "", max_chars=36).strip()
            if topic:
                topics.append(topic)
            if len(topics) >= 4:
                break
        return tuple(dict.fromkeys(topics)) or fallback
