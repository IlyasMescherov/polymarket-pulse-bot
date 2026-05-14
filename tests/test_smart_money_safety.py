from __future__ import annotations

from pathlib import Path


def test_smart_money_public_files_do_not_use_banned_promotional_phrases() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "bot" / "handlers" / "smart_money.py",
        root / "bot" / "services" / "smart_money_analyzer.py",
        root / "docs" / "SMART_MONEY_ANALYTICS.md",
        root / "README.md",
        root / "BUILDER_SUBMISSION_TEXT.md",
        root / "SUBMISSION_CHECKLIST.md",
        root / "landing" / "index.html",
    ]
    text = "\n".join(path.read_text() for path in paths).lower()

    for phrase in (
        "insider",
        "inside information",
        "guaranteed",
        "guaranteed profit",
        "buy now",
        "sell now",
        "copy this trader",
        "entry signal",
        "trade signal",
        "sure profit",
        "alpha leak",
        "private info",
    ):
        assert phrase not in text


def test_smart_money_safety_language_is_research_only() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs" / "SMART_MONEY_ANALYTICS.md").read_text().lower()

    assert "research-only" in text or "research only" in text
    assert "no trade execution" in text
    assert "no wallet connection" in text
