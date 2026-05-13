from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import set_notifications, upsert_user
from bot.keyboards.main import (
    MY_NOTIFICATIONS,
    NOTIFICATIONS_OFF,
    NOTIFICATIONS_ON,
    notifications_keyboard,
)
from bot.utils.logging import log_callback_action

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == MY_NOTIFICATIONS)
async def my_notifications(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "notifications_settings")
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
        reply_markup=notifications_keyboard(user.notifications_enabled),
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
        reply_markup=notifications_keyboard(user.notifications_enabled),
    )
