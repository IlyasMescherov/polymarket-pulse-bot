from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import create_user_feedback
from bot.handlers.common import load_user, user_language
from bot.utils.logging import log_user_action

logger = logging.getLogger(__name__)
router = Router()


class FeedbackStates(StatesGroup):
    waiting_feedback = State()


async def _language(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> str:
    try:
        return user_language(await load_user(session_factory, telegram_user))
    except Exception:
        logger.exception("Could not load user language")
        return "ru"


@router.message(Command("feedback"))
async def feedback_start(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "feedback_started")
    await state.set_state(FeedbackStates.waiting_feedback)
    language = await _language(session_factory, message.from_user)
    await message.answer(
        (
            "Send your feedback or idea in one message."
            if language == "en"
            else "Напиши отзыв или идею одним сообщением."
        )
    )


@router.message(FeedbackStates.waiting_feedback)
async def feedback_save(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    text = (message.text or "").strip()
    language = await _language(session_factory, message.from_user)
    if not text:
        await message.answer(
            (
                "Please send feedback as text."
                if language == "en"
                else "Пожалуйста, отправь отзыв текстом."
            )
        )
        return

    if message.from_user is None:
        await message.answer(
            "Could not save feedback." if language == "en" else "Не смог сохранить отзыв."
        )
        return

    try:
        async with session_factory() as session:
            await create_user_feedback(session, message.from_user, text)
            await session.commit()
    except Exception:
        logger.exception("Could not save user feedback")
        await message.answer(
            (
                "Could not save feedback. Please try again later."
                if language == "en"
                else "Не смог сохранить отзыв. Попробуйте позже."
            )
        )
        return

    await state.clear()
    log_user_action(logger, message.from_user, "feedback_saved")
    await message.answer(
        "Thank you. Feedback saved."
        if language == "en"
        else "Спасибо. Отзыв сохранён."
    )
