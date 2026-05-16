from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bot.services.ai_output_parser import detect_banned_language, detect_generic_phrases
from bot.services.ai_output_schema import AIOutputSchema
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class AIQualityResult:
    score: int
    flags: tuple[str, ...]


def _strings(payload: Any) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, Mapping):
        result: list[str] = []
        for value in payload.values():
            result.extend(_strings(value))
        return result
    if isinstance(payload, (list, tuple, set)):
        result = []
        for value in payload:
            result.extend(_strings(value))
        return result
    return []


def _repetitive(strings: list[str]) -> bool:
    normalized = [text.strip().lower() for text in strings if len(text.strip()) > 20]
    if len(normalized) < 3:
        return False
    return len(set(normalized)) <= max(1, len(normalized) // 2)


def _mentions_context(strings: list[str], context: Mapping[str, Any] | None) -> bool:
    if not context:
        return True
    haystack = " ".join(strings).lower()
    candidates: list[str] = []
    for key in ("title", "market_title", "dominant_outcome", "runner_up", "news_title", "category"):
        value = context.get(key)
        if value:
            candidates.extend(part for part in str(value).replace("/", " ").split() if len(part) >= 4)
    return not candidates or any(candidate.lower() in haystack for candidate in candidates[:12])


def score_ai_output(
    payload: Mapping[str, Any],
    schema: AIOutputSchema | None = None,
    context: Mapping[str, Any] | None = None,
) -> AIQualityResult:
    score = 100
    flags: list[str] = []
    strings = _strings(payload)
    joined = " ".join(strings)

    if not strings or not joined.strip():
        flags.append("empty_output")
        score -= 60

    if detect_banned_language(payload):
        flags.append("banned_language")
        score -= 80

    if detect_generic_phrases(payload):
        flags.append("generic_phrase")
        score -= 35

    if any(len(text) > 260 for text in strings):
        flags.append("too_long")
        score -= 10

    if _repetitive(strings):
        flags.append("repetitive")
        score -= 15

    if not _mentions_context(strings, context):
        flags.append("missing_concrete_context")
        score -= 15

    if schema is not None:
        for field_name in schema.critical_fields:
            value = payload.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                flags.append(f"empty:{field_name}")
                score -= 20
        if "what_changed" in schema.required_fields and context and context.get("has_changes"):
            value = payload.get("what_changed")
            if not value:
                flags.append("missing_what_changed")
                score -= 15
        if context and context.get("analysis_context") and not (
            payload.get("what_to_verify") or payload.get("what_to_check")
        ):
            flags.append("missing_what_to_verify")
            score -= 15

    return AIQualityResult(score=max(0, min(100, score)), flags=tuple(dict.fromkeys(flags)))


def fallback_interpretation(
    *,
    lang: str = "en",
    probability_moved: bool = False,
    news_exists: bool = False,
    market_flat: bool = False,
    near_deadline: bool = False,
    market_moved_without_news: bool = False,
    dominant_outcome: str | None = None,
    runner_up: str | None = None,
) -> str:
    normalized = normalize_language(lang)
    if normalized == "ru":
        if near_deadline:
            return "До завершения мало времени, поэтому важнее проверить правила разрешения и последние официальные источники."
        if dominant_outcome and runner_up:
            return f"Рынок больше склоняется к {dominant_outcome}, а разрыв с {runner_up} показывает, насколько выбор уже определён."
        if probability_moved and news_exists:
            return "Вероятность сдвинулась после новостного события, но важно проверить источник и правила разрешения."
        if news_exists and market_flat:
            return "Новость есть, но рынок почти не изменил оценку. Пока это больше внешний фон, чем сильная реакция рынка."
        if market_moved_without_news:
            return "Рынок сдвинулся без сильного внешнего подтверждения. Такое движение лучше читать осторожно."
        return "Данных достаточно для осторожного чтения, но не для сильного вывода."

    if near_deadline:
        return "Resolution is close, so the key check is the rule set and the latest official sources."
    if dominant_outcome and runner_up:
        return f"The market leans toward {dominant_outcome}, while the gap to {runner_up} shows how settled the field looks."
    if probability_moved and news_exists:
        return "Probability moved after a news event, but the source and resolution rules still matter."
    if news_exists and market_flat:
        return "News is present, but the market barely repriced. For now, this looks more like context than a strong market reaction."
    if market_moved_without_news:
        return "The market moved without strong external confirmation. That kind of move deserves caution."
    return "There is enough data for a cautious read, not a strong conclusion."
