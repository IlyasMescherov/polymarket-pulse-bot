from __future__ import annotations

from bot.services.polymarket_data_client import DataTrade, LeaderboardTrader
from bot.services.smart_money_analyzer import (
    aggregate_market_activity,
    detect_large_trades,
    explain_large_trade,
    explain_market_activity,
    score_public_trader,
    validate_wallet_address,
)


def _trade(
    market_id: str,
    amount: float,
    wallet: str = "0x1111111111111111111111111111111111111111",
) -> DataTrade:
    return DataTrade(
        market_id=market_id,
        market_title=f"Market {market_id}",
        wallet_address=wallet,
        amount_usd=amount,
        price=None,
        size=None,
        outcome=None,
        timestamp=None,
        raw={},
    )


def test_wallet_validation_accepts_public_evm_addresses_only() -> None:
    assert validate_wallet_address("0x1111111111111111111111111111111111111111")
    assert not validate_wallet_address("1111111111111111111111111111111111111111")
    assert not validate_wallet_address("0x1234")


def test_large_trade_detection_sorts_by_public_amount() -> None:
    signals = detect_large_trades(
        [_trade("small", 9999), _trade("large", 25000), _trade("larger", 50000)],
        min_usd=10_000,
    )

    assert [signal.market_id for signal in signals] == ["larger", "large"]


def test_trader_score_has_safe_fallback_for_missing_data() -> None:
    score = score_public_trader(
        LeaderboardTrader(
            wallet_address=None,
            display_name=None,
            volume=None,
            trades_count=None,
            rank=None,
            raw={},
        )
    )

    assert score.score < 40
    assert score.label == "Limited public data"


def test_market_activity_aggregation_groups_public_trades() -> None:
    activities = aggregate_market_activity(
        [
            _trade("m1", 10_000),
            _trade("m1", 20_000, wallet="0x2222222222222222222222222222222222222222"),
            _trade("m2", 5_000),
        ]
    )

    assert activities[0].market_id == "m1"
    assert activities[0].amount_usd == 30_000
    assert activities[0].participant_count == 2


def test_smart_money_text_has_research_only_language_without_banned_phrases() -> None:
    signal = detect_large_trades([_trade("m1", 50_000)])[0]
    activity = aggregate_market_activity([_trade("m1", 50_000)])[0]
    text = "\n".join([explain_large_trade(signal), explain_market_activity(activity)])
    lowered = text.lower()

    assert "research only" in lowered
    assert "no trade execution" in lowered
    for phrase in (
        "insider",
        "guaranteed",
        "buy now",
        "sell now",
        "copy this trader",
        "trade signal",
    ):
        assert phrase not in lowered
