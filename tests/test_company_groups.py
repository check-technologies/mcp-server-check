"""Tests for company group tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.company_groups import (
    add_company_group_companies,
    add_company_group_users,
    create_company_group,
    get_company_group,
    list_company_groups,
    remove_company_group_companies,
    remove_company_group_users,
    update_company_group,
)

GROUP = {"id": "pcg_1", "name": "West", "companies": ["com_1"], "users": ["usr_1"]}


@pytest.mark.anyio
async def test_list_company_groups(mock_api, ctx):
    mock_api.get("/company_groups").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": [GROUP]}
        )
    )
    result = await list_company_groups(ctx)
    assert result["results"] == [GROUP]


@pytest.mark.anyio
async def test_get_company_group(mock_api, ctx):
    mock_api.get("/company_groups/pcg_1").mock(
        return_value=httpx.Response(200, json=GROUP)
    )
    result = await get_company_group(ctx, "pcg_1")
    assert result["users"] == ["usr_1"]


@pytest.mark.anyio
async def test_create_company_group(mock_api, ctx):
    route = mock_api.post("/company_groups").mock(
        return_value=httpx.Response(201, json=GROUP)
    )
    await create_company_group(
        ctx, "West", companies=["com_1"], users=["usr_1"], idempotency_key="idem-1"
    )
    request = route.calls.last.request
    assert json.loads(request.content) == {
        "name": "West",
        "companies": ["com_1"],
        "users": ["usr_1"],
    }
    assert request.headers["X-Idempotency-Key"] == "idem-1"


@pytest.mark.anyio
async def test_update_company_group_omits_unsent_membership(mock_api, ctx):
    """Only sent fields go out, so omitted membership stays as it is."""
    route = mock_api.patch("/company_groups/pcg_1").mock(
        return_value=httpx.Response(200, json=GROUP)
    )
    await update_company_group(ctx, "pcg_1", name="East")
    assert json.loads(route.calls.last.request.content) == {"name": "East"}


@pytest.mark.anyio
async def test_update_company_group_sends_empty_list(mock_api, ctx):
    """An empty list is a real value: it clears that membership."""
    route = mock_api.patch("/company_groups/pcg_1").mock(
        return_value=httpx.Response(200, json=GROUP)
    )
    await update_company_group(ctx, "pcg_1", users=[])
    assert json.loads(route.calls.last.request.content) == {"users": []}


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("tool", "action", "field"),
    [
        (add_company_group_companies, "add_companies", "companies"),
        (remove_company_group_companies, "remove_companies", "companies"),
        (add_company_group_users, "add_users", "users"),
        (remove_company_group_users, "remove_users", "users"),
    ],
)
async def test_membership_actions(mock_api, ctx, tool, action, field):
    route = mock_api.post(f"/company_groups/pcg_1/{action}").mock(
        return_value=httpx.Response(200, json=GROUP)
    )
    result = await tool(ctx, "pcg_1", ["id_1", "id_2"], idempotency_key="idem-1")
    assert result["id"] == "pcg_1"
    request = route.calls.last.request
    assert json.loads(request.content) == {field: ["id_1", "id_2"]}
    assert request.headers["X-Idempotency-Key"] == "idem-1"
