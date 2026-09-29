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


class TestReportRequestRemedies:
    @staticmethod
    def journal(**overrides) -> ReportRequest:
        fields = {"start_date": "2026-09-13", "end_date": "2026-09-19", **overrides}
        return ReportRequest(
            company_id="com_001", report_type=ReportType.PAYROLL_JOURNAL, **fields
        )

    def test_oversized_journal_offers_every_way_out(self):
        remedies = self.journal().remedies(Failure.TOO_LARGE)

        assert [(r.tool, r.arguments) for r in remedies] == [
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
            ("get_company_report", ("payroll",)),
            ("get_company_report", ("start_date", "end_date")),
        ]
        assert [type(r) for r in remedies] == [Alternative, Alternative, Hint, Hint]

    @pytest.mark.parametrize(
        ("overrides", "parameters"),
        [
            pytest.param(
                {"payroll": ["prl_1"]}, {"payroll": "prl_1"}, id="one payroll"
            ),
            pytest.param(
                {"include_contractor_id": True},
                {"additional_columns": ["contractor.id"]},
                id="contractor column",
            ),
        ],
    )
    def test_report_run_keeps_the_request_scope(self, overrides, parameters):
        report_run = self.journal(**overrides).remedies(Failure.TIMED_OUT)[0]

        assert report_run.arguments["parameters"] == {
            "payday_from": "2026-09-13",
            "payday_to": "2026-09-19",
            **parameters,
        }

    @pytest.mark.parametrize(
        ("overrides", "needs"),
        [
            pytest.param(
                {"start_date": None, "end_date": None}, "payday range", id="no dates"
            ),
            pytest.param(
                {"payroll": ["prl_1", "prl_2"]}, "one per payroll", id="many payrolls"
            ),
        ],
    )
    def test_report_run_that_cannot_be_built_is_a_hint(self, overrides, needs):
        report_run = self.journal(**overrides).remedies(Failure.TIMED_OUT)[0]

        assert report_run == Hint(
            tool="create_report_run",
            description=report_run.description,
            arguments=("parameters",),
        )
        assert needs in report_run.description

    def test_no_hint_to_narrow_what_the_request_did_not_set(self):
        request = ReportRequest(
            company_id="com_001",
            report_type=ReportType.PAYROLL_JOURNAL,
            payroll=["prl_1"],
        )

        assert request.remedies(Failure.TIMED_OUT) == [
            request.remedies(Failure.TIMED_OUT)[0]
        ]

    @pytest.mark.parametrize(
        ("report_type", "response_format", "failure", "expected"),
        [
            pytest.param(
                ReportType.PAYROLL_SUMMARY,
                ReportFormat.JSON,
                Failure.TIMED_OUT,
                [Alternative, Hint],
                id="csv not offered for a timeout",
            ),
            pytest.param(
                ReportType.TAX_LIABILITIES,
                ReportFormat.JSON,
                Failure.TOO_LARGE,
                [Alternative, Hint, Hint],
                id="no report run for tax liabilities",
            ),
            pytest.param(
                ReportType.TAX_LIABILITIES,
                ReportFormat.CSV,
                Failure.TOO_LARGE,
                [Hint, Hint],
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

        assert [type(r) for r in request.remedies(failure)] == expected

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
