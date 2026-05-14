from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import (
    add_market_to_watchlist,
    get_user_watchlist,
    remove_watchlist_item,
    update_watchlist_probability,
)
from bot.handlers.common import load_user, user_language
from bot.keyboards.main import (
    WATCHLIST_ADD_PREFIX,
    WATCHLIST_REMOVE_PREFIX,
    WATCHLIST_VIEW,
    main_menu_keyboard,
    watchlist_item_keyboard,
)
from bot.services.market_analyzer import MarketAnalyzer
from bot.services.polymarket_client import PolymarketAPIError
from bot.utils.formatting import format_watchlist_card
from bot.utils.i18n import t
from bot.utils.logging import log_callback_action, log_user_action

logger = logging.getLogger(__name__)
router = Router()


async def _language(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> str:
    try:
        return user_language(await load_user(session_factory, telegram_user))
    except Exception:
        logger.exception("Could not load user language")
        return "ru"


async def _send_watchlist(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
    market_analyzer: MarketAnalyzer,
) -> None:
    language = await _language(session_factory, telegram_user)
    if telegram_user is None:
        await message.answer(t("empty_watchlist", language))
        return

    async with session_factory() as session:
        try:
            items = await get_user_watchlist(session, telegram_user)
            for item in items:
                try:
                    market = await market_analyzer.find_market_by_id(item.market_id)
                except PolymarketAPIError:
                    market = None
                if market is not None:
                    await update_watchlist_probability(session, item, market)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not load watchlist")
            await message.answer("Не смог открыть Watchlist. Попробуйте позже.")
            return

    if not items:
        await message.answer(
            t("empty_watchlist", language),
            reply_markup=main_menu_keyboard(language),
        )
        return

    for item in items[:10]:
        await message.answer(
            format_watchlist_card(item),
            reply_markup=watchlist_item_keyboard(
                item.id,
                item.market_id,
                item.market_url,
                language,
            ),
            disable_web_page_preview=True,
        )


@router.callback_query(F.data == WATCHLIST_VIEW)
async def watchlist_view(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    market_analyzer: MarketAnalyzer,
) -> None:
    log_callback_action(logger, callback, "watchlist_view")
    await callback.answer()
    if callback.message:
        await _send_watchlist(
            callback.message,
            session_factory,
            callback.from_user,
            market_analyzer,
        )


@router.message(Command("watchlist"))
async def watchlist_command(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    market_analyzer: MarketAnalyzer,
) -> None:
    log_user_action(logger, message.from_user, "watchlist_view")
    await _send_watchlist(message, session_factory, message.from_user, market_analyzer)


@router.callback_query(F.data.startswith(WATCHLIST_ADD_PREFIX))
async def watchlist_add(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    market_analyzer: MarketAnalyzer,
) -> None:
    market_id = (callback.data or "").removeprefix(WATCHLIST_ADD_PREFIX)
    log_callback_action(logger, callback, "watchlist_add", market_id=market_id)
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    language = await _language(session_factory, callback.from_user)
    try:
        market = await market_analyzer.find_market_by_id(market_id)
    except PolymarketAPIError:
        logger.exception("Could not fetch market for watchlist")
        await callback.message.answer(t("api_error", language))
        return

    if market is None:
        await callback.message.answer(
            "Не смог найти этот рынок. Попробуйте добавить его через поиск ещё раз."
        )
        return

    async with session_factory() as session:
        try:
            _, created = await add_market_to_watchlist(
                session,
                callback.from_user,
                market,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not add market to watchlist")
            await callback.message.answer("Не смог добавить рынок. Попробуйте позже.")
            return

    text = "Добавил рынок в Watchlist." if created else "Этот рынок уже есть в Watchlist."
    await callback.message.answer(text, reply_markup=main_menu_keyboard(language))


@router.callback_query(F.data.startswith(WATCHLIST_REMOVE_PREFIX))
async def watchlist_remove(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    item_id_text = (callback.data or "").removeprefix(WATCHLIST_REMOVE_PREFIX)
    log_callback_action(
        logger,
        callback,
        "watchlist_remove",
        market_id=item_id_text,
    )
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    try:
        item_id = int(item_id_text)
    except ValueError:
        await callback.message.answer("Не смог удалить этот пункт Watchlist.")
        return

    language = await _language(session_factory, callback.from_user)
    async with session_factory() as session:
        try:
            removed = await remove_watchlist_item(session, callback.from_user, item_id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not remove watchlist item")
            await callback.message.answer("Не смог удалить рынок. Попробуйте позже.")
            return

    text = "Удалил рынок из Watchlist." if removed else "Этот рынок уже не найден в Watchlist."
    await callback.message.answer(text, reply_markup=main_menu_keyboard(language))
