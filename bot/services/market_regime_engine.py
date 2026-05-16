from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from bot.services.market_memory_engine import compare_current_to_previous
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class MarketRegimeResult:
    key: str
    label: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "market_regime_key": self.key,
            "market_regime": self.label,
            "regime_reason": self.reason,
        }


REGIME_LABELS = {
    "en": {
        "quiet": "Quiet market",
        "active": "Market became active",
        "short_term_attention": "Short-term attention",
        "near_resolution": "Near resolution",
        "news_reaction": "News-driven reaction",
        "emotional": "Emotional reaction",
        "sustained_interest": "Sustained interest",
        "weak_confirmation": "Weak confirmation",
        "more_confident": "More confident move",
    },
    "ru": {
        "quiet": "Спокойный рынок",
        "active": "Рынок оживился",
        "short_term_attention": "Краткосрочное внимание",
        "near_resolution": "Перед завершением",
        "news_reaction": "Новостная реакция",
        "emotional": "Эмоциональная реакция",
        "sustained_interest": "Устойчивый интерес",
        "weak_confirmation": "Слабое подтверждение",
        "more_confident": "Более уверенное движение",
    },
}


def classify_market_regime(
    current_market: Mapping[str, Any] | Any,
    history: Sequence[Any] | None = None,
    *,
    related_count: int = 0,
    category_activity_level: str = "normal",
    lang: str = "en",
) -> MarketRegimeResult:
    normalized = normalize_language(lang)
    memory = compare_current_to_previous(current_market, history, lang=normalized)
    probability_delta = abs(_probability_delta(current_market, history))
    current_volume = _volume(current_market)
    volume_change = memory.volume_change_24h or 0.0
    activity_up = volume_change >= 25_000 or current_volume >= 100_000
    probability_flat = probability_delta < 0.02
    probability_moved = probability_delta >= 0.04
    weak_volume = current_volume < 50_000 and volume_change < 10_000
    strong_volume = current_volume >= 100_000 or volume_change >= 50_000
    close = _is_close_to_resolution(_end_datetime(current_market))

    if close and activity_up:
        return _result(
            "near_resolution",
            normalized,
            "Activity may be higher than usual because resolution is close.",
            "Активность может быть выше обычного, потому что рынок близок к завершению.",
        )
    if activity_up and probability_flat:
        return _result(
            "short_term_attention",
            normalized,
            "The market looks short-term active rather than sustainably repriced.",
            "Рынок выглядит краткосрочно активным, а не устойчиво переоценённым.",
        )
    if probability_moved and weak_volume:
        return _result(
            "weak_confirmation",
            normalized,
            "Probability moved, but volume gives limited confirmation.",
            "Вероятность изменилась, но объём даёт ограниченное подтверждение.",
        )
    if probability_moved and strong_volume:
        return _result(
            "more_confident",
            normalized,
            "Probability and volume moved together, so the read is stronger than usual.",
            "Вероятность и объём изменились вместе, поэтому чтение сильнее обычного.",
        )
    if related_count >= 2 and activity_up:
        return _result(
            "news_reaction",
            normalized,
            "Related markets are moving together, so the topic matters more than one card.",
            "Связанные рынки движутся вместе, поэтому важна вся тема, а не одна карточка.",
        )
    if category_activity_level == "high" or (
        memory.has_history and (memory.volume_change_24h or 0) >= 10_000 and current_volume >= 100_000
    ):
        return _result(
            "sustained_interest",
            normalized,
            "Interest is holding across snapshots rather than appearing once.",
            "Интерес держится между снимками, а не появился один раз.",
        )
    if current_volume >= 50_000 or volume_change >= 10_000:
        return _result(
            "active",
            normalized,
            "The market became more visible in the latest brief.",
            "Рынок стал заметнее в последнем обзоре.",
        )
    return _result(
        "quiet",
        normalized,
        "There is not enough activity for a strong comparison yet.",
        "Пока мало активности для сильного сравнения.",
    )


def _result(key: str, lang: str, en_reason: str, ru_reason: str) -> MarketRegimeResult:
    return MarketRegimeResult(
        key=key,
        label=REGIME_LABELS[lang][key],
        reason=en_reason if lang == "en" else ru_reason,
    )


def _get(source: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _probability(source: Mapping[str, Any] | Any) -> float | None:
    raw = (
        _get(source, "probability")
        if _get(source, "probability") is not None
        else _get(source, "yes_probability")
    )
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value / 100 if value > 1 else value


def _probability_delta(current_market: Mapping[str, Any] | Any, history: Sequence[Any] | None) -> float:
    raw = _get(current_market, "probability_delta")
    if raw is None:
        raw = _get(current_market, "delta", _get(current_market, "movement"))
    try:
        value = float(raw)
        if value:
            return value / 100 if abs(value) > 1 else value
    except (TypeError, ValueError):
        pass
    snapshots = [snapshot for snapshot in (history or []) if snapshot is not None]
    if not snapshots:
        return 0.0
    current = _probability(current_market)
    previous = _probability(snapshots[-1])
    if current is None or previous is None:
        return 0.0
    return current - previous


def _volume(source: Mapping[str, Any] | Any) -> float:
    raw = _get(source, "volume") or _get(source, "public_activity")
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def _end_datetime(source: Mapping[str, Any] | Any) -> datetime | None:
    raw = _get(source, "end_date") or _get(source, "endDate")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str) and raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def _is_close_to_resolution(end_date: datetime | None) -> bool:
    if end_date is None:
        return False
    return 0 <= (end_date - datetime.now(timezone.utc)).total_seconds() <= 48 * 60 * 60
