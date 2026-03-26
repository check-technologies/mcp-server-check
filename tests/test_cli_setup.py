"""Tests for the ``check setup`` command."""

from __future__ import annotations

import os

from click.testing import CliRunner

from mcp_server_check.cli import cli
from mcp_server_check.cli.setup import CLAUDE_MD_CONTENT


def test_setup_creates_claude_md():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        assert os.path.exists("CLAUDE.md")
        with open("CLAUDE.md") as f:
            assert f.read() == CLAUDE_MD_CONTENT


def test_setup_custom_filename():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup", "--file", "AGENTS.md"])
        assert result.exit_code == 0
        assert os.path.exists("AGENTS.md")
        assert not os.path.exists("CLAUDE.md")
        with open("AGENTS.md") as f:
            assert f.read() == CLAUDE_MD_CONTENT


def test_setup_prompts_before_overwrite():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("CLAUDE.md", "w") as f:
            f.write("existing content")

        # Decline overwrite
        result = runner.invoke(cli, ["setup"], input="n\n")
        assert result.exit_code != 0
        with open("CLAUDE.md") as f:
            assert f.read() == "existing content"

        # Accept overwrite
        result = runner.invoke(cli, ["setup"], input="y\n")
        assert result.exit_code == 0
        with open("CLAUDE.md") as f:
            assert f.read() == CLAUDE_MD_CONTENT


def test_setup_force_overwrites():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("CLAUDE.md", "w") as f:
            f.write("existing content")

        result = runner.invoke(cli, ["setup", "--force"])
        assert result.exit_code == 0
        with open("CLAUDE.md") as f:
            assert f.read() == CLAUDE_MD_CONTENT


def test_setup_does_not_require_api_key():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["setup"], env={})
        assert result.exit_code == 0
        assert os.path.exists("CLAUDE.md")


def test_setup_visible_in_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "setup" in result.output


def test_setup_visible_with_toolset_filter():
    """setup should appear even when CHECK_TOOLSETS restricts visible groups."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"], env={"CHECK_TOOLSETS": "companies"})
    assert result.exit_code == 0
    assert "setup" in result.output


def test_setup_custom_directory(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["setup", "--directory", str(tmp_path)])
    assert result.exit_code == 0
    target = tmp_path / "CLAUDE.md"
    assert target.exists()
    assert target.read_text() == CLAUDE_MD_CONTENT
