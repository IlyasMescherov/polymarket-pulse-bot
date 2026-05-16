from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from bot.services.ai_prompts import validate_ai_output
from bot.services.category_analyzer import category_summary
from bot.services.cross_market_analyzer import group_markets_by_narrative
from bot.services.market_memory_engine import NO_HISTORY_MESSAGE
from bot.services.market_regime_engine import REGIME_LABELS
from bot.services.market_side_engine import analyze_market_side
from bot.utils.i18n import normalize_language

FALLBACK_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "no_narrative": "There is no dominant market narrative today.",
        "weak_data": "Not enough activity to draw a clear interpretation.",
        "explain_fallback": "There is movement, but confirmation is still weak.",
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
        (range(50, 75), "Рынок заметнее"),
        (range(75, 90), "Высокий интерес"),
        (range(90, 101), "Очень активен"),
    ),
}

INSIGHT_STRENGTH_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "weak": "Weak confirmation",
        "interest": "Interest is present",
        "noticeable": "More noticeable than usual",
        "strong": "Strong attention",
        "convincing": "More convincing than usual",
    },
    "ru": {
        "weak": "Слабое подтверждение",
        "interest": "Есть интерес",
        "noticeable": "Рынок заметнее обычного",
        "strong": "Сильное внимание",
        "convincing": "Движение выглядит убедительнее обычного",
    },
}

CONFIDENCE_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "low": "Low confidence",
        "medium": "Medium confidence",
        "high": "Higher confidence",
    },
    "ru": {
        "low": "Низкая уверенность",
        "medium": "Средняя уверенность",
        "high": "Более высокая уверенность",
    },
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


def _probability(market: Mapping[str, Any]) -> float:
    value = _float(market, "probability", "yes_probability", "yesProbability")
    return value * 100 if 0 < value <= 1 else value


def _probability_delta(market: Mapping[str, Any]) -> float:
    value = abs(_float(market, "probability_delta", "delta", "movement"))
    return value * 100 if 0 < value < 0.5 else value


def _signed_probability_delta(market: Mapping[str, Any]) -> float:
    value = _float(market, "probability_delta", "delta", "movement")
    return value * 100 if -0.5 < value < 0.5 and value != 0 else value


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


def _category(market: Mapping[str, Any]) -> str:
    return str(market.get("category") or "global")


def _category_display(category: str, lang: str) -> str:
    labels = {
        "en": {
            "politics": "politics",
            "crypto": "crypto",
            "ai": "AI",
            "sports": "sports",
            "esports": "esports",
            "culture": "culture",
            "global": "global events",
        },
        "ru": {
            "politics": "политикой",
            "crypto": "криптой",
            "ai": "AI",
            "sports": "спортом",
            "esports": "киберспортом",
            "culture": "культурой",
            "global": "мировыми событиями",
        },
    }
    return labels[_lang(lang)].get(category, category.replace("_", " "))


def _title(market: Mapping[str, Any]) -> str:
    return str(market.get("title") or market.get("question") or "This market")


