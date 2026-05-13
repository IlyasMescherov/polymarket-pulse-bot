from __future__ import annotations

from bot.services.market_analyzer import is_sharp_move, probability_delta


def test_probability_delta() -> None:
    assert probability_delta(0.2, 0.35) == 0.14999999999999997


def test_is_sharp_move_uses_absolute_threshold() -> None:
    assert is_sharp_move(0.2, 0.31, 0.10)
    assert is_sharp_move(0.8, 0.69, 0.10)
    assert not is_sharp_move(0.2, 0.25, 0.10)
    assert not is_sharp_move(None, 0.25, 0.10)

