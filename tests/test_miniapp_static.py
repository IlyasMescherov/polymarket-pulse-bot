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
    visible_text = index_text + script_text

    for text in (
        "Morning Briefing",
        "What changed",
        "Market mood today",
        "Market Mood",
        "Today’s Narrative",
        "What this means",
        "Attention vs conviction",
        "How serious is this movement",
        "Activity Radar",
        "Search",
        "Saved markets",
        "Interests",
        "Language",
        "Theme",
        "About PulseMarket AI",
        "Research only · No trading · No wallets · No deposits · No private keys · No financial advice",
    ):
        assert text in visible_text

    assert index_text.find("Morning Briefing") < index_text.find("Activity Radar")
    assert "Safety scope" not in index_text
    assert "Markets worth watching today." in index_text
    assert "public attention is rising" in index_text

    for target_id in (
        'id="screen-today"',
        'id="screen-radar"',
        'id="screen-search"',
        'id="screen-saved"',
        'id="screen-more"',
    ):
        assert target_id in index_text

    for target_id in (
        "today-hero",
        "today-secondary",
        "what-changed",
        "mood-summary",
        "today-narrative",
        "category-chips",
        "smart-hero",
        "search-results",
        "interest-chips",
        "saved-list",
        "recently-opened-list",
    ):
        assert target_id in index_text
        assert target_id in script_text

    for class_name in (
        "context-bar",
        "category-rail",
        "category-chip",
        "bottom-nav",
        "bottom-nav__item",
        "screen-stack",
        "narrative-card",
        "story-card--hero",
        "insight-card",
        "horizontal-strip",
        "daily-snapshot",
        "mini-panel",
        "sheet-backdrop",
        "explain-sheet",
        "settings-card",
        "segmented",
        "switch",
        "pill--mood",
        "pulse-subtle",
        "simple-read",
        "search-summary",
        "skeleton-card",
        "empty-state--compact",
        "footer-note",
    ):
        assert class_name in styles_text

    assert "story-hero" not in styles_text
    assert "safety-grid" not in styles_text


def test_miniapp_navigation_and_search_are_app_like() -> None:
    root = Path(__file__).resolve().parents[1]
    index_text = (root / "miniapp" / "index.html").read_text()
    script_text = (root / "miniapp" / "app.js").read_text()

    assert 'class="top-tabs"' not in index_text
    assert "top-tabs" not in script_text
    assert 'class="bottom-nav"' in index_text
    assert 'class="context-bar"' in index_text
    assert 'data-tab="today"' in index_text
    assert 'data-tab="radar"' in index_text
    assert 'data-tab="search"' in index_text
    assert 'data-tab="saved"' in index_text
    assert 'data-tab="more"' in index_text

    for label in ("Today", "Radar", "Search", "Saved", "More"):
        assert label in index_text

    assert index_text.count('type="search"') == 1
    assert index_text.count('id="search-input"') == 1
    assert "switchTab" in script_text
    assert "scrollToSection" not in script_text


def test_miniapp_settings_language_theme_and_saved_features_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    index_text = (root / "miniapp" / "index.html").read_text()
    script_text = (root / "miniapp" / "app.js").read_text()
    styles_text = (root / "miniapp" / "styles.css").read_text()

    assert 'data-setting="language"' in index_text
    assert 'data-setting="theme"' in index_text
    assert 'data-toggle="compactMode"' in index_text
    assert 'data-toggle="reducedAnimations"' in index_text
    assert 'data-theme="light"' in styles_text
    assert "savedMarkets" in script_text
    assert "recentlyOpened" in script_text
    assert "userInterests" in script_text
    assert "saveMarket" in script_text
    assert "removeSaved" in script_text
    assert "recentSearches" in script_text
    assert "SEARCH_SUGGESTIONS" in script_text
    assert "marketMood" in script_text
    assert "simpleReadCopy" in script_text
    assert "data-explain-market" in script_text
    assert "renderDailySnapshot" in script_text
    assert "renderNarrative" in script_text
    assert "renderCategoryChips" in script_text
    assert "renderInterestChips" in script_text
    assert "pulseLabel" in script_text
    assert "attentionSignal" in script_text
    assert "what_this_means" in script_text
    assert "attention_vs_conviction" in script_text
    assert "related_topics" in script_text


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
    assert "where public attention is rising" in text
    assert "market mood" in text
    assert "morning briefing" in text
    assert "what changed" in text
    assert "today’s narrative" in text
    assert "what this means" in text
    assert "attention vs conviction" in text
    assert "interests" in text
    assert "explain" in text
    assert "wallet list" not in text
    assert "wallet hash" not in text

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
    assert "Morning Briefing" in landing
    assert "Activity Radar" in landing
    assert "Home dashboard" in guide.read_text()


def test_miniapp_cards_are_compressed_and_have_habit_layer() -> None:
    root = Path(__file__).resolve().parents[1]
    index_text = (root / "miniapp" / "index.html").read_text()
    script_text = (root / "miniapp" / "app.js").read_text()
    styles_text = (root / "miniapp" / "styles.css").read_text()

    assert 'id="what-changed"' in index_text
    assert 'id="mood-summary"' in index_text
    assert 'id="explain-sheet"' in index_text
    assert 'id="today-narrative"' in index_text
    assert "detailActionRow" in script_text
    assert "buttonRow(item)" in script_text
    assert "data-explain-market" in script_text
    assert "whatMarketAsks" in script_text
    assert "whatInfluences" in script_text
    assert "relatedTopics" in script_text
    assert "resolutionRules" in script_text
    assert "probabilityDisplay" in script_text
    assert "simple-read" not in script_text
    assert "Worth watching" in script_text
    assert "High attention" in script_text
    assert "grid-auto-columns: minmax(252px, 82%)" in styles_text
    assert ".daily-snapshot" in styles_text
    assert "pill--pulse" not in styles_text
    assert "People are watching this because activity increased" not in script_text
    assert "Public activity is above the visibility threshold" not in script_text
    assert "People are watching because activity increased" not in script_text
    assert "activity increased" not in script_text.lower()


def test_health_server_can_resolve_miniapp_assets() -> None:
    assert miniapp_asset_path("index.html").exists()
    assert miniapp_asset_path("styles.css").exists()
    assert miniapp_asset_path("app.js").exists()
