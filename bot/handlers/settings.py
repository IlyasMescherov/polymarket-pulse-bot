from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import (
    add_user_topic,
    get_user_topics,
    remove_user_topic,
    set_daily_digest,
    set_language,
    set_min_volume_for_alerts,
    set_movement_threshold,
    set_notifications,
    set_smart_money_alerts,
    upsert_user,
)
from bot.keyboards.main import (
    DAILY_DIGEST_OFF,
    DAILY_DIGEST_ON,
    LANGUAGE_EN,
    LANGUAGE_RU,
    MIN_VOLUME_PREFIX,
    MY_NOTIFICATIONS,
    NOTIFICATIONS_OFF,
    NOTIFICATIONS_ON,
    SETTINGS_MENU,
    SMART_MONEY_ALERTS_OFF,
    SMART_MONEY_ALERTS_ON,
    THRESHOLD_PREFIX,
    TOPIC_ADD,
    TOPIC_REMOVE_PREFIX,
    TOPICS_MENU,
    main_menu_keyboard,
    notifications_keyboard,
    settings_keyboard,
    topics_keyboard,
)
from bot.utils.i18n import t
from bot.utils.logging import log_callback_action, log_user_action

logger = logging.getLogger(__name__)
router = Router()


class TopicStates(StatesGroup):
    waiting_topic = State()


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

    title = "⚙️ PulseMarket AI Settings" if user.language == "en" else "⚙️ Настройки PulseMarket AI"
    await message.answer(title, reply_markup=settings_keyboard(user, user.language))


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


@router.callback_query(F.data.in_({SMART_MONEY_ALERTS_ON, SMART_MONEY_ALERTS_OFF}))
async def toggle_smart_money_alerts(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    enabled = callback.data == SMART_MONEY_ALERTS_ON
    log_callback_action(
        logger,
        callback,
        "smart_money_alerts_toggle",
        enabled=str(enabled).lower(),
    )
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    async with session_factory() as session:
        try:
            user = await set_smart_money_alerts(session, callback.from_user, enabled)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not update Smart Money alert setting")
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
    log_callback_action(logger, callback, "alert_settings_changed", threshold=value_text)
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


@router.callback_query(F.data.startswith(MIN_VOLUME_PREFIX))
async def change_min_volume(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    value_text = (callback.data or "").removeprefix(MIN_VOLUME_PREFIX)
    log_callback_action(
        logger,
        callback,
        "alert_settings_changed",
        min_volume=value_text,
    )
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    try:
        volume = float(value_text)
    except ValueError:
        await callback.message.answer("Не смог распознать минимальный объём.")
        return

    async with session_factory() as session:
        try:
            user = await set_min_volume_for_alerts(session, callback.from_user, volume)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not update min alert volume")
            await callback.message.answer(
                "Не смог сохранить настройки. Попробуйте позже."
            )
            return

    await callback.message.answer(
        t("settings_saved", user.language),
        reply_markup=settings_keyboard(user, user.language),
    )


@router.callback_query(F.data == TOPICS_MENU)
async def topics_menu(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "settings_opened", panel="topics")
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    async with session_factory() as session:
        try:
            user = await upsert_user(session, callback.from_user)
            topics = await get_user_topics(session, callback.from_user)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not load topics")
            await callback.message.answer("Не смог открыть темы. Попробуйте позже.")
            return

    text = "🎯 Мои темы\n\n"
    if topics:
        text += "\n".join(f"• {topic.topic}" for topic in topics)
    else:
        text += "Тем пока нет. Добавь: bitcoin, trump, fed, openai, nvidia, ufc."
    await callback.message.answer(
        text,
        reply_markup=topics_keyboard(topics, user.language),
    )


@router.callback_query(F.data == TOPIC_ADD)
async def topic_add_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    log_callback_action(logger, callback, "topic_add", step="start")
    await callback.answer()
    await state.set_state(TopicStates.waiting_topic)
    if callback.message:
        await callback.message.answer(
            "Напиши тему для smart alerts.\n\nНапример: bitcoin, trump, fed, openai, nvidia, ufc"
        )


@router.message(TopicStates.waiting_topic)
async def topic_add_finish(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    topic = (message.text or "").strip()
    log_user_action(logger, message.from_user, "topic_add", topic=topic[:80])
    if not topic:
        await message.answer("Напиши тему текстом, например bitcoin.")
        return

    await state.clear()
    async with session_factory() as session:
        try:
            user = await add_user_topic(session, message.from_user, topic)
            topics = await get_user_topics(session, message.from_user)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not add topic")
            await message.answer("Не смог добавить тему. Попробуйте позже.")
            return

    _, created = user
    text = "Тема добавлена." if created else "Такая тема уже есть."
    await message.answer(text, reply_markup=topics_keyboard(topics, "ru"))


@router.callback_query(F.data.startswith(TOPIC_REMOVE_PREFIX))
async def topic_remove(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    topic_id_text = (callback.data or "").removeprefix(TOPIC_REMOVE_PREFIX)
    log_callback_action(logger, callback, "topic_remove", topic_id=topic_id_text)
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return

    try:
        topic_id = int(topic_id_text)
    except ValueError:
        await callback.message.answer("Не смог удалить тему.")
        return

    async with session_factory() as session:
        try:
            user = await upsert_user(session, callback.from_user)
            removed = await remove_user_topic(session, callback.from_user, topic_id)
            topics = await get_user_topics(session, callback.from_user)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not remove topic")
            await callback.message.answer("Не смог удалить тему. Попробуйте позже.")
            return

    text = "Тема удалена." if removed else "Тема уже не найдена."
    await callback.message.answer(text, reply_markup=topics_keyboard(topics, user.language))
