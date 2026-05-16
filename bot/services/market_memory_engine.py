from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import get_recent_snapshots
from bot.utils.i18n import normalize_language


NO_HISTORY_MESSAGE = {
    "en": "Not enough history for comparison yet.",
    "ru": "Пока мало истории для сравнения.",
}


@dataclass(frozen=True, slots=True)
class MarketMemoryResult:
    summary: str
    pattern: str
    changed_since_last_seen: str
    historical_context: str
    has_history: bool
    probability_change_24h: float | None = None
    volume_change_24h: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "market_memory_summary": self.summary,
            "memory_pattern": self.pattern,
            "changed_since_last_seen": self.changed_since_last_seen,
            "historical_context": self.historical_context,
            "has_market_memory": self.has_history,
            "probability_change_24h": self.probability_change_24h,
            "volume_change_24h": self.volume_change_24h,
        }


async def get_market_history(
    session: AsyncSession,
    market_id: str,
    window: str = "48h",
) -> list[Any]:
    """Load recent market snapshots using the existing market_snapshots table."""

    limit = 96 if window == "7d" else 48
    snapshots = await get_recent_snapshots(session, market_id, limit=limit)
    cutoff = datetime.now(timezone.utc) - _window_delta(window)
    return [snapshot for snapshot in snapshots if _created_at(snapshot) >= cutoff]


def compare_current_to_previous(
    current_market: Mapping[str, Any] | Any,
    history: Sequence[Any] | None,
    lang: str = "en",
) -> MarketMemoryResult:
    return generate_memory_summary(current_market, history, lang=lang)


def generate_memory_summary(
    current_market: Mapping[str, Any] | Any,
    history: Sequence[Any] | None,
    lang: str = "en",
) -> MarketMemoryResult:
    normalized = normalize_language(lang)
    snapshots = [snapshot for snapshot in (history or []) if snapshot is not None]
    if not snapshots:
        message = NO_HISTORY_MESSAGE[normalized]
        return MarketMemoryResult(
            summary=message,
            pattern=message,
            changed_since_last_seen=message,
            historical_context=message,
            has_history=False,
        )

    previous = snapshots[-1]
    older = snapshots[-2] if len(snapshots) >= 2 else None
    current_probability = _probability(current_market)
    previous_probability = _probability(previous)
    probability_change = _diff(current_probability, previous_probability)
    current_volume = _volume(current_market)
    previous_volume = _volume(previous)
    volume_change = max(0.0, current_volume - previous_volume)
    previous_volume_change = (
        max(0.0, previous_volume - _volume(older)) if older is not None else None
    )
    end_date = _end_datetime(current_market) or _end_datetime(previous)
    close = _is_close_to_resolution(end_date)

    pattern = detect_memory_pattern(current_market, snapshots, lang=normalized)
    changed = _changed_since_last_seen(
        probability_change=probability_change,
        volume_change=volume_change,
        close=close,
        lang=normalized,
    )
    historical = _historical_context(
        probability_change=probability_change,
        volume_change=volume_change,
        previous_volume_change=previous_volume_change,
        close=close,
        lang=normalized,
    )
    summary = _memory_summary(
        pattern=pattern,
        probability_change=probability_change,
        volume_change=volume_change,
        previous_volume_change=previous_volume_change,
        close=close,
        lang=normalized,
    )

    return MarketMemoryResult(
        summary=summary,
        pattern=pattern,
        changed_since_last_seen=changed,
        historical_context=historical,
        has_history=True,
        probability_change_24h=round(probability_change, 4),
        volume_change_24h=round(volume_change, 2),
    )


def detect_memory_pattern(
    current_market: Mapping[str, Any] | Any,
    history: Sequence[Any] | None,
    lang: str = "en",
) -> str:
    normalized = normalize_language(lang)
    snapshots = [snapshot for snapshot in (history or []) if snapshot is not None]
    if not snapshots:
        return NO_HISTORY_MESSAGE[normalized]

    previous = snapshots[-1]
    older = snapshots[-2] if len(snapshots) >= 2 else None
    probability_change = _diff(_probability(current_market), _probability(previous))
    current_volume = _volume(current_market)
    previous_volume = _volume(previous)
    volume_change = max(0.0, current_volume - previous_volume)
    previous_volume_change = (
        max(0.0, previous_volume - _volume(older)) if older is not None else None
    )
    close = _is_close_to_resolution(_end_datetime(current_market) or _end_datetime(previous))

    if close and (volume_change >= 10_000 or current_volume >= 50_000):
        return (
            "The market is close to resolution"
            if normalized == "en"
            else "Рынок заметен перед завершением"
        )
    if previous_volume_change is not None and volume_change >= 10_000 and previous_volume_change >= 10_000:
        return (
            "Activity is holding for a second day"
            if normalized == "en"
            else "Активность держится второй день"
        )
    if previous_volume_change is not None and previous_volume_change >= 20_000 and volume_change < previous_volume_change * 0.35:
        return (
            "Interest cooled after yesterday’s activity"
            if normalized == "en"
            else "Вчера рынок оживился, сегодня интерес остыл"
        )
    if volume_change >= 25_000 and abs(probability_change) < 0.02:
        return (
            "Attention grew faster than probability"
            if normalized == "en"
            else "Внимание выросло быстрее вероятности"
        )
    if abs(probability_change) < 0.01:
        return (
            "Probability barely moved over 24h"
            if normalized == "en"
            else "Вероятность почти не изменилась за сутки"
        )
    if previous_volume <= 5_000 and current_volume >= 25_000:
        return (
            "Volume appeared only today"
            if normalized == "en"
            else "Объём появился только сегодня"
        )
    if current_volume >= max(100_000, previous_volume * 1.5):
        return (
            "The market stood out after a quiet period"
            if normalized == "en"
            else "Рынок резко выделился после спокойного периода"
        )
    return (
        "The market changed, but the pattern is still early"
        if normalized == "en"
        else "Рынок изменился, но паттерн ещё ранний"
    )