def _safe(text: str, fallback: str) -> str:
    cleaned = str(text or "").strip()
    return fallback if not cleaned or validate_ai_output(cleaned) else cleaned


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
            "Probability moved together with volume, which makes the reaction stronger than usual."
            if normalized == "en"
            else "Вероятность сдвинулась вместе с объёмом, поэтому реакция выглядит сильнее обычной."
        )
    elif high_attention and not large_move:
        attention_level, conviction_level = "high", "low"
        interpretation = (
            "The market is getting more attention, but expectations barely moved."
            if normalized == "en"
            else "Рынок обсуждают активнее, но ожидания почти не изменились."
        )
    elif not high_attention and large_move:
        attention_level, conviction_level = "low", "medium"
        interpretation = (
            "Probability moved, but volume is weak. Confirmation is limited."
            if normalized == "en"
            else "Вероятность сдвинулась, но объём слабый. Подтверждение ограниченное."
        )
    elif close_to_resolution and volume >= 50_000:
        attention_level, conviction_level = "medium", "low"
        interpretation = (
            "Public activity rose near resolution. Resolution rules matter here."
            if normalized == "en"
            else "Публичная активность поднялась перед завершением. Здесь важно проверить правила разрешения."
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


def detect_main_tension(market: Mapping[str, Any], lang: str = "en", related_count: int = 0) -> str:
    normalized = _lang(lang)
    delta = _probability_delta(market)
    volume = _volume(market)
    probability = _probability(market)

    if related_count >= 2 and delta >= 2:
        text = (
            "This is no longer a single-market move. The topic itself is moving."
            if normalized == "en"
            else "Это уже не одиночный рынок, а движение всей темы."
        )
    elif detect_resolution_proximity(market) and volume >= 50_000:
        text = (
            "Public activity rose near resolution. Resolution rules matter here."
            if normalized == "en"
            else "Публичная активность поднялась перед завершением. Важно проверить правила разрешения."
        )
    elif volume >= 100_000 and delta < 2:
        text = (
            "Interest increased, but expectations did not move."
            if normalized == "en"
            else "Интерес вырос, но рынок не меняет ожидания."
        )
    elif delta >= 5 and volume < 50_000:
        text = (
            "Probability moved, but volume is weak. Confirmation is limited."
            if normalized == "en"
            else "Вероятность сдвинулась, но объём слабый. Подтверждение ограниченное."
        )
    elif volume >= 100_000 and probability < 15:
        text = (
            "Volume is present, but the market still treats the outcome as unlikely."
            if normalized == "en"
            else "Объём есть, но рынок всё ещё оценивает сценарий как маловероятный."
        )
    else:
        text = (
            "The market stands out, but there is not enough data for a strong read yet."
            if normalized == "en"
            else "Рынок заметнее среднего, но данных для уверенного вывода пока мало."
        )
    return _safe(text, FALLBACK_MESSAGES[normalized]["explain_fallback"])


def classify_insight_strength(
    market: Mapping[str, Any],
    lang: str = "en",
    related_count: int = 0,
) -> dict[str, str]:
    normalized = _lang(lang)
    delta = _probability_delta(market)
    volume = _volume(market)
    pulse = int(_float(market, "pulse_score", default=0))

    if related_count >= 2 and delta >= 4 and volume >= 100_000:
        key, confidence = "convincing", "high"
    elif related_count >= 2 or volume >= 500_000:
        key, confidence = "strong", "medium"
    elif (pulse >= 60 and volume >= 50_000) or (delta >= 3 and volume >= 50_000):
        key, confidence = "noticeable", "medium"
    elif volume >= 100_000 and delta < 2:
        key, confidence = "interest", "low"
    else:
        key, confidence = "weak", "low"

    return {
        "key": key,
        "label": INSIGHT_STRENGTH_LABELS[normalized][key],
        "confidence_level": CONFIDENCE_LABELS[normalized][confidence],
    }


def generate_what_happened(market: Mapping[str, Any], lang: str = "en") -> str:
    normalized = _lang(lang)
    strength = classify_movement_strength(market)
    close = detect_resolution_proximity(market)
    delta = _signed_probability_delta(market)
    volume = _volume(market)
    if normalized == "en":
        if close:
            text = "The market is close to resolution, and public volume is easier to notice."
        elif abs(delta) >= 5:
            text = "Probability moved enough to change the read of this market."
        elif volume >= 100_000:
            text = "Public volume is visible, while the probability line is still steady."
        elif strength == "quiet":
            text = "The market has not shown a clear move yet."
        else:
            text = "The market is becoming more visible, but the move is still early."
    else:
        if close:
            text = "Рынок близок к завершению, и публичный объём легче заметить."
        elif abs(delta) >= 5:
            text = "Вероятность сдвинулась достаточно, чтобы изменить чтение рынка."
        elif volume >= 100_000:
            text = "Публичный объём заметен, но линия вероятности остаётся ровной."
        elif strength == "quiet":
            text = "Рынок пока не показал ясного движения."
        else:
            text = "Рынок становится заметнее, но движение ещё раннее."
    return _safe(text, FALLBACK_MESSAGES[normalized]["weak_data"])


def generate_what_this_means(
    market: Mapping[str, Any],
    lang: str = "en",
    related_count: int = 0,
) -> str:
    normalized = _lang(lang)
    delta = _probability_delta(market)
    volume = _volume(market)
    probability = _probability(market)

    if related_count >= 2:
        text = (
            "Several related markets are moving together, which makes the topic more important than one isolated card."
            if normalized == "en"
            else "Несколько связанных рынков движутся вместе, поэтому важна уже вся тема, а не одна карточка."
        )
    elif volume >= 100_000 and delta < 2:
        text = (
            "This looks more like growing interest than changing expectations."
            if normalized == "en"
            else "Это больше похоже на рост интереса, чем на смену ожиданий."
        )
    elif delta >= 5 and volume < 50_000:
        text = (
            "The probability moved, but the read is fragile without stronger volume."
            if normalized == "en"
            else "Вероятность сдвинулась, но вывод хрупкий без более сильного объёма."
        )
    elif volume >= 100_000 and probability < 15:
        text = (
            "The market is drawing volume, but participants still price the scenario as unlikely."
            if normalized == "en"
            else "Объём заметен, но участники всё ещё оценивают сценарий как маловероятный."
        )
    elif detect_resolution_proximity(market):
        text = (
            "Near resolution, even small updates can make the market feel busier than usual."
            if normalized == "en"
            else "Перед завершением даже небольшие обновления могут делать рынок заметнее обычного."
        )
    else:
        text = (
            "The market stands out enough to review, but the stronger conclusion depends on follow-through."
            if normalized == "en"
            else "Рынок достаточно заметен для разбора, но сильный вывод зависит от продолжения движения."
        )
    return _safe(text, FALLBACK_MESSAGES[normalized]["explain_fallback"])


def what_to_check_items(market: Mapping[str, Any], lang: str = "en") -> list[str]:
    normalized = _lang(lang)
    close = detect_resolution_proximity(market)
    delta = _probability_delta(market)
    volume = _volume(market)
    if normalized == "en":
        items = ["Official resolution rules", "Volume quality"]
        if close:
            items.append("Time left before resolution")
        if delta >= 2:
            items.append("Whether probability keeps moving")
        if volume >= 100_000:
            items.append("Whether public volume holds")
        return items[:4]
    items = ["Официальные правила разрешения", "Качество объёма"]
    if close:
        items.append("Сколько времени осталось")
    if delta >= 2:
        items.append("Продолжит ли двигаться вероятность")
    if volume >= 100_000:
        items.append("Сохранится ли публичный объём")
    return items[:4]


def resolution_note(market: Mapping[str, Any], lang: str = "en") -> str:
    normalized = _lang(lang)
    if detect_resolution_proximity(market):
        return (
            "This resolves soon, so the exact criteria matter more than usual."
            if normalized == "en"
            else "Рынок скоро завершается, поэтому точные критерии особенно важны."
        )
    return (
        "Open the market page and read the official resolution criteria."
        if normalized == "en"
        else "Открой страницу рынка и проверь официальные правила разрешения."
    )


def category_voice_summary(market: Mapping[str, Any], lang: str = "en") -> str:
    return category_summary(_category(market), _lang(lang))


def related_topics_for_market(market: Mapping[str, Any]) -> list[str]:
    text = f"{_title(market)} {market.get('description') or ''}".lower()
    topics: list[str] = []
    checks = (
        ("Bitcoin", ("bitcoin", "btc")),
        ("Crypto volatility", ("crypto", "ethereum", "eth", "binance", "coinbase")),
        ("US politics", ("trump", "president", "senate", "election")),
        ("Geopolitics", ("iran", "israel", "war", "diplomacy", "russia", "ukraine", "china")),
        ("AI", ("openai", "nvidia", "anthropic", " ai ")),
        ("Sports", ("nba", "nfl", "ufc", "soccer", "football", "tennis", "playoff", "match")),
        ("Esports", ("cs2", "league of legends", "valorant", "esports", "lck")),
        ("Culture", ("movie", "album", "grammy", "oscar", "celebrity", "eurovision")),
    )
    padded = f" {text} "
    for label, words in checks:
        if any(word in padded for word in words):
            topics.append(label)
    if not topics:
        topics.append(_category(market).replace("_", " ").title())
    return list(dict.fromkeys(topics))[:4]


def generate_market_briefing(
    market: Mapping[str, Any],
    lang: str = "en",
    related_count: int = 0,
) -> dict[str, str | list[str]]:
    normalized = _lang(lang)
    side = analyze_market_side(
        market,
        delta=_signed_probability_delta(market),
        confirmation_level=str(market.get("confirmation_level") or market.get("confirmation_level_key") or ""),
        language=normalized,
    )
    attention = classify_attention_vs_conviction(market, normalized)
    strength = classify_movement_strength(market)
    strength_read = classify_insight_strength(market, normalized, related_count=related_count)
    what_happened = generate_what_happened(market, normalized)
    main_tension = detect_main_tension(market, normalized, related_count=related_count)
    what_this_means = generate_what_this_means(market, normalized, related_count=related_count)
    checks = what_to_check_items(market, normalized)
    resolution = resolution_note(market, normalized)
    category_voice = category_voice_summary(market, normalized)
    related = related_topics_for_market(market)
    memory_summary = _safe(
        str(market.get("market_memory_summary") or ""),
        NO_HISTORY_MESSAGE[normalized],
    )
    memory_pattern = _safe(
        str(market.get("memory_pattern") or ""),
        memory_summary,
    )
    changed_since_last_seen = _safe(
        str(market.get("changed_since_last_seen") or ""),
        memory_summary,
    )
    historical_context = _safe(
        str(market.get("historical_context") or ""),
        memory_summary,
    )
    regime_label = _safe(
        str(market.get("market_regime") or ""),
        REGIME_LABELS[normalized]["quiet"],
    )
    regime_reason = _safe(
        str(market.get("regime_reason") or ""),
        (
            "There is not enough activity for a strong comparison yet."
            if normalized == "en"
            else "Пока мало активности для сильного сравнения."
        ),
    )

    if normalized == "en":
        strength_sentence = {
            "strong": "The move is strong because probability and volume are both visible.",
            "moderate": "The move is moderate; confirmation depends on follow-through.",
            "weak": "The move is weak, so the read should stay cautious.",
            "quiet": "The move is quiet; there is not enough evidence for a strong read.",
        }[strength]
    else:
        strength_sentence = {
            "strong": "Движение сильное: заметны и вероятность, и объём.",
            "moderate": "Движение умеренное; подтверждение зависит от продолжения.",
            "weak": "Движение слабое, поэтому вывод должен быть осторожным.",
            "quiet": "Движение спокойное; данных для сильного вывода мало.",
        }[strength]

    if market.get("has_market_memory") and "barely changed" in memory_summary.lower():
        quick_take = _safe(memory_summary, attention["interpretation"])
    elif market.get("has_market_memory") and "почти не изменилась" in memory_summary.lower():
        quick_take = _safe(memory_summary, attention["interpretation"])
    else:
        quick_take = _safe(attention["interpretation"], FALLBACK_MESSAGES[normalized]["explain_fallback"])
    if side.dominant_side != "UNKNOWN":
        quick_take = _safe(side.side_verdict, quick_take)
        main_tension = _safe(side.side_tension, main_tension)
        if side.dominant_side in {"YES", "NO", "BALANCED"}:
            what_this_means = _safe(
                (
                    f"{side.side_balance}. {side.side_risk_note}"
                    if normalized == "en"
                    else f"{side.side_balance}. {side.side_risk_note}"
                ),
                what_this_means,
            )
        side_check = "YES / NO balance" if normalized == "en" else "баланс YES / NO"
        if side_check not in checks:
            checks = [side_check, *checks][:4]
    return {
        "quick_take": quick_take,
        "what_happened": what_happened,
        "what_is_happening": what_happened,
        "main_tension": main_tension,
        "what_this_means": what_this_means,
        "attention_vs_conviction": attention["interpretation"],
        "insight_strength": strength_read["label"],
        "confidence_level": strength_read["confidence_level"],
        "strength_of_read": strength_sentence,
        "how_strong_is_the_move": strength_sentence,
        "what_to_check": checks,
        "related_topics": related,
        "related_themes": ", ".join(related),
        "resolution_note": resolution,
        "how_this_resolves": resolution,
        "category_voice": category_voice,
        "market_memory_summary": memory_summary,
        "memory_pattern": memory_pattern,
        "changed_since_last_seen": changed_since_last_seen,
        "historical_context": historical_context,
        "market_regime": regime_label,
        "regime_reason": regime_reason,
        **side.as_dict(),
    }


def generate_today_narrative(markets: Sequence[Mapping[str, Any]], lang: str = "en") -> str:
    normalized = _lang(lang)
    if not markets:
        return FALLBACK_MESSAGES[normalized]["no_narrative"]

    groups = group_markets_by_narrative([dict(market) for market in markets])
    if groups:
        top = groups[0]
        label = top["narrative"]
        text = (
            f"{label} is the clearest shared theme today. {top['group_interpretation']}"
            if normalized == "en"
            else f"{label} — самая ясная общая тема дня. {top['group_interpretation']}"
        )
    else:
        categories: dict[str, int] = {}
        for market in markets:
            category = _category(market)
            categories[category] = categories.get(category, 0) + 1
        if len(categories) >= 2:
            top_categories = sorted(categories, key=categories.get, reverse=True)[:2]
            if normalized == "en":
                text = (
                    "There is no single dominant story today. "
                    f"The market read is split between {_category_display(top_categories[0], normalized)} "
                    f"and {_category_display(top_categories[1], normalized)}."
                )
            else:
                text = (
                    "Сегодня нет одного доминирующего сюжета. "
                    f"Картина дня распределена между {_category_display(top_categories[0], normalized)} "
                    f"и {_category_display(top_categories[1], normalized)}."
                )
        else:
            top_category = next(iter(categories), "global")
            text = category_summary(top_category, normalized)
    return _safe(text, FALLBACK_MESSAGES[normalized]["no_narrative"])


def generate_what_changed(markets: Sequence[Mapping[str, Any]], lang: str = "en") -> list[str]:
    normalized = _lang(lang)
    if not markets:
        return [FALLBACK_MESSAGES[normalized]["no_narrative"]]

    grouped: dict[str, int] = {}
    for market in markets:
        grouped[_category(market)] = grouped.get(_category(market), 0) + 1
    ending = sum(1 for market in markets if detect_resolution_proximity(market))
    strong = sum(1 for market in markets if classify_movement_strength(market) in {"strong", "moderate"})

    bullets: list[str] = []
    if normalized == "en":
        labels = {
            "politics": "🔥 Political markets became more active",
            "crypto": "📈 Crypto activity returned",
            "ai": "👀 AI attention increased",
            "sports": "🔥 Sports markets heated up",
            "esports": "🔥 Esports markets heated up",
            "culture": "👀 Culture markets drew fresh interest",
            "global": "🔥 Global-event markets became more visible",
        }
        if grouped:
            for category in sorted(grouped, key=grouped.get, reverse=True)[:2]:
                bullets.append(labels.get(category, "👀 A market theme became more visible"))
        if ending:
            bullets.append(f"⚠️ {ending} markets are ending soon")
        if strong:
            bullets.append(f"📈 {strong} markets need a closer read")
    else:
        labels = {
            "politics": "🔥 Политические рынки оживились",
            "crypto": "📈 Крипта снова активна",
            "ai": "👀 Внимание к AI усилилось",
            "sports": "🔥 Спорт разогревается",
            "esports": "🔥 Киберспорт разогревается",
            "culture": "👀 Культурные рынки заметнее",
            "global": "🔥 Мировые события заметнее",
        }
        if grouped:
            for category in sorted(grouped, key=grouped.get, reverse=True)[:2]:
                bullets.append(labels.get(category, "👀 Тема стала заметнее"))
        if ending:
            bullets.append(f"⚠️ {ending} рынков скоро завершаются")
        if strong:
            bullets.append(f"📈 {strong} рынков требуют разбора")

    if not bullets:
        bullets.append("📈 No dominant market narrative today" if normalized == "en" else "📈 Сильного общего нарратива сегодня нет")
    return [_safe(bullet, FALLBACK_MESSAGES[normalized]["weak_data"]) for bullet in bullets[:5]]
