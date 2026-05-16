from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from bot.services.ai_prompts import validate_ai_output
from bot.services.category_analyzer import category_summary
from bot.services.cross_market_analyzer import group_markets_by_narrative
from bot.utils.i18n import normalize_language

FALLBACK_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "no_narrative": "There is no dominant market narrative today.",
        "weak_data": "Not enough activity to draw a clear interpretation.",
        "explain_fallback": "Movement detected, but confirmation is still weak.",
    },
    "ru": {
        "no_narrative": "Сегодня сильного доминирующего нарратива нет.",
        "weak_data": "Недостаточно активности для чёткого вывода.",
        "explain_fallback": "Движение есть, но подтверждение пока слабое.",
    },
}

PULSE_LABELS: dict[str, tuple[tuple[range, str], ...]] = {
    "en": (
        (range(0, 25), "Quiet"),
        (range(25, 50), "Worth watching"),
        (range(50, 75), "Attention rising"),
        (range(75, 90), "Strong interest"),
        (range(90, 101), "High activity"),
    ),
    "ru": (
        (range(0, 25), "Рынок спокойный"),
        (range(25, 50), "Стоит смотреть"),
        (range(50, 75), "Внимание выросло"),
        (range(75, 90), "Высокий интерес"),
        (range(90, 101), "Очень активен"),
    ),
}


def _lang(lang: str | None) -> str:
    return normalize_language(lang)


