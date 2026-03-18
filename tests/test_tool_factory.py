"""Tests for the declarative tool factory."""

from __future__ import annotations

import inspect

import httpx
import pytest

from mcp_server_check.tool_factory import (
    Field,
    Resource,
    _build_body,
    generate_tools,
)


# --- Unit tests for _build_body ---


class TestBuildBody:
    def test_create_includes_required_fields(self):
        fields = [
            Field("name", str, required_for="create"),
            Field("email", str),
        ]
        body = _build_body(fields, {"name": "Alice", "email": None}, is_create=True)
        assert body == {"name": "Alice"}

    def test_create_includes_optional_when_provided(self):
        fields = [
            Field("name", str, required_for="create"),
            Field("email", str),
        ]
        body = _build_body(
            fields, {"name": "Alice", "email": "a@b.com"}, is_create=True
        )
        assert body == {"name": "Alice", "email": "a@b.com"}

    def test_update_skips_none_fields(self):
        fields = [
            Field("name", str),
            Field("email", str),
        ]
        body = _build_body(fields, {"name": "Bob", "email": None}, is_create=False)
        assert body == {"name": "Bob"}

    def test_create_only_excluded_from_update(self):
        fields = [
            Field("company", str, required_for="create", create_only=True),
            Field("name", str),
        ]
        body = _build_body(
            fields, {"company": "com_1", "name": "Test"}, is_create=False
        )
        assert body == {"name": "Test"}

    def test_update_only_excluded_from_create(self):
        fields = [
            Field("name", str, required_for="create"),
            Field("active", bool, update_only=True),
        ]
        body = _build_body(fields, {"name": "Test", "active": True}, is_create=True)
        assert body == {"name": "Test"}


# --- Integration tests for generate_tools ---


@pytest.fixture
def simple_resource():
    return Resource(
        name="widgets",
        path="/widgets",
        id_param="widget_id",
        id_description="The widget ID.",
        description="widgets",
        list_filters=["company"],
        fields=[
            Field("company", str, required_for="create", doc="Company ID."),
            Field("name", str, required_for="create", doc="Widget name."),
            Field("color", str, doc="Widget color."),
        ],
    )


class TestGenerateTools:
    def test_generates_all_crud_tools(self, simple_resource):
        tools = generate_tools(simple_resource)
        assert tools.list_fn is not None
        assert tools.get_fn is not None
        assert tools.create_fn is not None
        assert tools.update_fn is not None
        assert tools.delete_fn is not None

    def test_no_delete_when_has_delete_false(self):
        res = Resource(
            name="things",
            path="/things",
            id_param="thing_id",
            has_delete=False,
            fields=[],
        )
        tools = generate_tools(res)
        assert tools.delete_fn is None

    def test_function_names(self, simple_resource):
        tools = generate_tools(simple_resource)
        assert tools.list_fn.__name__ == "list_widgets"
        assert tools.get_fn.__name__ == "get_widget"
        assert tools.create_fn.__name__ == "create_widget"
        assert tools.update_fn.__name__ == "update_widget"
        assert tools.delete_fn.__name__ == "delete_widget"

    def test_list_has_proper_signature(self, simple_resource):
        tools = generate_tools(simple_resource)
        sig = inspect.signature(tools.list_fn)
        param_names = list(sig.parameters.keys())
        assert "ctx" in param_names
        assert "company" in param_names
        assert "limit" in param_names
        assert "cursor" in param_names

    def test_get_has_proper_signature(self, simple_resource):
        tools = generate_tools(simple_resource)
        sig = inspect.signature(tools.get_fn)
        param_names = list(sig.parameters.keys())
        assert "ctx" in param_names
        assert "widget_id" in param_names

    def test_create_has_proper_signature(self, simple_resource):
        tools = generate_tools(simple_resource)
        sig = inspect.signature(tools.create_fn)
        params = sig.parameters
        assert "ctx" in params
        assert "company" in params
        assert "name" in params
        assert "color" in params
        # Required fields should not have defaults
        assert params["company"].default is inspect.Parameter.empty
        assert params["name"].default is inspect.Parameter.empty
        # Optional fields should default to None
        assert params["color"].default is None

    def test_update_has_proper_signature(self, simple_resource):
        tools = generate_tools(simple_resource)
        sig = inspect.signature(tools.update_fn)
        params = sig.parameters
        assert "ctx" in params
        assert "widget_id" in params
        assert "color" in params
        # All update fields should default to None
        assert params["color"].default is None

    def test_functions_have_docstrings(self, simple_resource):
        tools = generate_tools(simple_resource)
        for fn in tools.all():
            assert fn.__doc__ is not None
            assert len(fn.__doc__) > 10

    def test_all_helpers(self, simple_resource):
        tools = generate_tools(simple_resource)
        assert len(tools.all_read()) == 2
        assert len(tools.all_write()) == 3
        assert len(tools.all()) == 5


