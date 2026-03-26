"""Tests for document tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.documents import (
    create_company_provided_document,
    get_company_tax_document,
    list_company_authorization_documents,
    list_company_provided_documents,
    list_company_tax_documents,
    list_contractor_tax_documents,
    list_employee_tax_documents,
    list_setup_documents,
)


@pytest.mark.anyio
async def test_list_company_tax_documents(mock_api, ctx):
    mock_api.get("/company_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ctd_001"}]},
        )
    )
    result = await list_company_tax_documents(ctx)
    assert result["results"] == [{"id": "ctd_001"}]


@pytest.mark.anyio
async def test_get_company_tax_document(mock_api, ctx):
    mock_api.get("/company_tax_documents/ctd_001").mock(
        return_value=httpx.Response(200, json={"id": "ctd_001"})
    )
    result = await get_company_tax_document(ctx, document_id="ctd_001")
    assert result["id"] == "ctd_001"


@pytest.mark.anyio
async def test_list_employee_tax_documents(mock_api, ctx):
    mock_api.get("/employee_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "etd_001"}]},
        )
    )
    result = await list_employee_tax_documents(ctx)
    assert result["results"] == [{"id": "etd_001"}]


@pytest.mark.anyio
async def test_list_setup_documents(mock_api, ctx):
    mock_api.get("/setup_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "sd_001"}]},
        )
    )
    result = await list_setup_documents(ctx)
    assert result["results"] == [{"id": "sd_001"}]


@pytest.mark.anyio
async def test_list_company_tax_documents_with_filters(mock_api, ctx):
    mock_api.get("/company_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ctd_001"}]},
        )
    )
    result = await list_company_tax_documents(
        ctx, company="com_123", year=2025, quarter="Q1"
    )
    assert result["results"] == [{"id": "ctd_001"}]
    req = mock_api.get("/company_tax_documents").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["year"] == "2025"
    assert req.url.params["quarter"] == "Q1"


@pytest.mark.anyio
async def test_list_company_authorization_documents_with_filters(mock_api, ctx):
    mock_api.get("/company_authorization_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cad_001"}]},
        )
    )
    result = await list_company_authorization_documents(
        ctx, company="com_123", year=2025
    )
    assert result["results"] == [{"id": "cad_001"}]
    req = mock_api.get("/company_authorization_documents").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["year"] == "2025"


@pytest.mark.anyio
async def test_list_employee_tax_documents_with_filters(mock_api, ctx):
    mock_api.get("/employee_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "etd_001"}]},
        )
    )
    result = await list_employee_tax_documents(
        ctx, employee="emp_123", company="com_456", year=2025
    )
    assert result["results"] == [{"id": "etd_001"}]
    req = mock_api.get("/employee_tax_documents").calls.last.request
    assert req.url.params["employee"] == "emp_123"
    assert req.url.params["company"] == "com_456"
    assert req.url.params["year"] == "2025"


@pytest.mark.anyio
async def test_list_contractor_tax_documents_with_filters(mock_api, ctx):
    mock_api.get("/contractor_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ctd_001"}]},
        )
    )
    result = await list_contractor_tax_documents(
        ctx, contractor="ctr_123", company="com_456", year=2025
    )
    assert result["results"] == [{"id": "ctd_001"}]
    req = mock_api.get("/contractor_tax_documents").calls.last.request
    assert req.url.params["contractor"] == "ctr_123"
    assert req.url.params["company"] == "com_456"
    assert req.url.params["year"] == "2025"


@pytest.mark.anyio
async def test_list_setup_documents_with_filters(mock_api, ctx):
    mock_api.get("/setup_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "sd_001"}]},
        )
    )
    result = await list_setup_documents(ctx, company="com_123")
    assert result["results"] == [{"id": "sd_001"}]
    req = mock_api.get("/setup_documents").calls.last.request
    assert req.url.params["company"] == "com_123"


@pytest.mark.anyio
async def test_list_company_provided_documents_with_filters(mock_api, ctx):
    mock_api.get("/company_provided_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cpd_001"}]},
        )
    )
    result = await list_company_provided_documents(ctx, company="com_123")
    assert result["results"] == [{"id": "cpd_001"}]
    req = mock_api.get("/company_provided_documents").calls.last.request
    assert req.url.params["company"] == "com_123"


@pytest.mark.anyio
async def test_create_company_provided_document(mock_api, ctx):
    mock_api.post("/company_provided_documents").mock(
        return_value=httpx.Response(201, json={"id": "cpd_new"})
    )
    result = await create_company_provided_document(ctx, company="com_001")
    assert result["id"] == "cpd_new"
