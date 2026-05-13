from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import upsert_user
from bot.keyboards.main import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def start_command(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if message.from_user is not None:
        async with session_factory() as session:
            try:
                await upsert_user(session, message.from_user)
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Could not save Telegram user")

    await message.answer(
        "Я отслеживаю интересные рынки Polymarket и объясняю их простым языком.",
        reply_markup=main_menu_keyboard(),
    )

