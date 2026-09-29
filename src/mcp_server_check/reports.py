"""Company reports: which options each report takes, and how to get one that fails."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from mcp_server_check.helpers import build_params

_ChoiceT = TypeVar("_ChoiceT", bound="Choice")


class Choice(str, Enum):
    """A str-based Enum for tool arguments, which arrive as plain strings."""

    @classmethod
    def parse(cls: type[_ChoiceT], argument: str, value: str) -> _ChoiceT:
        try:
            return cls(value)
        except ValueError:
            valid = ", ".join(member.value for member in cls)
            raise ValueError(
                f"Unknown {argument}: '{value}'. Valid values: {valid}."
            ) from None


class ReportType(Choice):
    PAYROLL_JOURNAL = "payroll_journal"
    PAYROLL_SUMMARY = "payroll_summary"
    TAX_LIABILITIES = "tax_liabilities"
    CONTRACTOR_PAYMENTS = "contractor_payments"
    CHILD_SUPPORT_PAYMENTS = "child_support_payments"
    W4_EXEMPTION_STATUS = "w4_exemption_status"
    APPLIED_FOR_IDS_DETAILED = "applied_for_ids_detailed"
    W2_PREVIEW = "w2_preview"

    @property
    def has_report_run(self) -> bool:
        return self in _REPORT_RUN_TYPES

    @property
    def takes_date_range(self) -> bool:
        return self in _DATE_RANGE_TYPES

    @property
    def takes_payroll_filter(self) -> bool:
        return self in _PAYROLL_FILTER_TYPES


_REPORT_RUN_TYPES = frozenset({ReportType.PAYROLL_JOURNAL, ReportType.PAYROLL_SUMMARY})

# The rest take a year (w2_preview, w4_exemption_status) or no dates at all.
_DATE_RANGE_TYPES = frozenset(
    {
        ReportType.PAYROLL_JOURNAL,
        ReportType.PAYROLL_SUMMARY,
        ReportType.TAX_LIABILITIES,
        ReportType.CONTRACTOR_PAYMENTS,
        ReportType.CHILD_SUPPORT_PAYMENTS,
    }
)

_PAYROLL_FILTER_TYPES = frozenset(
    {
        ReportType.PAYROLL_JOURNAL,
        ReportType.TAX_LIABILITIES,
        ReportType.CONTRACTOR_PAYMENTS,
    }
)


class ReportFormat(Choice):
    JSON = "json"
    CSV = "csv"


@dataclass(frozen=True)
class Alternative:
    """Another call that gets the data a failed report request asked for."""

    tool: str
    description: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "description": self.description,
            "arguments": self.arguments,
        }


@dataclass(frozen=True)
class ReportRequest:
    company_id: str
    report_type: ReportType
    response_format: ReportFormat = ReportFormat.JSON
    start_date: str | None = None
    end_date: str | None = None
    year: str | None = None
    payroll: list[str] | None = None
    include_contractor_id: bool | None = None

    @classmethod
    def from_arguments(cls, arguments: dict[str, Any]) -> ReportRequest:
        """Build a request from get_company_report arguments; raises ValueError."""
        return cls(
            company_id=arguments.get("company_id", ""),
            report_type=ReportType.parse("report_type", arguments.get("report_type")),
            response_format=ReportFormat.parse(
                "response_format",
                arguments.get("response_format", ReportFormat.JSON.value),
            ),
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            year=arguments.get("year"),
            payroll=arguments.get("payroll"),
            include_contractor_id=arguments.get("include_contractor_id"),
        )

    @property
    def path(self) -> str:
        return f"/companies/{self.company_id}/reports/{self.report_type.value}"

    @property
    def query_params(self) -> dict | None:
        # The reports endpoints read the range as start and end.
        date_range = (
            {"start": self.start_date, "end": self.end_date}
            if self.report_type.takes_date_range
            else {}
        )
        return build_params(
            **date_range,
            year=self.year,
            payroll=self.payroll,
            include_contractor_id=self.include_contractor_id,
        )

    def alternatives(
        self, *, report_runs_available: bool, timed_out: bool
    ) -> list[Alternative]:
        """Return calls that can succeed where this one timed out or was too large.

        A CSV rendering is smaller but takes as long to generate, so it is only
        offered for a result that was too large.
        """
        alternatives = []
        if self.report_type.has_report_run and report_runs_available:
            alternatives.append(
                Alternative(
                    tool="create_report_run",
                    description=(
                        "Generate the report asynchronously, poll get_report_run "
                        "until its status is completed, then call "
                        "download_report_run. additional_columns adds the "
                        "employee, contractor, and payroll ID columns."
                    ),
                    arguments={
                        "company": self.company_id,
                        "report": self.report_type.value,
                        "parameters": {
                            "payday_from": self.start_date,
                            "payday_to": self.end_date,
                        },
                    },
                )
            )
        if not timed_out and self.response_format is ReportFormat.JSON:
            alternatives.append(
                Alternative(
                    tool="get_company_report",
                    description="Return the smaller CSV rendering of the report.",
                    arguments={"response_format": ReportFormat.CSV.value},
                )
            )
        if self.report_type.takes_payroll_filter:
            alternatives.append(
                Alternative(
                    tool="get_company_report",
                    description="Restrict the report to specific payroll IDs.",
                    arguments={"payroll": ["<payroll ID>"]},
                )
            )
        if self.report_type.takes_date_range:
            alternatives.append(
                Alternative(
                    tool="get_company_report",
                    description="Request a shorter start_date to end_date range.",
                )
            )
        return alternatives
