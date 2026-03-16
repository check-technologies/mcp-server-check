"""Tests for CLI code generation (command naming, type mapping, discovery)."""

from __future__ import annotations

import inspect
import typing

import click
from mcp_server_check.cli.codegen import (
    CSVList,
    JSONParam,
    _build_params,
    _is_id_param,
    _make_command_name,
    _singularize,
    _unwrap_optional,
    build_command,
    collect_tools,
)
from mcp_server_check.helpers import Ctx

# ---------------------------------------------------------------------------
# _singularize
# ---------------------------------------------------------------------------


class TestSingularize:
    def test_companies(self):
        assert _singularize("companies") == "company"

    def test_employees(self):
        assert _singularize("employees") == "employee"

    def test_payrolls(self):
        assert _singularize("payrolls") == "payroll"

    def test_accounts(self):
        assert _singularize("accounts") == "account"

    def test_items(self):
        assert _singularize("items") == "item"

    def test_tax(self):
        assert _singularize("tax") == "tax"

    def test_platform(self):
        assert _singularize("platform") == "platform"

    def test_no_double_strip(self):
        """'ss' ending should not be stripped."""
        assert _singularize("stress") == "stress"


# ---------------------------------------------------------------------------
# _make_command_name
# ---------------------------------------------------------------------------


class TestMakeCommandName:
    def test_list_companies(self):
        assert _make_command_name("list_companies", "companies") == "list"

    def test_get_company(self):
        assert _make_command_name("get_company", "companies") == "get"

    def test_create_company(self):
        assert _make_command_name("create_company", "companies") == "create"

    def test_get_company_paydays(self):
        assert _make_command_name("get_company_paydays", "companies") == "get-paydays"

    def test_list_company_tax_deposits(self):
        assert (
            _make_command_name("list_company_tax_deposits", "companies")
            == "list-tax-deposits"
        )

    def test_list_employee_paystubs(self):
        assert (
            _make_command_name("list_employee_paystubs", "employees") == "list-paystubs"
        )

    def test_get_employee_paystub(self):
        assert _make_command_name("get_employee_paystub", "employees") == "get-paystub"

    def test_simulate_start_processing(self):
        """No toolset name in function → full name preserved."""
        assert (
            _make_command_name("simulate_start_processing", "payrolls")
            == "simulate-start-processing"
        )

    def test_approve_payroll(self):
        assert _make_command_name("approve_payroll", "payrolls") == "approve"

    def test_list_bank_accounts(self):
        assert _make_command_name("list_bank_accounts", "bank_accounts") == "list"

    def test_get_bank_account(self):
        assert _make_command_name("get_bank_account", "bank_accounts") == "get"

    def test_reveal_bank_account_numbers(self):
        assert (
            _make_command_name("reveal_bank_account_numbers", "bank_accounts")
            == "reveal-numbers"
        )

    def test_list_contractor_payments(self):
        assert (
            _make_command_name("list_contractor_payments", "contractor_payments")
            == "list"
        )

    def test_get_company_tax_params(self):
        """tax toolset — strips 'tax' from middle."""
        assert (
            _make_command_name("get_company_tax_params", "tax") == "get-company-params"
        )

    def test_no_match_full_name(self):
        """When toolset name not in function name, return full name."""
        assert (
            _make_command_name("get_payroll_journal_report", "companies")
            == "get-payroll-journal-report"
        )


# ---------------------------------------------------------------------------
# _unwrap_optional
# ---------------------------------------------------------------------------


class TestUnwrapOptional:
    def test_plain_str(self):
        base, opt = _unwrap_optional(str)
        assert base is str
        assert opt is False

    def test_optional_str(self):
        base, opt = _unwrap_optional(str | None)
        assert base is str
        assert opt is True

    def test_optional_int(self):
        base, opt = _unwrap_optional(int | None)
        assert base is int
        assert opt is True

    def test_optional_dict(self):
        base, opt = _unwrap_optional(dict | None)
        assert base is dict
        assert opt is True

    def test_plain_dict(self):
        base, opt = _unwrap_optional(dict)
        assert base is dict
        assert opt is False

    def test_optional_bool(self):
        base, opt = _unwrap_optional(bool | None)
        assert base is bool
        assert opt is True

    def test_optional_list_str(self):
        base, opt = _unwrap_optional(list[str] | None)
        assert typing.get_origin(base) is list
        assert opt is True


# ---------------------------------------------------------------------------
# _is_id_param
# ---------------------------------------------------------------------------


class TestIsIdParam:
    def test_company_id(self):
        assert _is_id_param("company_id") is True

    def test_employee_id(self):
        assert _is_id_param("employee_id") is True

    def test_legal_name(self):
        assert _is_id_param("legal_name") is False

    def test_company(self):
        assert _is_id_param("company") is False


# ---------------------------------------------------------------------------
# _build_params
# ---------------------------------------------------------------------------


