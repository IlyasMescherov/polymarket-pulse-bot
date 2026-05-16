from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from bot.utils.i18n import normalize_language


OutcomeType = str


@dataclass(frozen=True, slots=True)
class NormalizedOutcomes:
    outcome_type: OutcomeType
    display_outcomes: tuple[dict[str, Any], ...]
    primary_outcome: dict[str, Any] | None
    secondary_outcome: dict[str, Any] | None
    dominant_outcome: dict[str, Any] | None
    dominant_outcome_label: str | None
    dominant_outcome_probability: float | None
    runner_up_label: str | None
    runner_up_probability: float | None
    outcome_spread: float | None
    outcome_balance_summary: str
    market_question_type: str
    should_use_yes_no: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome_type": self.outcome_type,
            "display_outcomes": list(self.display_outcomes),
            "primary_outcome": self.primary_outcome,
            "secondary_outcome": self.secondary_outcome,
            "dominant_outcome": self.dominant_outcome,
            "dominant_outcome_label": self.dominant_outcome_label,
            "dominant_outcome_probability": self.dominant_outcome_probability,
            "runner_up_label": self.runner_up_label,
            "runner_up_probability": self.runner_up_probability,
            "outcome_spread": self.outcome_spread,
            "outcome_balance_summary": self.outcome_balance_summary,
            "market_question_type": self.market_question_type,
            "should_use_yes_no": self.should_use_yes_no,
        }


def normalize_market_outcomes(
    market: Mapping[str, Any] | Any,
    *,
    language: str | None = "en",
) -> NormalizedOutcomes:
    """Normalize Gamma outcome fields into display-safe market options."""

    lang = normalize_language(language)
    raw = _raw(market)
    event_outcomes = _event_display_outcomes(market)
    if len(event_outcomes) >= 2:
        outcome_type = "sports_moneyline" if _looks_like_sports_market(market, event_outcomes) else "multi_outcome"
        return _build_result(
            outcome_type=outcome_type,
            outcomes=event_outcomes,
            should_use_yes_no=False,
            market_question_type="event_group",
            lang=lang,
        )

    labels = [str(value).strip() for value in _json_array(raw.get("outcomes") or _get(market, "outcomes"))]
    prices = _json_array(raw.get("outcomePrices") or _get(market, "outcomePrices"))
    token_ids = _json_array(raw.get("clobTokenIds") or _get(market, "clobTokenIds"))

    if labels:
        outcomes = [
            _outcome_dict(
                label=label,
                price=_price_at(prices, index),
                token_id=_token_at(token_ids, index),
                index=index,
            )
            for index, label in enumerate(labels)
            if label
        ]
        if len(outcomes) == 2 and _is_yes_no(labels):
            return _build_result(
                outcome_type="binary_yes_no",
                outcomes=_complete_yes_no_from_probability(outcomes, market),
                should_use_yes_no=True,
                market_question_type="binary",
                lang=lang,
            )
        if len(outcomes) == 2:
            return _build_result(
                outcome_type="binary_custom",
                outcomes=outcomes,
                should_use_yes_no=False,
                market_question_type="binary_custom",
                lang=lang,
            )
        if len(outcomes) == 3:
            return _build_result(
                outcome_type="sports_moneyline" if _looks_like_sports_market(market, outcomes) else "multi_outcome",
                outcomes=outcomes,
                should_use_yes_no=False,
                market_question_type="multi_outcome",
                lang=lang,
            )
        return _build_result(
            outcome_type="multi_outcome",
            outcomes=outcomes,
            should_use_yes_no=False,
            market_question_type="multi_outcome",
            lang=lang,
        )

    yes = _probability_percent(market)
    if yes is not None or _looks_like_yes_no_question(market):
        outcomes = _complete_yes_no_from_probability(
            (
                _outcome_dict(label="Yes", price=None, token_id=None, index=0),
                _outcome_dict(label="No", price=None, token_id=None, index=1),
            ),
            market,
            yes_probability=yes,
        )
        return _build_result(
            outcome_type="binary_yes_no",
            outcomes=outcomes,
            should_use_yes_no=True,
            market_question_type="binary_fallback",
            lang=lang,
        )

    return _unknown_result(lang)


