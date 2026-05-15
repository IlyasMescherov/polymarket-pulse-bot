from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import (
    create_market_link_click,
    create_search_query,
    get_latest_snapshots,
    get_recent_snapshots,
    upsert_user,
)
from bot.handlers.common import load_user, user_language
from bot.keyboards.main import (
    CATEGORIES,
    CATEGORY_PREFIX,
    EXPLAIN_PREFIX,
    HOT_MARKETS,
    MARKET_SEARCH,
    NEW_MARKETS,
    OPEN_MARKET_PREFIX,
    RESOLUTION_PREFIX,
    SHARE_MARKET_PREFIX,
    SHARP_MOVES,
    TODAY_PULSE,
    TIMELINE_PREFIX,
    WHY_MOVED_PREFIX,
    categories_keyboard,
    main_menu_keyboard,
    market_actions_keyboard,
)
from bot.services.ai_explainer import AIExplainer
from bot.services.market_analyzer import CATEGORY_LABELS, MarketAnalyzer, MarketMovement
from bot.services.market_health import calculate_market_health
from bot.services.movement_explainer import explain_movement
from bot.services.polymarket_client import Market, PolymarketAPIError
from bot.services.pulse_score import calculate_pulse_score
from bot.services.risk_flags import count_strong_snapshot_moves, market_risk_flags
from bot.services.resolution_explainer import ResolutionExplainer
from bot.services.today_pulse import TodayPulseItem, build_today_pulse_items
from bot.utils.formatting import (
    format_beginner_explanation,
    format_market_card,
    format_market_timeline,
    format_movement_card,
    format_share_market_card,
    format_today_pulse_card,
    format_probability,
)
from bot.utils.i18n import t
from bot.utils.logging import log_callback_action, log_user_action

logger = logging.getLogger(__name__)
router = Router()


class MarketSearchStates(StatesGroup):
    waiting_query = State()