class TestBuildParams:
    def test_excludes_ctx(self):
        """The ctx parameter should never appear in click params."""

        async def sample(ctx: Ctx, company_id: str) -> dict:
            pass

        params = _build_params(sample)
        param_names = [p.name for p in params]
        assert "ctx" not in param_names
        assert "company_id" in param_names

    def test_required_id_is_argument(self):
        async def sample(ctx: Ctx, company_id: str) -> dict:
            pass

        params = _build_params(sample)
        assert len(params) == 1
        assert isinstance(params[0], click.Argument)
        assert params[0].name == "company_id"

    def test_required_str_is_required_option(self):
        async def sample(ctx: Ctx, legal_name: str) -> dict:
            pass

        params = _build_params(sample)
        assert len(params) == 1
        assert isinstance(params[0], click.Option)
        assert params[0].required is True

    def test_optional_str(self):
        async def sample(ctx: Ctx, trade_name: str | None = None) -> dict:
            pass

        params = _build_params(sample)
        assert len(params) == 1
        assert isinstance(params[0], click.Option)
        assert params[0].required is False

    def test_optional_int(self):
        async def sample(ctx: Ctx, limit: int | None = None) -> dict:
            pass

        params = _build_params(sample)
        assert isinstance(params[0], click.Option)
        assert params[0].type is click.INT

    def test_optional_bool(self):
        async def sample(ctx: Ctx, active: bool | None = None) -> dict:
            pass

        params = _build_params(sample)
        assert isinstance(params[0], click.Option)
        assert params[0].is_flag is True

    def test_dict_param(self):
        async def sample(ctx: Ctx, address: dict | None = None) -> dict:
            pass

        params = _build_params(sample)
        assert isinstance(params[0].type, JSONParam)

    def test_required_dict(self):
        async def sample(ctx: Ctx, data: dict) -> dict:
            pass

        params = _build_params(sample)
        assert isinstance(params[0], click.Option)
        assert isinstance(params[0].type, JSONParam)
        assert params[0].required is True

    def test_list_str(self):
        async def sample(ctx: Ctx, ids: list[str] | None = None) -> dict:
            pass

        params = _build_params(sample)
        assert isinstance(params[0].type, CSVList)

    def test_list_dict(self):
        async def sample(ctx: Ctx, parameters: list[dict] | None = None) -> dict:
            pass

        params = _build_params(sample)
        assert isinstance(params[0].type, JSONParam)

    def test_float_param(self):
        async def sample(ctx: Ctx, amount: float | None = None) -> dict:
            pass

        params = _build_params(sample)
        assert params[0].type is click.FLOAT


# ---------------------------------------------------------------------------
# build_command
# ---------------------------------------------------------------------------


class TestBuildCommand:
    def test_produces_valid_command(self):
        async def list_companies(ctx: Ctx, limit: int | None = None) -> dict:
            """List companies."""
            pass

        cmd_name, cmd, func_name = build_command(list_companies, "companies")
        assert cmd_name == "list"
        assert func_name == "list_companies"
        assert isinstance(cmd, click.Command)
        assert cmd.help == "List companies."

    def test_multiple_id_args(self):
        async def get_employee_paystub(
            ctx: Ctx, employee_id: str, payroll_id: str
        ) -> dict:
            """Get paystub."""
            pass

        cmd_name, cmd, _ = build_command(get_employee_paystub, "employees")
        assert cmd_name == "get-paystub"
        args = [p for p in cmd.params if isinstance(p, click.Argument)]
        assert len(args) == 2
        assert args[0].name == "employee_id"
        assert args[1].name == "payroll_id"


# ---------------------------------------------------------------------------
# collect_tools — full discovery
# ---------------------------------------------------------------------------


class TestCollectTools:
    def test_returns_all_toolsets(self):
        tools = collect_tools()
        assert len(tools) == 18
        assert "companies" in tools
        assert "employees" in tools
        assert "payrolls" in tools
        assert "bank_accounts" in tools
        assert "tax" in tools

    def test_all_functions_are_async(self):
        tools = collect_tools()
        for toolset_name, funcs in tools.items():
            for fn in funcs:
                assert inspect.iscoroutinefunction(fn), (
                    f"{toolset_name}.{fn.__name__} is not async"
                )

    def test_all_functions_have_ctx_param(self):
        tools = collect_tools()
        for toolset_name, funcs in tools.items():
            for fn in funcs:
                sig = inspect.signature(fn)
                assert "ctx" in sig.parameters, (
                    f"{toolset_name}.{fn.__name__} missing ctx param"
                )

    def test_every_function_produces_valid_command(self):
        """Every registered tool function should produce a valid click command."""
        tools = collect_tools()
        total = 0
        for toolset_name, funcs in tools.items():
            for fn in funcs:
                cmd_name, cmd, func_name = build_command(fn, toolset_name)
                assert cmd_name, f"Empty command name for {fn.__name__}"
                assert isinstance(cmd, click.Command)
                assert func_name == fn.__name__
                # ctx should not appear in click params
                param_names = [p.name for p in cmd.params]
                assert "ctx" not in param_names, (
                    f"ctx leaked into params for {fn.__name__}"
                )
                total += 1
        # Sanity check: we should have a large number of commands
        assert total > 200, f"Expected 200+ tools but found {total}"

    def test_no_duplicate_command_names_per_toolset(self):
        """Each toolset should have unique command names."""
        tools = collect_tools()
        for toolset_name, funcs in tools.items():
            names = []
            for fn in funcs:
                cmd_name, _, _ = build_command(fn, toolset_name)
                names.append(cmd_name)
            assert len(names) == len(set(names)), (
                f"Duplicate command names in {toolset_name}: "
                f"{[n for n in names if names.count(n) > 1]}"
            )
