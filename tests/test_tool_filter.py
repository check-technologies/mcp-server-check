"""Unit tests for ToolFilter."""

from __future__ import annotations

import os
from unittest import mock

import pytest
from mcp_server_check.tool_filter import (
    TOOLSETS,
    ToolFilter,
    is_write_tool,
)

# --- is_write_tool ---


class TestIsWriteTool:
    @pytest.mark.parametrize(
        "name",
        [
            "create_company",
            "update_employee",
            "delete_payroll",
            "bulk_update_payroll_items",
            "bulk_delete_payroll_items",
            "approve_payroll",
            "reopen_payroll",
            "onboard_company",
            "submit_employee_form",
            "sign_and_submit_employee_form",
            "authorize_integration_partner",
            "simulate_start_processing",
            "retry_payment",
            "refund_payment",
            "cancel_payment",
            "start_implementation",
            "cancel_implementation",
            "request_embedded_setup",
            "ping_webhook_config",
            "refresh_accounting_accounts",
            "toggle_accounting_mappings",
            "sync_accounting",
            "upload_company_provided_document_file",
            "request_tax_filing_refile",
        ],
    )
    def test_write_tools_detected(self, name):
        assert is_write_tool(name), f"{name} should be a write tool"

    @pytest.mark.parametrize(
        "name",
        [
            "list_companies",
            "get_company",
            "get_employee",
            "list_payrolls",
            "preview_payroll",
            "download_company_tax_document",
            "validate_address",
            "list_webhook_configs",
            "reveal_employee_ssn",
            "get_enrollment_profile",
        ],
    )
    def test_read_tools_not_detected(self, name):
        assert not is_write_tool(name), f"{name} should NOT be a write tool"


# --- ToolFilter.from_env ---


class TestFromEnv:
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            tf = ToolFilter.from_env()
        assert tf.toolsets is None
        assert tf.tools is None
        assert tf.exclude_tools == frozenset()
        assert tf.read_only is False

    def test_toolsets(self):
        with mock.patch.dict(os.environ, {"CHECK_TOOLSETS": "companies, employees"}):
            tf = ToolFilter.from_env()
        assert tf.toolsets == frozenset({"companies", "employees"})

    def test_tools(self):
        with mock.patch.dict(os.environ, {"CHECK_TOOLS": "list_companies,get_company"}):
            tf = ToolFilter.from_env()
        assert tf.tools == frozenset({"list_companies", "get_company"})

    def test_exclude_tools(self):
        with mock.patch.dict(
            os.environ, {"CHECK_EXCLUDE_TOOLS": "create_company,delete_company"}
        ):
            tf = ToolFilter.from_env()
        assert tf.exclude_tools == frozenset({"create_company", "delete_company"})

    def test_read_only_true(self):
        for val in ("1", "true", "yes", "True", "YES"):
            with mock.patch.dict(os.environ, {"CHECK_READ_ONLY": val}):
                tf = ToolFilter.from_env()
            assert tf.read_only is True, f"CHECK_READ_ONLY={val} should be True"

    def test_read_only_false(self):
        for val in ("0", "false", "no", ""):
            with mock.patch.dict(os.environ, {"CHECK_READ_ONLY": val}):
                tf = ToolFilter.from_env()
            assert tf.read_only is False, f"CHECK_READ_ONLY={val} should be False"

    def test_empty_values_yield_none(self):
        with mock.patch.dict(os.environ, {"CHECK_TOOLSETS": "", "CHECK_TOOLS": ""}):
            tf = ToolFilter.from_env()
        assert tf.toolsets is None
        assert tf.tools is None


# --- ToolFilter.from_headers ---


class TestFromHeaders:
    def test_all_headers(self):
        headers = {
            "x-mcp-toolsets": "companies,employees",
            "x-mcp-tools": "list_companies",
            "x-mcp-exclude-tools": "create_company",
            "x-mcp-readonly": "true",
        }
        tf = ToolFilter.from_headers(headers)
        assert tf.toolsets == frozenset({"companies", "employees"})
        assert tf.tools == frozenset({"list_companies"})
        assert tf.exclude_tools == frozenset({"create_company"})
        assert tf.read_only is True

    def test_empty_headers(self):
        tf = ToolFilter.from_headers({})
        assert tf == ToolFilter()

    def test_no_get_method(self):
        tf = ToolFilter.from_headers(42)  # type: ignore[arg-type]
        assert tf == ToolFilter()

    def test_case_insensitive_header_names(self):
        """Dict keys are already lowercase, matching HTTP header convention."""
        headers = {"x-mcp-readonly": "1"}
        tf = ToolFilter.from_headers(headers)
        assert tf.read_only is True


