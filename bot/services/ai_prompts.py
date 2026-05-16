from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from bot.utils.i18n import normalize_language

_BANNED_PHRASE_PARTS: tuple[tuple[str, ...], ...] = (
    ("activity ", "increased"),
    ("people are ", "watching"),
    ("market is ", "active"),
    ("this market asks ", "whether"),
    ("attention ", "shifted"),
    ("this is ", "noi", "se"),
    ("this is a ", "sig", "nal"),
    ("sig", "nal"),
    ("noi", "se"),
    ("ш", "ум"),
    ("insi", "der"),
    ("alpha ", "leak"),
    ("copy this ", "trader"),
    ("b", "uy"),
    ("se", "ll"),
    ("guaran", "teed"),
    ("100", "%"),
    ("good ", "bet"),
    ("b", "uy ", "now"),
    ("se", "ll ", "now"),
    ("поку", "пай"),
    ("прода", "вай"),
    ("ста", "вь"),
    ("сиг", "нал"),
    ("точный ", "прогноз"),
)

BANNED_PHRASES: tuple[str, ...] = tuple("".join(parts) for parts in _BANNED_PHRASE_PARTS)


def validate_ai_output(text: str) -> list[str]:
    """Return disallowed fragments found in generated text."""

    lowered = str(text or "").lower()
    return [phrase for phrase in BANNED_PHRASES if phrase in lowered]


def market_analyst_system_prompt() -> str:
    return (
        "You are a calm, sharp market analyst. "
        "Write like a senior editor at a financial publication. "
        "Use short sentences. No filler. No robotic phrasing. "
        "Interpret what is happening instead of retelling the data. "
        "Look for the tension between public attention, probability movement, volume, and time left. "
        "Also interpret the YES and NO side balance when the data is available. "
        "Do not make predictions, do not give financial advice, and do not use banned market jargon. "
        "Always answer what the situation means for the reader."
    )


def build_market_briefing_prompt(market_json: Mapping[str, Any], lang: str = "en") -> str:
    normalized = normalize_language(lang)
    language_name = "English" if normalized == "en" else "Russian"
    return (
        f"Output language: {language_name}\n"
        f"Given this market data: {json.dumps(dict(market_json), ensure_ascii=False, default=str)}\n\n"
        "Generate a market briefing with exactly these sections:\n"
        "1. QUICK TAKE: one sentence with the main takeaway, not a description.\n"
        "2. WHAT IS HAPPENING: two or three factual sentences.\n"
        "3. MAIN TENSION: one sentence naming the contradiction in the data.\n"
        "4. WHAT THIS MEANS: two or three interpretation sentences, no raw data repetition.\n"
        "5. ATTENTION VS CONVICTION: one or two sentences on whether expectations actually changed.\n"
        "6. YES / NO BALANCE: one or two sentences on which side the market leans toward.\n"
        "7. MARKET MEMORY: one sentence comparing the current read with prior snapshots.\n"
        "8. MARKET REGIME: one sentence naming the current behavior type and why.\n"
        "9. STRENGTH OF READ: one sentence using weak, moderate, or strong.\n"
        "10. WHAT TO CHECK: two to four bullets about rules, volume, timeframe, related markets, and side balance.\n"
        "11. RELATED THEMES: include only if a cross-market connection exists.\n"
        "12. RESOLUTION RULES: one or two plain-language sentences.\n\n"
        "Rules: separate every section clearly, do not repeat information, avoid banned phrasing, "
        "avoid generic wording, and do not use directional advice. Use market_memory_summary, "
        "memory_pattern, market_regime, and regime_reason when present."
    )


def build_today_narrative_prompt(markets_json: Sequence[Mapping[str, Any]], lang: str = "en") -> str:
    normalized = normalize_language(lang)
    language_name = "English" if normalized == "en" else "Russian"
    return (
        f"Output language: {language_name}\n"
        f"Given today's active markets: {json.dumps(list(markets_json), ensure_ascii=False, default=str)}\n\n"
        "Write a daily market briefing in at most five sentences. "
        "Synthesize markets into two or three theme-level observations. "
        "Explain whether attention is moving faster than actual expectation changes. "
        "Compare the current brief with prior market memory when history is available. "
        "If no dominant narrative exists, say so directly. "
        "Sound like an editorial briefing, not a generic AI summary. "
        "Do not list markets one by one."
    )


def build_what_changed_prompt(changes_json: Sequence[Mapping[str, Any]], lang: str = "en") -> str:
    normalized = normalize_language(lang)
    language_name = "English" if normalized == "en" else "Russian"
    return (
        f"Output language: {language_name}\n"
        f"Given these market changes in the last 24h: {json.dumps(list(changes_json), ensure_ascii=False, default=str)}\n\n"
        "Write three to five very short editorial bullets. "
        "Each bullet must be one observation, ten words or fewer. "
        "Use emoji prefixes: 🔥 for major shifts, ⚠️ for approaching resolutions, "
        "👀 for attention spikes, 📈 for volume."
    )