def _json_array(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []
    return []


def _get(source: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    if key in {"title", "question"}:
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


def _normalize_price(value: float | None) -> float | None:
    if value is None or value < 0:
        return None
    return value / 100 if value > 1 else value


def _price_to_probability(value: float | None) -> float | None:
    if value is None:
        return None
    return _round_probability(max(0.0, min(100.0, _normalize_price(value) * 100)))


def _round_probability(value: float | None) -> float | None:
    if value is None:
        return None
    rounded = round(float(value), 1)
    return int(rounded) if rounded.is_integer() else rounded


def _price_at(prices: list[Any], index: int) -> float | None:
    if index >= len(prices):
        return None
    return _normalize_price(_float(prices[index]))


def _token_at(token_ids: list[Any], index: int) -> str | None:
    if index >= len(token_ids):
        return None
    value = str(token_ids[index] or "").strip()
    return value or None


def _outcome_dict(
    *,
    label: str,
    price: float | None,
    token_id: str | None,
    index: int,
) -> dict[str, Any]:
    normalized_label = _clean_label(label)
    probability = _price_to_probability(price)
    result: dict[str, Any] = {
        "label": normalized_label,
        "short_label": _short_label(normalized_label),
        "probability": probability,
        "price": round(price, 4) if price is not None else None,
        "color_role": "neutral",
        "token_id": token_id,
        "index": index,
    }
    return result


def _clean_label(value: str) -> str:
    label = " ".join(str(value or "").split())
    return label or "Outcome"


def _short_label(value: str, limit: int = 18) -> str:
    label = re.sub(r"\s*\([^)]*\)", "", _clean_label(value)).strip()
    replacements = {
        "Yes": "YES",
        "No": "NO",
        "yes": "YES",
        "no": "NO",
    }
    label = replacements.get(label, label)
    if len(label) <= limit:
        return label
    return label[: limit - 1].rstrip() + "…"


def _is_yes_no(labels: list[str]) -> bool:
    cleaned = [label.strip().lower() for label in labels]
    return len(cleaned) == 2 and set(cleaned) == {"yes", "no"}


def _complete_yes_no_from_probability(
    outcomes: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    market: Mapping[str, Any] | Any,
    yes_probability: float | None = None,
) -> tuple[dict[str, Any], ...]:
    completed = [dict(outcome) for outcome in outcomes]
    yes_probability = _probability_percent(market) if yes_probability is None else yes_probability
    yes_index = next(
        (index for index, outcome in enumerate(completed) if str(outcome["label"]).lower() == "yes"),
        0,
    )
    no_index = next(
        (index for index, outcome in enumerate(completed) if str(outcome["label"]).lower() == "no"),
        1 if len(completed) > 1 else 0,
    )
    if yes_probability is not None and completed[yes_index].get("probability") is None:
        completed[yes_index]["probability"] = _round_probability(yes_probability)
        completed[yes_index]["price"] = round(float(yes_probability) / 100, 4)
    yes_value = completed[yes_index].get("probability")
    if yes_value is not None and completed[no_index].get("probability") is None:
        no_value = max(0.0, min(100.0, 100 - float(yes_value)))
        completed[no_index]["probability"] = _round_probability(no_value)
        completed[no_index]["price"] = round(no_value / 100, 4)
    return tuple(completed)


def _probability_percent(source: Mapping[str, Any] | Any) -> float | None:
    raw = _get(source, "probability")
    if raw is None:
        raw = _get(source, "yes_probability")
    value = _float(raw)
    if value is None:
        return None
    return _round_probability(value * 100 if 0 <= value <= 1 else value)


def _event_display_outcomes(source: Mapping[str, Any] | Any) -> tuple[dict[str, Any], ...]:
    raw = _raw(source)
    event_markets = raw.get("eventMarkets")
    if not isinstance(event_markets, list):
        events = raw.get("events")
        if isinstance(events, list) and events:
            first_event = events[0]
            if isinstance(first_event, Mapping) and isinstance(first_event.get("markets"), list):
                event_markets = first_event["markets"]
    if not isinstance(event_markets, list):
        return ()

    outcomes: list[dict[str, Any]] = []
    for index, market in enumerate(event_markets):
        if not isinstance(market, Mapping):
            continue
        label = str(
            market.get("groupItemTitle")
            or market.get("title")
            or market.get("question")
            or ""
        ).strip()
        if not label:
            continue
        prices = _json_array(market.get("outcomePrices"))
        labels = [str(value).strip().lower() for value in _json_array(market.get("outcomes"))]
        yes_index = labels.index("yes") if "yes" in labels else 0
        token_ids = _json_array(market.get("clobTokenIds"))
        outcomes.append(
            _outcome_dict(
                label=label,
                price=_price_at(prices, yes_index),
                token_id=_token_at(token_ids, yes_index),
                index=index,
            )
        )
    return tuple(outcomes)


def _looks_like_sports_market(source: Mapping[str, Any] | Any, outcomes: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> bool:
    raw = _raw(source)
    title = " ".join(
        str(value or "")
        for value in (
            _get(source, "title"),
            _get(source, "question"),
            raw.get("sportsMarketType"),
            raw.get("eventTitle"),
        )
    ).lower()
    labels = " ".join(str(outcome.get("label") or "") for outcome in outcomes).lower()
    return (
        " vs " in title
        or " vs. " in title
        or "draw" in labels
        or "tie" in labels
        or bool(raw.get("sportsMarketType"))
    )


def _looks_like_yes_no_question(source: Mapping[str, Any] | Any) -> bool:
    title = str(_get(source, "title") or _get(source, "question") or "").strip().lower()
    return title.startswith("will ") or title.startswith("will:")


def _build_result(
    *,
    outcome_type: OutcomeType,
    outcomes: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    should_use_yes_no: bool,
    market_question_type: str,
    lang: str,
) -> NormalizedOutcomes:
    normalized_outcomes = tuple(dict(outcome) for outcome in outcomes)
    if outcome_type == "multi_outcome" and len(normalized_outcomes) > 3:
        normalized_outcomes = tuple(
            sorted(
                normalized_outcomes,
                key=lambda outcome: float(outcome.get("probability") or 0),
                reverse=True,
            )
        )
    display = _with_color_roles(normalized_outcomes, should_use_yes_no)
    primary = display[0] if display else None
    secondary = display[1] if len(display) > 1 else None
    ranked = sorted(
        [outcome for outcome in display if outcome.get("probability") is not None],
        key=lambda outcome: float(outcome["probability"]),
        reverse=True,
    )
    dominant = ranked[0] if ranked else primary
    runner_up = ranked[1] if len(ranked) > 1 else secondary
    dominant_probability = _round_probability(dominant.get("probability")) if dominant else None
    runner_probability = _round_probability(runner_up.get("probability")) if runner_up else None
    spread = (
        _round_probability(float(dominant_probability) - float(runner_probability))
        if dominant_probability is not None and runner_probability is not None
        else None
    )
    return NormalizedOutcomes(
        outcome_type=outcome_type,
        display_outcomes=display,
        primary_outcome=primary,
        secondary_outcome=secondary,
        dominant_outcome=dominant,
        dominant_outcome_label=str(dominant.get("label")) if dominant else None,
        dominant_outcome_probability=dominant_probability,
        runner_up_label=str(runner_up.get("label")) if runner_up else None,
        runner_up_probability=runner_probability,
        outcome_spread=spread,
        outcome_balance_summary=_balance_summary(
            outcome_type=outcome_type,
            dominant=dominant,
            runner_up=runner_up,
            spread=spread,
            should_use_yes_no=should_use_yes_no,
            lang=lang,
        ),
        market_question_type=market_question_type,
        should_use_yes_no=should_use_yes_no,
    )


def _with_color_roles(outcomes: tuple[dict[str, Any], ...], should_use_yes_no: bool) -> tuple[dict[str, Any], ...]:
    if should_use_yes_no:
        result: list[dict[str, Any]] = []
        for outcome in outcomes:
            item = dict(outcome)
            label = str(item.get("label") or "").lower()
            item["color_role"] = "yes" if label == "yes" else "no" if label == "no" else "neutral"
            item["short_label"] = "YES" if label == "yes" else "NO" if label == "no" else item["short_label"]
            result.append(item)
        return tuple(result)

    ranked_labels = [
        str(outcome.get("label"))
        for outcome in sorted(
            [outcome for outcome in outcomes if outcome.get("probability") is not None],
            key=lambda outcome: float(outcome["probability"]),
            reverse=True,
        )
    ]
    dominant_label = ranked_labels[0] if ranked_labels else (str(outcomes[0].get("label")) if outcomes else "")
    runner_label = ranked_labels[1] if len(ranked_labels) > 1 else ""
    result = []
    for outcome in outcomes:
        item = dict(outcome)
        label = str(item.get("label"))
        if label == dominant_label:
            item["color_role"] = "dominant"
        elif label == runner_label:
            item["color_role"] = "runner_up"
        else:
            item["color_role"] = "field"
        result.append(item)
    return tuple(result)


def _balance_summary(
    *,
    outcome_type: OutcomeType,
    dominant: dict[str, Any] | None,
    runner_up: dict[str, Any] | None,
    spread: float | None,
    should_use_yes_no: bool,
    lang: str,
) -> str:
    if dominant is None:
        return "Outcome data unavailable." if lang == "en" else "Данных по вариантам пока мало."
    label = str(dominant.get("short_label") or dominant.get("label"))
    runner = str(runner_up.get("short_label") or runner_up.get("label")) if runner_up else None
    if should_use_yes_no:
        if label.upper() == "YES":
            return "Market leans YES." if lang == "en" else "Рынок сильнее склоняется к YES."
        if label.upper() == "NO":
            return "Market leans NO." if lang == "en" else "Рынок сильнее склоняется к NO."
        return "Both sides are close." if lang == "en" else "Стороны почти равны."
    if spread is not None and spread <= 8 and runner:
        return (
            f"{label} leads narrowly, with {runner} close behind."
            if lang == "en"
            else f"{label} лидирует с небольшим отрывом, {runner} рядом."
        )
    if outcome_type == "binary_custom":
        return (
            f"Market leans {label}."
            if lang == "en"
            else f"Рынок сильнее склоняется к {label}."
        )
    if runner:
        return (
            f"{label} leads, with {runner} as the next scenario."
            if lang == "en"
            else f"{label} лидирует, {runner} остаётся вторым сценарием."
        )
    return (
        f"{label} is the leading outcome."
        if lang == "en"
        else f"{label} выглядит главным вариантом."
    )


def _unknown_result(lang: str) -> NormalizedOutcomes:
    text = "Outcome data unavailable." if lang == "en" else "Данных по вариантам пока мало."
    return NormalizedOutcomes(
        outcome_type="unknown",
        display_outcomes=(),
        primary_outcome=None,
        secondary_outcome=None,
        dominant_outcome=None,
        dominant_outcome_label=None,
        dominant_outcome_probability=None,
        runner_up_label=None,
        runner_up_probability=None,
        outcome_spread=None,
        outcome_balance_summary=text,
        market_question_type="unknown",
        should_use_yes_no=False,
    )
