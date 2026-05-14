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
    DASHBOARD,
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

GITHUB_URL = "https://github.com/IlyasMescherov/polymarket-pulse-bot"
DEFAULT_BOT_HANDLE = "@PulseMarketAIBot"


async def _language(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> str:
    try:
        return user_language(await load_user(session_factory, telegram_user))
    except Exception:
        logger.exception("Could not load user language")
        return "ru"


def _telegram_bot_url(settings: Settings) -> str:
    handle = settings.project_telegram_handle or DEFAULT_BOT_HANDLE
    if handle.startswith(("http://", "https://")):
        return handle
    return f"https://t.me/{handle.lstrip('@')}"


def _mini_app_preview_url(settings: Settings) -> str:
    if settings.project_public_url:
        return f"{settings.project_public_url.rstrip('/')}/app"
    return "http://2.26.80.27:8080/app"


def _mini_app_preview_text(settings: Settings, language: str) -> str:
    preview_url = _mini_app_preview_url(settings)
    if language == "ru":
        return (
            "Mini App подготовлен, но Telegram требует HTTPS. Текущий preview:\n"
            f"{preview_url}"
        )
    return (
        "Mini App is prepared, but Telegram requires HTTPS. Current preview:\n"
        f"{preview_url}"
    )


def _share_lines(settings: Settings, language: str) -> list[str]:
    lines = [t("share", language)]
    if settings.project_channel_url:
        lines.extend(
            [
                "",
                (
                    f"Обновления: {settings.project_channel_url}"
                    if language == "ru"
                    else f"Updates: {settings.project_channel_url}"
                ),
            ]
        )
    if settings.project_support_url:
        lines.extend(
            [
                "",
                (
                    f"Поддержка: {settings.project_support_url}"
                    if language == "ru"
                    else f"Support: {settings.project_support_url}"
                ),
            ]
        )
    if settings.project_x_url:
        lines.extend(
            [
                "",
                (
                    f"X/Twitter: {settings.project_x_url}"
                    if language == "ru"
                    else f"X/Twitter: {settings.project_x_url}"
                ),
            ]
        )
    return lines


def _about_lines(settings: Settings, language: str) -> list[str]:
    lines = [
        t("about", language),
        "",
        "Ссылки:" if language == "ru" else "Links:",
        f"GitHub: {GITHUB_URL}",
        f"Bot: {_telegram_bot_url(settings)}",
    ]
    if settings.project_channel_url:
        lines.append(
            f"Канал: {settings.project_channel_url}"
            if language == "ru"
            else f"Channel: {settings.project_channel_url}"
        )
    if settings.project_support_url:
        lines.append(
            f"Поддержка: {settings.project_support_url}"
            if language == "ru"
            else f"Support: {settings.project_support_url}"
        )
    if settings.project_x_url:
        lines.append(f"X/Twitter: {settings.project_x_url}")
    return lines


@router.callback_query(F.data == BACK_TO_MENU)
async def back_to_menu(
    callback: CallbackQuery,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(
            t("dashboard", language),
            reply_markup=main_menu_keyboard(language, settings.mini_app_url),
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
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(
            t("dashboard", language),
            reply_markup=main_menu_keyboard(language, settings.mini_app_url),
        )


@router.callback_query(F.data == DASHBOARD)
async def dashboard_preview(
    callback: CallbackQuery,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "dashboard_opened")
    await callback.answer()
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(
            _mini_app_preview_text(settings, language),
            reply_markup=main_menu_keyboard(language, settings.mini_app_url),
            disable_web_page_preview=True,
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
        lines = _share_lines(settings, language)
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(language, settings.mini_app_url),
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
    lines = _about_lines(settings, language)

    if callback.message:
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(language, settings.mini_app_url),
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
    lines = _about_lines(settings, language)
    await message.answer(
        "\n".join(lines),
        reply_markup=main_menu_keyboard(language, settings.mini_app_url),
        disable_web_page_preview=True,
    )
