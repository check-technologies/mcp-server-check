"""Company reports: which options each report takes, and how to get one that fails."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from mcp_server_check.helpers import build_params
from mcp_server_check.recovery import Alternative, Failure, Hint, Remedy

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
    def parse(
        cls,
        *,
        company_id: str,
        report_type: str,
        response_format: str = ReportFormat.JSON.value,
        start_date: str | None = None,
        end_date: str | None = None,
        year: str | None = None,
        payroll: list[str] | None = None,
        include_contractor_id: bool | None = None,
    ) -> ReportRequest:
        """Build a request from get_company_report arguments; raises ValueError."""
        return cls(
            company_id=company_id,
            report_type=ReportType.parse("report_type", report_type),
            response_format=ReportFormat.parse("response_format", response_format),
            start_date=start_date,
            end_date=end_date,
            year=year,
            payroll=payroll,
            include_contractor_id=include_contractor_id,
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

    @classmethod
    def recover(cls, arguments: dict[str, Any], failure: Failure) -> list[Remedy]:
        """Remedy provider for get_company_report.

        A report's cost depends on how much payroll data falls in its range,
        mostly company size, so a request that is too big cannot be spotted up
        front: a full-year journal returns in seconds for most companies and
        times out for the largest. Reports are tried synchronously, and these
        remedies are offered once one fails.
        """
        try:
            request = cls.parse(**arguments)
        except (TypeError, ValueError):
            return []
        return request.remedies(failure)

    def remedies(self, failure: Failure) -> list[Remedy]:
        """Return what can succeed where this request failed.

        A CSV rendering is smaller but takes as long to generate, so it is only
        offered for a result that was too large.
        """
        remedies: list[Remedy] = []
        if self.report_type.has_report_run:
            remedies.append(self._report_run_remedy())
        if failure is Failure.TOO_LARGE and self.response_format is ReportFormat.JSON:
            remedies.append(
                Alternative(
                    tool="get_company_report",
                    description="Return the smaller CSV rendering of the report.",
                    arguments={"response_format": ReportFormat.CSV.value},
                )
            )
        if self.report_type.takes_payroll_filter:
            remedies.append(Hint("Pass the IDs of the payrolls you need as payroll."))
        if self.report_type.takes_date_range:
            remedies.append(Hint("Request a shorter start_date to end_date range."))
        return remedies

    def _report_run_remedy(self) -> Remedy:
        description = (
            "Generate the report asynchronously with create_report_run, poll "
            "get_report_run until its status is completed, then call "
            "download_report_run. additional_columns adds the employee, "
            "contractor, and payroll ID columns."
        )
        if self.start_date is None or self.end_date is None:
            return Hint(f"{description} It needs payday_from and payday_to dates.")
        return Alternative(
            tool="create_report_run",
            description=description,
            arguments={
                "company": self.company_id,
                "report": self.report_type.value,
                "parameters": {
                    "payday_from": self.start_date,
                    "payday_to": self.end_date,
                },
            },
        )
