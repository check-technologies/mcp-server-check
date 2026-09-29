"""Tests for the company report domain objects."""

from __future__ import annotations

import pytest
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

    def test_from_arguments_defaults_to_json(self):
        request = ReportRequest.from_arguments(
            {"company_id": "com_001", "report_type": "payroll_summary"}
        )

        assert request == ReportRequest(
            company_id="com_001", report_type=ReportType.PAYROLL_SUMMARY
        )

    def test_from_arguments_rejects_unknown_report(self):
        with pytest.raises(ValueError, match="Unknown report_type"):
            ReportRequest.from_arguments({"report_type": "nonexistent"})


class TestReportRequestAlternatives:
    @staticmethod
    def tools_and_arguments(request, **kwargs):
        return [
            (alternative.tool, alternative.arguments)
            for alternative in request.alternatives(**kwargs)
        ]

    def test_oversized_journal_offers_every_way_out(self):
        request = ReportRequest(
            company_id="com_001",
            report_type=ReportType.PAYROLL_JOURNAL,
            start_date="2026-09-13",
            end_date="2026-09-19",
        )

        assert self.tools_and_arguments(
            request, report_runs_available=True, timed_out=False
        ) == [
            (
                "create_report_run",
                {
                    "company": "com_001",
                    "report": "payroll_journal",
                    "parameters": {
                        "payday_from": "2026-09-13",
                        "payday_to": "2026-09-19",
                    },
                },
            ),
            ("get_company_report", {"response_format": "csv"}),
            ("get_company_report", {"payroll": ["<payroll ID>"]}),
            ("get_company_report", {}),
        ]

    @pytest.mark.parametrize(
        ("report_type", "report_runs_available", "timed_out", "expected_tools"),
        [
            pytest.param(
                ReportType.PAYROLL_SUMMARY,
                False,
                False,
                ["get_company_report", "get_company_report"],
                id="report runs hidden in read-only mode",
            ),
            pytest.param(
                ReportType.PAYROLL_SUMMARY,
                True,
                True,
                ["create_report_run", "get_company_report"],
                id="csv not offered for a timeout",
            ),
            pytest.param(
                ReportType.TAX_LIABILITIES,
                True,
                False,
                ["get_company_report"] * 3,
                id="no report run for tax liabilities",
            ),
            pytest.param(
                ReportType.APPLIED_FOR_IDS_DETAILED,
                True,
                True,
                [],
                id="nothing to narrow",
            ),
        ],
    )
    def test_alternatives_follow_report_and_availability(
        self, report_type, report_runs_available, timed_out, expected_tools
    ):
        request = ReportRequest(company_id="com_001", report_type=report_type)

        alternatives = request.alternatives(
            report_runs_available=report_runs_available, timed_out=timed_out
        )

        assert [alternative.tool for alternative in alternatives] == expected_tools

    def test_csv_request_is_not_told_to_use_csv(self):
        request = ReportRequest(
            company_id="com_001",
            report_type=ReportType.TAX_LIABILITIES,
            response_format=ReportFormat.CSV,
        )

        alternatives = self.tools_and_arguments(
            request, report_runs_available=True, timed_out=False
        )

        assert ("get_company_report", {"response_format": "csv"}) not in alternatives
