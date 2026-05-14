from __future__ import annotations

from dataclasses import dataclass

from bot.services.ai_explainer import AIExplainer
from bot.services.polymarket_client import Market
from bot.utils.formatting import format_date, format_probability
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class ResolutionFields:
    description: str | None
    rules: str | None
    resolution_source: str | None
    condition: str | None


def _string_field(market: Market, *keys: str) -> str | None:
    for key in keys:
        value = market.raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def extract_resolution_fields(market: Market) -> ResolutionFields:
    return ResolutionFields(
        description=_string_field(market, "description", "marketDescription"),
        rules=_string_field(market, "rules", "resolutionRules", "resolutionCriteria"),
        resolution_source=_string_field(
            market,
            "resolutionSource",
            "resolution_source",
            "source",
        ),
        condition=_string_field(market, "condition", "conditionId", "question"),
    )


def build_resolution_explanation(
    market: Market,
    ai_text: str | None = None,
    language: str | None = None,
) -> str:
    fields = extract_resolution_fields(market)
    if normalize_language(language) == "en":
        lines = [
            "📜 Resolution rules",
            "",
            "1. What this market means:",
            market.question,
            "",
            "2. What must happen:",
            fields.description
            or fields.condition
            or "Check the market description and rules on Polymarket.",
            "",
            "3. When it ends:",
            format_date(market.end_date, language),
            "",
            "4. Rules to check:",
            fields.rules
            or "Open the market page and check resolution rules, data source, and payout conditions.",
            "",
            "5. Why probability is not a guarantee:",
            f"{format_probability(market.yes_probability, language)} is the market's current estimate, not a promised result.",
        ]
        if fields.resolution_source:
            lines.extend(["", "Resolution source:", fields.resolution_source])
        if ai_text:
            lines.extend(["", "AI explanation:", ai_text])
        return "\n".join(lines)

    lines = [
        "📜 Как решится рынок?",
        "",
        "1. Что означает рынок:",
        market.question,
        "",
        "2. Что должно произойти:",
        fields.description or fields.condition or "Нужно проверить описание и правила рынка на странице Polymarket.",
        "",
        "3. Когда рынок завершится:",
        format_date(market.end_date, language),
        "",
        "4. Какие правила надо проверить:",
        fields.rules or "Открой страницу рынка и проверь правила разрешения, источник данных и условия выплаты.",
        "",
        "5. Почему вероятность не гарантия:",
        f"{format_probability(market.yes_probability, language)} — это текущая оценка рынка, а не обещание результата.",
    ]
    if fields.resolution_source:
        lines.extend(["", "Источник разрешения:", fields.resolution_source])
    if ai_text:
        lines.extend(["", "AI explanation:", ai_text])
    return "\n".join(lines)


class ResolutionExplainer:
    async def explain(
        self,
        market: Market,
        ai_explainer: AIExplainer,
        language: str | None = None,
    ) -> str:
        ai_text = await ai_explainer.explain_resolution(market)
        return build_resolution_explanation(market, ai_text=ai_text, language=language)
