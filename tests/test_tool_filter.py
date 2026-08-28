"""Unit tests for ToolFilter."""

from __future__ import annotations

import os
from unittest import mock

import pytest
from mcp_server_check.tool_filter import (
    TOOLSETS,
    ToolFilter,
    is_destructive_tool,
    is_money_movement_tool,
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
            "add_filing_blockers",
            "remove_filing_blockers",
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


# --- ToolFilter.from_query_params ---


class TestFromQueryParams:
    def test_read_only_true(self):
        tf = ToolFilter.from_query_params({"read_only": "true"})
        assert tf.read_only is True

    def test_read_only_numeric(self):
        tf = ToolFilter.from_query_params({"read_only": "1"})
        assert tf.read_only is True

    def test_read_only_false(self):
        tf = ToolFilter.from_query_params({"read_only": "false"})
        assert tf.read_only is False

    def test_empty_query_params(self):
        tf = ToolFilter.from_query_params({})
        assert tf == ToolFilter()

    def test_no_get_method(self):
        tf = ToolFilter.from_query_params(42)  # type: ignore[arg-type]
        assert tf == ToolFilter()

    def test_unrelated_params_ignored(self):
        tf = ToolFilter.from_query_params({"foo": "bar", "baz": "1"})
        assert tf == ToolFilter()

    def test_only_read_only_is_parsed(self):
        """Query params for other filter fields (toolsets, exclusion flags, etc.) are ignored."""
        tf = ToolFilter.from_query_params(
            {
                "read_only": "true",
                "exclude_money_movement": "true",
                "exclude_destructive": "true",
                "toolsets": "companies",
                "tools": "list_companies",
                "exclude_tools": "delete_company",
            }
        )
        assert tf.read_only is True
        assert tf.exclude_money_movement is False
        assert tf.exclude_destructive is False
        assert tf.toolsets is None
        assert tf.tools is None
        assert tf.exclude_tools == frozenset()


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


# --- is_destructive_tool ---


class TestIsDestructiveTool:
    @pytest.mark.parametrize(
        "name",
        [
            "approve_payroll",
            "delete_payroll",
            "delete_company",
            "bulk_delete_payroll_items",
            "simulate_start_processing",
            "simulate_complete_funding",
            "refund_payment",
            "cancel_payment",
            "start_implementation",
            "cancel_implementation",
        ],
    )
    def test_destructive_detected(self, name):
        assert is_destructive_tool(name), f"{name} should be destructive"

    @pytest.mark.parametrize(
        "name",
        [
            "list_companies",
            "get_employee",
            "create_company",
            "update_employee",
            "preview_payroll",
            "onboard_company",
            "submit_employee_form",
        ],
    )
    def test_non_destructive(self, name):
        assert not is_destructive_tool(name), f"{name} should NOT be destructive"


# --- is_money_movement_tool ---


class TestIsMoneyMovementTool:
    @pytest.mark.parametrize(
        "name",
        [
            "approve_payroll",
            "retry_payment",
            "refund_payment",
            "cancel_payment",
            "create_bank_account",
            "update_bank_account",
            "delete_bank_account",
        ],
    )
    def test_money_movement_detected(self, name):
        assert is_money_movement_tool(name), f"{name} should be money movement"

    @pytest.mark.parametrize(
        "name",
        [
            # Reads that would match a naive *payment* substring rule
            "list_payments",
            "get_payment",
            "list_payment_attempts",
            "diagnose_payment",
            "list_bank_accounts",
            "get_bank_account",
            # Prefix lookalikes that move no money
            "retry_webhook_delivery",
            "cancel_implementation",
            "approve_external_payroll",
            # Amount-shaping tools that cannot disburse on their own
            "create_payroll",
            "create_payroll_item",
            "create_contractor_payment",
            "create_net_pay_split",
        ],
    )
    def test_not_money_movement(self, name):
        assert not is_money_movement_tool(name), f"{name} should NOT be money movement"


# --- category exclusion flags ---


class TestExcludeMoneyMovement:
    def test_disabled_by_default(self):
        tf = ToolFilter()
        assert tf.is_tool_allowed("approve_payroll", "payrolls") is True

    def test_hides_money_movement_tools(self):
        tf = ToolFilter(exclude_money_movement=True)
        assert tf.is_tool_allowed("approve_payroll", "payrolls") is False
        assert tf.is_tool_allowed("create_bank_account", "bank_accounts") is False

    def test_leaves_other_tools_visible(self):
        tf = ToolFilter(exclude_money_movement=True)
        assert tf.is_tool_allowed("list_companies", "companies") is True
        assert tf.is_tool_allowed("create_payroll", "payrolls") is True
        assert tf.is_tool_allowed("delete_payroll", "payrolls") is True

    def test_overrides_tools_allowlist(self):
        """Category exclusion is a floor: it beats an explicit allowlist."""
        tf = ToolFilter(
            tools=frozenset({"approve_payroll"}), exclude_money_movement=True
        )
        assert tf.is_tool_allowed("approve_payroll", "payrolls") is False

    def test_from_env(self):
        with mock.patch.dict(os.environ, {"CHECK_EXCLUDE_MONEY_MOVEMENT": "true"}):
            tf = ToolFilter.from_env()
        assert tf.exclude_money_movement is True

    def test_from_headers(self):
        tf = ToolFilter.from_headers({"x-mcp-exclude-money-movement": "1"})
        assert tf.exclude_money_movement is True


class TestExcludeDestructive:
    def test_disabled_by_default(self):
        tf = ToolFilter()
        assert tf.is_tool_allowed("delete_payroll", "payrolls") is True

    def test_hides_destructive_tools(self):
        tf = ToolFilter(exclude_destructive=True)
        assert tf.is_tool_allowed("delete_payroll", "payrolls") is False
        assert tf.is_tool_allowed("bulk_delete_payroll_items", "payroll_items") is False
        assert tf.is_tool_allowed("cancel_implementation", "companies") is False

    def test_leaves_other_writes_visible(self):
        tf = ToolFilter(exclude_destructive=True)
        assert tf.is_tool_allowed("create_payroll", "payrolls") is True
        assert tf.is_tool_allowed("update_employee", "employees") is True

    def test_overrides_tools_allowlist(self):
        tf = ToolFilter(tools=frozenset({"delete_payroll"}), exclude_destructive=True)
        assert tf.is_tool_allowed("delete_payroll", "payrolls") is False

    def test_from_env(self):
        with mock.patch.dict(os.environ, {"CHECK_EXCLUDE_DESTRUCTIVE": "true"}):
            tf = ToolFilter.from_env()
        assert tf.exclude_destructive is True

    def test_from_headers(self):
        tf = ToolFilter.from_headers({"x-mcp-exclude-destructive": "1"})
        assert tf.exclude_destructive is True


class TestDirectorySafeProfile:
    """Both flags together — the Anthropic directory deployment profile."""

    def test_money_and_destructive_tools_hidden(self):
        tf = ToolFilter(exclude_money_movement=True, exclude_destructive=True)
        for name, toolset in [
            ("approve_payroll", "payrolls"),
            ("cancel_payment", "payments"),
            ("refund_payment", "payments"),
            ("retry_payment", "payments"),
            ("create_bank_account", "bank_accounts"),
            ("update_bank_account", "bank_accounts"),
            ("delete_bank_account", "bank_accounts"),
            ("delete_payroll", "payrolls"),
            ("bulk_delete_payroll_items", "payroll_items"),
        ]:
            assert tf.is_tool_allowed(name, toolset) is False, name

    def test_payroll_preparation_still_possible(self):
        """Agents can still prepare a payroll run; they just cannot disburse it."""
        tf = ToolFilter(exclude_money_movement=True, exclude_destructive=True)
        for name, toolset in [
            ("list_companies", "companies"),
            ("create_payroll", "payrolls"),
            ("create_payroll_item", "payroll_items"),
            ("create_contractor_payment", "contractor_payments"),
            ("create_net_pay_split", "compensation"),
            ("preview_payroll", "payrolls"),
        ]:
            assert tf.is_tool_allowed(name, toolset) is True, name


class TestMerge:
    def test_merge_defaults_returns_default(self):
        a = ToolFilter()
        b = ToolFilter()
        assert a.merge(b) == ToolFilter()

    def test_merge_preserves_read_only_from_env(self):
        """Env sets read_only; header does not -- result is read_only."""
        env = ToolFilter(read_only=True)
        header = ToolFilter(toolsets=frozenset({"companies"}))
        merged = env.merge(header)
        assert merged.read_only is True
        assert merged.toolsets == frozenset({"companies"})

    def test_merge_header_cannot_relax_read_only(self):
        """Header sending read_only=False cannot override env read_only=True."""
        env = ToolFilter(read_only=True)
        header = ToolFilter(read_only=False)
        assert env.merge(header).read_only is True

    def test_merge_unions_exclude_tools(self):
        env = ToolFilter(exclude_tools=frozenset({"delete_company"}))
        header = ToolFilter(exclude_tools=frozenset({"delete_payroll"}))
        merged = env.merge(header)
        assert merged.exclude_tools == frozenset({"delete_company", "delete_payroll"})

    def test_merge_intersects_toolsets(self):
        env = ToolFilter(toolsets=frozenset({"companies", "employees"}))
        header = ToolFilter(toolsets=frozenset({"companies", "payrolls"}))
        merged = env.merge(header)
        assert merged.toolsets == frozenset({"companies"})

    def test_merge_env_toolsets_restricts_when_header_none(self):
        env = ToolFilter(toolsets=frozenset({"companies"}))
        header = ToolFilter()  # toolsets=None means "all"
        merged = env.merge(header)
        assert merged.toolsets == frozenset({"companies"})

    def test_merge_header_toolsets_restricts_when_env_none(self):
        env = ToolFilter()  # toolsets=None means "all"
        header = ToolFilter(toolsets=frozenset({"companies"}))
        merged = env.merge(header)
        assert merged.toolsets == frozenset({"companies"})

    def test_merge_intersects_tools(self):
        env = ToolFilter(tools=frozenset({"list_companies", "get_company"}))
        header = ToolFilter(tools=frozenset({"list_companies", "create_company"}))
        merged = env.merge(header)
        assert merged.tools == frozenset({"list_companies"})

    def test_merge_exclude_money_movement_or(self):
        """A client cannot relax an exclusion the server set."""
        env = ToolFilter(exclude_money_movement=True)
        header = ToolFilter(exclude_money_movement=False)
        assert env.merge(header).exclude_money_movement is True

    def test_merge_exclude_destructive_or(self):
        env = ToolFilter(exclude_destructive=True)
        header = ToolFilter(exclude_destructive=False)
        assert env.merge(header).exclude_destructive is True

    def test_merge_header_can_add_exclusions(self):
        """A client may tighten beyond the server policy."""
        env = ToolFilter()
        header = ToolFilter(exclude_money_movement=True, exclude_destructive=True)
        merged = env.merge(header)
        assert merged.exclude_money_movement is True
        assert merged.exclude_destructive is True

    def test_merge_three_way_env_header_query(self):
        """Env, header, and query-param filters combine correctly."""
        env = ToolFilter(toolsets=frozenset({"companies", "employees"}))
        header = ToolFilter(toolsets=frozenset({"companies", "payrolls"}))
        query = ToolFilter(read_only=True)
        merged = env.merge(header).merge(query)
        assert merged.toolsets == frozenset({"companies"})
        assert merged.read_only is True

    def test_merge_query_param_cannot_relax_env(self):
        """read_only=False from query params cannot override read_only=True from env."""
        env = ToolFilter(read_only=True)
        query = ToolFilter(read_only=False)
        assert env.merge(query).read_only is True

    def test_merge_full_policy_scenario(self):
        """Realistic scenario: env locks down to read-only companies,
        header tries to request employees + write access."""
        env = ToolFilter(
            toolsets=frozenset({"companies"}),
            read_only=True,
            exclude_tools=frozenset({"some_sensitive_tool"}),
        )
        header = ToolFilter(
            toolsets=frozenset({"companies", "employees"}),
            read_only=False,
        )
        merged = env.merge(header)
        assert merged.toolsets == frozenset({"companies"})
        assert merged.read_only is True
        assert merged.exclude_tools == frozenset({"some_sensitive_tool"})


class TestToolsets:
    def test_has_20_toolsets(self):
        assert len(TOOLSETS) == 20

    def test_known_toolsets(self):
        expected = {
            "agencies",
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
            "logs",
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
