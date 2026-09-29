"""Tests for recovery alternatives in CLI error output."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from click.testing import CliRunner
from mcp_server_check.cli import cli

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


def invoke(*args: str) -> dict:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/companies/com_001/reports/payroll_journal").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = CliRunner().invoke(
            cli, list(args), env={"CHECK_API_KEY": "sk_test_123"}
        )
    assert result.exit_code == 1, "invoke: Expected the command to fail"
    return json.loads(result.stderr)


class TestCLIRecovery:
    def test_timeout_lists_command_lines(self):
        error = invoke(*GET_JOURNAL)

        assert error["timeout"] is True
        assert [alternative["command"] for alternative in error["alternatives"]] == [
            "check report-runs create --company com_001 --report payroll_journal "
            """--parameters '{"payday_from": "2026-09-13", "payday_to": "2026-09-19"}'""",
            "check companies get-report com_001 --report-type payroll_journal "
            "--start-date 2026-09-13 --end-date 2026-09-19 "
            "--payroll '<payroll ID>'",
            "check companies get-report com_001 --report-type payroll_journal "
            "--start-date 2026-09-13 --end-date 2026-09-19",
        ]

    @pytest.mark.parametrize(
        "flag", ["--read-only", None], ids=["read-only flag", "default"]
    )
    def test_read_only_drops_report_run(self, flag):
        error = invoke(*([flag] if flag else []), *GET_JOURNAL)

        commands = [alternative["command"] for alternative in error["alternatives"]]
        assert any(c.startswith("check report-runs create") for c in commands) is (
            flag is None
        )

    def test_other_errors_are_unchanged(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/companies/com_001/reports/payroll_journal").mock(
                return_value=httpx.Response(400, json={"error": "Bad range"})
            )
            result = CliRunner().invoke(
                cli, GET_JOURNAL, env={"CHECK_API_KEY": "sk_test_123"}
            )

        assert json.loads(result.stderr) == {
            "error": True,
            "status_code": 400,
            "detail": {"error": "Bad range"},
        }
