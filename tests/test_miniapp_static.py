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
        "Market memory",
        "Market behavior",
        "YES / NO balance",
        "Side read",
        "Market read",
        "Read",
        "Caution",
        "Timing",
        "Volume",
        "AI read",
        "Strength of read",
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
        "pill--regime",
        "pill--heat",
        "pill--time",
        "unified-market-card",
        "unified-market-card--hero",
        "unified-market-card--list",
        "unified-market-card--compact",
        "market-side-buttons",
        "outcome-buttons",
        "outcome-duel",
        "yes-no-duel",
        "yes-no-duel__split",
        "yes-no-duel__track",
        "market-row-list",
        "market-avatar",
        "unified-market-card__odds",
        "mini-side-bar",
        "hero-insight-row",
        "daily-brief-card__top",
        "updated-pill",
        "verdict-line",
        "today-dashboard",
        "dashboard-item",
        "pulse-subtle",
        "simple-read",
        "search-summary",
        "skeleton-card",
        "app-loading",
        "skeleton-line",
        "error-state",
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
    assert "insightStrength" in script_text
    assert "what_this_means" in script_text
    assert "attention_vs_conviction" in script_text
    assert "market_memory_summary" in script_text
    assert "marketRegime" in script_text
    assert "market_heat" in script_text
    assert "confirmation_level" in script_text
    assert "error_risk" in script_text
    assert "time_pressure" in script_text
    assert "market_depth" in script_text
    assert "ai_verdict" in script_text
    assert "dominant_side" in script_text
    assert "yes_probability" in script_text
    assert "no_probability" in script_text
    assert "side_verdict" in script_text
    assert "renderMarketScorecard" in script_text
    assert "renderYesNoStrip" in script_text
    assert "renderYesNoDuel" in script_text
    assert "outcomeList" in script_text
    assert "shouldUseYesNo" in script_text
    assert "outcomeBalanceLabel" in script_text
    assert "renderMarketCard" in script_text
    assert "getMarketVisual" in script_text
    assert "sortByRealHeat" in script_text
    assert "hotMarketRow" not in script_text
    assert "todaySummaryStrip" in script_text
    assert "changed_since_last_brief" in script_text
    assert "related_topics" in script_text


def test_unified_market_card_system_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    script_text = (root / "miniapp" / "app.js").read_text()
    styles_text = (root / "miniapp" / "styles.css").read_text()

    assert "function renderMarketCard" in script_text
    assert 'variant = "compact"' in script_text
    assert 'variant === "hero"' in script_text
    assert 'variant === "analysis"' in script_text
    assert "getMarketVisual" in script_text
    assert "sortByRealHeat" in script_text
    assert "marketHeatScore" in script_text
    assert "outcomeList" in script_text
    assert "visibleOutcomeList" in script_text
    assert "outcomeBarSegments" in script_text
    assert "unified-market-card--hero" in styles_text
    assert "unified-market-card--list" in styles_text
    assert "unified-market-card--compact" in styles_text
    assert "yes-no-duel__side--yes" in styles_text
    assert "yes-no-duel__side--no" in styles_text
    assert "mini-side-bar__yes" in styles_text
    assert "mini-side-bar__no" in styles_text
    assert "mini-side-bar__runner" in styles_text
    assert "outcome-button--runner" in styles_text
    assert "green" not in "yes-no-duel__side--no"


def test_miniapp_supports_real_outcome_display_without_forced_yes_no() -> None:
    root = Path(__file__).resolve().parents[1]
    script_text = (root / "miniapp" / "app.js").read_text()
    styles_text = (root / "miniapp" / "styles.css").read_text()

    assert "should_use_yes_no" in script_text
    assert "outcome_type" in script_text
    assert "display_outcomes" in script_text
    assert "dominant_outcome_label" in script_text
    assert "outcome_balance_summary" in script_text
    assert "news_context" in script_text
    assert "why_moving_now" in script_text
    assert "renderNewsBadges" in script_text
    assert "renderNewsThemeStrip" in script_text
    assert "renderStoryCard" in script_text
    assert "hasStrongStory" in script_text
    assert "renderStoryContextPanel" in script_text
    assert "story_clusters" in script_text
    assert "top_story" in script_text
    assert "story_context" in script_text
    assert "news_impact_type" in script_text
    assert "catalyst_type" in script_text
    assert "likely_catalyst" in script_text
    assert "catalyst_evidence" in script_text
    assert "movement_timing" in script_text
    assert "price_probability_context" in script_text
    assert "what_to_verify_next" in script_text
    assert "what_changed_in_story" in script_text
    assert "news-badge" in script_text
    assert "news-theme-strip" in styles_text
    assert "story-brief-card" in styles_text
    assert "story-context-panel" in styles_text
    assert "Market outcomes" in script_text
    assert "Баланс вариантов" in script_text
    assert "outcome.short_label || outcome.label" in script_text


