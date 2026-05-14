from __future__ import annotations

from bot.handlers.smart_money import (
    _active_markets_empty_state,
    _format_public_traders,
    _invalid_wallet_message,
    _track_wallet_prompt,
    _unusual_empty_state,
)
from bot.services.smart_money_analyzer import TraderScore


def test_active_markets_empty_state_mentions_visibility_threshold() -> None:
    text = _active_markets_empty_state("en")

    assert "No active public markets above the visibility threshold right now." in text
    assert "Research only" in text
    assert "No trade execution" in text


def test_unusual_activity_empty_state_is_specific() -> None:
    text = _unusual_empty_state("en")

    assert "No strong unusual public activity detected right now." in text
    assert "large activity threshold" in text


def test_wallet_prompt_and_invalid_message_are_clear() -> None:
    prompt = _track_wallet_prompt("en")
    invalid = _invalid_wallet_message("en")

    assert "Example:" in prompt
    assert "0x1234...abcd" in prompt
    assert "Never send a private key or seed phrase." in prompt
    assert "It should start with 0x and contain 42 characters." in invalid


def test_wallet_prompt_has_ru_copy() -> None:
    prompt = _track_wallet_prompt("ru")
    invalid = _invalid_wallet_message("ru")

    assert "Отправь публичный адрес кошелька" in prompt
    assert "Никогда не отправляй private key или seed phrase." in prompt
    assert "Адрес должен начинаться с 0x и содержать 42 символа." in invalid


def test_public_traders_does_not_show_unknown_fields() -> None:
    text = _format_public_traders(
        [
            TraderScore(
                wallet_address=None,
                display_name=None,
                score=13,
                label="Limited public data",
                volume=None,
                trades_count=None,
                rank=None,
            )
        ]
    )
    lowered = text.lower()

    assert "unknown" not in lowered
    assert "public events" not in lowered
    assert "public volume:" not in lowered
    assert "rank:" not in lowered
