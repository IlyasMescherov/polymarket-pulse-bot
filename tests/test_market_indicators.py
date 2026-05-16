from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.market_indicators import calculate_market_indicators
from bot.services.polymarket_client import Market


def _market(
    *,
    volume: float = 120_000,
    end_date: datetime | None = None,
    probability: float | None = 0.63,
) -> Market:
    return Market(
        id="m1",
        question="Will Bitcoin hit $150k by December 31, 2026?",
        slug="will-bitcoin-hit-150k-by-december-31-2026",
        yes_probability=probability,
        volume=volume,
        end_date=end_date or datetime.now(timezone.utc) + timedelta(days=30),
        url="https://polymarket.com/market/will-bitcoin-hit-150k-by-december-31-2026",
        raw={},
    )


def test_high_pulse_gives_hot_and_warm_labels() -> None:
    hot = calculate_market_indicators(_market(), pulse_score=80, delta=0.01, language="ru")
    warm = calculate_market_indicators(_market(), pulse_score=60, delta=0.01, language="en")

    assert hot.market_heat == "Горячий"
    assert hot.market_heat_key == "hot"
    assert warm.market_heat == "Warm"
    assert warm.market_heat_key == "warm"


def test_low_volume_gives_higher_error_risk() -> None:
    indicators = calculate_market_indicators(_market(volume=4_000), pulse_score=50, delta=0.04)

    assert indicators.market_depth == "Weak volume"
    assert indicators.error_risk == "High"
    assert indicators.ai_verdict == "Not enough data"


def test_ending_soon_gives_time_pressure() -> None:
    indicators = calculate_market_indicators(
        _market(end_date=datetime.now(timezone.utc) + timedelta(hours=8)),
        pulse_score=58,
        delta=0.005,
    )

    assert indicators.time_pressure == "Ending soon"
    assert indicators.time_pressure_key == "ending_soon"


def test_activity_up_probability_flat_gives_weak_confirmation() -> None:
    indicators = calculate_market_indicators(_market(volume=250_000), pulse_score=68, delta=0.005)

    assert indicators.confirmation_level == "Weak"
    assert indicators.confirmation_level_key == "weak"
    assert indicators.ai_verdict in {"Worth watching", "Caution"}


def test_probability_move_and_live_volume_gives_strong_confirmation() -> None:
    indicators = calculate_market_indicators(_market(volume=250_000), pulse_score=72, delta=0.06)

    assert indicators.confirmation_level == "Strong"
    assert indicators.error_risk == "Low"
    assert indicators.ai_verdict == "Strong interest"


def test_indicator_text_has_no_trading_advice() -> None:
    indicators = calculate_market_indicators(_market(), pulse_score=80, delta=0.06)
    text = " ".join(indicators.as_dict().values()).lower()

    for phrase in ("buy", "sell", "good bet", "ставь", "покупай", "продавай"):
        assert phrase not in text
