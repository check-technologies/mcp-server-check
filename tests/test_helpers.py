"""Tests for HTTP helpers."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.helpers import (
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
    _SUMMARY_FIELDS,
    check_api_put,
    merge_metadata_filter_params,
    shape_payroll,
)


@pytest.mark.anyio
async def test_check_api_get(mock_api, ctx):
    mock_api.get("/test").mock(return_value=httpx.Response(200, json={"id": "t_1"}))
    result = await check_api_get(ctx, "/test")
    assert result == {"id": "t_1"}


@pytest.mark.anyio
async def test_check_api_get_with_params(mock_api, ctx):
    route = mock_api.get("/test").mock(
        return_value=httpx.Response(200, json={"id": "t_1"})
    )
    await check_api_get(ctx, "/test", params={"limit": 5})
    assert "limit=5" in str(route.calls[0].request.url)


@pytest.mark.anyio
async def test_check_api_post(mock_api, ctx):
    mock_api.post("/test").mock(return_value=httpx.Response(201, json={"id": "t_new"}))
    result = await check_api_post(ctx, "/test", data={"name": "foo"})
    assert result == {"id": "t_new"}


@pytest.mark.anyio
async def test_check_api_patch(mock_api, ctx):
    mock_api.patch("/test/t_1").mock(
        return_value=httpx.Response(200, json={"id": "t_1", "name": "updated"})
    )
    result = await check_api_patch(ctx, "/test/t_1", data={"name": "updated"})
    assert result["name"] == "updated"


@pytest.mark.anyio
async def test_check_api_put(mock_api, ctx):
    mock_api.put("/test/t_1").mock(
        return_value=httpx.Response(200, json={"id": "t_1", "name": "replaced"})
    )
    result = await check_api_put(ctx, "/test/t_1", data={"name": "replaced"})
    assert result["name"] == "replaced"


@pytest.mark.anyio
async def test_check_api_delete(mock_api, ctx):
    mock_api.delete("/test/t_1").mock(return_value=httpx.Response(204))
    result = await check_api_delete(ctx, "/test/t_1")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_check_api_delete_with_body(mock_api, ctx):
    mock_api.delete("/test/t_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    result = await check_api_delete(ctx, "/test/t_1")
    assert result == {"deleted": True}


@pytest.mark.anyio
async def test_check_api_list(mock_api, ctx):
    mock_api.get("/items").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": "https://sandbox.checkhq.com/items?cursor=c2",
                "previous": None,
                "results": [{"id": "i_1"}],
            },
        )
    )
    result = await check_api_list(ctx, "/items")
    assert result["results"] == [{"id": "i_1"}]
    assert result["next_cursor"] == "c2"
    assert result["previous_cursor"] is None


@pytest.mark.anyio
async def test_http_error_returns_error_dict(mock_api, ctx):
    mock_api.get("/bad").mock(
        return_value=httpx.Response(422, json={"detail": "Validation error"})
    )
    result = await check_api_get(ctx, "/bad")
    assert result["error"] is True
    assert result["status_code"] == 422
    assert result["detail"] == {"detail": "Validation error"}


@pytest.mark.anyio
async def test_http_error_with_text_body(mock_api, ctx):
    mock_api.get("/bad").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    result = await check_api_get(ctx, "/bad")
    assert result["error"] is True
    assert result["status_code"] == 500


def test_merge_metadata_filter_params() -> None:
    assert merge_metadata_filter_params(None, None) is None
    assert merge_metadata_filter_params({"company": "com_1"}, None) == {
        "company": "com_1"
    }
    assert merge_metadata_filter_params(
        {"company": "com_1"},
        {"Type": "Loan", "User": "Bob"},
    ) == {
        "company": "com_1",
        "metadata[Type]": "Loan",
        "metadata[User]": "Bob",
    }
    assert merge_metadata_filter_params(None, {"external_id": "123"}) == {
        "metadata[external_id]": "123"
    }


# --- shape_payroll ---


def test_shape_payroll_replaces_inlined_lists_with_counts():
    payroll = {
        "id": "pay_1",
        "status": "draft",
        "items": [{"id": "itm_1"}, {"id": "itm_2"}],
        "contractor_payments": [{"id": "cpm_1"}],
    }
    shaped = shape_payroll(payroll)
    assert shaped == {
        "id": "pay_1",
        "status": "draft",
        "items_count": 2,
        "contractor_payments_count": 1,
    }
    # The input is not mutated.
    assert "items" in payroll


def test_shape_payroll_leaves_a_response_without_inlined_lists_alone():
    payroll = {"id": "pay_1", "status": "draft", "totals": {"cash_requirement": "1"}}
    assert shape_payroll(payroll) == payroll
    assert "items_count" not in shape_payroll(payroll)


def test_shape_payroll_keeps_lists_when_items_are_wanted():
    payroll = {"id": "pay_1", "items": [{"id": "itm_1"}], "contractor_payments": []}
    assert shape_payroll(payroll, include_items=True) is payroll


def test_shape_payroll_counts_an_empty_inlined_list():
    assert shape_payroll({"id": "pay_1", "items": []}) == {
        "id": "pay_1",
        "items_count": 0,
    }


def test_shape_payroll_passes_errors_and_non_dicts_through():
    error = {"error": True, "status_code": 404, "detail": {"items": []}}
    assert shape_payroll(error) is error
    assert shape_payroll(None) is None  # type: ignore[arg-type]
    assert shape_payroll([1]) == [1]  # type: ignore[arg-type]


# Check's real public ID prefixes for the entities whose lists carry the
# most bulk. The summary table was keyed on invented prefixes (prl_, pit_,
# pmt_) for months, so these lists were never summarized and a company's
# recent payrolls came back with every payroll item inline.
@pytest.mark.parametrize(
    ("record_id", "bulky_field"),
    [
        ("pay_001", "items"),
        ("itm_001", "earnings"),
        ("pyt_001", "attempts"),
    ],
)
@pytest.mark.anyio
async def test_check_api_list_summarizes_payroll_entities(
    mock_api, ctx, record_id, bulky_field
):
    mock_api.get("/things").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": record_id,
                        "status": "paid",
                        bulky_field: [{"id": "x"} for _ in range(50)],
                    }
                ],
            },
        )
    )
    result = await check_api_list(ctx, "/things")
    row = result["results"][0]
    assert row["id"] == record_id
    assert row["status"] == "paid"
    assert bulky_field not in row


def test_summary_prefixes_are_real_check_prefixes() -> None:
    """Payrolls are pay_, payroll items itm_, payments pyt_ (check-api's
    public_id_prefix values). A typo here silently turns summaries off."""
    assert {"pay_", "itm_", "pyt_"} <= set(_SUMMARY_FIELDS)
    assert not {"prl_", "pit_", "pmt_"} & set(_SUMMARY_FIELDS)
