from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import upsert_user
from bot.handlers.common import load_user, user_language
from bot.keyboards.main import (
    CATEGORIES,
    CATEGORY_PREFIX,
    HOT_MARKETS,
    MARKET_SEARCH,
    NEW_MARKETS,
    SHARP_MOVES,
    categories_keyboard,
    main_menu_keyboard,
    market_actions_keyboard,
)
from bot.services.ai_explainer import AIExplainer
from bot.services.market_analyzer import CATEGORY_LABELS, MarketAnalyzer, MarketMovement
from bot.services.polymarket_client import Market, PolymarketAPIError
from bot.utils.formatting import format_market_card, format_movement_card
from bot.utils.i18n import t
from bot.utils.logging import log_callback_action, log_user_action

logger = logging.getLogger(__name__)
router = Router()


class MarketSearchStates(StatesGroup):
    waiting_query = State()


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
    heading: str = "🔥 Рынок:",
) -> None:
    if not markets:
        await message.answer("Пока не нашёл подходящих рынков. Попробуйте позже.")
        return

    for market in markets[:5]:
        explanation = await ai_explainer.explain_market(market)
        await message.answer(
            format_market_card(market, explanation=explanation, heading=heading),
            reply_markup=market_actions_keyboard(market.url, market.id, language),
            disable_web_page_preview=True,
        )


async def _send_movement_cards(
    message: Message,
    movements: list[MarketMovement],
    ai_explainer: AIExplainer,
    language: str,
) -> None:
    if not movements:
        await message.answer(
            "Пока не вижу резких движений. Если это первый запуск, я уже сохранил снимок рынков и смогу сравнить его со следующим."
        )
        return

    for movement in movements[:5]:
        explanation = await ai_explainer.explain_market(movement.market)
        await message.answer(
            format_movement_card(movement, explanation=explanation),
            reply_markup=market_actions_keyboard(
                movement.market.url,
                movement.market.id,
                language,
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
    await callback.answer("Ищу горячие рынки")
    if not callback.message:
        return
    language = await _language(session_factory, callback.from_user)
    try:
        markets = await market_analyzer.get_hot_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch hot markets")
        await callback.message.answer(t("api_error", language))
        return
    await _send_market_cards(callback.message, markets, ai_explainer, language)


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
    await _send_market_cards(message, markets, ai_explainer, language)


@router.callback_query(F.data == NEW_MARKETS)
async def new_markets(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "new_markets")
    await callback.answer("Ищу новые рынки")
    if not callback.message:
        return
    language = await _language(session_factory, callback.from_user)
    try:
        markets = await market_analyzer.get_new_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch new markets")
        await callback.message.answer(t("api_error", language))
        return
    await _send_market_cards(callback.message, markets, ai_explainer, language)


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
    await _send_market_cards(message, markets, ai_explainer, language)


@router.callback_query(F.data == SHARP_MOVES)
async def sharp_moves(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
) -> None:
    log_callback_action(logger, callback, "sharp_moves")
    await callback.answer("Сравниваю снимки рынков")
    if not callback.message:
        return
    language = await _language(session_factory, callback.from_user)
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
            "Не смог сравнить рынки. Я уже записал ошибку в лог, попробуйте позже."
        )
        return

    await _send_movement_cards(callback.message, movements, ai_explainer, language)


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
            "Не смог сравнить рынки. Я уже записал ошибку в лог, попробуйте позже."
        )
        return
    await _send_movement_cards(message, movements, ai_explainer, language)


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

    if not markets:
        await message.answer(
            "Ничего не нашёл по этому запросу. Попробуйте другую тему.",
            reply_markup=main_menu_keyboard(language),
        )
        return

    await _send_market_cards(
        message,
        markets,
        ai_explainer,
        language,
        heading="🔍 Найден рынок",
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
            "Выберите категорию:",
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
    await callback.answer("Ищу рынки в категории")
    if not callback.message:
        return

    language = await _language(session_factory, callback.from_user)
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
        heading=heading,
    )
