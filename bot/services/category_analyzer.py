from __future__ import annotations

from bot.utils.i18n import normalize_language

CATEGORY_VOICE: dict[str, dict[str, tuple[str, ...] | str]] = {
    "politics": {
        "focus": ("diplomatic expectations", "geopolitical positioning", "policy cues"),
        "avoid": ("volume-first language", "sports timing language"),
        "example_tone": "The market reflects cautious diplomatic expectations rather than a firm shift.",
    },
    "crypto": {
        "focus": ("short-term volatility", "volume bursts", "longer-term calm"),
        "avoid": ("geopolitical framing", "sports timing language"),
        "example_tone": "Short-term volatility markets activated, but longer-term crypto expectations remain stable.",
    },
    "sports": {
        "focus": ("event proximity", "match-driven activity", "short resolution windows"),
        "avoid": ("geopolitical framing", "macro language"),
        "example_tone": "The market became busier as the match approaches. The short resolution window matters.",
    },
    "esports": {
        "focus": ("match timing", "bracket narratives", "short resolution windows"),
        "avoid": ("macro language", "geopolitical framing"),
        "example_tone": "Interest is tied to match timing, where expectations can change quickly.",
    },
    "ai": {
        "focus": ("news cycles", "announcement-driven interest", "discussion versus conviction"),
        "avoid": ("sports timing language", "macro language"),
        "example_tone": "Attention rose around a recent announcement, but conviction remains limited.",
    },
    "global": {
        "focus": ("macro events", "policy timing", "cross-market attention"),
        "avoid": ("sports framing", "celebrity framing"),
        "example_tone": "The market is reading a wider event cycle rather than one isolated headline.",
    },
    "culture": {
        "focus": ("public discussion", "release timing", "audience attention"),
        "avoid": ("macro language", "geopolitical framing"),
        "example_tone": "The topic became more visible, but expectations remain cautious.",
    },
}


def get_category_prompt_modifier(category: str, lang: str = "en") -> str:
    """Return category-specific tone guidance for prompt construction."""

    normalized = normalize_language(lang)
    voice = CATEGORY_VOICE.get(category) or CATEGORY_VOICE["global"]
    focus = ", ".join(str(item) for item in voice["focus"])
    avoid = ", ".join(str(item) for item in voice["avoid"])
    example = str(voice["example_tone"])
    if normalized == "ru":
        return (
            f"Категория: {category}. Фокус: {focus}. Избегай: {avoid}. "
            f"Тон: {example}"
        )
    return (
        f"Category: {category}. Focus on {focus}. Avoid {avoid}. "
        f"Tone example: {example}"
    )


def category_summary(category: str, lang: str = "en") -> str:
    normalized = normalize_language(lang)
    if normalized == "ru":
        return {
            "politics": "Политические рынки читают осторожные ожидания вокруг дипломатии и решений власти.",
            "crypto": "Крипторынки реагируют на краткосрочную волатильность, пока долгий горизонт спокойнее.",
            "sports": "Спортивные рынки оживают ближе к событиям с коротким окном разрешения.",
            "esports": "Киберспорт чаще двигается вокруг матчевого тайминга и сетки турнира.",
            "ai": "AI-рынки реагируют на новости и обсуждения, но уверенность часто появляется позже.",
            "global": "Мировые рынки отражают широкий событийный фон, а не одну isolated headline.",
            "culture": "Культурные рынки зависят от публичного обсуждения и календаря релизов.",
        }.get(category, "Эта категория заметна, но сильного вывода пока нет.")
    return {
        "politics": "Political markets are reading cautious expectations around diplomacy and policy.",
        "crypto": "Crypto markets are reacting to short-term volatility while longer horizons look calmer.",
        "sports": "Sports markets get busier near events with short resolution windows.",
        "esports": "Esports markets often move around match timing and bracket narratives.",
        "ai": "AI markets react to announcements and discussion before conviction appears.",
        "global": "Global markets reflect a wider event cycle rather than one isolated headline.",
        "culture": "Culture markets depend on public discussion and release timing.",
    }.get(category, "This category is visible, but the read is still limited.")

