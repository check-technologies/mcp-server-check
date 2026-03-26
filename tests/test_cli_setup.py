"""Tests for the ``check setup`` command."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

from click.testing import CliRunner

from mcp_server_check.cli import cli
from mcp_server_check.cli.setup import (
    BASH_CHECK_PERMISSION,
    CHECK_SENTINEL,
    _render_content,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_settings(directory: str, filename: str, data: dict) -> None:
    claude_dir = os.path.join(directory, ".claude")
    os.makedirs(claude_dir, exist_ok=True)
    with open(os.path.join(claude_dir, filename), "w") as f:
        json.dump(data, f)


def _read_settings(directory: str, filename: str = "settings.json") -> dict:
    with open(os.path.join(directory, ".claude", filename)) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# claude-code target
# ---------------------------------------------------------------------------


def test_claude_code_creates_claude_md():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0
        assert os.path.exists("CLAUDE.md")
        with open("CLAUDE.md") as f:
            content = f.read()
        assert CHECK_SENTINEL in content
        assert "# Check Payroll API" in content


def test_claude_code_appends_to_existing_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("CLAUDE.md", "w") as f:
            f.write("# My Project\n\nExisting instructions.\n")

        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0
        assert "Appended to" in result.output

        with open("CLAUDE.md") as f:
            content = f.read()
        # Original content preserved
        assert content.startswith("# My Project")
        # Check content appended
        assert CHECK_SENTINEL in content
        assert "# Check Payroll API" in content


def test_claude_code_adds_bash_permission():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0
        assert f"Added {BASH_CHECK_PERMISSION}" in result.output

        settings = _read_settings(".")
        assert BASH_CHECK_PERMISSION in settings["permissions"]["allow"]


def test_claude_code_preserves_existing_settings():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_settings(
            ".",
            "settings.json",
            {"permissions": {"allow": ["Read", "Bash(git *)"], "deny": ["Bash(rm *)"]}},
        )

        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0

        settings = _read_settings(".")
        allow = settings["permissions"]["allow"]
        assert "Read" in allow
        assert "Bash(git *)" in allow
        assert BASH_CHECK_PERMISSION in allow
        assert settings["permissions"]["deny"] == ["Bash(rm *)"]


def test_claude_code_skips_permission_if_already_present():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_settings(
            ".",
            "settings.json",
            {"permissions": {"allow": [BASH_CHECK_PERMISSION]}},
        )

        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0
        assert f"Added {BASH_CHECK_PERMISSION}" not in result.output

        # Should not duplicate
        settings = _read_settings(".")
        assert settings["permissions"]["allow"].count(BASH_CHECK_PERMISSION) == 1


def test_claude_code_skips_permission_if_broader_pattern_in_local():
    """A broader pattern like Bash(uv run check:*) in settings.local.json is sufficient."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_settings(
            ".",
            "settings.local.json",
            {"permissions": {"allow": ["Bash(uv run check:*)"]}},
        )

        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0
        assert f"Added {BASH_CHECK_PERMISSION}" not in result.output


# ---------------------------------------------------------------------------
# cursor target
# ---------------------------------------------------------------------------


def test_cursor_creates_cursorrules():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup", "cursor"])
        assert result.exit_code == 0
        assert os.path.exists(".cursorrules")
        with open(".cursorrules") as f:
            content = f.read()
        assert CHECK_SENTINEL in content
        assert "Created" in result.output


def test_cursor_appends_to_existing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open(".cursorrules", "w") as f:
            f.write("Existing cursor rules.\n")

        result = runner.invoke(cli, ["setup", "cursor"])
        assert result.exit_code == 0
        assert "Appended to" in result.output

        with open(".cursorrules") as f:
            content = f.read()
        assert content.startswith("Existing cursor rules.")
        assert CHECK_SENTINEL in content


def test_cursor_does_not_write_settings():
    """The cursor target should not touch .claude/settings.json."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup", "cursor"])
        assert result.exit_code == 0
        assert not os.path.exists(os.path.join(".claude", "settings.json"))


# ---------------------------------------------------------------------------
# agents-md target
# ---------------------------------------------------------------------------


def test_agents_md_creates_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup", "agents-md"])
        assert result.exit_code == 0
        assert os.path.exists("AGENTS.md")
        with open("AGENTS.md") as f:
            content = f.read()
        assert CHECK_SENTINEL in content
        assert "Created" in result.output


def test_agents_md_appends_to_existing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("AGENTS.md", "w") as f:
            f.write("# Agents\n")

        result = runner.invoke(cli, ["setup", "agents-md"])
        assert result.exit_code == 0
        assert "Appended to" in result.output

        with open("AGENTS.md") as f:
            content = f.read()
        assert content.startswith("# Agents")
        assert CHECK_SENTINEL in content


# ---------------------------------------------------------------------------
# Idempotency — safe to run multiple times
# ---------------------------------------------------------------------------


def test_skips_if_file_already_has_check_instructions():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # First run
        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0

        # Second run should skip
        result = runner.invoke(cli, ["setup", "claude-code"])
        assert result.exit_code == 0
        assert "already has Check CLI instructions" in result.output


def test_skip_works_for_all_targets():
    runner = CliRunner()
    for target in ("claude-code", "cursor", "agents-md"):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["setup", target])
            assert result.exit_code == 0

            result = runner.invoke(cli, ["setup", target])
            assert result.exit_code == 0
            assert "already has Check CLI instructions" in result.output


# ---------------------------------------------------------------------------
# uv run prefix when check is not on PATH
# ---------------------------------------------------------------------------


def test_uses_uv_run_prefix_when_not_on_path():
    with patch("mcp_server_check.cli.setup._check_is_on_path", return_value=False):
        content = _render_content()
    assert "uv run check companies list" in content
    assert "\ncheck companies list" not in content


def test_no_prefix_when_on_path():
    with patch("mcp_server_check.cli.setup._check_is_on_path", return_value=True):
        content = _render_content()
    assert "\ncheck companies list" in content
    assert "uv run check" not in content


# ---------------------------------------------------------------------------
# General CLI behavior
# ---------------------------------------------------------------------------


def test_does_not_require_api_key():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup", "claude-code"], env={})
        assert result.exit_code == 0
        assert os.path.exists("CLAUDE.md")


def test_visible_in_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "setup" in result.output


def test_visible_with_toolset_filter():
    """setup should appear even when CHECK_TOOLSETS restricts visible groups."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"], env={"CHECK_TOOLSETS": "companies"})
    assert result.exit_code == 0
    assert "setup" in result.output


def test_custom_directory(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["setup", "claude-code", "--directory", str(tmp_path)])
    assert result.exit_code == 0
    target = tmp_path / "CLAUDE.md"
    assert target.exists()
    assert CHECK_SENTINEL in target.read_text()


def test_setup_help_shows_targets():
    runner = CliRunner()
    result = runner.invoke(cli, ["setup", "--help"])
    assert result.exit_code == 0
    assert "claude-code" in result.output
    assert "cursor" in result.output
    assert "agents-md" in result.output
