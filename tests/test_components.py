"""Tests for component tools."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.tools.components import (
    COMPANY_COMPONENTS,
    CONTRACTOR_COMPONENTS,
    EMPLOYEE_COMPONENTS,
    create_component,
    list_component_types,
)

# --- list_component_types ---


@pytest.mark.anyio
async def test_list_all_component_types(mock_api, ctx):
    result = await list_component_types(ctx)
    assert "company" in result
    assert "employee" in result
    assert "contractor" in result
    assert result["company"]["component_types"] == COMPANY_COMPONENTS
    assert result["employee"]["component_types"] == EMPLOYEE_COMPONENTS
    assert result["contractor"]["component_types"] == CONTRACTOR_COMPONENTS


@pytest.mark.anyio
async def test_list_component_types_filtered(mock_api, ctx):
    result = await list_component_types(ctx, entity_type="employee")
    assert result["entity_type"] == "employee"
    assert result["component_types"] == EMPLOYEE_COMPONENTS


@pytest.mark.anyio
async def test_list_component_types_invalid_entity(mock_api, ctx):
    result = await list_component_types(ctx, entity_type="invalid")
    assert result["error"] is True
    assert "Unknown entity_type" in result["detail"]


# --- create_component ---


@pytest.mark.anyio
async def test_create_company_component(mock_api, ctx):
    mock_api.post("/companies/com_001/components/run_payroll").mock(
        return_value=httpx.Response(200, json={"url": "https://embed.checkhq.com/..."})
    )
    result = await create_component(
        ctx, entity_type="company", entity_id="com_001", component_type="run_payroll"
    )
    assert "url" in result


@pytest.mark.anyio
async def test_create_employee_component(mock_api, ctx):
    mock_api.post("/employees/emp_001/components/tax_setup").mock(
        return_value=httpx.Response(200, json={"url": "https://embed.checkhq.com/..."})
    )
    result = await create_component(
        ctx, entity_type="employee", entity_id="emp_001", component_type="tax_setup"
    )
    assert "url" in result


@pytest.mark.anyio
async def test_create_contractor_component(mock_api, ctx):
    mock_api.post("/contractors/ctr_001/components/tax_documents").mock(
        return_value=httpx.Response(200, json={"url": "https://embed.checkhq.com/..."})
    )
    result = await create_component(
        ctx,
        entity_type="contractor",
        entity_id="ctr_001",
        component_type="tax_documents",
    )
    assert "url" in result


@pytest.mark.anyio
async def test_create_component_with_data(mock_api, ctx):
    mock_api.post("/companies/com_001/components/details").mock(
        return_value=httpx.Response(200, json={"url": "https://embed.checkhq.com/..."})
    )
    result = await create_component(
        ctx,
        entity_type="company",
        entity_id="com_001",
        component_type="details",
        data={"theme": "dark"},
    )
    assert "url" in result


@pytest.mark.anyio
async def test_create_component_invalid_entity_type(mock_api, ctx):
    result = await create_component(
        ctx, entity_type="invalid", entity_id="x", component_type="tax_setup"
    )
    assert result["error"] is True
    assert "Unknown entity_type" in result["detail"]


@pytest.mark.anyio
async def test_create_component_invalid_component_type(mock_api, ctx):
    result = await create_component(
        ctx,
        entity_type="company",
        entity_id="com_001",
        component_type="nonexistent",
    )
    assert result["error"] is True
    assert "Unknown component_type" in result["detail"]
    assert "nonexistent" in result["detail"]


def test_component_type_counts():
    """Verify expected component type counts."""
    assert len(COMPANY_COMPONENTS) == 25
    assert len(EMPLOYEE_COMPONENTS) == 9
    assert len(CONTRACTOR_COMPONENTS) == 1
