from __future__ import annotations

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = {"ru", "en"}

TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        "dashboard": (
            "🚀 PulseMarket AI\n\n"
            "PulseMarket AI помогает быстро понять, что важно на Polymarket.\n\n"
            "Начни с:\n"
            "📰 Today’s Pulse — главные рынки дня\n"
            "🧠 Радар активности — публичная активность\n"
            "🔍 Поиск — найти рынок\n\n"
            "Для анализа · Без сделок"
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
            "Watchlist пока пуст. Найди рынок через поиск или добавь из горячих рынков."
        ),
        "share": (
            "Поделись PulseMarket AI:\n\n"
            "https://t.me/PulseMarketAIBot\n\n"
            "Находи рынки Polymarket, отслеживай резкие движения и понимай вероятность простым языком.\n\n"
            "Только аналитика.\n"
            "Без торговли.\n"
            "Без кошельков.\n"
            "Без финансовых советов."
        ),
        "about": (
            "PulseMarket AI\n\n"
            "Telegram discovery and analytics assistant для Polymarket.\n\n"
            "Что он делает:\n"
            "• горячие и новые рынки\n"
            "• резкие движения\n"
            "• поиск\n"
            "• Watchlist\n"
            "• уведомления по темам\n"
            "• Smart Money Radar\n"
            "• простые объяснения\n"
            "• прямые ссылки на Polymarket\n\n"
            "Безопасность:\n"
            "Без торговли.\n"
            "Без кошельков.\n"
            "Без пополнений.\n"
            "Без приватных ключей.\n"
            "Без финансовых советов."
        ),
        "settings_saved": "Готово. Настройки сохранены.",
        "api_error": "Не смог получить данные Polymarket. Попробуйте чуть позже.",
    },
    "en": {
        "dashboard": (
            "🚀 PulseMarket AI\n\n"
            "PulseMarket AI helps you find what matters on Polymarket.\n\n"
            "Start with:\n"
            "📰 Today’s Pulse — daily market highlights\n"
            "🧠 Smart Money — public activity radar\n"
            "🔍 Search — find any market\n\n"
            "Research only · No trade execution"
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
            "Your Watchlist is empty. Search for a market or add one from hot markets."
        ),
        "share": (
            "Share PulseMarket AI:\n\n"
            "https://t.me/PulseMarketAIBot\n\n"
            "Discover Polymarket markets, track sharp movements, and understand probabilities in simple language.\n\n"
            "Analytics only.\n"
            "No trading.\n"
            "No wallets.\n"
            "No financial advice."
        ),
        "about": (
            "PulseMarket AI\n\n"
            "Telegram discovery and analytics assistant for Polymarket.\n\n"
            "What it does:\n"
            "• Hot and new markets\n"
            "• Sharp movement alerts\n"
            "• Search\n"
            "• Watchlist\n"
            "• Topic alerts\n"
            "• Smart Money Radar\n"
            "• Simple explanations\n"
            "• Direct Polymarket links\n\n"
            "Safety:\n"
            "No trading.\n"
            "No wallets.\n"
            "No deposits.\n"
            "No private keys.\n"
            "No financial advice."
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
