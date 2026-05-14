from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.handlers.common import load_user, user_language
from bot.keyboards.main import main_menu_keyboard
from bot.utils.i18n import t
from bot.utils.logging import log_user_action

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def start_command(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "start")
    user = None
    if message.from_user is not None:
        try:
            user = await load_user(session_factory, message.from_user)
        except Exception:
            logger.exception("Could not save Telegram user")

    language = user_language(user)
    await message.answer(
        t("dashboard", language),
        reply_markup=main_menu_keyboard(language),
    )
