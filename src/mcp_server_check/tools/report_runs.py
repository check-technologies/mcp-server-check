"""Report run tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_get,
    check_api_list,
    check_api_post,
)

REPORT_RUN_TYPES = [
    "payroll_journal",
    "payroll_summary",
]


async def list_report_runs(
    ctx: Ctx,
    company: str | None = None,
    report_type: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List payroll journal and payroll summary report runs.

    Args:
        company: Filter to report runs scoped to this company ID.
        report_type: Filter by report: "payroll_journal" or "payroll_summary".
            create_report_run takes the same value as `report`.
        status: Filter by report run status: "generating", "completed", or
            "failed".
        limit: Maximum number of results to return.
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/report_runs",
        params=build_params(
            company=company,
            report_type=report_type,
            status=status,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_report_run(ctx: Ctx, report_run_id: str) -> dict:
    """Get a single report run by ID, including its current status.

    Poll this after create_report_run until `status` is terminal: "completed"
    or "failed". A run still working reads "generating". A completed run is
    ready for download_report_run.

    Args:
        report_run_id: The Check report run ID (e.g. "run_xxxxx").
    """
    return await check_api_get(ctx, f"/report_runs/{report_run_id}")


async def download_report_run(ctx: Ctx, report_run_id: str) -> dict:
    """Get a download link for a completed report run.

    The returned `download_url` is presigned and expires after about 60
    seconds, so fetch it immediately rather than storing it. It points at a ZIP
    archive of CSV files, described by `extension` and `content_type`.

    Args:
        report_run_id: The Check report run ID (e.g. "run_xxxxx").
    """
    return await check_api_get(ctx, f"/report_runs/{report_run_id}/download")


async def create_report_run(
    ctx: Ctx,
    report: str,
    parameters: dict,
    company: str | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Start an asynchronous payroll journal or payroll summary report run.

    Reports are generated in the background: this returns a report run with a
    `run_` ID and a "generating" status. Poll get_report_run until it reaches a
    terminal status, then call download_report_run for the file.

    Args:
        report: The report to generate: "payroll_journal" or "payroll_summary".
        parameters: Report parameters; "payday_from" and "payday_to" are required.
            Both are YYYY-MM-DD and bound the paydays the report covers. Optional
            "additional_columns" is a list of extra columns: both reports accept
            "employee.id" and "contractor.id", and "payroll_journal" also
            accepts "payroll.id".
        company: Company ID to scope the report to. Omit to cover every company
            the API key can reach.
        metadata: Arbitrary key-value object stored on the report run.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    if report not in REPORT_RUN_TYPES:
        return {
            "error": True,
            "detail": (
                f"Unknown report: '{report}'. "
                f"Valid reports: {', '.join(REPORT_RUN_TYPES)}."
            ),
        }
    return await check_api_post(
        ctx,
        "/report_runs",
        data=build_body(
            {"report": report, "parameters": parameters},
            company=company,
            metadata=metadata,
        ),
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_report_runs)
    add_annotated_tool(mcp, get_report_run)
    add_annotated_tool(mcp, download_report_run)
    if not read_only:
        add_annotated_tool(mcp, create_report_run)
