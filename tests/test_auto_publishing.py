from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from bot.services.auto_publisher import DailyPublishingJob, parse_publish_time, parse_timezone


class FakeContentPublisher:
    def __init__(self) -> None:
        self.channel_calls = 0
        self.x_calls = 0

    async def generate_today_pulse_channel_post(self, lang: str = "en") -> str:
        self.channel_calls += 1
        return "channel post"

    async def generate_x_today_pulse_draft(self, lang: str = "en") -> str:
        self.x_calls += 1
        return "x draft"


class FakeChannelPublisher:
    def __init__(self) -> None:
        self.calls = 0

    async def publish_to_telegram_channel(self, text: str, post_type: str = "today_pulse"):
        self.calls += 1
        return SimpleNamespace(status="published")


class FakeXPublisher:
    def __init__(self) -> None:
        self.calls = 0

    async def create_x_draft(self, text: str, post_type: str = "today_pulse"):
        self.calls += 1
        return SimpleNamespace(status="draft")


def _settings(**overrides: object) -> SimpleNamespace:
    values = {
        "auto_channel_posting_enabled": False,
        "auto_channel_posting_time": "09:00",
        "auto_channel_posting_timezone": "UTC",
        "x_drafts_enabled": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_publish_time_and_timezone_parsing_have_safe_fallbacks() -> None:
    assert parse_publish_time("10:30").hour == 10
    assert parse_publish_time("bad").hour == 9
    assert str(parse_timezone("UTC")) == "UTC"


@pytest.mark.asyncio
async def test_daily_job_creates_x_draft_but_does_not_channel_post_when_disabled() -> None:
    content = FakeContentPublisher()
    channel = FakeChannelPublisher()
    x_publisher = FakeXPublisher()
    job = DailyPublishingJob(
        content,
        channel,
        x_publisher,
        _settings(auto_channel_posting_enabled=False),
        interval_seconds=900,
    )

    await job.run_due(datetime(2026, 5, 14, 9, 5, tzinfo=timezone.utc))

    assert content.channel_calls == 1
    assert channel.calls == 0
    assert content.x_calls == 1
    assert x_publisher.calls == 1


@pytest.mark.asyncio
async def test_daily_job_runs_only_once_per_day() -> None:
    content = FakeContentPublisher()
    channel = FakeChannelPublisher()
    x_publisher = FakeXPublisher()
    job = DailyPublishingJob(
        content,
        channel,
        x_publisher,
        _settings(auto_channel_posting_enabled=True),
        interval_seconds=900,
    )

    now = datetime(2026, 5, 14, 9, 5, tzinfo=timezone.utc)
    await job.run_due(now)
    await job.run_due(now)

    assert channel.calls == 1
    assert x_publisher.calls == 1


@pytest.mark.asyncio
async def test_daily_job_skips_outside_due_window() -> None:
    content = FakeContentPublisher()
    channel = FakeChannelPublisher()
    x_publisher = FakeXPublisher()
    job = DailyPublishingJob(
        content,
        channel,
        x_publisher,
        _settings(auto_channel_posting_enabled=True),
        interval_seconds=900,
    )

    await job.run_due(datetime(2026, 5, 14, 17, 0, tzinfo=timezone.utc))

    assert content.channel_calls == 0
    assert channel.calls == 0
    assert x_publisher.calls == 0