def _float(market: Mapping[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        raw = market.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return default


def _probability_delta(market: Mapping[str, Any]) -> float:
    value = abs(_float(market, "probability_delta", "delta", "movement"))
    return value * 100 if value < 0.5 else value


def _volume(market: Mapping[str, Any]) -> float:
    return max(
        _float(market, "volume"),
        _float(market, "volume_delta"),
        _float(market, "public_activity"),
    )


def _end_datetime(market: Mapping[str, Any]) -> datetime | None:
    raw = market.get("end_date") or market.get("endDate")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str) and raw:
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _safe(text: str, fallback: str) -> str:
    return fallback if validate_ai_output(text) else text


def humanize_pulse_score(score: int, lang: str = "en") -> str:
    normalized = _lang(lang)
    bounded = max(0, min(100, int(score)))
    for score_range, label in PULSE_LABELS[normalized]:
        if bounded in score_range:
            return label
    return PULSE_LABELS[normalized][-1][1]


def detect_resolution_proximity(market: Mapping[str, Any]) -> bool:
    end_date = _end_datetime(market)
    if end_date is None:
        return False
    return 0 <= (end_date - datetime.now(timezone.utc)).total_seconds() <= 48 * 60 * 60


def detect_speculative_attention(market: Mapping[str, Any]) -> bool:
    return _volume(market) >= 100_000 and _probability_delta(market) < 2


def classify_movement_strength(market: Mapping[str, Any]) -> str:
    delta = _probability_delta(market)
    volume = _volume(market)
    close_to_resolution = detect_resolution_proximity(market)
    if delta >= 8 or (delta >= 5 and volume >= 100_000):
        return "strong"
    if delta >= 3 or (volume >= 500_000 and close_to_resolution):
        return "moderate"
    if delta >= 1 or volume >= 50_000:
        return "weak"
    return "quiet"


def classify_attention_vs_conviction(market: Mapping[str, Any], lang: str = "en") -> dict[str, str]:
    normalized = _lang(lang)
    delta = _probability_delta(market)
    volume = _volume(market)
    high_attention = volume >= 100_000
    large_move = delta >= 5
    close_to_resolution = detect_resolution_proximity(market)

    if high_attention and large_move:
        attention_level = conviction_level = "high"
        interpretation = (
            "The market looks more confident because attention and probability moved together."
            if normalized == "en"
            else "Рынок выглядит увереннее: внимание и вероятность двигались вместе."
        )
    elif high_attention and not large_move:
        attention_level, conviction_level = "high", "low"
        interpretation = (
            "Interest increased, but the market does not look confident yet."
            if normalized == "en"
            else "Интерес вырос, но рынок пока не выглядит уверенным."
        )
    elif not high_attention and large_move:
        attention_level, conviction_level = "low", "medium"
        interpretation = (
            "There is movement, but confirmation is still weak."
            if normalized == "en"
            else "Движение есть, но подтверждение пока слабое."
        )
    elif close_to_resolution and volume >= 50_000:
        attention_level, conviction_level = "medium", "low"
        interpretation = (
            "The market became busier ahead of resolution."
            if normalized == "en"
            else "Рынок оживился перед завершением события."
        )
    else:
        attention_level = conviction_level = "low"
        interpretation = (
            "Probability barely moved, which suggests expectations remain stable."
            if normalized == "en"
            else "Вероятность почти не изменилась. Значит, участники пока не пересмотрели ожидания."
        )

    return {
        "attention_level": attention_level,
        "conviction_level": conviction_level,
        "interpretation": _safe(interpretation, FALLBACK_MESSAGES[normalized]["explain_fallback"]),
    }


def generate_what_this_means(market: Mapping[str, Any], lang: str = "en") -> str:
    normalized = _lang(lang)
    delta = _probability_delta(market)
    volume = _volume(market)
    attention = classify_attention_vs_conviction(market, normalized)

    if detect_speculative_attention(market):
        text = (
            "Despite growing attention, the market has not shown strong conviction yet."
            if normalized == "en"
            else "Несмотря на рост внимания, рынок пока не показывает сильной уверенности."
        )
    elif delta >= 5 and volume < 50_000:
        text = (
            "The probability moved, but public activity is still too thin for a confident read."
            if normalized == "en"
            else "Вероятность изменилась, но публичной активности пока мало для уверенного вывода."
        )
    elif detect_resolution_proximity(market):
        text = (
            "The market is near resolution, so timing matters as much as the probability move."
            if normalized == "en"
            else "Рынок близок к разрешению, поэтому тайминг важен не меньше движения вероятности."
        )
    elif attention["attention_level"] == "low" and attention["conviction_level"] == "low":
        text = FALLBACK_MESSAGES[normalized]["weak_data"]
    else:
        text = (
            "This market stands out more than usual, but the stronger read depends on follow-through."
            if normalized == "en"
            else "Рынок выглядит заметнее обычного, но сильный вывод зависит от продолжения движения."
        )
    return _safe(text, FALLBACK_MESSAGES[normalized]["explain_fallback"])


def generate_market_briefing(market: Mapping[str, Any], lang: str = "en") -> dict[str, str | list[str]]:
    normalized = _lang(lang)
    attention = classify_attention_vs_conviction(market, normalized)
    strength = classify_movement_strength(market)
    what_this_means = generate_what_this_means(market, normalized)
    title = str(market.get("title") or market.get("question") or "Market")
    resolution = (
        "Open the market page and read the official resolution criteria."
        if normalized == "en"
        else "Открой страницу рынка и проверь официальные правила разрешения."
    )
    happening = (
        f"{title} is getting enough activity to review. Probability movement is {strength}."
        if normalized == "en"
        else f"{title} получил достаточно активности для проверки. Движение вероятности: {strength}."
    )
    quick_take = attention["interpretation"]
    sections: dict[str, str | list[str]] = {
        "quick_take": quick_take,
        "what_is_happening": _safe(happening, FALLBACK_MESSAGES[normalized]["explain_fallback"]),
        "what_this_means": what_this_means,
        "attention_vs_conviction": attention["interpretation"],
        "how_strong_is_the_move": (
            f"The move looks {strength}; check whether volume confirms it."
            if normalized == "en"
            else f"Движение выглядит как {strength}; проверь, подтверждает ли его объём."
        ),
        "what_to_check": (
            [
                "Resolution rules",
                "Volume quality",
                "Time to resolution",
                "Related markets",
            ]
            if normalized == "en"
            else [
                "Правила разрешения",
                "Качество объёма",
                "Время до завершения",
                "Связанные рынки",
            ]
        ),
        "related_themes": str(market.get("category") or "global"),
        "how_this_resolves": resolution,
    }
    return sections


def generate_today_narrative(markets: Sequence[Mapping[str, Any]], lang: str = "en") -> str:
    normalized = _lang(lang)
    if not markets:
        return FALLBACK_MESSAGES[normalized]["no_narrative"]
    groups = group_markets_by_narrative([dict(market) for market in markets])
    if groups:
        top = groups[0]
        text = (
            f"{top['narrative']} is the clearest shared theme today. {top['group_interpretation']}"
            if normalized == "en"
            else f"{top['narrative']} — самая ясная общая тема дня. {top['group_interpretation']}"
        )
    else:
        categories = {str(market.get("category") or "global") for market in markets}
        top_category = sorted(categories)[0]
        text = category_summary(top_category, normalized)
    return _safe(text, FALLBACK_MESSAGES[normalized]["no_narrative"])


def generate_what_changed(markets: Sequence[Mapping[str, Any]], lang: str = "en") -> list[str]:
    normalized = _lang(lang)
    if not markets:
        return [FALLBACK_MESSAGES[normalized]["no_narrative"]]

    ending = sum(1 for market in markets if detect_resolution_proximity(market))
    speculative = sum(1 for market in markets if detect_speculative_attention(market))
    strong = sum(1 for market in markets if classify_movement_strength(market) in {"strong", "moderate"})
    bullets: list[str] = []
    if strong:
        bullets.append(f"🔥 {strong} markets need a closer read" if normalized == "en" else f"🔥 {strong} рынков требуют проверки")
    if ending:
        bullets.append(f"⚠️ {ending} markets resolve soon" if normalized == "en" else f"⚠️ {ending} рынков скоро завершаются")
    if speculative:
        bullets.append(f"👀 Attention outran conviction in {speculative} markets" if normalized == "en" else f"👀 Интерес опередил уверенность в {speculative} рынках")
    if not bullets:
        bullets.append("📈 No dominant market narrative today" if normalized == "en" else "📈 Сильного общего нарратива сегодня нет")
    return [_safe(bullet, FALLBACK_MESSAGES[normalized]["weak_data"]) for bullet in bullets[:5]]
