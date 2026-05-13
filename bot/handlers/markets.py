from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.keyboards.main import HOT_MARKETS, NEW_MARKETS, SHARP_MOVES, market_link_keyboard
from bot.services.ai_explainer import AIExplainer
from bot.services.market_analyzer import MarketAnalyzer, MarketMovement
from bot.services.polymarket_client import Market, PolymarketAPIError
from bot.utils.formatting import format_market_card, format_movement_card
from bot.utils.logging import log_callback_action

logger = logging.getLogger(__name__)
router = Router()


async def _send_market_cards(
    message: Message,
    markets: list[Market],
    ai_explainer: AIExplainer,
) -> None:
    if not markets:
        await message.answer("Пока не нашёл подходящих рынков. Попробуйте позже.")
        return

    for market in markets[:5]:
        explanation = await ai_explainer.explain_market(market)
        await message.answer(
            format_market_card(market, explanation=explanation),
            reply_markup=market_link_keyboard(market.url),
            disable_web_page_preview=True,
        )


async def _send_movement_cards(
    message: Message,
    movements: list[MarketMovement],
    ai_explainer: AIExplainer,
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
            reply_markup=market_link_keyboard(movement.market.url),
            disable_web_page_preview=True,
        )


@router.callback_query(F.data == HOT_MARKETS)
async def hot_markets(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
) -> None:
    log_callback_action(logger, callback, "hot_markets")
    await callback.answer("Ищу горячие рынки")
    if not callback.message:
        return
    try:
        markets = await market_analyzer.get_hot_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch hot markets")
        await callback.message.answer(
            "Не смог получить данные Polymarket. Попробуйте чуть позже."
        )
        return
    await _send_market_cards(callback.message, markets, ai_explainer)


@router.callback_query(F.data == NEW_MARKETS)
async def new_markets(
    callback: CallbackQuery,
    market_analyzer: MarketAnalyzer,
    ai_explainer: AIExplainer,
) -> None:
    log_callback_action(logger, callback, "new_markets")
    await callback.answer("Ищу новые рынки")
    if not callback.message:
        return
    try:
        markets = await market_analyzer.get_new_markets(limit=5)
    except PolymarketAPIError:
        logger.exception("Could not fetch new markets")
        await callback.message.answer(
            "Не смог получить данные Polymarket. Попробуйте чуть позже."
        )
        return
    await _send_market_cards(callback.message, markets, ai_explainer)


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
    try:
        async with session_factory() as session:
            movements = await market_analyzer.detect_movements(session)
    except PolymarketAPIError:
        logger.exception("Could not fetch markets for movement detection")
        await callback.message.answer(
            "Не смог получить данные Polymarket. Попробуйте чуть позже."
        )
        return
    except Exception:
        logger.exception("Could not detect market movements")
        await callback.message.answer(
            "Не смог сравнить рынки. Я уже записал ошибку в лог, попробуйте позже."
        )
        return

    await _send_movement_cards(callback.message, movements, ai_explainer)
