from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class MarketSideAnalysis:
    side_summary: str
    dominant_side: str
    opposite_side: str
    yes_probability: int | None
    no_probability: int | None
    yes_price: float | None
    no_price: float | None
    side_balance: str
    side_tension: str
    side_confidence: str
    opposite_interest: str
    side_verdict: str
    side_risk_note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "side_summary": self.side_summary,
            "dominant_side": self.dominant_side,
            "opposite_side": self.opposite_side,
            "yes_probability": self.yes_probability,
            "no_probability": self.no_probability,
            "yes_price": self.yes_price,
            "no_price": self.no_price,
            "side_balance": self.side_balance,
            "side_tension": self.side_tension,
            "side_confidence": self.side_confidence,
            "opposite_interest": self.opposite_interest,
            "side_verdict": self.side_verdict,
            "side_risk_note": self.side_risk_note,
        }


def analyze_market_side(
    market: Mapping[str, Any] | Any,
    *,
    delta: float | None = None,
    confirmation_level: str | None = None,
    language: str | None = "en",
) -> MarketSideAnalysis:
    """Interpret the YES / NO balance without recommending an action."""

    lang = normalize_language(language)
    yes_price, no_price, has_price_data = _extract_yes_no_prices(market)
    yes_probability = _price_to_percent(yes_price)
    no_probability = _price_to_percent(no_price)

    if yes_probability is None:
        yes_probability = _probability_percent(market)
        if yes_probability is not None:
            yes_price = round(yes_probability / 100, 4)
            no_probability = max(0, min(100, 100 - yes_probability))
            no_price = round(no_probability / 100, 4)

    if yes_probability is None or no_probability is None:
        return _unknown_result(lang)

    dominant_side = _dominant_side(yes_probability)
    opposite_side = _opposite_side(dominant_side)
    volume = _volume(market)
    movement = abs(_movement(delta, market))
    confirmation_key = _confirmation_key(confirmation_level)
    side_confidence = _side_confidence(
        dominant_side=dominant_side,
        yes_probability=yes_probability,
        volume=volume,
        movement=movement,
        confirmation_key=confirmation_key,
        has_price_data=has_price_data,
    )
    opposite_interest = _opposite_interest(
        dominant_side=dominant_side,
        yes_probability=yes_probability,
        volume=volume,
        movement=movement,
    )

    side_balance = _side_balance(dominant_side, lang)
    side_tension = _side_tension(
        dominant_side=dominant_side,
        yes_probability=yes_probability,
        volume=volume,
        movement=movement,
        confirmation_key=confirmation_key,
        lang=lang,
    )
    side_verdict = _side_verdict(
        dominant_side=dominant_side,
        yes_probability=yes_probability,
        side_confidence=side_confidence,
        opposite_interest=opposite_interest,
        volume=volume,
        movement=movement,
        lang=lang,
    )
    side_risk_note = _side_risk_note(
        has_price_data=has_price_data,
        volume=volume,
        side_confidence=side_confidence,
        lang=lang,
    )

    return MarketSideAnalysis(
        side_summary=side_verdict,
        dominant_side=dominant_side,
        opposite_side=opposite_side,
        yes_probability=yes_probability,
        no_probability=no_probability,
        yes_price=_round_price(yes_price),
        no_price=_round_price(no_price),
        side_balance=side_balance,
        side_tension=side_tension,
        side_confidence=side_confidence,
        opposite_interest=opposite_interest,
        side_verdict=side_verdict,
        side_risk_note=side_risk_note,
    )


