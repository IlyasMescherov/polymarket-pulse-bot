from __future__ import annotations

from bot.main import PUBLIC_BOT_COMMANDS


def test_public_commands_include_traction_commands_without_admin_commands() -> None:
    command_names = {item.command for item in PUBLIC_BOT_COMMANDS}

    assert "today" in command_names
    assert "feedback" in command_names
    assert "admin_stats" not in command_names
    assert "admin_digest" not in command_names
    assert "admin_feedback" not in command_names
