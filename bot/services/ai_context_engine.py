from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import httpx

from bot.services.event_categories import category_label, classify_market_category
from bot.services.market_mood import MarketMood
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


@dataclass(frozen=True, slots=True)
class DailyNarrative:
    headline: str
    what_changed: tuple[str, ...]
    category_summaries: dict[str, str]


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

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    def probability_interpretation(
        self,
        probability: float | None,
        language: str | None = None,
    ) -> str:
        normalized = normalize_language(language)
        if probability is None:
            return "Unknown" if normalized == "en" else "Пока нет данных"
        value = probability * 100
        if value < 1:
            return "Very low probability" if normalized == "en" else "Очень низкая вероятность"
        if value < 35:
            return "Possible" if normalized == "en" else "Возможно"
        if value < 70:
            return "Likely" if normalized == "en" else "Вероятно"
        return "Highly likely" if normalized == "en" else "Очень вероятно"

    async def market_context(
        self,
        market: Market,
        pulse_score: PulseScore,
        mood: MarketMood,
        delta: float | None = None,
        language: str | None = None,
    ) -> MarketContext:
        fallback = self.fallback_market_context(
            market,
            pulse_score,
            mood,
            delta=delta,
            language=language,
        )
        if not self._api_key:
            return fallback

        cache_key = self._cache_key("market", market.id, market.question, market.yes_probability, delta, language)
        cached = self._cache.get(cache_key)
        if isinstance(cached, MarketContext):
            return cached

        prompt = self._market_prompt(market, pulse_score, mood, delta, language)
        result = await self._complete_json(prompt, language=language)
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
    ) -> MarketContext:
        normalized = normalize_language(language)
        category = classify_market_category(market)
        probability_label = self.probability_interpretation(market.yes_probability, normalized)
        abs_delta = abs(delta or 0)
        high_volume = (market.volume or 0) >= 100_000
        topic_reason = self._topic_reason(market.question, normalized)

        if normalized == "en":
            if abs_delta >= 0.05:
                why = "Probability moved enough to make this market stand out."
                attention = "Probability movement made the market more noticeable."
            elif high_volume:
                why = topic_reason
                attention = self._topic_attention(market.question, normalized)
            elif pulse_score.value >= 70:
                why = topic_reason
                attention = "This market is one of the clearer stories in today’s briefing."
            else:
                why = "The story is still forming, but attention is present."
                attention = "No major shift yet, but the topic is worth keeping on the radar."

            simple = "This market asks whether the event in the title will happen."
            watch = "Watch probability changes, public activity, time left, and resolution rules."
            narrative = f"{category_label(category, 'en')} markets are part of today’s attention map."
        else:
            if abs_delta >= 0.05:
                why = "Вероятность заметно изменилась, и рынок стал заметнее."
                attention = "Движение вероятности сделало рынок заметнее."
            elif high_volume:
                why = topic_reason
                attention = self._topic_attention(market.question, normalized)
            elif pulse_score.value >= 70:
                why = topic_reason
                attention = "Этот рынок стал одной из более понятных историй дня."
            else:
                why = "История ещё формируется, но интерес уже есть."
                attention = "Сильного сдвига пока нет, но тему стоит держать на радаре."

            simple = "Этот рынок спрашивает, произойдёт ли событие из названия."
            watch = "Следи за вероятностью, активностью, временем до завершения и правилами."
            narrative = f"{category_label(category, 'ru')} входят в сегодняшнюю карту внимания."

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
        result = await self._complete_json(prompt, language=language)
        if not result:
            return fallback

        headline = self._safe_short(result.get("headline"), fallback.headline, max_chars=180)
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
                headline = "PulseMarket is preparing today’s market read."
                changes = ["No major shift yet."]
            else:
                headline = "PulseMarket готовит сегодняшнюю картину рынка."
                changes = ["Сильного сдвига пока нет."]

        return DailyNarrative(
            headline=headline,
            what_changed=tuple(changes[:3]),
            category_summaries=summaries,
        )

    def _topic_reason(self, title: str, language: str) -> str:
        text = title.lower()
        if any(word in text for word in ("bitcoin", "btc", "ethereum", "crypto", "binance")):
            return (
                "Crypto volatility brought more attention to this market."
                if language == "en"
                else "Активность усилилась после движения крипторынка."
            )
        if any(word in text for word in ("iran", "israel", "trump", "election", "president", "war", "diplomacy")):
            return (
                "Attention increased around political headlines."
                if language == "en"
                else "Внимание выросло вокруг политической повестки."
            )
        if any(word in text for word in ("nba", "nfl", "ufc", "soccer", "football", "tennis", "match", "playoff")):
            return (
                "Activity grew ahead of the event."
                if language == "en"
                else "Рынок оживился перед спортивным событием."
            )
        if any(word in text for word in ("openai", "nvidia", "anthropic", " ai ")):
            return (
                "AI-related attention increased today."
                if language == "en"
                else "Внимание к AI-теме усилилось."
            )
        return (
            "Users started watching this topic more actively."
            if language == "en"
            else "Пользователи активнее следят за развитием темы."
        )

    def _topic_attention(self, title: str, language: str) -> str:
        reason = self._topic_reason(title, language)
        if language == "en":
            return reason.replace("brought more attention to this market", "is shaping today’s attention").replace("increased today", "is rising")
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
            fallback = "👀 Market attention increased"
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
            fallback = "👀 Внимание к рынкам выросло"
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

    async def _complete_json(
        self,
        prompt: str,
        language: str | None = None,
    ) -> Mapping[str, Any] | None:
        if not self._api_key:
            return None
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a calm market intelligence analyst for Polymarket. "
                        "Explain context, attention, and what to watch. "
                        "Do not predict outcomes, do not provide financial advice, "
                        "and avoid hype. Return compact JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 360,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                loaded = json.loads(content)
                return loaded if isinstance(loaded, Mapping) else None
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("AI context generation failed: %s", exc)
            return None

    def _market_prompt(
        self,
        market: Market,
        pulse_score: PulseScore,
        mood: MarketMood,
        delta: float | None,
        language: str | None,
    ) -> str:
        normalized = normalize_language(language)
        language_name = "English" if normalized == "en" else "Russian"
        return (
            f"Language: {language_name}\n"
            "Return JSON with keys: why_people_care, simple_read, what_to_watch, "
            "attention_summary, topic_narrative, market_mood_reasoning.\n"
            "Each value must be one short sentence. No directional advice.\n\n"
            f"Market title: {market.question}\n"
            f"Probability: {market.yes_probability}\n"
            f"Volume: {market.volume}\n"
            f"Probability delta: {delta}\n"
            f"Pulse score: {pulse_score.value}/100 {pulse_score.label}\n"
            f"Market mood: {mood.label} - {mood.reason}\n"
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
            }
            for market, context in zip(markets[:5], contexts[:5], strict=False)
        ]
        return (
            f"Language: {language_name}\n"
            "Return JSON with keys: headline, what_changed, category_summaries.\n"
            "headline: one calm sentence about what markets are reacting to today.\n"
            "what_changed: array of 2-3 very short bullets.\n"
            "category_summaries: object keyed by category with one short sentence.\n"
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
        if len(text) > max_chars:
            text = text[: max_chars - 1].rstrip(" ,.;:") + "."
        return text
