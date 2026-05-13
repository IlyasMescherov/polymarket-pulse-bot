from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.keyboards.main import ABOUT_PROJECT, BACK_TO_MENU, main_menu_keyboard
from bot.utils.logging import log_callback_action

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == BACK_TO_MENU)
async def back_to_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Выберите, что посмотреть:",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == ABOUT_PROJECT)
async def about_project(callback: CallbackQuery, settings: Settings) -> None:
    log_callback_action(logger, callback, "about")
    await callback.answer()
    lines = [
        "PulseMarket Bot — аналитический Telegram бот вокруг Polymarket.",
        "",
        "Что он делает:",
        "• показывает горячие и новые рынки",
        "• отслеживает резкие движения вероятностей",
        "• отправляет уведомления, если вы их включили",
        "",
        "Важно: бот не торгует, не подключает кошельки, не просит приватные ключи и не принимает деньги.",
        "",
        "Источник данных: публичный Gamma API Polymarket.",
    ]
    if settings.project_public_url:
        lines.extend(["", f"Публичная ссылка: {settings.project_public_url}"])
    if settings.project_telegram_handle:
        lines.append(f"Telegram: {settings.project_telegram_handle}")

    if callback.message:
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(),
            disable_web_page_preview=True,
        )
