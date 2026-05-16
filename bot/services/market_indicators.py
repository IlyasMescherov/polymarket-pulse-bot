from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from bot.utils.i18n import normalize_language


LABELS = {
    "en": {
        "heat": {"hot": "Hot", "warm": "Warm", "calm": "Calm"},
        "confirmation": {"weak": "Weak", "medium": "Medium", "strong": "Strong"},
        "risk": {"low": "Low", "medium": "Medium", "high": "High"},
        "time": {
            "ending_soon": "Ending soon",
            "has_time": "Time available",
            "long_market": "Long market",
        },
        "depth": {
            "live": "Live volume",
            "medium": "Medium volume",
            "weak": "Weak volume",
        },
        "verdict": {
            "worth_watching": "Worth watching",
            "caution": "Caution",
            "not_enough_data": "Not enough data",
            "strong_interest": "Strong interest",
            "not_confident": "Not confident",
        },
    },
    "ru": {
        "heat": {"hot": "Горячий", "warm": "Тёплый", "calm": "Спокойный"},
        "confirmation": {"weak": "Слабое", "medium": "Среднее", "strong": "Сильное"},
        "risk": {"low": "Низкий", "medium": "Средний", "high": "Высокий"},
        "time": {
            "ending_soon": "Скоро завершение",
            "has_time": "Есть время",
            "long_market": "Долгий рынок",
        },
        "depth": {
            "live": "Живой объём",
            "medium": "Средний объём",
            "weak": "Слабый объём",
        },
        "verdict": {
            "worth_watching": "Стоит смотреть",
            "caution": "Осторожно",
            "not_enough_data": "Мало данных",
            "strong_interest": "Сильный интерес",
            "not_confident": "Не выглядит уверенно",
        },
    },
}


@dataclass(frozen=True, slots=True)
class MarketIndicators:
    market_heat_key: str
    market_heat: str
    confirmation_level_key: str
    confirmation_level: str
    error_risk_key: str
    error_risk: str
    time_pressure_key: str
    time_pressure: str
    market_depth_key: str
    market_depth: str
    ai_verdict_key: str
    ai_verdict: str
    indicator_summary: str

    def as_dict(self) -> dict[str, str]:
        return {
            "market_heat_key": self.market_heat_key,
            "market_heat": self.market_heat,
            "confirmation_level_key": self.confirmation_level_key,
            "confirmation_level": self.confirmation_level,
            "error_risk_key": self.error_risk_key,
            "error_risk": self.error_risk,
            "time_pressure_key": self.time_pressure_key,
            "time_pressure": self.time_pressure,
            "market_depth_key": self.market_depth_key,
            "market_depth": self.market_depth,
            "ai_verdict_key": self.ai_verdict_key,
            "ai_verdict": self.ai_verdict,
            "indicator_summary": self.indicator_summary,
        }


def calculate_market_indicators(
    market: Mapping[str, Any] | Any,
    *,
    pulse_score: int | None = None,
    delta: float | None = None,
    language: str | None = "en",
) -> MarketIndicators:
    """Return compact research indicators for a market.

    The output is descriptive only. It never recommends an action or outcome.
    """

    lang = normalize_language(language)
    score = _pulse_score(market, pulse_score)
    volume = _volume(market)
    movement = abs(_delta(market, delta))
    end_date = _end_datetime(market)

    heat_key = _heat_key(score)
    depth_key = _depth_key(volume)
    time_key = _time_key(end_date)
    confirmation_key = _confirmation_key(movement, depth_key, score)
    risk_key = _risk_key(depth_key, time_key, confirmation_key, market)
    verdict_key = _verdict_key(
        heat_key=heat_key,
        confirmation_key=confirmation_key,
        risk_key=risk_key,
        depth_key=depth_key,
        score=score,
    )

    return MarketIndicators(
        market_heat_key=heat_key,
        market_heat=_label("heat", heat_key, lang),
        confirmation_level_key=confirmation_key,
        confirmation_level=_label("confirmation", confirmation_key, lang),
        error_risk_key=risk_key,
        error_risk=_label("risk", risk_key, lang),
        time_pressure_key=time_key,
        time_pressure=_label("time", time_key, lang),
        market_depth_key=depth_key,
        market_depth=_label("depth", depth_key, lang),
        ai_verdict_key=verdict_key,
        ai_verdict=_label("verdict", verdict_key, lang),
        indicator_summary=_summary(
            confirmation_key=confirmation_key,
            risk_key=risk_key,
            time_key=time_key,
            depth_key=depth_key,
            heat_key=heat_key,
            lang=lang,
        ),
    )


