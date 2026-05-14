from __future__ import annotations

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = {"ru", "en"}

TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        "dashboard": (
            "🚀 PulseMarket AI\n\n"
            "Я отслеживаю рынки Polymarket, нахожу резкие движения и объясняю их простым языком.\n\n"
            "Режим:\n"
            "Analytics only\n\n"
            "Без кошельков.\n"
            "Без пополнений.\n"
            "Без торговли."
        ),
        "quick_start": (
            "Как пользоваться ботом:\n\n"
            "1. Нажми “Горячие рынки”, чтобы увидеть активные рынки.\n"
            "2. Нажми “Резкие движения”, чтобы увидеть рынки, где вероятность резко изменилась.\n"
            "3. Используй “Поиск рынка”, чтобы найти рынок по теме.\n"
            "4. Добавляй интересные рынки в Watchlist.\n"
            "5. Включи уведомления, чтобы не пропускать сильные движения."
        ),
        "search_prompt": (
            "Введите тему рынка.\n\n"
            "Например: trump, bitcoin, fed, election, ai"
        ),
        "empty_watchlist": (
            "Watchlist пока пуст. Добавь рынок из поиска, горячих рынков или новых рынков."
        ),
        "share": (
            "Поделись PulseMarket AI с другом:\n\n"
            "https://t.me/PulseMarketAIBot\n\n"
            "Это не финансовая реферальная программа.\n"
            "Без бонусов.\n"
            "Без денег.\n"
            "Просто share link."
        ),
        "about": (
            "PulseMarket AI — аналитический Telegram бот вокруг Polymarket.\n\n"
            "Что он делает:\n"
            "• показывает горячие, новые и тематические рынки\n"
            "• ищет рынки по теме\n"
            "• ведёт Watchlist\n"
            "• отслеживает резкие движения вероятностей\n"
            "• отправляет уведомления, если вы их включили\n\n"
            "Важно: бот не торгует, не подключает кошельки, не просит приватные ключи и не принимает деньги.\n\n"
            "Источник данных: публичный Gamma API Polymarket."
        ),
        "settings_saved": "Готово. Настройки сохранены.",
        "api_error": "Не смог получить данные Polymarket. Попробуйте чуть позже.",
    },
    "en": {
        "dashboard": (
            "🚀 PulseMarket AI\n\n"
            "I monitor Polymarket markets, find sharp movements, and explain them in plain language.\n\n"
            "Mode:\n"
            "Analytics only\n\n"
            "No wallets.\n"
            "No deposits.\n"
            "No trading."
        ),
        "quick_start": (
            "How to use the bot:\n\n"
            "1. Tap “Hot Markets” to see active markets.\n"
            "2. Tap “Sharp Moves” to see markets where probabilities changed quickly.\n"
            "3. Use “Market Search” to find markets by topic.\n"
            "4. Add interesting markets to your Watchlist.\n"
            "5. Enable alerts so you do not miss strong moves."
        ),
        "search_prompt": (
            "Type a market topic.\n\n"
            "Examples: trump, bitcoin, fed, election, ai"
        ),
        "empty_watchlist": (
            "Your Watchlist is empty. Add a market from search, hot markets, or new markets."
        ),
        "share": (
            "Share PulseMarket AI with a friend:\n\n"
            "https://t.me/PulseMarketAIBot\n\n"
            "This is not a financial referral program.\n"
            "No bonuses.\n"
            "No money.\n"
            "Just a share link."
        ),
        "about": (
            "PulseMarket AI is an analytics Telegram bot for Polymarket.\n\n"
            "What it does:\n"
            "• shows hot, new, and themed markets\n"
            "• searches markets by topic\n"
            "• keeps a Watchlist\n"
            "• tracks sharp probability movements\n"
            "• sends alerts if you enable them\n\n"
            "Important: the bot does not trade, connect wallets, ask for private keys, or accept money.\n\n"
            "Data source: public Polymarket Gamma API."
        ),
        "settings_saved": "Done. Settings saved.",
        "api_error": "Could not load Polymarket data. Please try again later.",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    normalized = language.lower()
    return normalized if normalized in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, language: str | None = None) -> str:
    normalized = normalize_language(language)
    return TEXTS.get(normalized, TEXTS[DEFAULT_LANGUAGE]).get(
        key,
        TEXTS[DEFAULT_LANGUAGE].get(key, key),
    )
