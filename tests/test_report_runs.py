"""Tests for report run tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.report_runs import (
    REPORT_RUN_TYPES,
    create_report_run,
    download_report_run,
    get_report_run,
    list_report_runs,
)


def test_report_run_type_count():
    assert len(REPORT_RUN_TYPES) == 2


@pytest.mark.anyio
async def test_create_report_run(mock_api, ctx):
    route = mock_api.post("/report_runs").mock(
        return_value=httpx.Response(
            201,
            json={"id": "run_001", "report": "payroll_journal", "status": "pending"},
        )
    )
    result = await create_report_run(
        ctx,
        report="payroll_journal",
        parameters={
            "payday_from": "2026-01-01",
            "payday_to": "2026-03-31",
            "additional_columns": ["employee.id", "payroll.id"],
        },
        company="com_001",
        metadata={"source": "quarterly-close"},
    )
    assert result["id"] == "run_001"
    assert json.loads(route.calls.last.request.content) == {
        "report": "payroll_journal",
        "parameters": {
            "payday_from": "2026-01-01",
            "payday_to": "2026-03-31",
            "additional_columns": ["employee.id", "payroll.id"],
        },
        "company": "com_001",
        "metadata": {"source": "quarterly-close"},
    }


@pytest.mark.anyio
async def test_create_report_run_rejects_unknown_report(mock_api, ctx):
    route = mock_api.post("/report_runs").mock(
        return_value=httpx.Response(201, json={"id": "run_001"})
    )
    result = await create_report_run(
        ctx,
        report="tax_liabilities",
        parameters={"payday_from": "2026-01-01", "payday_to": "2026-03-31"},
    )
    assert result["error"] is True
    assert "tax_liabilities" in result["detail"]
    # Validation short-circuits before any request reaches the API.
    assert not route.called


@pytest.mark.anyio
async def test_create_report_run_sends_idempotency_key(mock_api, ctx):
    route = mock_api.post("/report_runs").mock(
        return_value=httpx.Response(201, json={"id": "run_001"})
    )
    await create_report_run(
        ctx,
        report="payroll_summary",
        parameters={"payday_from": "2026-01-01", "payday_to": "2026-03-31"},
        idempotency_key="idem-1",
    )
    assert route.calls.last.request.headers["X-Idempotency-Key"] == "idem-1"


@pytest.mark.anyio
async def test_create_report_run_omits_idempotency_key_when_unset(mock_api, ctx):
    route = mock_api.post("/report_runs").mock(
        return_value=httpx.Response(201, json={"id": "run_001"})
    )
    await create_report_run(
        ctx,
        report="payroll_summary",
        parameters={"payday_from": "2026-01-01", "payday_to": "2026-03-31"},
    )
    assert "X-Idempotency-Key" not in route.calls.last.request.headers
    # Unset optionals stay out of the body rather than going up as nulls.
    assert json.loads(route.calls.last.request.content) == {
        "report": "payroll_summary",
        "parameters": {"payday_from": "2026-01-01", "payday_to": "2026-03-31"},
    }


@pytest.mark.anyio
async def test_list_report_runs_summarizes_results(mock_api, ctx):
    mock_api.get("/report_runs").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": "run_001",
                        "report": "payroll_journal",
                        "status": "completed",
                        "company": "com_001",
                        "created_at": "2026-04-01T00:00:00Z",
                        "completed_at": "2026-04-01T00:01:00Z",
                        "parameters": {"payday_from": "2026-01-01"},
                        "row_count": 42,
                    }
                ],
            },
        )
    )
    result = await list_report_runs(ctx)
    assert result["result_count"] == 1
    # run_ results are summarized down to the identifying fields.
    assert result["results"][0] == {
        "id": "run_001",
        "report": "payroll_journal",
        "status": "completed",
        "company": "com_001",
        "created_at": "2026-04-01T00:00:00Z",
        "completed_at": "2026-04-01T00:01:00Z",
    }


@pytest.mark.anyio
async def test_list_report_runs_with_filters(mock_api, ctx):
    route = mock_api.get("/report_runs").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": []}
        )
    )
    await list_report_runs(
        ctx,
        company="com_001",
        report_type="payroll_summary",
        status="completed",
        limit=50,
    )
    params = route.calls.last.request.url.params
    assert params["company"] == "com_001"
    # The list filter is report_type; create takes the same value as report.
    assert params["report_type"] == "payroll_summary"
    assert params["status"] == "completed"
    assert params["limit"] == "50"


@pytest.mark.anyio
async def test_get_report_run(mock_api, ctx):
    mock_api.get("/report_runs/run_001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "run_001",
                "report": "payroll_journal",
                "status": "completed",
                "row_count": 42,
            },
        )
    )
    result = await get_report_run(ctx, report_run_id="run_001")
    assert result["status"] == "completed"
    assert result["row_count"] == 42


@pytest.mark.anyio
async def test_download_report_run(mock_api, ctx):
    mock_api.get("/report_runs/run_001/download").mock(
        return_value=httpx.Response(
            200,
            json={
                "download_url": "https://files.example.com/run_001.zip?sig=abc",
                "expires_at": "2026-04-01T00:02:00Z",
            },
        )
    )
    result = await download_report_run(ctx, report_run_id="run_001")
    assert result["download_url"].startswith("https://files.example.com/")
