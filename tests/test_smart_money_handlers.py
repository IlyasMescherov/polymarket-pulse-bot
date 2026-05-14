from __future__ import annotations

from bot.handlers.smart_money import (
    _active_markets_empty_state,
    _format_public_trader_card,
    _invalid_wallet_message,
    _public_traders_empty_state,
    _public_traders_intro,
    _smart_intro,
    _track_wallet_prompt,
    _unusual_empty_state,
    _wallet_saved_text,
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
    assert "0x1234567890abcdef1234567890abcdef12345678" in prompt
    assert "Never send a private key or seed phrase." in prompt
    assert "It should start with 0x and contain 42 characters." in invalid


def test_wallet_prompt_has_ru_copy() -> None:
    prompt = _track_wallet_prompt("ru")
    invalid = _invalid_wallet_message("ru")

    assert "Отправь полный публичный адрес кошелька." in prompt
    assert "Никогда не отправляй private key или seed phrase." in prompt
    assert "Адрес должен начинаться с 0x и содержать 42 символа." in invalid


def test_public_traders_does_not_show_unknown_fields() -> None:
    text = _format_public_trader_card(
        TraderScore(
            wallet_address=None,
            display_name=None,
            score=13,
            label="Limited public data",
            volume=None,
            trades_count=None,
            rank=None,
        ),
        1,
        "en",
    )
    lowered = text.lower()

    assert "unknown" not in lowered
    assert "public events" not in lowered
    assert "public volume:" not in lowered
    assert "rank:" not in lowered


def test_public_trader_card_localizes_wallet_label() -> None:
    trader = TraderScore(
        wallet_address="0x1111111111111111111111111111111111111111",
        display_name=None,
        score=80,
        label="High public activity",
        volume=1_000_000,
        trades_count=120,
        rank=3,
    )
    en = _format_public_trader_card(trader, 1, "en")
    ru = _format_public_trader_card(trader, 1, "ru")

    assert "Wallet:" in en
    assert "0x1111…1111" in en
    assert "Кошелёк:" in ru
    assert "Оценка участника" in ru
    assert "Публичные сделки: 120" in ru


def test_smart_money_texts_do_not_mix_language_on_key_screens() -> None:
    ru_text = "\n".join(
        [
            _smart_intro("ru"),
            _unusual_empty_state("ru"),
            _active_markets_empty_state("ru"),
            _track_wallet_prompt("ru"),
            _invalid_wallet_message("ru"),
            _public_traders_intro("ru"),
            _public_traders_empty_state("ru"),
            _wallet_saved_text(
                created=True,
                wallet_address="0x1111111111111111111111111111111111111111",
                tracked_count=1,
                language="ru",
            ),
        ]
    )
    en_text = "\n".join(
        [
            _smart_intro("en"),
            _unusual_empty_state("en"),
            _active_markets_empty_state("en"),
            _track_wallet_prompt("en"),
            _invalid_wallet_message("en"),
            _public_traders_intro("en"),
            _public_traders_empty_state("en"),
            _wallet_saved_text(
                created=True,
                wallet_address="0x1111111111111111111111111111111111111111",
                tracked_count=1,
                language="en",
            ),
        ]
    )

    assert "Research only" not in ru_text
    assert "No trade execution" not in ru_text
    assert "Track Public Wallet" not in ru_text
    assert "Для анализа" not in en_text
    assert "Без сделок" not in en_text
    assert "Кошелёк" not in en_text


def test_wallet_saved_text_handles_duplicates() -> None:
    en = _wallet_saved_text(
        created=False,
        wallet_address="0x1111111111111111111111111111111111111111",
        tracked_count=1,
        language="en",
    )
    ru = _wallet_saved_text(
        created=False,
        wallet_address="0x1111111111111111111111111111111111111111",
        tracked_count=1,
        language="ru",
    )

    assert "Wallet is already tracked." in en
    assert "Кошелёк уже отслеживается." in ru