def _label(group: str, key: str, lang: str) -> str:
    return LABELS[lang][group][key]


def _get(source: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _pulse_score(source: Mapping[str, Any] | Any, explicit: int | None) -> int:
    raw = explicit if explicit is not None else _get(source, "pulse_score", 0)
    try:
        return max(0, min(100, int(raw or 0)))
    except (TypeError, ValueError):
        return 0


def _volume(source: Mapping[str, Any] | Any) -> float:
    raw = _get(source, "volume")
    if raw is None:
        raw = _get(source, "public_activity")
    try:
        return max(0.0, float(raw or 0))
    except (TypeError, ValueError):
        return 0.0


def _delta(source: Mapping[str, Any] | Any, explicit: float | None) -> float:
    raw = explicit
    if raw is None:
        raw = (
            _get(source, "probability_delta")
            if _get(source, "probability_delta") is not None
            else _get(source, "movement", 0)
        )
    try:
        value = float(raw or 0)
    except (TypeError, ValueError):
        return 0.0
    return value / 100 if abs(value) > 1 else value


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


def _heat_key(score: int) -> str:
    if score >= 75:
        return "hot"
    if score >= 55:
        return "warm"
    return "calm"


def _depth_key(volume: float) -> str:
    if volume >= 100_000:
        return "live"
    if volume >= 25_000:
        return "medium"
    return "weak"


def _time_key(end_date: datetime | None) -> str:
    if end_date is None:
        return "long_market"
    seconds_left = (end_date - datetime.now(timezone.utc)).total_seconds()
    if seconds_left <= 24 * 60 * 60:
        return "ending_soon"
    if seconds_left <= 7 * 24 * 60 * 60:
        return "has_time"
    return "long_market"


def _confirmation_key(movement: float, depth_key: str, score: int) -> str:
    probability_moved = movement >= 0.03
    strong_volume = depth_key == "live"
    medium_volume = depth_key == "medium"
    activity_without_move = score >= 55 and movement < 0.02

    if probability_moved and strong_volume:
        return "strong"
    if probability_moved and medium_volume:
        return "medium"
    if activity_without_move:
        return "weak"
    if probability_moved:
        return "weak"
    return "weak"


def _risk_key(
    depth_key: str,
    time_key: str,
    confirmation_key: str,
    source: Mapping[str, Any] | Any,
) -> str:
    probability_missing = _get(source, "yes_probability") is None and _get(source, "probability") is None
    if probability_missing or depth_key == "weak":
        return "high"
    if time_key == "ending_soon" and confirmation_key != "strong":
        return "high"
    if confirmation_key == "strong" and depth_key == "live":
        return "low"
    return "medium"


def _verdict_key(
    *,
    heat_key: str,
    confirmation_key: str,
    risk_key: str,
    depth_key: str,
    score: int,
) -> str:
    if depth_key == "weak" or score < 25:
        return "not_enough_data"
    if confirmation_key == "strong":
        return "strong_interest"
    if confirmation_key == "weak" and risk_key == "high":
        return "caution"
    if heat_key in {"hot", "warm"} and confirmation_key == "weak":
        return "worth_watching"
    if risk_key == "high":
        return "not_confident"
    return "worth_watching"


def _summary(
    *,
    confirmation_key: str,
    risk_key: str,
    time_key: str,
    depth_key: str,
    heat_key: str,
    lang: str,
) -> str:
    if lang == "ru":
        if depth_key == "weak":
            return "Объём слабый, поэтому вывод требует осторожности."
        if time_key == "ending_soon" and risk_key == "high":
            return "Рынок близок к завершению, поэтому важны правила разрешения."
        if confirmation_key == "strong":
            return "Вероятность и объём подтверждают друг друга."
        if heat_key in {"hot", "warm"} and confirmation_key == "weak":
            return "Интерес есть, но рынок пока не выглядит уверенным."
        return "Рынок заметен, но вывод лучше проверять по объёму и правилам."

    if depth_key == "weak":
        return "Volume is weak, so the read needs caution."
    if time_key == "ending_soon" and risk_key == "high":
        return "The market is close to resolution, so rules matter here."
    if confirmation_key == "strong":
        return "Probability and volume are confirming each other."
    if heat_key in {"hot", "warm"} and confirmation_key == "weak":
        return "Interest is present, but the market does not look confident yet."
    return "The market stands out, but volume and rules still need review."