# --- is_tool_allowed precedence ---


class TestIsToolAllowed:
    def test_no_filter(self):
        tf = ToolFilter()
        assert tf.is_tool_allowed("create_company", "companies") is True

    def test_exclude_wins_over_everything(self):
        tf = ToolFilter(
            tools=frozenset({"create_company"}),
            exclude_tools=frozenset({"create_company"}),
        )
        assert tf.is_tool_allowed("create_company", "companies") is False

    def test_readonly_blocks_write(self):
        tf = ToolFilter(read_only=True)
        assert tf.is_tool_allowed("create_company", "companies") is False
        assert tf.is_tool_allowed("list_companies", "companies") is True

    def test_readonly_does_not_block_if_in_tools(self):
        """Read-only takes precedence over tools allowlist."""
        tf = ToolFilter(
            tools=frozenset({"create_company"}),
            read_only=True,
        )
        assert tf.is_tool_allowed("create_company", "companies") is False

    def test_tools_allowlist(self):
        tf = ToolFilter(tools=frozenset({"list_companies", "get_company"}))
        assert tf.is_tool_allowed("list_companies", "companies") is True
        assert tf.is_tool_allowed("get_company", "companies") is True
        assert tf.is_tool_allowed("create_company", "companies") is False
        assert tf.is_tool_allowed("list_employees", "employees") is False

    def test_tools_overrides_toolsets(self):
        """When tools is set, toolsets is ignored."""
        tf = ToolFilter(
            toolsets=frozenset({"employees"}),
            tools=frozenset({"list_companies"}),
        )
        assert tf.is_tool_allowed("list_companies", "companies") is True
        assert tf.is_tool_allowed("list_employees", "employees") is False

    def test_toolsets_filter(self):
        tf = ToolFilter(toolsets=frozenset({"companies"}))
        assert tf.is_tool_allowed("list_companies", "companies") is True
        assert tf.is_tool_allowed("create_company", "companies") is True
        assert tf.is_tool_allowed("list_employees", "employees") is False

    def test_exclude_with_toolsets(self):
        tf = ToolFilter(
            toolsets=frozenset({"companies"}),
            exclude_tools=frozenset({"create_company"}),
        )
        assert tf.is_tool_allowed("list_companies", "companies") is True
        assert tf.is_tool_allowed("create_company", "companies") is False

    def test_readonly_with_toolsets(self):
        tf = ToolFilter(
            toolsets=frozenset({"companies"}),
            read_only=True,
        )
        assert tf.is_tool_allowed("list_companies", "companies") is True
        assert tf.is_tool_allowed("create_company", "companies") is False
        assert tf.is_tool_allowed("list_employees", "employees") is False


# --- Invalid toolset handling ---


class TestInvalidToolsets:
    def test_unknown_toolsets_are_stripped(self):
        tf = ToolFilter(toolsets=frozenset({"companies", "not_a_real_one"}))
        assert tf.toolsets == frozenset({"companies"})

    def test_all_unknown_yields_empty(self):
        tf = ToolFilter(toolsets=frozenset({"bogus"}))
        assert tf.toolsets == frozenset()
        # With empty toolsets, no tools should be allowed
        assert tf.is_tool_allowed("list_companies", "companies") is False


# --- TOOLSETS constant ---


class TestToolsets:
    def test_has_18_toolsets(self):
        assert len(TOOLSETS) == 18

    def test_known_toolsets(self):
        expected = {
            "bank_accounts",
            "companies",
            "compensation",
            "components",
            "contractor_payments",
            "contractors",
            "documents",
            "employees",
            "external_payrolls",
            "forms",
            "payments",
            "payroll_items",
            "payrolls",
            "platform",
            "tax",
            "webhooks",
            "workflows",
            "workplaces",
        }
        assert TOOLSETS == expected
