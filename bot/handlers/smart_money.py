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
    SMART_TRACK_WALLET_PREFIX,
    SMART_TRADERS,
    SMART_UNUSUAL,
    main_menu_keyboard,
    public_trader_keyboard,
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


def _smart_intro(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "🧠 Радар активности",
                "",
                "PulseMarket отслеживает публичную активность на Polymarket и показывает рынки, к которым растёт внимание.",
                "",
                "Это помогает быстрее замечать, где появляется интерес.",
                "",
                "Для анализа · Без сделок",
            ]
        )
    return "\n".join(
        [
            "🧠 Activity Radar",
            "",
            "PulseMarket watches public Polymarket activity and highlights markets that are getting unusual attention.",
            "",
            "Use it to notice where attention is moving.",
            "",
            "Research only · No trade execution",
        ]
    )


def _short_wallet(address: str | None) -> str:
    if not address:
        return "public participant"
    return f"{address[:6]}…{address[-4:]}"


def _participant_label(language: str) -> str:
    return "публичный участник" if language == "ru" else "public participant"


def _wallet_label(language: str) -> str:
    return "Кошелёк" if language == "ru" else "Wallet"


def _short_wallet_label(address: str | None, language: str) -> str:
    return _short_wallet(address) if address else _participant_label(language)


def _trader_score_label(label: str, language: str) -> str:
    if language != "ru":
        return label
    return {
        "High public activity": "Высокая публичная активность",
        "Active public participant": "Активный публичный участник",
        "Limited public data": "Мало публичных данных",
    }.get(label, label)


def _unusual_empty_state(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "🐋 Всплески активности",
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
            "🐋 Activity spikes",
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
                "📈 Рынки с ростом внимания",
                "",
                "Сейчас нет рынков выше порога видимости.",
                "PulseMarket продолжит отслеживание.",
                "",
                "Для анализа · Без сделок",
            ]
        )
    return "\n".join(
        [
            "📈 Markets getting attention",
            "",
            "No public markets above the visibility threshold right now.",
            "PulseMarket will keep watching.",
            "",
            "Research only · No trade execution",
        ]
    )


def _track_wallet_prompt(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "👀 Следить за активностью",
                "",
                "Вставь публичный адрес кошелька, чтобы отслеживать его публичную активность на Polymarket.",
                "",
                "Пример:",
                "0x1234567890abcdef1234567890abcdef12345678",
                "",
                "Мы читаем только публичные данные.",
                "Никогда не отправляй private key или seed phrase.",
            ]
        )
    return "\n".join(
        [
            "👀 Follow public activity",
            "",
            "Paste a public wallet address to follow its public Polymarket activity.",
            "",
            "Example:",
            "0x1234567890abcdef1234567890abcdef12345678",
            "",
            "We only read public data.",
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


def _public_traders_intro(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "👥 Активные участники",
                "",
                "Это публичные адреса с заметной активностью.",
                "Используй это, чтобы понять, куда может смещаться внимание, а не как инструкцию к действию.",
            ]
        )
    return "\n".join(
        [
            "👥 Active participants",
            "",
            "These are public wallets with noticeable activity.",
            "Use this to understand where attention may be moving, not as instructions.",
        ]
    )


def _public_traders_empty_state(language: str) -> str:
    if language == "ru":
        return "\n".join(
            [
                "👥 Активные участники",
                "",
                "Данные по активным участникам сейчас недоступны.",
                "",
                "Для анализа · Без сделок",
            ]
        )
    return "\n".join(
        [
            "👥 Active participants",
            "",
            "Active participant data is not available right now.",
            "",
            "Research only · No trade execution",
        ]
    )


def _format_public_trader_card(
    trader: TraderScore,
    index: int,
    language: str,
) -> str:
    if language == "ru":
        lines = [
            f"{index}. Активный публичный участник",
            "",
            "Почему это важно:",
            "Этот кошелёк сегодня заметно активен на публичных рынках Polymarket.",
        ]
        if trader.volume is not None:
            lines.extend(["", "Публичная активность:", format_compact_usd(trader.volume, "ru")])
        lines.extend(
            [
                "",
                "Оценка активности:",
                f"{trader.score}/100 · {_trader_score_label(trader.label, language)}",
                "",
                "Отсортировано по недавней публичной активности.",
            ]
        )
        if trader.wallet_address:
            lines.extend(["", _wallet_label(language) + ":", _short_wallet(trader.wallet_address)])
        return "\n".join(lines)

    lines = [
        f"{index}. Active public participant",
        "",
        "Why it matters:",
        "This wallet has been active across public Polymarket markets today.",
    ]
    if trader.volume is not None:
        lines.extend(["", "Public activity:", format_compact_usd(trader.volume, "en")])
    lines.extend(
        [
            "",
            "Activity score:",
            f"{trader.score}/100 · {trader.label}",
            "",
            "Listed by recent public activity.",
        ]
    )
    if trader.wallet_address:
        lines.extend(["", _wallet_label(language) + ":", _short_wallet(trader.wallet_address)])
    return "\n".join(lines)


def _wallet_saved_text(
    *,
    created: bool,
    wallet_address: str,
    tracked_count: int,
    language: str,
) -> str:
    if language == "ru":
        status = (
            "Кошелёк сохранён. PulseMarket AI будет показывать публичную активность этого кошелька."
            if created
            else "Кошелёк уже отслеживается."
        )
        return "\n".join(
            [
                f"✅ {status}",
                "",
                "Кошелёк:",
                _short_wallet(wallet_address),
                f"Отслеживаемых кошельков: {tracked_count}",
                "",
                "Только публичные данные · Без сделок",
            ]
        )

    status = (
        "Wallet saved. PulseMarket AI will show public activity for this wallet."
        if created
        else "Wallet is already tracked."
    )
    return "\n".join(
        [
            f"✅ {status}",
            "",
            "Wallet:",
            _short_wallet(wallet_address),
            f"Tracked public wallets: {tracked_count}",
            "",
            "Public data only · No trade execution",
        ]
    )


def _wallet_save_error(language: str) -> str:
    if language == "ru":
        return "Не смог сохранить публичный адрес. Попробуйте позже."
    return "Could not save this public wallet. Please try again later."


async def _save_tracked_wallet(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object,
    wallet_address: str,
    source: str,
) -> tuple[bool, int]:
    normalized_wallet = wallet_address.strip().lower()
    async with session_factory() as session:
        item, created = await add_tracked_trader(
            session,
            telegram_user,
            normalized_wallet,
        )
        await create_smart_money_snapshot(
            session,
            "tracked_wallet",
            wallet_address=item.wallet_address,
            raw_data={"source": source},
        )
        tracked = await get_user_tracked_traders(session, telegram_user)
        await session.commit()
        return created, len(tracked)


async def _send_smart_menu(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: object | None,
) -> None:
    language = await _language(session_factory, telegram_user)
    await message.answer(_smart_intro(language), reply_markup=smart_money_keyboard(language))


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
    if not callback.message:
        await callback.answer()
        return

    language = await _language(session_factory, callback.from_user)
    await callback.answer(
        "Проверяю публичную активность"
        if language == "ru"
        else "Checking public activity"
    )
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
                    explain_large_trade(signal, language),
                    "",
                    "Рынок:" if language == "ru" else "Market:",
                    signal.market_title,
                ]
            )
        )


