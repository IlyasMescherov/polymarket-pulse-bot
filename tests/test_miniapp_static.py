from __future__ import annotations

from pathlib import Path

from bot.services.health_server import miniapp_asset_path


def test_miniapp_files_exist_and_include_telegram_script() -> None:
    root = Path(__file__).resolve().parents[1]
    index = root / "miniapp" / "index.html"
    styles = root / "miniapp" / "styles.css"
    script = root / "miniapp" / "app.js"
    readme = root / "miniapp" / "README.md"

    assert index.exists()
    assert styles.exists()
    assert script.exists()
    assert readme.exists()
    assert "https://telegram.org/js/telegram-web-app.js" in index.read_text()


def test_miniapp_sections_render_as_premium_dashboard() -> None:
    root = Path(__file__).resolve().parents[1]
    index_text = (root / "miniapp" / "index.html").read_text()
    script_text = (root / "miniapp" / "app.js").read_text()
    styles_text = (root / "miniapp" / "styles.css").read_text()

    for text in (
        "Today’s Pulse",
        "Smart Money Radar",
        "Hot Markets",
        "Sharp Moves",
        "Search",
        "Watchlist",
        "Safety scope",
    ):
        assert text in index_text

    for target_id in (
        "today-hero",
        "today-secondary",
        "smart-hero",
        "hot-strip",
        "moves-list",
        "search-results",
    ):
        assert target_id in index_text
        assert target_id in script_text

    for class_name in (
        "story-hero",
        "pulse-hero",
        "smart-hero",
        "horizontal-strip",
        "skeleton-card",
    ):
        assert class_name in styles_text


def test_miniapp_static_text_has_safety_and_no_banned_phrases() -> None:
    root = Path(__file__).resolve().parents[1]
    text = "\n".join(
        (root / "miniapp" / name).read_text().lower()
        for name in ("index.html", "app.js", "README.md")
    )

    assert "no trading" in text
    assert "no wallets" in text
    assert "no deposits" in text
    assert "no private keys" in text
    assert "no financial advice" in text

    banned = (
        "insider",
        "guaranteed",
        "buy now",
        "sell now",
        "copy this trader",
        "trade signal",
        "alpha leak",
        "wallet connection",
        "order placement",
    )
    for phrase in banned:
        assert phrase not in text


def test_landing_and_screenshot_docs_reference_miniapp_polish() -> None:
    root = Path(__file__).resolve().parents[1]
    landing = (root / "landing" / "index.html").read_text()
    guide = root / "docs" / "MINIAPP_SCREENSHOT_GUIDE.md"

    assert guide.exists()
    assert "Telegram Mini App Dashboard" in landing
    assert "Today’s Pulse" in landing
    assert "Smart Money Radar" in landing
    assert "Home dashboard" in guide.read_text()


def test_health_server_can_resolve_miniapp_assets() -> None:
    assert miniapp_asset_path("index.html").exists()
    assert miniapp_asset_path("styles.css").exists()
    assert miniapp_asset_path("app.js").exists()
