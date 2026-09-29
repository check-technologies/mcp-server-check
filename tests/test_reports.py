"""Tests for the company report domain objects."""

from __future__ import annotations

import pytest
from mcp_server_check.recovery import Alternative, Failure, Hint
from mcp_server_check.reports import (
    ReportFormat,
    ReportRequest,
    ReportType,
)


class TestChoice:
    def test_parse_returns_member(self):
        assert ReportType.parse("report_type", "tax_liabilities") is (
            ReportType.TAX_LIABILITIES
        )

    def test_parse_names_argument_and_valid_values(self):
        with pytest.raises(ValueError) as excinfo:
            ReportFormat.parse("response_format", "xml")

        assert str(excinfo.value) == (
            "Unknown response_format: 'xml'. Valid values: json, csv."
        )


class TestReportRequest:
    def test_date_range_sent_as_start_and_end(self):
        request = ReportRequest(
            company_id="com_001",
            report_type=ReportType.TAX_LIABILITIES,
            start_date="2026-04-01",
            end_date="2026-06-30",
            payroll=["pay_001"],
        )

        assert request.path == "/companies/com_001/reports/tax_liabilities"
        assert request.query_params == {
            "start": "2026-04-01",
            "end": "2026-06-30",
            "payroll": ["pay_001"],
        }

    def test_date_range_dropped_for_year_reports(self):
        request = ReportRequest(
            company_id="com_001",
            report_type=ReportType.W2_PREVIEW,
            start_date="2026-01-01",
            year="2025",
        )

        assert request.query_params == {"year": "2025"}

    def test_parse_defaults_to_json(self):
        request = ReportRequest.parse(
            company_id="com_001", report_type="payroll_summary"
        )

        assert request == ReportRequest(
            company_id="com_001", report_type=ReportType.PAYROLL_SUMMARY
        )

    def test_parse_rejects_unknown_report(self):
        with pytest.raises(ValueError, match="Unknown report_type"):
            ReportRequest.parse(company_id="com_001", report_type="nonexistent")


def kinds(remedies):
    return [
        remedy.tool if isinstance(remedy, Alternative) else "hint"
        for remedy in remedies
    ]


class TestReportRequestRemedies:
    def test_oversized_journal_offers_every_way_out(self):
        request = ReportRequest(
            company_id="com_001",
            report_type=ReportType.PAYROLL_JOURNAL,
            start_date="2026-09-13",
            end_date="2026-09-19",
        )

        remedies = request.remedies(Failure.TOO_LARGE)

        assert remedies[:2] == [
            Alternative(
                tool="create_report_run",
                description=remedies[0].description,
                arguments={
                    "company": "com_001",
                    "report": "payroll_journal",
                    "parameters": {
                        "payday_from": "2026-09-13",
                        "payday_to": "2026-09-19",
                    },
                },
            ),
            Alternative(
                tool="get_company_report",
                description="Return the smaller CSV rendering of the report.",
                arguments={"response_format": "csv"},
            ),
        ]
        assert remedies[2:] == [
            Hint("Pass the IDs of the payrolls you need as payroll."),
            Hint("Request a shorter start_date to end_date range."),
        ]

    def test_report_run_without_dates_is_a_hint(self):
        request = ReportRequest(
            company_id="com_001", report_type=ReportType.PAYROLL_SUMMARY
        )

        report_run = request.remedies(Failure.TIMED_OUT)[0]

        assert isinstance(report_run, Hint)
        assert "payday_from and payday_to" in report_run.description

    @pytest.mark.parametrize(
        ("report_type", "response_format", "failure", "expected"),
        [
            pytest.param(
                ReportType.PAYROLL_SUMMARY,
                ReportFormat.JSON,
                Failure.TIMED_OUT,
                ["create_report_run", "hint"],
                id="csv not offered for a timeout",
            ),
            pytest.param(
                ReportType.TAX_LIABILITIES,
                ReportFormat.JSON,
                Failure.TOO_LARGE,
                ["get_company_report", "hint", "hint"],
                id="no report run for tax liabilities",
            ),
            pytest.param(
                ReportType.TAX_LIABILITIES,
                ReportFormat.CSV,
                Failure.TOO_LARGE,
                ["hint", "hint"],
                id="csv request not told to use csv",
            ),
            pytest.param(
                ReportType.APPLIED_FOR_IDS_DETAILED,
                ReportFormat.JSON,
                Failure.TIMED_OUT,
                [],
                id="nothing to narrow",
            ),
        ],
    )
    def test_remedies_follow_report_and_failure(
        self, report_type, response_format, failure, expected
    ):
        request = ReportRequest(
            company_id="com_001",
            report_type=report_type,
            response_format=response_format,
            start_date="2026-01-01",
            end_date="2026-03-31",
        )

        assert kinds(request.remedies(failure)) == expected

    @pytest.mark.parametrize(
        "arguments",
        [
            {"company_id": "com_001", "report_type": "nope"},
            {"report_type": "tax_liabilities"},
        ],
        ids=["unknown report", "missing company"],
    )
    def test_recover_ignores_invalid_arguments(self, arguments):
        assert ReportRequest.recover(arguments, Failure.TIMED_OUT) == []