def _json_array(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []
    return []


def _get(source: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    if key == "title":
        return getattr(source, "question", default)
    return getattr(source, key, default)


def _raw(source: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(source, Mapping):
        raw = source.get("raw")
        return raw if isinstance(raw, Mapping) else source
    raw = getattr(source, "raw", None)
    return raw if isinstance(raw, Mapping) else {}


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_yes_no_prices(source: Mapping[str, Any] | Any) -> tuple[float | None, float | None, bool]:
    raw = _raw(source)

    yes_price = _float(_get(source, "yes_price"))
    no_price = _float(_get(source, "no_price"))
    if yes_price is not None and no_price is not None:
        return _normalize_price(yes_price), _normalize_price(no_price), True

    outcomes = _json_array(raw.get("outcomes") or _get(source, "outcomes"))
    prices = _json_array(raw.get("outcomePrices") or _get(source, "outcomePrices"))
    if not outcomes or not prices:
        return None, None, False

    yes_index = _find_outcome_index(outcomes, "yes")
    no_index = _find_outcome_index(outcomes, "no")
    yes = _float(prices[yes_index]) if yes_index is not None and yes_index < len(prices) else None
    no = _float(prices[no_index]) if no_index is not None and no_index < len(prices) else None
    if yes is None and prices:
        yes = _float(prices[0])
    if no is None and len(prices) > 1:
        no = _float(prices[1])
    return _normalize_price(yes), _normalize_price(no), yes is not None or no is not None


def _find_outcome_index(outcomes: list[Any], target: str) -> int | None:
    for index, value in enumerate(outcomes):
        if isinstance(value, str) and value.strip().lower() == target:
            return index
    return None


def _normalize_price(value: float | None) -> float | None:
    if value is None:
        return None
    if value < 0:
        return None
    return value / 100 if value > 1 else value


def _round_price(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def _price_to_percent(value: float | None) -> int | None:
    if value is None:
        return None
    return max(0, min(100, round(value * 100)))


def _probability_percent(source: Mapping[str, Any] | Any) -> int | None:
    raw = _get(source, "probability")
    if raw is None:
        raw = _get(source, "yes_probability")
    value = _float(raw)
    if value is None:
        return None
    return max(0, min(100, round(value * 100 if 0 <= value <= 1 else value)))


def _volume(source: Mapping[str, Any] | Any) -> float:
    value = _float(_get(source, "volume"))
    if value is None:
        value = _float(_get(source, "public_activity"))
    return max(0.0, value or 0.0)


def _movement(delta: float | None, source: Mapping[str, Any] | Any) -> float:
    value = delta if delta is not None else _float(_get(source, "movement"))
    if value is None:
        value = _float(_get(source, "probability_delta"))
    if value is None:
        return 0.0
    return abs(value * 100 if -1 < value < 1 and value != 0 else value)


def _confirmation_key(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if text in {"strong", "medium", "weak"}:
        return text
    if "силь" in text:
        return "strong"
    if "сред" in text:
        return "medium"
    return "weak"


def _dominant_side(yes_probability: int) -> str:
    if yes_probability >= 65:
        return "YES"
    if yes_probability <= 35:
        return "NO"
    if 40 <= yes_probability <= 60:
        return "BALANCED"
    return "YES" if yes_probability > 60 else "NO"


def _opposite_side(dominant_side: str) -> str:
    if dominant_side == "YES":
        return "NO"
    if dominant_side == "NO":
        return "YES"
    return "UNKNOWN"


def _side_confidence(
    *,
    dominant_side: str,
    yes_probability: int,
    volume: float,
    movement: float,
    confirmation_key: str,
    has_price_data: bool,
) -> str:
    if dominant_side in {"UNKNOWN", "BALANCED"}:
        return "low" if volume < 100_000 else "medium"
    extreme = yes_probability >= 85 or yes_probability <= 15
    if not has_price_data or volume < 25_000:
        return "low"
    if confirmation_key == "strong" and volume >= 100_000 and (extreme or movement >= 3):
        return "high"
    if confirmation_key in {"medium", "strong"} or volume >= 100_000:
        return "medium"
    return "low"


def _opposite_interest(*, dominant_side: str, yes_probability: int, volume: float, movement: float) -> str:
    if dominant_side == "UNKNOWN":
        return "unknown"
    if dominant_side == "BALANCED":
        return "medium"
    if movement >= 5 and volume >= 100_000:
        return "high"
    if dominant_side == "NO" and yes_probability <= 15 and volume >= 100_000:
        return "medium"
    if dominant_side == "YES" and yes_probability >= 85 and volume >= 100_000:
        return "medium"
    if volume >= 50_000:
        return "medium"
    return "low"


def _side_balance(dominant_side: str, lang: str) -> str:
    labels = {
        "en": {
            "YES": "market leans clearly YES",
            "NO": "market leans clearly NO",
            "BALANCED": "both sides are close",
            "UNKNOWN": "not enough side data yet",
        },
        "ru": {
            "YES": "рынок заметно склоняется к YES",
            "NO": "рынок заметно склоняется к NO",
            "BALANCED": "стороны близки",
            "UNKNOWN": "данных по сторонам пока мало",
        },
    }
    return labels[lang][dominant_side]


def _side_tension(
    *,
    dominant_side: str,
    yes_probability: int,
    volume: float,
    movement: float,
    confirmation_key: str,
    lang: str,
) -> str:
    if dominant_side == "BALANCED":
        return (
            "Both sides are close. The market has not clearly chosen a side."
            if lang == "en"
            else "Стороны близки. Рынок пока не выбрал сторону."
        )
    if dominant_side == "UNKNOWN":
        return "Not enough side data yet." if lang == "en" else "Данных по сторонам пока мало."
    if volume < 25_000 and dominant_side == "YES":
        return (
            "YES leads, but volume does not strongly confirm confidence."
            if lang == "en"
            else "YES впереди, но объём не подтверждает сильную уверенность."
        )
    if volume < 25_000 and dominant_side == "NO":
        return (
            "NO looks stronger, but volume is limited."
            if lang == "en"
            else "NO выглядит сильнее, но объём низкий."
        )
    if yes_probability <= 15 and movement >= 1:
        return (
            "YES remains unlikely, but attention to the scenario increased."
            if lang == "en"
            else "YES остаётся маловероятным, но внимание к сценарию выросло."
        )
    if dominant_side == "NO":
        return (
            "The market is pricing rejection of the scenario more than its occurrence."
            if lang == "en"
            else "Рынок скорее отвергает сценарий, чем ждёт его."
        )
    if confirmation_key == "weak":
        return (
            "YES leads, but confirmation is still weak."
            if lang == "en"
            else "YES лидирует, но подтверждение слабое."
        )
    return (
        "YES leads, and the side read is clearer than average."
        if lang == "en"
        else "YES лидирует, и баланс сторон читается яснее обычного."
    )


def _side_verdict(
    *,
    dominant_side: str,
    yes_probability: int,
    side_confidence: str,
    opposite_interest: str,
    volume: float,
    movement: float,
    lang: str,
) -> str:
    if dominant_side == "UNKNOWN":
        return "Not enough side data yet." if lang == "en" else "Данных по сторонам пока мало."
    if dominant_side == "BALANCED":
        return (
            "Both sides are close, so the market looks uncertain."
            if lang == "en"
            else "Стороны близки, поэтому рынок выглядит неопределённым."
        )
    if dominant_side == "NO":
        if yes_probability <= 15 and (volume >= 50_000 or movement >= 1):
            return (
                "Probability is low, but YES interest is still visible."
                if lang == "en"
                else "Вероятность низкая, но интерес к YES всё ещё заметен."
            )
        return (
            "NO remains the stronger side, and the market does not show strong doubt yet."
            if lang == "en"
            else "NO остаётся сильной стороной, рынок пока не показывает сильных сомнений."
        )
    if side_confidence == "high":
        return (
            "The market leans YES with stronger confirmation than usual."
            if lang == "en"
            else "Рынок склоняется к YES с более сильным подтверждением, чем обычно."
        )
    if opposite_interest == "high":
        return (
            "The market leans YES, but the opposite side is still drawing interest."
            if lang == "en"
            else "Рынок склоняется к YES, но противоположная сторона ещё заметна."
        )
    return (
        "The market leans YES, but confirmation is only moderate."
        if lang == "en"
        else "Рынок больше верит в YES, но подтверждение пока среднее."
    )


def _side_risk_note(
    *,
    has_price_data: bool,
    volume: float,
    side_confidence: str,
    lang: str,
) -> str:
    if not has_price_data:
        return (
            "Side read uses probability fallback because detailed side data is limited."
            if lang == "en"
            else "Баланс сторон рассчитан через вероятность, потому что детальных данных мало."
        )
    if volume < 25_000:
        return (
            "Low volume makes the side read less stable."
            if lang == "en"
            else "Низкий объём делает баланс сторон менее устойчивым."
        )
    if side_confidence == "high":
        return (
            "Side balance is supported by clearer market data."
            if lang == "en"
            else "Баланс сторон поддержан более ясными рыночными данными."
        )
    return (
        "Side balance is useful, but confirmation still matters."
        if lang == "en"
        else "Баланс сторон полезен, но подтверждение всё ещё важно."
    )


def _unknown_result(lang: str) -> MarketSideAnalysis:
    text = "Not enough side data yet." if lang == "en" else "Данных по сторонам пока мало."
    return MarketSideAnalysis(
        side_summary=text,
        dominant_side="UNKNOWN",
        opposite_side="UNKNOWN",
        yes_probability=None,
        no_probability=None,
        yes_price=None,
        no_price=None,
        side_balance=text,
        side_tension=text,
        side_confidence="low",
        opposite_interest="unknown",
        side_verdict=text,
        side_risk_note=text,
    )
