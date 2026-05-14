from __future__ import annotations

from pathlib import Path

from bot.services.health_server import landing_asset_path


def test_static_landing_page_exists_and_has_safety_scope() -> None:
    root = Path(__file__).resolve().parents[1]
    index = root / "landing" / "index.html"
    styles = root / "landing" / "styles.css"

    assert index.exists()
    assert styles.exists()

    text = index.read_text()
    assert "PulseMarket AI" in text
    assert "Smart Money Radar" in text
    assert "No trading" in text
    assert "https://t.me/PulseMarketAIBot" in text


def test_health_server_can_resolve_landing_assets() -> None:
    assert landing_asset_path("index.html").exists()
    assert landing_asset_path("styles.css").exists()
