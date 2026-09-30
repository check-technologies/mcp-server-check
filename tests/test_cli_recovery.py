"""Tests for recovery remedies in CLI error output."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from click.testing import CliRunner
from mcp_server_check.cli import cli
from mcp_server_check.cli.recovery import CommandLines

BASE_URL = "https://sandbox.checkhq.com"
GET_JOURNAL = [
    "companies",
    "get-report",
    "com_001",
    "--report-type",
    "payroll_journal",
    "--start-date",
    "2026-09-13",
    "--end-date",
    "2026-09-19",
]


@pytest.fixture
def invoke():
    def run(*args: str, response: httpx.Response | Exception):
        with respx.mock(base_url=BASE_URL) as mock:
            route = mock.get("/companies/com_001/reports/payroll_journal")
            if isinstance(response, Exception):
                route.mock(side_effect=response)
            else:
                route.mock(return_value=response)
            return CliRunner().invoke(
                cli, list(args), env={"CHECK_API_KEY": "sk_test_123"}
            )

    return run


@pytest.fixture
def make_command_lines():
    def make(*args: str) -> CommandLines:
        return CommandLines(cli.make_context("check", [*args, "companies"]))

    return make


class TestCLIRecovery:
    def test_timeout_lists_command_lines_and_hints(self, invoke):
        result = invoke(*GET_JOURNAL, response=httpx.ReadTimeout("timed out"))

        error = json.loads(result.stderr)
        assert result.exit_code == 1
        assert error["timeout"] is True
        assert [a["command"] for a in error["alternatives"]] == [
            "check report-runs create --report payroll_journal --parameters "
            """'{"payday_from": "2026-09-13", "payday_to": "2026-09-19"}' """
            "--company com_001"
        ]
        assert error["hints"] == [
            {
                "command": "check companies get-report",
                "description": "Restrict the report to the payrolls you need.",
                "options": ["--payroll"],
            },
            {
                "command": "check companies get-report",
                "description": "Request a shorter date range.",
                "options": ["--start-date", "--end-date"],
            },
        ]

    def test_read_only_keeps_only_hints(self, invoke):
        result = invoke(
            "--read-only", *GET_JOURNAL, response=httpx.ReadTimeout("timed out")
        )

        error = json.loads(result.stderr)
        assert error["alternatives"] == []
        assert len(error["hints"]) == 2

    def test_other_errors_are_unchanged(self, invoke):
        result = invoke(
            *GET_JOURNAL, response=httpx.Response(400, json={"error": "Bad range"})
        )

        assert json.loads(result.stderr) == {
            "error": True,
            "status_code": 400,
            "detail": {"error": "Bad range"},
        }


class TestCommandLines:
    def test_renders_positional_first_then_options_in_command_order(
        self, make_command_lines
    ):
        command_lines = make_command_lines()

        line = command_lines.command_line(
            "get_company_report",
            {
                "payroll": ["pay_001", "pay_002"],
                "include_contractor_id": False,
                "start_date": None,
                "report_type": "tax_liabilities",
                "company_id": "com 001",
            },
        )

        assert line == (
            "check companies get-report 'com 001' --report-type tax_liabilities "
            "--payroll pay_001,pay_002 --no-include-contractor-id"
        )

    @pytest.mark.parametrize(
        ("args", "expected"), [((), True), (("--read-only",), False)]
    )
    def test_is_available_follows_read_only(self, make_command_lines, args, expected):
        assert make_command_lines(*args).is_available("create_report_run") is expected

    def test_unknown_tool_is_unavailable(self, make_command_lines):
        assert make_command_lines().is_available("no_such_tool") is False
