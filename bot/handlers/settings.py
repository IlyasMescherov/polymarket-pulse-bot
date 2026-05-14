from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import (
    set_daily_digest,
    set_language,
    set_movement_threshold,
    set_notifications,
    upsert_user,
)
from bot.keyboards.main import (
    DAILY_DIGEST_OFF,
    DAILY_DIGEST_ON,
    LANGUAGE_EN,
    LANGUAGE_RU,
    MY_NOTIFICATIONS,
    NOTIFICATIONS_OFF,
    NOTIFICATIONS_ON,
    SETTINGS_MENU,
    THRESHOLD_PREFIX,
    main_menu_keyboard,
    notifications_keyboard,
    settings_keyboard,
)
from bot.utils.i18n import t
from bot.utils.logging import log_callback_action, log_user_action

logger = logging.getLogger(__name__)
router = Router()


async def _open_settings(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> None:
    if telegram_user is None:
        await message.answer("Не смог определить пользователя Telegram.")
        return

    async with session_factory() as session:
        try:
            user = await upsert_user(session, telegram_user)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not load settings")
            await message.answer("Не смог открыть настройки. Попробуйте позже.")
            return

    await message.answer(
        "⚙️ Настройки PulseMarket AI",
        reply_markup=settings_keyboard(user, user.language),
    )


@router.callback_query(F.data == SETTINGS_MENU)
async def settings_menu(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "settings_opened")
    await callback.answer()
    if callback.message:
        await _open_settings(callback.message, session_factory, callback.from_user)


@router.message(Command("settings"))
async def settings_command(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "settings_opened")
    await _open_settings(message, session_factory, message.from_user)


@router.callback_query(F.data == MY_NOTIFICATIONS)
async def my_notifications(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "settings_opened", panel="notifications")
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    async with session_factory() as session:
        try:
            user = await upsert_user(session, callback.from_user)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not load notification settings")
            await callback.message.answer("Не смог открыть настройки. Попробуйте позже.")
            return

    status = "включены" if user.notifications_enabled else "выключены"
    await callback.message.answer(
        f"Уведомления о резких движениях сейчас {status}.",
        reply_markup=notifications_keyboard(user.notifications_enabled, user.language),
    )


@router.callback_query(F.data.in_({NOTIFICATIONS_ON, NOTIFICATIONS_OFF}))
async def toggle_notifications(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    enabled = callback.data == NOTIFICATIONS_ON
    log_callback_action(
        logger,
        callback,
        "notifications_toggle",
        enabled=str(enabled).lower(),
    )
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    async with session_factory() as session:
        try:
            user = await set_notifications(session, callback.from_user, enabled)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not update notification settings")
            await callback.message.answer(
                "Не смог сохранить настройки. Попробуйте позже."
            )
            return

    status = "включены" if user.notifications_enabled else "выключены"
    await callback.message.answer(
        f"Готово. Уведомления теперь {status}.",
        reply_markup=settings_keyboard(user, user.language),
    )


@router.callback_query(F.data.in_({DAILY_DIGEST_ON, DAILY_DIGEST_OFF}))
async def toggle_daily_digest(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    enabled = callback.data == DAILY_DIGEST_ON
    log_callback_action(
        logger,
        callback,
        "daily_digest_toggle",
        enabled=str(enabled).lower(),
    )
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    async with session_factory() as session:
        try:
            user = await set_daily_digest(session, callback.from_user, enabled)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not update daily digest setting")
            await callback.message.answer(
                "Не смог сохранить настройки. Попробуйте позже."
            )
            return

    await callback.message.answer(
        t("settings_saved", user.language),
        reply_markup=settings_keyboard(user, user.language),
    )


@router.callback_query(F.data.in_({LANGUAGE_RU, LANGUAGE_EN}))
async def change_language(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = "en" if callback.data == LANGUAGE_EN else "ru"
    log_callback_action(logger, callback, "language_changed", language=language)
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    async with session_factory() as session:
        try:
            user = await set_language(session, callback.from_user, language)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not update language setting")
            await callback.message.answer(
                "Не смог сохранить настройки. Попробуйте позже."
            )
            return

    await callback.message.answer(
        t("settings_saved", user.language),
        reply_markup=settings_keyboard(user, user.language),
    )


@router.callback_query(F.data.startswith(THRESHOLD_PREFIX))
async def change_threshold(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    value_text = (callback.data or "").removeprefix(THRESHOLD_PREFIX)
    log_callback_action(logger, callback, "threshold_changed", threshold=value_text)
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    try:
        threshold = int(value_text) / 100
    except ValueError:
        await callback.message.answer("Не смог распознать порог движения.")
        return

    async with session_factory() as session:
        try:
            user = await set_movement_threshold(
                session,
                callback.from_user,
                threshold,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not update movement threshold")
            await callback.message.answer(
                "Не смог сохранить настройки. Попробуйте позже."
            )
            return

    await callback.message.answer(
        t("settings_saved", user.language),
        reply_markup=settings_keyboard(user, user.language),
    )
