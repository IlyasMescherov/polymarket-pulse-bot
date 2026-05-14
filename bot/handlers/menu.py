from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.handlers.common import load_user, user_language
from bot.keyboards.main import (
    ABOUT_PROJECT,
    BACK_TO_MENU,
    QUICK_START,
    QUICK_START_OK,
    SHARE_BOT,
    main_menu_keyboard,
    quick_start_keyboard,
)
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


@router.callback_query(F.data == BACK_TO_MENU)
async def back_to_menu(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(
            t("dashboard", language),
            reply_markup=main_menu_keyboard(language),
        )


@router.callback_query(F.data == QUICK_START)
async def quick_start(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "quick_start")
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(
            t("quick_start", language),
            reply_markup=quick_start_keyboard(language),
        )


@router.callback_query(F.data == QUICK_START_OK)
async def quick_start_ok(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(
            t("dashboard", language),
            reply_markup=main_menu_keyboard(language),
        )


@router.callback_query(F.data == SHARE_BOT)
async def share_bot(
    callback: CallbackQuery,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "share_bot")
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        lines = [t("share", language)]
        if settings.polymarket_referral_url:
            lines.extend(
                [
                    "",
                    "Optional Polymarket link:",
                    settings.polymarket_referral_url,
                ]
            )
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(language),
            disable_web_page_preview=True,
        )


@router.callback_query(F.data == ABOUT_PROJECT)
async def about_project(
    callback: CallbackQuery,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "about_opened")
    await callback.answer()
    language = await _language(session_factory, callback.from_user)
    lines = [t("about", language)]
    if settings.project_public_url:
        lines.extend(["", f"Public URL: {settings.project_public_url}"])
    if settings.project_telegram_handle:
        lines.append(f"Telegram: {settings.project_telegram_handle}")
    if settings.polymarket_referral_url:
        lines.extend(
            [
                "",
                f"Optional Polymarket referral URL: {settings.polymarket_referral_url}",
            ]
        )

    if callback.message:
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(language),
            disable_web_page_preview=True,
        )


@router.message(Command("about"))
async def about_command(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "about_opened")
    language = await _language(session_factory, message.from_user)
    lines = [t("about", language)]
    if settings.project_public_url:
        lines.extend(["", f"Public URL: {settings.project_public_url}"])
    if settings.project_telegram_handle:
        lines.append(f"Telegram: {settings.project_telegram_handle}")
    if settings.polymarket_referral_url:
        lines.extend(
            [
                "",
                f"Optional Polymarket referral URL: {settings.polymarket_referral_url}",
            ]
        )
    await message.answer(
        "\n".join(lines),
        reply_markup=main_menu_keyboard(language),
        disable_web_page_preview=True,
    )
