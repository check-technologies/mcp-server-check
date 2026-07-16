"""Tests for tool title and annotation derivation."""

from __future__ import annotations

import asyncio

import pytest
from mcp_server_check.annotations import (
    add_annotated_tool,
    build_tool,
    derive_annotations,
    derive_title,
)
from mcp_server_check.server import CheckMCP
from mcp_server_check.tools import register_all


class TestDeriveTitle:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("list_companies", "List Companies"),
            ("get_company", "Get Company"),
            ("get_employee_paystub", "Get Employee Paystub"),
            ("create_employee", "Create Employee"),
            ("update_company", "Update Company"),
            ("delete_payroll", "Delete Payroll"),
            ("simulate_complete_funding", "Simulate Complete Funding (Sandbox)"),
            ("simulate_fail_funding", "Simulate Fail Funding (Sandbox)"),
            ("sign_and_submit_employee_form", "Sign and Submit Employee Form"),
            ("bulk_delete_payroll_items", "Bulk Delete Payroll Items"),
            ("validate_address", "Validate Address"),
            ("render_form", "Render Form"),
            ("ping_webhook_config", "Ping Webhook Config"),
            ("download_employee_tax_document", "Download Employee Tax Document"),
            ("get_applied_for_ids_report", "Get Applied for IDs Report"),
        ],
    )
    def test_titles(self, name: str, expected: str) -> None:
        assert derive_title(name) == expected


class TestDeriveAnnotations:
    def test_read_only_list_tool(self) -> None:
        a = derive_annotations("list_companies")
        assert a.title == "List Companies"
        assert a.readOnlyHint is True
        assert a.destructiveHint is False
        assert a.idempotentHint is True
        assert a.openWorldHint is False

    def test_read_only_get_tool(self) -> None:
        a = derive_annotations("get_employee")
        assert a.readOnlyHint is True
        assert a.destructiveHint is False

    def test_destructive_delete_tool(self) -> None:
        a = derive_annotations("delete_payroll")
        assert a.readOnlyHint is False
        assert a.destructiveHint is True
        # delete is idempotent (calling twice has no extra effect after the
        # first call)
        assert a.idempotentHint is True

    def test_destructive_approve_tool(self) -> None:
        a = derive_annotations("approve_payroll")
        assert a.readOnlyHint is False
        assert a.destructiveHint is True
        assert a.idempotentHint is False

    def test_destructive_simulate_tool(self) -> None:
        a = derive_annotations("simulate_complete_funding")
        assert a.readOnlyHint is False
        assert a.destructiveHint is True
        assert a.openWorldHint is False

    def test_non_destructive_mutating_create(self) -> None:
        a = derive_annotations("create_employee")
        assert a.readOnlyHint is False
        assert a.destructiveHint is False
        assert a.idempotentHint is False

    def test_non_destructive_mutating_update(self) -> None:
        a = derive_annotations("update_company")
        assert a.readOnlyHint is False
        assert a.destructiveHint is False
        assert a.idempotentHint is True

    def test_non_destructive_bulk_update(self) -> None:
        a = derive_annotations("bulk_update_exemptible_taxes")
        assert a.readOnlyHint is False
        assert a.destructiveHint is False
        assert a.idempotentHint is True

    def test_destructive_bulk_update_payroll_items(self) -> None:
        # Shapes the amounts a payroll disburses, so it carries the
        # destructive hint and the confirmation gate.
        a = derive_annotations("bulk_update_payroll_items")
        assert a.readOnlyHint is False
        assert a.destructiveHint is True

    def test_destructive_bulk_delete(self) -> None:
        a = derive_annotations("bulk_delete_payroll_items")
        assert a.readOnlyHint is False
        assert a.destructiveHint is True
        assert a.idempotentHint is True

    def test_open_world_always_false(self) -> None:
        for name in (
            "list_companies",
            "create_employee",
            "delete_payroll",
            "simulate_complete_funding",
            "ping_webhook_config",
        ):
            assert derive_annotations(name).openWorldHint is False, name


class TestBuildTool:
    def test_build_tool_sets_title_and_annotations(self) -> None:
        async def list_companies() -> dict:  # pragma: no cover - dummy fn
            """Dummy tool."""
            return {}

        tool = build_tool(list_companies)
        assert tool.name == "list_companies"
        assert tool.title == "List Companies"
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True


class TestAddAnnotatedTool:
    def test_register_through_collector(self) -> None:
        captured: list = []

        class Collector:
            _annotated_tool_supports_kwargs = True

            @staticmethod
            def add_tool(fn, **kwargs):
                captured.append((fn, kwargs))

        async def get_company() -> dict:  # pragma: no cover - dummy fn
            return {}

        add_annotated_tool(Collector(), get_company)
        assert len(captured) == 1
        fn, kwargs = captured[0]
        assert fn is get_company
        assert kwargs["title"] == "Get Company"
        assert kwargs["annotations"].readOnlyHint is True


class TestRegisteredServerTools:
    """End-to-end checks that the live server exposes correct annotations."""

    @pytest.fixture
    def server(self) -> CheckMCP:
        s = CheckMCP("Test")
        register_all(s, registry=s._registry)
        return s

    def _tools_by_name(self, server: CheckMCP) -> dict:
        return {t.name: t for t in asyncio.run(server.list_tools())}

    def test_list_companies_is_read_only(self, server: CheckMCP) -> None:
        tools = self._tools_by_name(server)
        t = tools["list_companies"]
        assert t.title == "List Companies"
        assert t.annotations is not None
        assert t.annotations.readOnlyHint is True
        assert t.annotations.destructiveHint is False
        assert t.annotations.openWorldHint is False

    def test_delete_payroll_is_destructive(self, server: CheckMCP) -> None:
        tools = self._tools_by_name(server)
        t = tools["delete_payroll"]
        assert t.title == "Delete Payroll"
        assert t.annotations is not None
        assert t.annotations.readOnlyHint is False
        assert t.annotations.destructiveHint is True

    def test_create_employee_is_non_destructive_mutating(
        self, server: CheckMCP
    ) -> None:
        tools = self._tools_by_name(server)
        t = tools["create_employee"]
        assert t.title == "Create Employee"
        assert t.annotations is not None
        assert t.annotations.readOnlyHint is False
        assert t.annotations.destructiveHint is False

    def test_simulate_tool_marked_sandbox_and_destructive(
        self, server: CheckMCP
    ) -> None:
        tools = self._tools_by_name(server)
        t = tools["simulate_complete_funding"]
        assert t.title == "Simulate Complete Funding (Sandbox)"
        assert t.annotations is not None
        assert t.annotations.destructiveHint is True

    def test_all_tools_have_title_and_annotations(self, server: CheckMCP) -> None:
        tools = self._tools_by_name(server)
        # Every Check API tool should have a derived title and annotations
        # with openWorldHint=False (closed-world API).
        missing = [name for name, t in tools.items() if not t.title]
        assert not missing, f"tools missing titles: {missing[:5]}"
        for name, t in tools.items():
            assert t.annotations is not None, f"{name} missing annotations"
            assert t.annotations.openWorldHint is False, name