def test_story_layer_is_additive_and_has_market_fallback() -> None:
    root = Path(__file__).resolve().parents[1]
    script_text = (root / "miniapp" / "app.js").read_text()

    assert "state.todayMeta.top_story" in script_text
    assert "state.todayMeta.story_clusters" in script_text
    assert "hero.innerHTML = renderStoryCard(state.todayMeta.top_story, \"hero\")" in script_text
    assert "hero.innerHTML = renderMarketCard(visibleToday[0], \"hero\")" in script_text
    assert "if (!hasMarketStory(item)) return \"\";" in script_text
    assert "Hot markets" in script_text
    assert "state.hot = dataFrom(payload)" in script_text


def test_story_context_payload_is_attached_before_analysis_opens() -> None:
    root = Path(__file__).resolve().parents[1]
    script_text = (root / "miniapp" / "app.js").read_text()

    assert "function storyPayloadForMarket" in script_text
    assert "function attachStoryPayloadToMarket" in script_text
    assert "function findLoadedStoryForMarket" in script_text
    assert "function enrichMarketWithLoadedStory" in script_text
    assert "story.linked_markets.map((market) => attachStoryPayloadToMarket(normalizeMarket(market), story))" in script_text
    assert "state.todayMeta.top_story" in script_text
    assert "...state.todayMeta.story_clusters" in script_text
    assert "const normalized = enrichMarketWithLoadedStory(item);" in script_text
    assert "renderStoryContextPanel(normalized)" in script_text


def test_story_context_not_rendered_for_weak_market_without_story() -> None:
    root = Path(__file__).resolve().parents[1]
    script_text = (root / "miniapp" / "app.js").read_text()

    assert "function renderStoryContextPanel(item)" in script_text
    assert 'if (!hasMarketStory(item)) return "";' in script_text
    assert "linked >= 2 || normalized.official_source_signal" in script_text


def test_ru_story_labels_and_today_focus_copy_are_present() -> None:
    root = Path(__file__).resolve().parents[1]
    script_text = (root / "miniapp" / "app.js").read_text()

    for phrase in (
        "Сильное подтверждение",
        "Возможный катализатор",
        "Фоновый контекст",
        "Слабый сигнал",
        "Нет явного сигнала",
        "Баланс YES / NO",
        "Правила расчёта",
        "Качество объёма",
        'hotCountLabel: "В фокусе"',
    ):
        assert phrase in script_text
    assert 'hotCountLabel: "Горячих рынков"' not in script_text


def test_music_award_category_uses_word_boundaries_in_miniapp() -> None:
    root = Path(__file__).resolve().parents[1]
    script_text = (root / "miniapp" / "app.js").read_text()

    assert "function hasMarketKeyword" in script_text
    assert "escapeRegExp(normalized)" in script_text
    assert '"award", "oscars", "grammy", "movie", "film", "music", "celebrity"' in script_text
    assert "category === \"culture\"" in script_text


