from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import (
    add_tracked_trader,
    create_smart_money_snapshot,
    get_user_tracked_traders,
)
from bot.handlers.common import load_user, user_language
from bot.keyboards.main import (
    SMART_ACTIVE_MARKETS,
    SMART_MONEY,
    SMART_TRACK_WALLET,
    SMART_TRADERS,
    SMART_UNUSUAL,
    main_menu_keyboard,
    smart_money_keyboard,
)
from bot.services.smart_money_analyzer import (
    SmartMoneyAnalyzer,
    TraderScore,
    explain_large_trade,
    explain_market_activity,
    validate_wallet_address,
)
from bot.utils.formatting import format_compact_usd
from bot.utils.logging import log_callback_action, log_user_action

logger = logging.getLogger(__name__)
router = Router()


class SmartMoneyStates(StatesGroup):
    waiting_wallet = State()


async def _language(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> str:
    try:
        return user_language(await load_user(session_factory, telegram_user))
    except Exception:
        logger.exception("Could not load user language")
        return "ru"


def _smart_intro() -> str:
    return "\n".join(
        [
            "🧠 Smart Money Radar",
            "",
            "PulseMarket tracks public activity from larger and active Polymarket participants.",
            "",
            "Use it to spot markets that may be heating up before they become obvious.",
            "",
            "Research only.",
            "No copy trading.",
            "No trade execution.",
        ]
    )


def _short_wallet(address: str | None) -> str:
    if not address:
        return "public participant"
    return f"{address[:6]}…{address[-4:]}"


def _unusual_empty_state(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "🐋 Необычная активность",
                "",
                "Сейчас нет сильной необычной публичной активности.",
                "PulseMarket продолжит отслеживание.",
                "",
                "Так бывает, когда нет свежих публичных сделок выше крупного порога активности.",
                "",
                "Для анализа · Без сделок",
            ]
        )
    return "\n".join(
        [
            "🐋 Unusual Activity",
            "",
            "No strong unusual public activity detected right now.",
            "PulseMarket will keep watching.",
            "",
            "This can happen when there are no recent public trades above the large activity threshold.",
            "",
            "Research only · No trade execution",
        ]
    )


def _active_markets_empty_state(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "📊 Активные рынки",
                "",
                "Сейчас нет активных публичных рынков выше порога видимости.",
                "PulseMarket продолжит отслеживание.",
                "",
                "Для анализа · Без сделок",
            ]
        )
    return "\n".join(
        [
            "📊 Active Markets",
            "",
            "No active public markets above the visibility threshold right now.",
            "PulseMarket will keep watching.",
            "",
            "Research only · No trade execution",
        ]
    )


def _track_wallet_prompt(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "👀 Отслеживать публичный адрес",
                "",
                "Отправь публичный адрес кошелька:",
                "",
                "Пример:",
                "0x1234...abcd",
                "",
                "Только публичный адрес.",
                "Никогда не отправляй private key или seed phrase.",
            ]
        )
    return "\n".join(
        [
            "👀 Track Public Wallet",
            "",
            "Send a public wallet address:",
            "",
            "Example:",
            "0x1234...abcd",
            "",
            "Only public addresses.",
            "Never send a private key or seed phrase.",
        ]
    )


def _invalid_wallet_message(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "Это не похоже на публичный адрес кошелька.",
                "Адрес должен начинаться с 0x и содержать 42 символа.",
            ]
        )
    return "\n".join(
        [
            "This does not look like a public wallet address.",
            "It should start with 0x and contain 42 characters.",
        ]
    )


def _format_public_traders(traders: list[TraderScore]) -> str:
    lines = [
        "🏆 Public Traders",
        "",
        "Past performance does not guarantee future results.",
        "Use this for research, not copy trading.",
        "",
    ]
    if not traders:
        lines.extend(
            [
                "Leaderboard data is not available right now.",
                "",
                "Research only · No trade execution",
            ]
        )
        return "\n".join(lines)

    for index, trader in enumerate(traders, start=1):
        name = trader.display_name or _short_wallet(trader.wallet_address)
        lines.extend([f"{index}. {name}", f"Trader Score: {trader.score}/100 · {trader.label}"])
        if trader.wallet_address:
            lines.append(f"Wallet: {_short_wallet(trader.wallet_address)}")
        if trader.volume is not None:
            lines.append(f"Public volume: {format_compact_usd(trader.volume, 'en')}")
        if trader.trades_count is not None:
            lines.append(f"Public trades: {trader.trades_count}")
        if trader.rank is not None:
            lines.append(f"Rank: {trader.rank}")
        lines.append("")

    lines.append("Research only · No trade execution")
    return "\n".join(lines)