@router.inline_query()
async def inline_market_search(
    inline_query: InlineQuery,
    market_analyzer: MarketAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    query = (inline_query.query or "").strip()
    log_user_action(logger, inline_query.from_user, "search_query", query=query[:80], source="inline")
    if not query:
        await inline_query.answer([], cache_time=5, is_personal=True)
        return

    try:
        markets = await market_analyzer.search_markets(query, limit=5)
    except PolymarketAPIError:
        logger.exception("Could not search inline markets")
        await inline_query.answer([], cache_time=5, is_personal=True)
        return

    language = await _language(session_factory, inline_query.from_user)
    results = [
        InlineQueryResultArticle(
            id=market.id,
            title=market.question[:90],
            description=f"Probability: {format_probability(market.yes_probability, language)}",
            input_message_content=InputTextMessageContent(
                message_text=format_share_market_card(
                    market,
                    pulse_score=calculate_pulse_score(market),
                    language=language,
                ),
                disable_web_page_preview=True,
            ),
        )
        for market in markets
    ]
    await inline_query.answer(results, cache_time=30, is_personal=True)


async def _language(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> str:
    try:
        return user_language(await load_user(session_factory, telegram_user))
    except Exception:
        logger.exception("Could not load user language")
        return "ru"


async def _send_market_cards(
    message: Message,
    markets: list[Market],
    ai_explainer: AIExplainer,
    language: str,
    session_factory: async_sessionmaker[AsyncSession],
    threshold: float = 0.10,
    heading: str = "🔥 Рынок:",
    source: str = "hot",
) -> None:
    if not markets:
        await message.answer(
            "No matching markets yet. Please try again later."
            if language == "en"
            else "Пока не нашёл подходящих рынков. Попробуйте позже."
        )
        return

    for market in markets[:5]:
        delta = None
        strong_moves = 0
        async with session_factory() as session:
            latest = await get_latest_snapshots(session, [market.id])
            snapshot = latest.get(market.id)
            if snapshot is not None and snapshot.yes_probability is not None and market.yes_probability is not None:
                delta = market.yes_probability - snapshot.yes_probability
            recent = await get_recent_snapshots(session, market.id, limit=8)
            strong_moves = count_strong_snapshot_moves(recent, threshold)
        pulse_score = calculate_pulse_score(market, delta=delta)
        risk_flags = market_risk_flags(
            market,
            delta=delta,
            threshold=threshold,
            strong_moves_count=strong_moves,
        )
        market_health = calculate_market_health(market)
        explanation = await ai_explainer.explain_market(market)
        await message.answer(
            format_market_card(
                market,
                explanation=explanation,
                heading=heading,
                movement_delta=delta,
                pulse_score=pulse_score,
                market_health=market_health,
                risk_flags=risk_flags,
                language=language,
            ),
            reply_markup=market_actions_keyboard(
                market.url,
                market.id,
                language,
                source=source,
            ),
            disable_web_page_preview=True,
        )


async def _send_movement_cards(
    message: Message,
    movements: list[MarketMovement],
    ai_explainer: AIExplainer,
    language: str,
    session_factory: async_sessionmaker[AsyncSession],
    threshold: float = 0.10,
) -> None:
    if not movements:
        await message.answer(
            (
                "No sharp moves yet. If this is the first run, I saved a market snapshot and will compare it with the next one."
                if language == "en"
                else "Пока не вижу резких движений. Если это первый запуск, я уже сохранил снимок рынков и смогу сравнить его со следующим."
            )
        )
        return

    for movement in movements[:5]:
        async with session_factory() as session:
            recent = await get_recent_snapshots(session, movement.market.id, limit=8)
            strong_moves = count_strong_snapshot_moves(recent, threshold)
        pulse_score = calculate_pulse_score(movement.market, delta=movement.delta)
        risk_flags = market_risk_flags(
            movement.market,
            delta=movement.delta,
            threshold=threshold,
            strong_moves_count=strong_moves,
        )
        market_health = calculate_market_health(movement.market)
        explanation = await ai_explainer.explain_market(movement.market)
        await message.answer(
            format_movement_card(
                movement,
                explanation=explanation,
                pulse_score=pulse_score,
                market_health=market_health,
                risk_flags=risk_flags,
                language=language,
            ),
            reply_markup=market_actions_keyboard(
                movement.market.url,
                movement.market.id,
                language,
                source="moves",
            ),
            disable_web_page_preview=True,
        )


async def _build_today_pulse(
    market_analyzer: MarketAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
    language: str,
    threshold: float = 0.10,
    limit: int = 5,
) -> list[TodayPulseItem]:
    hot_markets = await market_analyzer.get_hot_markets(limit=20)
    new_markets = await market_analyzer.get_new_markets(limit=20)
    markets = hot_markets + new_markets
    async with session_factory() as session:
        latest = await get_latest_snapshots(session, [market.id for market in markets])
    return build_today_pulse_items(
        markets,
        latest_snapshots=latest,
        threshold=threshold,
        limit=limit,
        language=language,
    )


async def _send_today_pulse_cards(
    message: Message,
    items: list[TodayPulseItem],
    ai_explainer: AIExplainer,
    language: str,
) -> None:
    if not items:
        await message.answer(
            "No strong Morning Briefing candidates yet. Please try again later."
            if language == "en"
            else "Пока нет сильных кандидатов для Пульса дня. Попробуйте позже."
        )
        return

    for index, item in enumerate(items[:5], start=1):
        ai_why = await ai_explainer.explain_market(item.market)
        await message.answer(
            format_today_pulse_card(
                item,
                index,
                ai_why=ai_why,
                language=language,
            ),
            reply_markup=market_actions_keyboard(
                item.market.url,
                item.market.id,
                language,
                source="today",
            ),
            disable_web_page_preview=True,
        )


@router.callback_query(F.data == HOT_MARKETS)
async def hot_markets(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "hot_markets")
    language = await _language(session_factory, callback.from_user)
    await callback.answer("Searching hot markets" if language == "en" else "Ищу горячие рынки")
    if not callback.message:
        return
    try:
        markets = await market_analyzer.get_hot_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch hot markets")
        await callback.message.answer(t("api_error", language))
        return
    await _send_market_cards(
        callback.message,
        markets,
        ai_explainer,
        language,
        session_factory,
        heading="🔥 Hot market" if language == "en" else "🔥 Горячий рынок",
        source="hot",
    )


@router.message(Command("hot"))
async def hot_markets_command(
    message: Message,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "hot_markets")
    language = await _language(session_factory, message.from_user)
    try:
        markets = await market_analyzer.get_hot_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch hot markets")
        await message.answer(t("api_error", language))
        return
    await _send_market_cards(
        message,
        markets,
        ai_explainer,
        language,
        session_factory,
        heading="🔥 Hot market" if language == "en" else "🔥 Горячий рынок",
        source="hot",
    )


@router.callback_query(F.data == TODAY_PULSE)
async def today_pulse(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "today_pulse")
    language = await _language(session_factory, callback.from_user)
    await callback.answer("Building Morning Briefing" if language == "en" else "Собираю Пульс дня")
    if not callback.message:
        return
    try:
        async with session_factory() as session:
            user = await upsert_user(session, callback.from_user)
            threshold = user.movement_threshold
            await session.commit()
        items = await _build_today_pulse(
            market_analyzer,
            session_factory,
            language,
            threshold=threshold,
            limit=5,
        )
    except PolymarketAPIError:
        logger.exception("Could not fetch markets for today's pulse")
        await callback.message.answer(t("api_error", language))
        return
    except Exception:
        logger.exception("Could not build today's pulse")
        await callback.message.answer(
            "Could not build Morning Briefing. Please try again later."
            if language == "en"
            else "Не смог собрать Пульс дня. Попробуйте позже."
        )
        return
    await _send_today_pulse_cards(callback.message, items, ai_explainer, language)


@router.message(Command("today"))
async def today_pulse_command(
    message: Message,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "today_pulse")
    language = await _language(session_factory, message.from_user)
    try:
        async with session_factory() as session:
            user = await upsert_user(session, message.from_user)
            threshold = user.movement_threshold
            await session.commit()
        items = await _build_today_pulse(
            market_analyzer,
            session_factory,
            language,
            threshold=threshold,
            limit=5,
        )
    except PolymarketAPIError:
        logger.exception("Could not fetch markets for today's pulse")
        await message.answer(t("api_error", language))
        return
    except Exception:
        logger.exception("Could not build today's pulse")
        await message.answer(
            "Could not build Morning Briefing. Please try again later."
            if language == "en"
            else "Не смог собрать Пульс дня. Попробуйте позже."
        )
        return
    await _send_today_pulse_cards(message, items, ai_explainer, language)


@router.callback_query(F.data == NEW_MARKETS)
async def new_markets(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "new_markets")
    language = await _language(session_factory, callback.from_user)
    await callback.answer("Searching new markets" if language == "en" else "Ищу новые рынки")
    if not callback.message:
        return
    try:
        markets = await market_analyzer.get_new_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch new markets")
        await callback.message.answer(t("api_error", language))
        return
    await _send_market_cards(
        callback.message,
        markets,
        ai_explainer,
        language,
        session_factory,
        heading="🆕 New market" if language == "en" else "🆕 Новый рынок",
        source="new",
    )


@router.message(Command("new"))
async def new_markets_command(
    message: Message,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "new_markets")
    language = await _language(session_factory, message.from_user)
    try:
        markets = await market_analyzer.get_new_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch new markets")
        await message.answer(t("api_error", language))
        return
    await _send_market_cards(
        message,
        markets,
        ai_explainer,
        language,
        session_factory,
        heading="🆕 New market" if language == "en" else "🆕 Новый рынок",
        source="new",
    )


@router.callback_query(F.data == SHARP_MOVES)
async def sharp_moves(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
) -> None:
    log_callback_action(logger, callback, "sharp_moves")
    language = await _language(session_factory, callback.from_user)
    await callback.answer(
        "Comparing market snapshots" if language == "en" else "Сравниваю снимки рынков"
    )
    if not callback.message:
        return
    try:
        async with session_factory() as session:
            user = await upsert_user(session, callback.from_user)
            movements = await market_analyzer.detect_movements(
                session,
                threshold=user.movement_threshold,
            )
    except PolymarketAPIError:
        logger.exception("Could not fetch markets for movement detection")
        await callback.message.answer(t("api_error", language))
        return
    except Exception:
        logger.exception("Could not detect market movements")
        await callback.message.answer(
            "Could not compare markets. Please try again later."
            if language == "en"
            else "Не смог сравнить рынки. Я уже записал ошибку в лог, попробуйте позже."
        )
        return

    await _send_movement_cards(
        callback.message,
        movements,
        ai_explainer,
        language,
        session_factory,
        threshold=user.movement_threshold,
    )


@router.message(Command("moves"))
async def sharp_moves_command(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
) -> None:
    log_user_action(logger, message.from_user, "sharp_moves")
    language = await _language(session_factory, message.from_user)
    try:
        async with session_factory() as session:
            user = await upsert_user(session, message.from_user)
            movements = await market_analyzer.detect_movements(
                session,
                threshold=user.movement_threshold,
            )
    except PolymarketAPIError:
        logger.exception("Could not fetch markets for movement detection")
        await message.answer(t("api_error", language))
        return
    except Exception:
        logger.exception("Could not detect market movements")
        await message.answer(
            "Could not compare markets. Please try again later."
            if language == "en"
            else "Не смог сравнить рынки. Я уже записал ошибку в лог, попробуйте позже."
        )
        return
    await _send_movement_cards(
        message,
        movements,
        ai_explainer,
        language,
        session_factory,
        threshold=user.movement_threshold,
    )


@router.callback_query(F.data == MARKET_SEARCH)
async def start_market_search(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "search_started")
    await callback.answer()
    await state.set_state(MarketSearchStates.waiting_query)
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(t("search_prompt", language))


@router.message(Command("search"))
async def start_market_search_command(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "search_started")
    await state.set_state(MarketSearchStates.waiting_query)
    language = await _language(session_factory, message.from_user)
    await message.answer(t("search_prompt", language))


@router.message(MarketSearchStates.waiting_query)
async def market_search_query(
    message: Message,
    state: FSMContext,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    query = (message.text or "").strip()
    log_user_action(logger, message.from_user, "search_query", query=query[:80])
    language = await _language(session_factory, message.from_user)
    if not query:
        await message.answer(t("search_prompt", language))
        return

    await state.clear()
    try:
        markets = await market_analyzer.search_markets(query, limit=5)
    except PolymarketAPIError:
        logger.exception("Could not search markets")
        await message.answer(t("api_error", language))
        return
    if message.from_user is not None:
        async with session_factory() as session:
            try:
                await create_search_query(
                    session,
                    message.from_user.id,
                    query,
                    len(markets),
                )
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Could not save search query")

    if not markets:
        await message.answer(
            (
                "No markets found for this query. Try another topic."
                if language == "en"
                else "Ничего не нашёл по этому запросу. Попробуйте другую тему."
            ),
            reply_markup=main_menu_keyboard(language),
        )
        return

    await _send_market_cards(
        message,
        markets,
        ai_explainer,
        language,
        session_factory,
        heading="🔍 Found market" if language == "en" else "🔍 Найден рынок",
        source="search",
    )


@router.callback_query(F.data == CATEGORIES)
async def categories_menu(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "category_selected", category="menu")
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(
            "Choose a category:" if language == "en" else "Выберите категорию:",
            reply_markup=categories_keyboard(language),
        )


@router.callback_query(F.data.startswith(CATEGORY_PREFIX))
async def category_selected(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    category = (callback.data or "").removeprefix(CATEGORY_PREFIX)
    log_callback_action(logger, callback, "category_selected", category=category)
    language = await _language(session_factory, callback.from_user)
    await callback.answer(
        "Searching category markets" if language == "en" else "Ищу рынки в категории"
    )
    if not callback.message:
        return

    try:
        markets = await market_analyzer.get_category_markets(category, limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch category markets")
        await callback.message.answer(t("api_error", language))
        return

    heading = f"🗂 {CATEGORY_LABELS.get(category, 'Категория')}:"
    await _send_market_cards(
        callback.message,
        markets,
        ai_explainer,
        language,
        session_factory,
        heading=heading,
        source="category",
    )


@router.callback_query(F.data.startswith(OPEN_MARKET_PREFIX))
async def open_market_link(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    payload = (callback.data or "").removeprefix(OPEN_MARKET_PREFIX)
    source, _, market_id = payload.partition(":")
    source = source or "hot"
    log_callback_action(
        logger,
        callback,
        "market_open",
        market_id=market_id,
        source=source,
    )
    await callback.answer()
    if not callback.message or callback.from_user is None or not market_id:
        return

    language = await _language(session_factory, callback.from_user)
    try:
        market = await market_analyzer.find_market_by_id(market_id)
    except PolymarketAPIError:
        logger.exception("Could not fetch market for open tracking")
        await callback.message.answer(t("api_error", language))
        return
    if market is None:
        await callback.message.answer(
            "Could not find this market." if language == "en" else "Не смог найти этот рынок."
        )
        return

    async with session_factory() as session:
        try:
            await create_market_link_click(
                session,
                callback.from_user.id,
                market.id,
                market.question,
                source,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not save market link click")

    await callback.message.answer(
        (
            "🔗 Open this market on Polymarket:\n\n"
            if language == "en"
            else "🔗 Открыть рынок на Polymarket:\n\n"
        )
        + market.url,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith(EXPLAIN_PREFIX))
async def explain_market(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    market_id = (callback.data or "").removeprefix(EXPLAIN_PREFIX)
    log_callback_action(logger, callback, "beginner_explain", market_id=market_id)
    await callback.answer()
    if not callback.message:
        return

    language = await _language(session_factory, callback.from_user)
    try:
        market = await market_analyzer.find_market_by_id(market_id)
    except PolymarketAPIError:
        logger.exception("Could not fetch market for beginner explanation")
        await callback.message.answer(t("api_error", language))
        return
    if market is None:
        await callback.message.answer(
            "Could not find this market." if language == "en" else "Не смог найти этот рынок."
        )
        return

    ai_brief = await ai_explainer.explain_market(market)
    await callback.message.answer(
        format_beginner_explanation(market, ai_brief=ai_brief, language=language),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith(RESOLUTION_PREFIX))
async def explain_resolution(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    market_id = (callback.data or "").removeprefix(RESOLUTION_PREFIX)
    log_callback_action(logger, callback, "resolution_explain", market_id=market_id)
    await callback.answer()
    if not callback.message:
        return

    language = await _language(session_factory, callback.from_user)
    try:
        market = await market_analyzer.find_market_by_id(market_id)
    except PolymarketAPIError:
        logger.exception("Could not fetch market for resolution explanation")
        await callback.message.answer(t("api_error", language))
        return
    if market is None:
        await callback.message.answer(
            "Could not find this market." if language == "en" else "Не смог найти этот рынок."
        )
        return

    explanation = await ResolutionExplainer().explain(market, ai_explainer, language=language)
    await callback.message.answer(explanation, disable_web_page_preview=True)


@router.callback_query(F.data.startswith(TIMELINE_PREFIX))
async def market_timeline(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    market_id = (callback.data or "").removeprefix(TIMELINE_PREFIX)
    log_callback_action(logger, callback, "market_timeline", market_id=market_id)
    await callback.answer()
    if not callback.message:
        return

    async with session_factory() as session:
        try:
            snapshots = await get_recent_snapshots(session, market_id, limit=8)
        except Exception:
            logger.exception("Could not load market timeline")
            language = await _language(session_factory, callback.from_user)
            await callback.message.answer(
                "Could not load the timeline. Please try again later."
                if language == "en"
                else "Не смог загрузить динамику. Попробуйте позже."
            )
            return
    language = await _language(session_factory, callback.from_user)
    await callback.message.answer(format_market_timeline(snapshots, language=language))


@router.callback_query(F.data.startswith(WHY_MOVED_PREFIX))
async def why_market_moved(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    market_id = (callback.data or "").removeprefix(WHY_MOVED_PREFIX)
    log_callback_action(logger, callback, "why_it_moved", market_id=market_id)
    await callback.answer()
    if not callback.message:
        return

    language = await _language(session_factory, callback.from_user)
    try:
        market = await market_analyzer.find_market_by_id(market_id)
    except PolymarketAPIError:
        logger.exception("Could not fetch market for movement explanation")
        await callback.message.answer(t("api_error", language))
        return
    if market is None:
        await callback.message.answer(
            "Could not find this market." if language == "en" else "Не смог найти этот рынок."
        )
        return

    async with session_factory() as session:
        user = await upsert_user(session, callback.from_user)
        threshold = user.movement_threshold
        latest = await get_latest_snapshots(session, [market.id])
        recent = await get_recent_snapshots(session, market.id, limit=8)
        await session.commit()
    snapshot = latest.get(market.id)
    delta = (
        market.yes_probability - snapshot.yes_probability
        if snapshot is not None
        and snapshot.yes_probability is not None
        and market.yes_probability is not None
        else None
    )
    risk_flags = market_risk_flags(
        market,
        delta=delta,
        threshold=threshold,
        strong_moves_count=count_strong_snapshot_moves(recent, threshold),
    )
    await callback.message.answer(
        explain_movement(market, delta=delta, risk_flags=risk_flags, language=language).to_text()
    )


@router.callback_query(F.data.startswith(SHARE_MARKET_PREFIX))
async def share_market(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    market_id = (callback.data or "").removeprefix(SHARE_MARKET_PREFIX)
    log_callback_action(logger, callback, "share_market", market_id=market_id)
    await callback.answer()
    if not callback.message:
        return

    language = await _language(session_factory, callback.from_user)
    try:
        market = await market_analyzer.find_market_by_id(market_id)
    except PolymarketAPIError:
        logger.exception("Could not fetch market for share card")
        await callback.message.answer(t("api_error", language))
        return
    if market is None:
        await callback.message.answer(
            "Could not find this market." if language == "en" else "Не смог найти этот рынок."
        )
        return

    pulse_score = calculate_pulse_score(market)
    await callback.message.answer(
        format_share_market_card(market, pulse_score=pulse_score, language=language),
        disable_web_page_preview=True,
    )