@router.callback_query(F.data == SMART_TRADERS)
async def public_traders(
    callback: CallbackQuery,
    smart_money_analyzer: SmartMoneyAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "smart_money_public_traders")
    if not callback.message:
        await callback.answer()
        return

    language = await _language(session_factory, callback.from_user)
    await callback.answer(
        "Загружаю активных участников"
        if language == "ru"
        else "Loading active participants"
    )
    traders = await smart_money_analyzer.public_traders(limit=5)
    if not traders:
        await callback.message.answer(_public_traders_empty_state(language))
        return

    await callback.message.answer(_public_traders_intro(language))
    for index, trader in enumerate(traders, start=1):
        reply_markup = (
            public_trader_keyboard(trader.wallet_address.strip().lower(), language)
            if trader.wallet_address and validate_wallet_address(trader.wallet_address)
            else None
        )
        await callback.message.answer(
            _format_public_trader_card(trader, index, language),
            reply_markup=reply_markup,
        )


@router.callback_query(F.data.startswith(SMART_TRACK_WALLET_PREFIX))
async def track_public_trader_wallet(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    wallet_address = (callback.data or "").removeprefix(SMART_TRACK_WALLET_PREFIX)
    language = await _language(session_factory, callback.from_user)
    log_callback_action(
        logger,
        callback,
        "smart_money_track_wallet_from_leaderboard",
        valid=str(validate_wallet_address(wallet_address)).lower(),
    )
    await callback.answer()
    if not callback.message or callback.from_user is None:
        return
    if not validate_wallet_address(wallet_address):
        await callback.message.answer(_invalid_wallet_message(language))
        return

    try:
        created, tracked_count = await _save_tracked_wallet(
            session_factory,
            callback.from_user,
            wallet_address,
            "leaderboard_button",
        )
    except Exception:
        logger.exception("Could not save tracked wallet from leaderboard")
        await callback.message.answer(_wallet_save_error(language))
        return

    await callback.message.answer(
        _wallet_saved_text(
            created=created,
            wallet_address=wallet_address,
            tracked_count=tracked_count,
            language=language,
        ),
        reply_markup=main_menu_keyboard(language),
    )


@router.callback_query(F.data == SMART_ACTIVE_MARKETS)
async def active_markets(
    callback: CallbackQuery,
    smart_money_analyzer: SmartMoneyAnalyzer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_callback_action(logger, callback, "smart_money_active_markets")
    if not callback.message:
        await callback.answer()
        return

    language = await _language(session_factory, callback.from_user)
    await callback.answer(
        "Собираю публичную активность"
        if language == "ru"
        else "Aggregating public activity"
    )
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
    try:
        created, tracked_count = await _save_tracked_wallet(
            session_factory,
            message.from_user,
            address,
            "manual_tracking",
        )
    except Exception:
        logger.exception("Could not save tracked wallet")
        await message.answer(_wallet_save_error(language))
        return

    await message.answer(
        _wallet_saved_text(
            created=created,
            wallet_address=address,
            tracked_count=tracked_count,
            language=language,
        ),
        reply_markup=main_menu_keyboard(language),
    )
