from __future__ import annotations

from dataclasses import dataclass

from bot.services.polymarket_client import Market
from bot.utils.formatting import (
    format_compact_usd,
    format_percentage_points,
    format_time_until,
)
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class MovementExplanation:
    title: str
    lines: list[str]

    def to_text(self) -> str:
        return "\n".join([self.title, "", *self.lines])


def explain_movement(
    market: Market,
    delta: float | None = None,
    risk_flags: list[str] | None = None,
    topic_match: str | None = None,
    language: str | None = None,
) -> MovementExplanation:
    normalized = normalize_language(language)
    flags = risk_flags or []

    if delta is None:
        if normalized == "en":
            return MovementExplanation(
                title="🧭 Why this matters",
                lines=[
                    "Not enough movement data yet.",
                    "PulseMarket AI will improve this after more snapshots.",
                ],
            )
        return MovementExplanation(
            title="🧭 Почему это важно",
            lines=[
                "Пока мало данных о движении.",
                "PulseMarket AI станет точнее после нескольких снимков рынка.",
            ],
        )

    if normalized == "en":
        movement = format_percentage_points(delta, "en")
        lines = [
            f"• Probability changed by {movement}.",
            f"• Volume is {format_compact_usd(market.volume, 'en')}.",
            f"• Time left: {format_time_until(market.end_date, language='en')}.",
        ]
        if topic_match:
            lines.append(f"• Topic match: {topic_match}.")
        if flags:
            lines.append(f"• Risk flags: {', '.join(flags[:3])}.")
        return MovementExplanation(title="🧭 Why this matters", lines=lines)

    movement = format_percentage_points(delta, "ru")
    lines = [
        f"• Вероятность изменилась на {movement}.",
        f"• Объём: {format_compact_usd(market.volume, 'ru')}.",
        f"• До завершения: {format_time_until(market.end_date, language='ru')}.",
    ]
    if topic_match:
        lines.append(f"• Совпадение с темой: {topic_match}.")
    if flags:
        lines.append(f"• Флаги риска: {', '.join(flags[:3])}.")
    return MovementExplanation(title="🧭 Почему это важно", lines=lines)