def _memory_summary(
    *,
    pattern: str,
    probability_change: float,
    volume_change: float,
    previous_volume_change: float | None,
    close: bool,
    lang: str,
) -> str:
    if close:
        return (
            "Compared with the previous brief, this market is closer to resolution and public volume is easier to notice."
            if lang == "en"
            else "По сравнению с прошлым обзором рынок ближе к завершению, и публичный объём заметнее."
        )
    if previous_volume_change is not None and volume_change >= 10_000 and previous_volume_change >= 10_000 and abs(probability_change) < 0.02:
        return (
            "Activity is holding, but probability barely changed."
            if lang == "en"
            else "Активность держится, но вероятность почти не изменилась."
        )
    if volume_change >= 25_000 and abs(probability_change) < 0.02:
        return (
            "Compared with the previous brief, this market stands out more, while expectations stayed stable."
            if lang == "en"
            else "По сравнению с прошлым обзором рынок стал заметнее, а ожидания остались стабильными."
        )
    if abs(probability_change) >= 0.05 and volume_change < 10_000:
        return (
            "Probability moved, but the historical volume change is still limited."
            if lang == "en"
            else "Вероятность изменилась, но исторический прирост объёма пока ограничен."
        )
    return pattern


def _changed_since_last_seen(
    *,
    probability_change: float,
    volume_change: float,
    close: bool,
    lang: str,
) -> str:
    if close:
        return (
            "This market moved closer to resolution."
            if lang == "en"
            else "Рынок стал ближе к завершению."
        )
    if volume_change >= 25_000 and abs(probability_change) < 0.02:
        return (
            "Public volume grew faster than probability."
            if lang == "en"
            else "Публичный объём вырос быстрее вероятности."
        )
    if abs(probability_change) >= 0.05:
        return (
            "Probability changed more than in the previous brief."
            if lang == "en"
            else "Вероятность изменилась сильнее, чем в прошлом обзоре."
        )
    return (
        "The market is broadly similar to the previous brief."
        if lang == "en"
        else "Рынок в целом похож на прошлый обзор."
    )


def _historical_context(
    *,
    probability_change: float,
    volume_change: float,
    previous_volume_change: float | None,
    close: bool,
    lang: str,
) -> str:
    if close:
        return (
            "Near-resolution markets can look busier, so the rules matter more."
            if lang == "en"
            else "Перед завершением рынок может выглядеть активнее, поэтому правила важнее."
        )
    if previous_volume_change is None:
        return (
            "The first comparison is available, but the longer pattern is still forming."
            if lang == "en"
            else "Первое сравнение уже есть, но длинный паттерн ещё формируется."
        )
    if volume_change >= previous_volume_change * 0.8 and abs(probability_change) < 0.02:
        return (
            "The attention pattern is repeating, while conviction has not caught up."
            if lang == "en"
            else "Паттерн внимания повторяется, но уверенность рынка не догоняет."
        )
    if volume_change < previous_volume_change * 0.35:
        return (
            "The market cooled compared with the previous snapshot."
            if lang == "en"
            else "По сравнению с прошлым снимком рынок остыл."
        )
    return (
        "The current move needs more history before the pattern is clear."
        if lang == "en"
        else "Текущему движению нужно больше истории, чтобы паттерн стал яснее."
    )


def _window_delta(window: str) -> timedelta:
    return {
        "24h": timedelta(hours=24),
        "48h": timedelta(hours=48),
        "7d": timedelta(days=7),
    }.get(window, timedelta(hours=48))


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


def _volume(source: Mapping[str, Any] | Any) -> float:
    raw = _get(source, "volume")
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def _diff(current: float | None, previous: float | None) -> float:
    if current is None or previous is None:
        return 0.0
    return current - previous


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


def _created_at(source: Mapping[str, Any] | Any) -> datetime:
    raw = _get(source, "created_at") or _get(source, "captured_at")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _is_close_to_resolution(end_date: datetime | None) -> bool:
    if end_date is None:
        return False
    return 0 <= (end_date - datetime.now(timezone.utc)).total_seconds() <= 48 * 60 * 60
