from __future__ import annotations

from dataclasses import dataclass

from bot.handlers.menu import _mini_app_preview_text
from bot.keyboards.main import DASHBOARD, label, main_menu_keyboard


def _buttons(keyboard):
    return [button for row in keyboard.inline_keyboard for button in row]


def test_dashboard_button_labels_are_localized() -> None:
    assert label("dashboard", "en") == "📊 Dashboard"
    assert label("dashboard", "ru") == "📊 Дашборд"


def test_dashboard_button_uses_callback_without_https_url() -> None:
    buttons = _buttons(main_menu_keyboard("en", mini_app_url="http://example.com/app"))
    dashboard = next(button for button in buttons if button.text == "📊 Dashboard")

    assert dashboard.callback_data == DASHBOARD
    assert dashboard.web_app is None


def test_dashboard_button_uses_web_app_only_for_https_url() -> None:
    buttons = _buttons(main_menu_keyboard("en", mini_app_url="https://example.com/app"))
    dashboard = next(button for button in buttons if button.text == "📊 Dashboard")

    assert dashboard.callback_data is None
    assert dashboard.web_app is not None
    assert dashboard.web_app.url == "https://example.com/app"


def test_main_menu_prioritizes_curated_onboarding_actions() -> None:
    buttons = _buttons(main_menu_keyboard("en"))

    assert [button.text for button in buttons] == [
        "📰 Today’s Pulse",
        "📊 Dashboard",
        "🧠 Activity Radar",
        "🔍 Search",
        "🔥 Hot",
        "📈 Moves",
        "⭐ Watchlist",
        "⚙️ Settings",
        "ℹ️ About",
        "🤝 Share",
    ]


@dataclass(slots=True)
class PreviewSettings:
    project_public_url: str = "https://pulsemarketai.com"


def test_dashboard_fallback_explains_https_requirement() -> None:
    text = _mini_app_preview_text(PreviewSettings(), "en")

    assert "Mini App preview is ready." in text
    assert "Telegram requires HTTPS" in text
    assert "https://pulsemarketai.com/app" in text
