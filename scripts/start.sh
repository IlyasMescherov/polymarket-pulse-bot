#!/bin/sh
set -eu

if [ -f /run/secrets/pulsemarket.env ]; then
  set -a
  . /run/secrets/pulsemarket.env
  set +a
elif [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

python - <<'PY'
import asyncio

from bot.config import load_settings
from bot.database.db import create_engine, ping_database


async def wait_for_database() -> None:
    settings = load_settings()
    engine = create_engine(settings)
    try:
        for attempt in range(1, 61):
            try:
                await ping_database(engine)
            except Exception as exc:
                print(f"Waiting for database ({attempt}/60): {exc}", flush=True)
                await asyncio.sleep(2)
            else:
                print("Database is ready", flush=True)
                return
        raise SystemExit("Database was not ready after 120 seconds")
    finally:
        await engine.dispose()


asyncio.run(wait_for_database())
PY

alembic upgrade head
exec python -m bot.main