async def _send_smart_menu(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> None:
    language = await _language(session_factory, telegram_user)
    await message.answer(_smart_intro(), reply_markup=smart_money_keyboard(language))


@router.message(Command("smart"))
async def smart_money_command(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "smart_money_opened")
    await _send_smart_menu(message, session_factory, message.from_user)


@router.callback_query(F.data == SMART_MONEY)
async def smart_money_menu(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "smart_money_opened")
    await callback.answer()
    if callback.message:
        await _send_smart_menu(callback.message, session_factory, callback.from_user)


@router.callback_query(F.data == SMART_UNUSUAL)
async def unusual_activity(
    callback: CallbackQuery,
    smart_money_analyzer: SmartMoneyAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "smart_money_unusual_activity")
    await callback.answer("Checking public activity")
    if not callback.message:
        return

    language = await _language(session_factory, callback.from_user)
    signals = await smart_money_analyzer.unusual_activity(limit=5)
    if not signals:
        await callback.message.answer(_unusual_empty_state(language))
        return

    async with session_factory() as session:
        try:
            for signal in signals:
                await create_smart_money_snapshot(
                    session,
                    "large_trade",
                    market_id=signal.market_id,
                    market_title=signal.market_title,
                    wallet_address=signal.wallet_address,
                    amount_usd=signal.amount_usd,
                    raw_data={"source": "data-api"},
                )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not save Smart Money snapshots")

    for signal in signals:
        await callback.message.answer(
            "\n".join(
                [
                    explain_large_trade(signal),
                    "",
                    "Market:",
                    signal.market_title,
                    "",
                    "Public participant:",
                    _short_wallet(signal.wallet_address),
                ]
            )
        )


@router.callback_query(F.data == SMART_TRADERS)
async def public_traders(
    callback: CallbackQuery,
    smart_money_analyzer: SmartMoneyAnalyzer,
) -> None:
    log_callback_action(logger, callback, "smart_money_public_traders")
    await callback.answer("Loading public leaderboard")
    if not callback.message:
        return

    traders = await smart_money_analyzer.public_traders(limit=5)
    await callback.message.answer(_format_public_traders(traders))


@router.callback_query(F.data == SMART_ACTIVE_MARKETS)
async def active_markets(
    callback: CallbackQuery,
    smart_money_analyzer: SmartMoneyAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "smart_money_active_markets")
    await callback.answer("Aggregating public activity")
    if not callback.message:
        return

    language = await _language(session_factory, callback.from_user)
    activities = await smart_money_analyzer.active_markets(limit=5)
    if not activities:
        await callback.message.answer(_active_markets_empty_state(language))
        return

    async with session_factory() as session:
        try:
            for activity in activities:
                await create_smart_money_snapshot(
                    session,
                    "active_market",
                    market_id=activity.market_id,
                    market_title=activity.market_title,
                    amount_usd=activity.amount_usd,
                    raw_data={
                        "trades_count": activity.trades_count,
                        "participant_count": activity.participant_count,
                    },
                )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not save Smart Money market activity")

    for activity in activities:
        await callback.message.answer(explain_market_activity(activity, language))


@router.callback_query(F.data == SMART_TRACK_WALLET)
async def track_wallet_start(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "smart_money_track_wallet_started")
    await callback.answer()
    await state.set_state(SmartMoneyStates.waiting_wallet)
    if callback.message:
        language = await _language(session_factory, callback.from_user)
        await callback.message.answer(_track_wallet_prompt(language))


@router.message(SmartMoneyStates.waiting_wallet)
async def track_wallet_finish(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    address = (message.text or "").strip()
    language = await _language(session_factory, message.from_user)
    log_user_action(
        logger,
        message.from_user,
        "smart_money_track_wallet_submitted",
        valid=str(validate_wallet_address(address)).lower(),
    )
    if not validate_wallet_address(address):
        await message.answer(_invalid_wallet_message(language))
        return

    await state.clear()
    async with session_factory() as session:
        try:
            item, created = await add_tracked_trader(session, message.from_user, address)
            await create_smart_money_snapshot(
                session,
                "tracked_wallet",
                wallet_address=item.wallet_address,
                raw_data={"source": "user_tracking"},
            )
            tracked = await get_user_tracked_traders(session, message.from_user)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Could not save tracked wallet")
            await message.answer("Could not save this public wallet. Please try again later.")
            return

    status = "Public wallet added." if created else "This public wallet is already tracked."
    await message.answer(
        "\n".join(
            [
                f"✅ {status}",
                "",
                f"Wallet: {_short_wallet(address)}",
                f"Tracked public wallets: {len(tracked)}",
                "",
                "Research only · No wallet connection · No trade execution",
            ]
        ),
        reply_markup=main_menu_keyboard(language),
    )