@pytest.mark.anyio
async def test_generated_list_calls_api(mock_api, ctx):
    """Generated list function makes the right API call."""
    res = Resource(
        name="widgets",
        path="/widgets",
        id_param="widget_id",
        list_filters=["company"],
        fields=[],
    )
    tools = generate_tools(res)
    mock_api.get("/widgets").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": [{"id": "w_1"}]}
        )
    )
    result = await tools.list_fn(ctx, company="com_1")
    assert result["results"][0]["id"] == "w_1"


@pytest.mark.anyio
async def test_generated_get_calls_api(mock_api, ctx):
    """Generated get function makes the right API call."""
    res = Resource(
        name="widgets",
        path="/widgets",
        id_param="widget_id",
        fields=[],
    )
    tools = generate_tools(res)
    mock_api.get("/widgets/w_1").mock(
        return_value=httpx.Response(200, json={"id": "w_1", "name": "Foo"})
    )
    result = await tools.get_fn(ctx, widget_id="w_1")
    assert result == {"id": "w_1", "name": "Foo"}


@pytest.mark.anyio
async def test_generated_create_calls_api(mock_api, ctx):
    """Generated create function sends the right body."""
    res = Resource(
        name="widgets",
        path="/widgets",
        id_param="widget_id",
        fields=[
            Field("company", str, required_for="create"),
            Field("name", str, required_for="create"),
            Field("color", str),
        ],
    )
    tools = generate_tools(res)
    route = mock_api.post("/widgets").mock(
        return_value=httpx.Response(201, json={"id": "w_new"})
    )
    result = await tools.create_fn(ctx, company="com_1", name="Foo", color="red")
    assert result["id"] == "w_new"
    # Verify the body was sent correctly
    import json

    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {"company": "com_1", "name": "Foo", "color": "red"}


@pytest.mark.anyio
async def test_generated_update_calls_api(mock_api, ctx):
    """Generated update function sends only non-None fields."""
    res = Resource(
        name="widgets",
        path="/widgets",
        id_param="widget_id",
        fields=[
            Field("name", str),
            Field("color", str),
        ],
    )
    tools = generate_tools(res)
    route = mock_api.patch("/widgets/w_1").mock(
        return_value=httpx.Response(200, json={"id": "w_1", "color": "blue"})
    )
    result = await tools.update_fn(ctx, widget_id="w_1", color="blue")
    assert result["id"] == "w_1"
    import json

    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {"color": "blue"}


@pytest.mark.anyio
async def test_generated_delete_calls_api(mock_api, ctx):
    """Generated delete function makes the right API call."""
    res = Resource(
        name="widgets",
        path="/widgets",
        id_param="widget_id",
        fields=[],
    )
    tools = generate_tools(res)
    mock_api.delete("/widgets/w_1").mock(return_value=httpx.Response(204))
    result = await tools.delete_fn(ctx, widget_id="w_1")
    assert result == {"success": True}
