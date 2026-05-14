from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.movement_explainer import explain_movement
from bot.services.polymarket_client import Market


def _market() -> Market:
    return Market(
        id="btc",
        question="Will Bitcoin hit $150k?",
        slug="will-bitcoin-hit-150k",
        yes_probability=0.63,
        volume=120_000,
        end_date=datetime.now(timezone.utc) + timedelta(days=12),
        url="https://polymarket.com/market/will-bitcoin-hit-150k",
        raw={},
    )


def test_movement_explainer_handles_missing_data() -> None:
    text = explain_movement(_market(), delta=None, language="en").to_text()

    assert "Not enough movement data yet" in text


def test_movement_explainer_includes_delta_volume_time_and_flags() -> None:
    text = explain_movement(
        _market(),
        delta=0.12,
        risk_flags=["⚠️ Sharp move"],
        topic_match="bitcoin",
        language="en",
    ).to_text()

    assert "Probability changed by +12%" in text
    assert "Volume is $120K" in text
    assert "Topic match: bitcoin" in text
    assert "Sharp move" in text


def test_movement_explainer_supports_russian() -> None:
    text = explain_movement(_market(), delta=-0.05, language="ru").to_text()

    assert "Почему двигается" in text
    assert "Вероятность изменилась на -5%" in text
