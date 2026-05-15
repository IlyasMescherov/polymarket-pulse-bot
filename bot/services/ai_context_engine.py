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

_GENERIC_FRAGMENTS = (
    "people are watching because activity " + "increased",
    "activity " + "increased",
    "this market is active today",
    "public activity is above threshold",
    "public activity is above the visibility threshold",
    "активность выросла",
    "рынок активен сегодня",
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
    related_topics: tuple[str, ...]


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
            what_this_means=self._safe_short(
                result.get("what_this_means"),
                fallback.what_this_means,
                max_chars=190,
            ),
            attention_signal=self._safe_signal(
                result.get("attention_signal"),
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
        signal = self._attention_signal(
            market,
            pulse_score,
            mood,
            delta=delta,
            language=normalized,
        )
        attention_vs_conviction = self._attention_vs_conviction(
            market,
            mood,
            delta=delta,
            language=normalized,
        )
        what_this_means = self._what_this_means(
            market,
            mood,
            delta=delta,
            language=normalized,
        )
        related_topics = self._related_topics(market)

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
            what_this_means=what_this_means,
            attention_signal=signal,
            attention_vs_conviction=attention_vs_conviction,
            related_topics=related_topics,
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
                headline = "PulseMarket is preparing today’s market read."
                changes = ["No major shift yet."]
                interpretation = "There is not enough fresh market activity to build a clear read yet."
            else:
                headline = "PulseMarket готовит сегодняшнюю картину рынка."
                changes = ["Сильного сдвига пока нет."]
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
                return "Meaningful attention shift"
            if strong:
                return "Strong interest"
            if moderate:
                return "Moderate attention"
            return "Noise"
        if meaningful:
            return "Значимое движение внимания"
        if strong:
            return "Сильный интерес"
        if moderate:
            return "Умеренное внимание"
        return "Шум"

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
                return "Attention and probability moved together, so the reaction looks more meaningful."
            if volume >= 100_000 and abs_delta < 0.02:
                return "Attention rose, but expectations barely changed."
            if mood.key == "ending_soon":
                return "Attention is higher near resolution, but that does not always mean expectations changed."
            if abs_delta < 0.02:
                return "So far this looks more like background attention than a conviction shift."
            return "Probability moved, but more public attention would make the expectations read stronger."
        if abs_delta >= 0.05 and volume >= 100_000:
            return "Внимание и вероятность двигались вместе, поэтому реакция выглядит значимее."
        if volume >= 100_000 and abs_delta < 0.02:
            return "Внимание выросло, но ожидания участников почти не изменились."
        if mood.key == "ending_soon":
            return "Перед завершением внимание выше, но это не всегда означает смену ожиданий."
        if abs_delta < 0.02:
            return "Пока это больше похоже на фоновое внимание, а не на сдвиг убеждённости."
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
                return "People are watching the topic, but the market has not changed its mind much yet."
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
            context.attention_signal
            in {"Meaningful attention shift", "Значимое движение внимания"}
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
                return f"{category_label(top_category, 'en')} is moving with clearer attention and probability changes today."
            if attention_without_conviction:
                return "Several markets drew attention, but expectations have mostly stayed stable."
            return "Today looks more like attention building than a broad shift in expectations."
        if meaningful:
            return f"{category_label(top_category, 'ru')} сегодня движется заметнее: внимание и вероятность меняются вместе."
        if attention_without_conviction:
            return "Несколько рынков привлекли внимание, но ожидания в основном остаются стабильными."
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
            "attention_summary, topic_narrative, market_mood_reasoning, "
            "what_this_means, attention_signal, attention_vs_conviction, related_topics.\n"
            "attention_signal must be exactly one of: Noise, Moderate attention, Strong interest, Meaningful attention shift.\n"
            "related_topics must be an array of 2-4 short topic labels.\n"
            "Each sentence must explain meaning, not outcomes. No directional advice.\n\n"
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
            "Return JSON with keys: headline, what_changed, category_summaries, interpretation.\n"
            "headline: one calm sentence about what markets are reacting to today.\n"
            "what_changed: array of 2-3 very short bullets.\n"
            "category_summaries: object keyed by category with one short sentence.\n"
            "interpretation: one short sentence connecting attention and expectations across markets.\n"
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
            "Noise",
            "Moderate attention",
            "Strong interest",
            "Meaningful attention shift",
        }
        allowed_ru = {
            "Шум",
            "Умеренное внимание",
            "Сильный интерес",
            "Значимое движение внимания",
        }
        if language == "en":
            return text if text in allowed_en else fallback
        return text if text in allowed_ru else fallback

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
