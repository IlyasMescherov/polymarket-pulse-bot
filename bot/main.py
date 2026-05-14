from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ErrorEvent

from bot.config import load_settings
from bot.database.db import create_engine, create_session_factory, ping_database
from bot.handlers import markets, menu, settings as settings_handlers, start, watchlist
from bot.services.ai_explainer import AIExplainer
from bot.services.health_server import HealthServer
from bot.services.market_analyzer import MarketAnalyzer
from bot.services.notifier import Notifier
from bot.services.polymarket_client import PolymarketClient
from bot.services.scheduler import Scheduler
from bot.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def on_error(event: ErrorEvent) -> bool:
    logger.exception("Update failed", exc_info=event.exception)
    return True


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Main menu"),
            BotCommand(command="hot", description="Hot markets"),
            BotCommand(command="new", description="New markets"),
            BotCommand(command="moves", description="Sharp movements"),
            BotCommand(command="search", description="Search markets"),
            BotCommand(command="watchlist", description="My watchlist"),
            BotCommand(command="settings", description="Settings"),
            BotCommand(command="about", description="About project"),
        ]
    )


async def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    engine = create_engine(settings)
    await ping_database(engine)
    session_factory = create_session_factory(engine)

    bot = Bot(token=settings.bot_token)
    polymarket_client = PolymarketClient(settings.polymarket_base_url)
    market_analyzer = MarketAnalyzer(
        polymarket_client,
        movement_threshold=settings.movement_threshold,
    )
    ai_explainer = AIExplainer(
        settings.openai_api_key,
        model=settings.openai_model,
    )
    notifier = Notifier(bot, session_factory, market_analyzer, ai_explainer)
    scheduler = Scheduler(
        notifier,
        interval_seconds=settings.market_poll_interval_seconds,
    )
    health_server = HealthServer(settings.app_host, settings.app_port, engine)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(markets.router)
    dp.include_router(watchlist.router)
    dp.include_router(settings_handlers.router)
    dp.errors.register(on_error)

    dp["settings"] = settings
    dp["session_factory"] = session_factory
    dp["market_analyzer"] = market_analyzer
    dp["ai_explainer"] = ai_explainer

    await health_server.start()
    scheduler_task = asyncio.create_task(scheduler.run())
    try:
        logger.info("PulseMarket Bot started")
        await bot.delete_webhook(drop_pending_updates=True)
        await set_bot_commands(bot)
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        await polymarket_client.close()
        await bot.session.close()
        await health_server.stop()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