def test_miniapp_removes_raw_technical_indicator_labels() -> None:
    root = Path(__file__).resolve().parents[1]
    visible_text = (root / "miniapp" / "index.html").read_text() + (root / "miniapp" / "app.js").read_text()

    for phrase in (
        "Риск ошибки",
        "Живость",
        "Уверенность стороны",
        "Market regime",
        "Market scorecard",
        "Side confidence",
        "Error risk",
        "Market depth",
    ):
        assert phrase not in visible_text

    for phrase in (
        "Подтверждение Слабое",
        "Риск ошибки Высокий",
        "Объём Живой объём",
        "Pulse Score Pulse",
    ):
        assert phrase not in visible_text


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
    assert "yes / no balance" in text
    assert "market scorecard" not in text
    assert "error risk" not in text
    assert "market regime" not in text
    assert "side confidence" not in text
    assert "morning briefing" in text
    assert "what changed" in text
    assert "today’s narrative" in text
    assert "what this means" in text
    assert "attention vs conviction" in text
    assert "interests" in text
    assert "analysis" in text
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
        "good bet",
        "buy now",
        "sell now",
        "this market asks whether",
        "market is active",
        "people are watching",
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
    assert "quickTake" in script_text
    assert "mainTension" in script_text
    assert "marketMemory" in script_text
    assert "marketRegime" in script_text
    assert "marketIndicators" in script_text
    assert "renderMarketScorecard" in script_text
    assert "renderYesNoStrip" in script_text
    assert "renderSideAnalysisPanel" in script_text
    assert "renderScoreGrid" in script_text
    assert "score-grid" in script_text
    assert "market-scorecard" in script_text
    assert "probability-bar" in script_text
    assert "confidence-bar" in script_text
    assert "yes-no-strip" in script_text
    assert "side-split-bar" in script_text
    assert "side-panel" in script_text
    assert "indicatorSummary" in script_text
    assert "confidenceLevel" in script_text
    assert "whatInfluences" in script_text
    assert "relatedTopics" in script_text
    assert "resolutionRules" in script_text
    assert "probabilityDisplay" in script_text
    assert "uniqueAnalysisRows" in script_text
    assert "renderWhatToCheck" in script_text
    assert "analysis-note" in script_text
    assert "simple-read" not in script_text
    assert "Notable" in script_text
    assert "High attention" in script_text
    assert "grid-auto-columns: minmax(252px, 82%)" in styles_text
    assert "@media (max-width: 420px)" in styles_text
    assert "grid-auto-flow: row" in styles_text
    assert ".daily-snapshot" in styles_text
    assert "pill--pulse" not in styles_text
    assert "indicatorGrid" not in script_text
    assert "indicator-grid" not in styles_text
    assert "Pulse Score Pulse" not in script_text
    assert "Подтверждение Слабое" not in script_text
    assert "Риск ошибки Высокий" not in script_text
    assert "Объём Живой объём" not in script_text
    assert "People are watching this because activity increased" not in script_text
    assert "Public activity is above the visibility threshold" not in script_text
    assert "People are watching because activity increased" not in script_text
    assert "activity increased" not in script_text.lower()
    assert "Рынок близок к разрешению, поэтому внимание выше" not in script_text
    assert "Этот рынок спрашивает" not in script_text
    assert "Смотри на вероятность и правила разрешения" not in script_text
    assert "Рынок активен" not in script_text
    assert "Внимание выросло" not in script_text
    assert "Стоит изучить" not in script_text


def test_miniapp_loading_skeleton_and_error_states_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    index_text = (root / "miniapp" / "index.html").read_text()
    script_text = (root / "miniapp" / "app.js").read_text()
    styles_text = (root / "miniapp" / "styles.css").read_text()

    assert 'id="app-loading"' in index_text
    assert "Preparing market briefing" in index_text
    assert "collecting markets" in index_text
    assert "Готовим рыночный обзор" in script_text
    assert "собираем рынки" in script_text
    assert "renderLoadingSkeletons" in script_text
    assert "skeletonMarketCard" in script_text
    assert "skeletonLines" in script_text
    assert "skeletonPills" in script_text
    assert "skeleton-card--structured" in script_text
    assert "skeleton-pill" in index_text
    assert "skeleton-button" in index_text
    assert 'id="today-hero" class="story-card story-card--hero skeleton-card"></div>' not in index_text
    assert index_text.count("skeleton-line") >= 14
    assert index_text.count("skeleton-pill") >= 8
    assert index_text.count("skeleton-button") >= 2
    assert "BOOT_LOADING_MIN_MS = 520" in script_text
    assert "tg.ready()" in script_text
    assert "tg.expand()" in script_text
    assert 'tg.isVersionAtLeast("7.7")' in script_text
    assert "tg.disableVerticalSwipes()" in script_text
    assert "tg.setHeaderColor" in script_text
    assert "tg.setBackgroundColor" in script_text
    assert "hideBootLoader" in script_text
    assert "Promise.race" in script_text
    assert "Could not load briefing." in script_text
    assert "Не удалось загрузить обзор." in script_text
    assert "Updated just now" in script_text
    assert "min ago" in script_text
    assert "мин назад" in script_text
    assert "Showing last briefing, refreshing in background" in script_text
    assert "Показываем последний обзор, обновляем в фоне" in script_text
    assert "briefingUpdatedLabel" in script_text
    assert "updated_ago_seconds" in script_text
    assert "state.todayMeta.is_stale" in script_text
    assert "refresh_status" in script_text
    assert "errorState" in script_text
    assert "data-refresh" in script_text
    assert "state.loading.today" in script_text
    assert script_text.find("if (state.loading.today)") < script_text.find("emptyState(t(\"todayEmpty\")")
    assert "refreshDashboard({ initial: true })" in script_text
    assert ".app-loading" in styles_text
    assert ".skeleton-line" in styles_text
    assert ".skeleton-pill" in styles_text
    assert ".skeleton-button" in styles_text
    assert "overscroll-behavior: none" in styles_text
    assert "overscroll-behavior: contain" in styles_text
    assert ".error-state" in styles_text
    assert ".briefing-status" in styles_text
    assert "@keyframes loadingBar" in styles_text


def test_health_server_can_resolve_miniapp_assets() -> None:
    assert miniapp_asset_path("index.html").exists()
    assert miniapp_asset_path("styles.css").exists()
    assert miniapp_asset_path("app.js").exists()
