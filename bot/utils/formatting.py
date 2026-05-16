from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bot.database.models import MarketSnapshot, UserWatchlist
from bot.services.market_analyzer import MarketMovement
from bot.services.market_health import MarketHealth
from bot.services.market_indicators import calculate_market_indicators
from bot.services.market_mood import calculate_market_mood
from bot.services.market_side_engine import analyze_market_side
from bot.services.polymarket_client import Market
from bot.services.pulse_score import PulseScore
from bot.utils.i18n import normalize_language


def _missing_data(language: str | None = None) -> str:
    return "data not available yet" if normalize_language(language) == "en" else "данных пока нет"


def _label(ru: str, en: str, language: str | None = None) -> str:
    return en if normalize_language(language) == "en" else ru


def format_probability(value: float | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    percent = value * 100
    if percent <= 0:
        return _label("Маловероятно", "Unlikely", language)
    if percent < 1:
        return "<1%"
    return f"{percent:.0f}%"


def format_percentage_points(value: float | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    return f"{value * 100:+.0f}%"


def _format_outcome_percent(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if 0 < number < 1:
        return "<1%"
    return f"{number:.0f}%" if number.is_integer() else f"{number:.1f}%"


def _outcome_balance_heading(market: Market, language: str | None = None, delta: float | None = None) -> str:
    side = analyze_market_side(market, delta=delta, language=language)
    if side.should_use_yes_no:
        return _label("Баланс YES / NO:", "YES / NO balance:", language)
    if side.outcome_type == "sports_moneyline":
        return _label("Варианты рынка:", "Market outcomes:", language)
    return _label("Баланс вариантов:", "Outcome balance:", language)


def _side_lines(market: Market, language: str | None = None, delta: float | None = None) -> list[str]:
    side = analyze_market_side(market, delta=delta, language=language)
    if not side.should_use_yes_no:
        lines = [
            f"{outcome.get('short_label') or outcome.get('label')}: {_format_outcome_percent(outcome.get('probability'))}"
            for outcome in side.display_outcomes[:5]
        ]
        if len(side.display_outcomes) > 5:
            lines.append(_label(f"ещё {len(side.display_outcomes) - 5}", f"+{len(side.display_outcomes) - 5} more", language))
        lines.extend(
            [
                side.outcome_balance_summary,
                f"{_label('Короткий вывод', 'Quick read', language)}: {side.side_verdict}",
            ]
        )
        return lines

    if side.dominant_side == "YES":
        lean = _label("Рынок склоняется к YES.", "Market leans YES.", language)
    elif side.dominant_side == "NO":
        lean = _label("Рынок склоняется к NO.", "Market leans NO.", language)
    elif side.dominant_side == "BALANCED":
        lean = _label("Стороны почти равны.", "Both sides are close.", language)
    else:
        lean = _label("Данных по сторонам пока мало.", "Not enough side data yet.", language)
    return [
        f"YES: {_format_outcome_percent(side.yes_probability)}",
        f"NO: {_format_outcome_percent(side.no_probability)}",
        lean,
        f"{_label('Короткий вывод', 'Quick read', language)}: {side.side_verdict}",
    ]


def format_usd(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value:,.0f}"
    return f"${value:.0f}"


def format_compact_usd(value: float | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def format_date(value: datetime | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    return value.date().isoformat()


def format_time_until(
    value: datetime | None,
    now: datetime | None = None,
    language: str | None = None,
) -> str:
    if value is None:
        return _missing_data(language)
    current = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    seconds = int((value - current).total_seconds())
    if seconds <= 0:
        return _label("завершён или скоро завершится", "ended or ending soon", language)
    days = seconds // 86_400
    if days >= 1:
        return f"{days} days"
    hours = max(1, seconds // 3_600)
    return f"{hours} hours"


def format_market_card(
    market: Market,
    explanation: str | None = None,
    heading: str = "🔥 Горячий рынок",
    movement_delta: float | None = None,
    pulse_score: PulseScore | None = None,
    market_health: MarketHealth | None = None,
    risk_flags: list[str] | None = None,
    language: str | None = None,
    news_context: str | None = None,
) -> str:
    indicators = calculate_market_indicators(
        market,
        pulse_score=pulse_score.value if pulse_score is not None else None,
        delta=movement_delta,
        language=language,
    )
    lines = [
        heading,
        "",
        _label("Название:", "Title:", language),
        market.question,
        "",
        _label("Вероятность:", "Probability:", language),
        format_probability(market.yes_probability, language),
        "",
        _outcome_balance_heading(market, language=language, delta=movement_delta),
        *_side_lines(market, language=language, delta=movement_delta),
        "",
        _label("Движение:", "Movement:", language),
        (
            f"{format_percentage_points(movement_delta, language)} "
            f"{_label('за 24ч', 'over 24h', language)}"
        )
        if movement_delta is not None
        else _missing_data(language),
        "",
        _label("Объём:", "Volume:", language),
        format_compact_usd(market.volume, language),
        "",
        _label("До завершения:", "Time left:", language),
        format_time_until(market.end_date, language=language),
        "",
        _label("Короткий вывод:", "Quick read:", language),
        indicators.indicator_summary,
    ]
    if news_context:
        lines.extend(
            [
                "",
                _label("Новостной фон:", "News context:", language),
                news_context,
            ]
        )
    mood = calculate_market_mood(market, delta=movement_delta, language=language)
    lines.extend(
        [
            "",
            _label("Настроение рынка:", "Market Mood:", language),
            f"{mood.label} · {mood.reason}",
            _label(
                "Почему люди сейчас обращают внимание.",
                "Why people are paying attention.",
                language,
            ),
        ]
    )
    if pulse_score is not None:
        lines.extend(
            [
                "",
                "⚡ Pulse Score:",
                f"{pulse_score.value}/100 · {pulse_score.label}",
                _label(
                    "Насколько рынок сейчас интересен.",
                    "How interesting this market looks today.",
                    language,
                ),
            ]
        )
    if market_health is not None:
        lines.extend(
            [
                "",
                "🩺 Market Health:",
                f"{market_health.value}/100 · {market_health.label}",
                _label(
                    "Насколько рынок понятный и живой.",
                    "How clean and readable the market looks.",
                    language,
                ),
            ]
        )
    if risk_flags:
        lines.extend(["", _label("Риски:", "Risk flags:", language), *risk_flags[:3]])
    if explanation:
        lines.extend(["", "AI brief:", explanation])
    return "\n".join(lines)


def format_watchlist_card(item: UserWatchlist, language: str | None = None) -> str:
    delta = None
    if item.initial_probability is not None and item.last_probability is not None:
        delta = item.last_probability - item.initial_probability
    return "\n".join(
        [
            "⭐ Watchlist",
            "",
            _label("Название:", "Title:", language),
            item.market_title,
            "",
            _label("Было:", "Initial:", language),
            format_probability(item.initial_probability, language),
            "",
            _label("Сейчас:", "Current:", language),
            format_probability(item.last_probability, language),
            "",
            _label("Изменение:", "Change:", language),
            format_percentage_points(delta, language),
        ]
    )


def format_movement_card(
    movement: MarketMovement,
    explanation: str | None = None,
    pulse_score: PulseScore | None = None,
    market_health: MarketHealth | None = None,
    risk_flags: list[str] | None = None,
    language: str | None = None,
) -> str:
    indicators = calculate_market_indicators(
        movement.market,
        pulse_score=pulse_score.value if pulse_score is not None else None,
        delta=movement.delta,
        language=language,
    )
    if normalize_language(language) == "en":
        direction = "increased" if movement.delta > 0 else "decreased"
        movement_label = f"Probability {direction}:"
    else:
        direction = "выросла" if movement.delta > 0 else "снизилась"
        movement_label = f"Вероятность {direction}:"
    lines = [
        _label("⚡ Резкое движение:", "⚡ Sharp move:", language),
        movement.market.question,
        "",
        movement_label,
        f"{format_probability(movement.old_probability, language)} → {format_probability(movement.new_probability, language)}",
        "",
        _label("Изменение:", "Change:", language),
        format_percentage_points(movement.delta, language),
        "",
        _label("Объём:", "Volume:", language),
        format_compact_usd(movement.market.volume, language),
        "",
        _label("До завершения:", "Time left:", language),
        format_time_until(movement.market.end_date, language=language),
        "",
        _outcome_balance_heading(movement.market, language=language, delta=movement.delta),
        *_side_lines(movement.market, language=language, delta=movement.delta),
        "",
        _label("Короткий вывод:", "Quick read:", language),
        indicators.indicator_summary,
    ]
    if pulse_score is not None:
        lines.extend(["", "⚡ Pulse Score:", f"{pulse_score.value}/100 · {pulse_score.label}"])
    if market_health is not None:
        lines.extend(["", "🩺 Market Health:", f"{market_health.value}/100 · {market_health.label}"])
    if risk_flags:
        lines.extend(["", _label("Риски:", "Risk flags:", language), *risk_flags[:3]])
    if explanation:
        lines.extend(["", "AI brief:", explanation])
    return "\n".join(lines)


def format_today_pulse_card(
    item: Any,
    index: int,
    ai_why: str | None = None,
    language: str | None = None,
) -> str:
    market = item.market
    why = ai_why or item.why_it_matters
    mood = calculate_market_mood(market, delta=item.delta, language=language)
    indicators = calculate_market_indicators(
        market,
        pulse_score=item.pulse_score.value,
        delta=item.delta,
        language=language,
    )
    if normalize_language(language) == "en":
        lines = [
            "📰 Morning Briefing",
            "",
            "Your quick read of what matters today.",
            "",
            f"{index}. {market.question}",
            "",
            "Why people care:",
            why,
            "",
            "Market Mood:",
            f"{mood.label} · {mood.reason}",
            "",
            "Watch:",
            "Probability, activity, and resolution rules.",
            "",
            "Probability:",
            format_probability(market.yes_probability, language),
            "",
            _outcome_balance_heading(market, language=language, delta=item.delta),
            *_side_lines(market, language=language, delta=item.delta),
            "",
            "Pulse Score:",
            f"{item.pulse_score.value}/100",
            "How interesting this market looks today.",
            "",
            "Indicators:",
            f"Market heat: {indicators.market_heat}",
            f"Confirmation: {indicators.confirmation_level}",
            f"Error risk: {indicators.error_risk}",
            "",
            "Verdict:",
            indicators.indicator_summary,
            "",
            "Research only · No trade execution",
        ]
        return "\n".join(lines)

    lines = [
        "📰 Утренний обзор",
        "",
        "Короткая картина дня.",
        "",
        f"{index}. {market.question}",
        "",
        "Почему людям это интересно:",
        why,
        "",
        "Настроение рынка:",
        f"{mood.label} · {mood.reason}",
        "",
        "За чем следить:",
        "Вероятность, активность и правила разрешения.",
        "",
        "Вероятность:",
        format_probability(market.yes_probability, language),
        "",
        _outcome_balance_heading(market, language=language, delta=item.delta),
        *_side_lines(market, language=language, delta=item.delta),
        "",
        "Pulse Score:",
        f"{item.pulse_score.value}/100",
        "Насколько рынок сейчас интересен.",
        "",
        "Индикаторы:",
        f"Температура: {indicators.market_heat}",
        f"Подтверждение: {indicators.confirmation_level}",
        f"Риск ошибки: {indicators.error_risk}",
        "",
        "Вывод:",
        indicators.indicator_summary,
        "",
        "Для анализа · Без сделок",
    ]
    return "\n".join(lines)


def format_channel_digest(
    items: list[Any],
    language: str | None = "en",
) -> str:
    normalized = normalize_language(language)
    if normalized == "en":
        lines = [
            "📰 Today’s Pulse",
            "",
            "3 Polymarket markets worth watching today:",
        ]
        for index, item in enumerate(items[:3], start=1):
            lines.extend(
                [
                    "",
                    f"{index}. {item.market.question}",
                    f"Probability: {format_probability(item.market.yes_probability, 'en')}",
                    f"Pulse Score: {item.pulse_score.value}/100",
                    f"Why people care: {item.why_it_matters}",
                ]
            )
        lines.extend(
            [
                "",
                "Analytics only.",
                "No trading. No wallets. No financial advice.",
                "",
                "Bot: https://t.me/PulseMarketAIBot",
            ]
        )
        return "\n".join(lines)

    lines = [
        "📰 Пульс дня",
        "",
        "3 рынка Polymarket, за которыми сегодня стоит следить:",
    ]
    for index, item in enumerate(items[:3], start=1):
        lines.extend(
            [
                "",
                f"{index}. {item.market.question}",
                f"Вероятность: {format_probability(item.market.yes_probability, 'ru')}",
                f"Pulse Score: {item.pulse_score.value}/100",
                f"Почему людям интересно: {item.why_it_matters}",
            ]
        )
    lines.extend(
        [
            "",
            "Только аналитика.",
            "Без торговли. Без кошельков. Без финансовых советов.",
            "",
            "Бот: https://t.me/PulseMarketAIBot",
        ]
    )
    return "\n".join(lines)


def format_market_timeline(
    snapshots: list[MarketSnapshot],
    language: str | None = None,
) -> str:
    if len(snapshots) < 3:
        if normalize_language(language) == "en":
            return (
                "📊 Market timeline\n\n"
                "Not enough data yet. The bot will show a timeline after a few updates."
            )
        return "📊 Динамика рынка\n\nПока мало данных. Бот начнёт показывать динамику после нескольких обновлений."

    values = [snapshot.yes_probability for snapshot in snapshots if snapshot.yes_probability is not None]
    if len(values) < 3:
        if normalize_language(language) == "en":
            return (
                "📊 Market timeline\n\n"
                "Not enough data yet. The bot will show a timeline after a few updates."
            )
        return "📊 Динамика рынка\n\nПока мало данных. Бот начнёт показывать динамику после нескольких обновлений."

    delta = values[-1] - values[0]
    chain = " → ".join(format_probability(value, language) for value in values[-8:])
    return "\n".join(
        [
            _label("📊 Динамика рынка", "📊 Market timeline", language),
            "",
            "24ч:",
            chain,
            "",
            _label("Изменение:", "Change:", language),
            format_percentage_points(delta, language),
            "",
            _label("Снимков:", "Snapshots:", language),
            str(len(values)),
        ]
    )


def format_beginner_explanation(
    market: Market,
    ai_brief: str | None = None,
    language: str | None = None,
    pulse_score: PulseScore | None = None,
    movement_delta: float | None = None,
) -> str:
    indicators = calculate_market_indicators(
        market,
        pulse_score=pulse_score.value if pulse_score is not None else None,
        delta=movement_delta,
        language=language,
    )
    if normalize_language(language) == "en":
        lines = [
            "🧠 Analysis",
            "",
            "In plain English:",
            "Quick take:",
            "This market is about the event named in the title.",
            "The useful read is whether probability, volume, and timing point in the same direction.",
            "Check the rules, volume quality, and time left before drawing conclusions.",
            "",
            f"Current probability: {format_probability(market.yes_probability, language)}",
            "",
            _outcome_balance_heading(market, language=language, delta=movement_delta),
            *_side_lines(market, language=language, delta=movement_delta),
            "",
            "Market indicators:",
            f"Market heat: {indicators.market_heat}",
            f"Confirmation: {indicators.confirmation_level}",
            f"Error risk: {indicators.error_risk}",
            f"Time pressure: {indicators.time_pressure}",
            f"Market depth: {indicators.market_depth}",
            f"AI verdict: {indicators.ai_verdict}",
        ]
        if ai_brief:
            lines.extend(["", "AI market read:", ai_brief])
        return "\n".join(lines)

    lines = [
        "🧠 Разбор",
        "",
        "Простыми словами:",
        "Короткий вывод:",
        "Этот рынок про событие, указанное в названии.",
        "Полезное чтение — совпадают ли вероятность, объём и тайминг.",
        "Проверь правила, качество объёма и время до завершения, прежде чем делать выводы.",
        "",
        f"Текущая вероятность: {format_probability(market.yes_probability)}",
        "",
        _outcome_balance_heading(market, language=language, delta=movement_delta),
        *_side_lines(market, language=language, delta=movement_delta),
        "",
        "Индикаторы рынка:",
        f"Температура: {indicators.market_heat}",
        f"Подтверждение: {indicators.confirmation_level}",
        f"Риск ошибки: {indicators.error_risk}",
        f"Давление времени: {indicators.time_pressure}",
        f"Объём: {indicators.market_depth}",
        f"AI вывод: {indicators.ai_verdict}",
    ]
    if ai_brief:
        lines.extend(["", "AI анализ:", ai_brief])
    return "\n".join(lines)


def format_share_market_card(
    market: Market,
    pulse_score: PulseScore | None = None,
    language: str | None = None,
) -> str:
    if normalize_language(language) == "en":
        lines = [
            "📤 Polymarket market",
            "",
            market.question,
            "",
            f"Probability: {format_probability(market.yes_probability, language)}",
            f"Volume: {format_compact_usd(market.volume, language)}",
        ]
        if pulse_score is not None:
            lines.append(f"Pulse Score: {pulse_score.value}/100 · {pulse_score.label}")
        lines.extend(
            [
                "",
                "PulseMarket AI shows hot markets, sharp moves, and plain-language explanations.",
                market.url,
            ]
        )
        return "\n".join(lines)

    lines = [
        "📤 Рынок Polymarket",
        "",
        market.question,
        "",
        f"Вероятность: {format_probability(market.yes_probability)}",
        f"Объём: {format_compact_usd(market.volume)}",
    ]
    if pulse_score is not None:
        lines.append(f"Pulse Score: {pulse_score.value}/100 · {pulse_score.label}")
    lines.extend(
        [
            "",
            "PulseMarket AI показывает горячие рынки, резкие движения и объясняет всё простым языком.",
            market.url,
        ]
    )
    return "\n".join(lines)
