"""End-to-end tests for the Check CLI."""

from __future__ import annotations

import json

import httpx
import respx
from click.testing import CliRunner

from mcp_server_check.cli import cli

BASE_URL = "https://sandbox.checkhq.com"
RUNNER_ENV = {"CHECK_API_KEY": "sk_test_123"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _invoke(*args: str, env: dict | None = None, **kwargs) -> object:
    runner = CliRunner()
    merged_env = {**RUNNER_ENV, **(env or {})}
    return runner.invoke(cli, list(args), env=merged_env, **kwargs)


# ---------------------------------------------------------------------------
# Basic CLI tests
# ---------------------------------------------------------------------------


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Check Payroll API CLI" in result.output
    assert "companies" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help_without_api_key():
    """--help should work without an API key."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"], env={"CHECK_API_KEY": ""})
    assert result.exit_code == 0
    assert "companies" in result.output


def test_companies_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["companies", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "get" in result.output
    assert "create" in result.output


# ---------------------------------------------------------------------------
# Command execution with mocked API
# ---------------------------------------------------------------------------


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_companies_list(respx_mock):
    respx_mock.get("/companies").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"id": "com_001", "legal_name": "Acme"}], "next": None, "previous": None},
        )
    )
    result = _invoke("companies", "list")
    assert result.exit_code == 0
    data = json.loads(result.output.strip())
    assert data["results"][0]["id"] == "com_001"


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_companies_get(respx_mock):
    respx_mock.get("/companies/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001", "legal_name": "Acme"})
    )
    result = _invoke("companies", "get", "com_001")
    assert result.exit_code == 0
    data = json.loads(result.output.strip())
    assert data["id"] == "com_001"
    assert data["legal_name"] == "Acme"


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_companies_create(respx_mock):
    respx_mock.post("/companies").mock(
        return_value=httpx.Response(201, json={"id": "com_new", "legal_name": "New Co"})
    )
    result = _invoke("companies", "create", "--legal-name", "New Co")
    assert result.exit_code == 0
    data = json.loads(result.output.strip())
    assert data["id"] == "com_new"


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_companies_create_with_address_json(respx_mock):
    route = respx_mock.post("/companies").mock(
        return_value=httpx.Response(201, json={"id": "com_addr"})
    )
    result = _invoke(
        "companies",
        "create",
        "--legal-name",
        "Addr Co",
        "--address",
        '{"line1": "123 Main St", "city": "SF", "state": "CA", "postal_code": "94105"}',
    )
    assert result.exit_code == 0
    body = json.loads(route.calls[0].request.content)
    assert body["address"]["line1"] == "123 Main St"


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_employees_list_with_options(respx_mock):
    route = respx_mock.get("/employees").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"id": "emp_001"}], "next": None, "previous": None},
        )
    )
    result = _invoke("employees", "list", "--company", "com_001", "--limit", "5")
    assert result.exit_code == 0
    url = str(route.calls[0].request.url)
    assert "company=com_001" in url
    assert "limit=5" in url


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_employees_get_paystub(respx_mock):
    """Multi-ID positional args work."""
    respx_mock.get("/employees/emp_001/paystubs/prl_001").mock(
        return_value=httpx.Response(200, json={"id": "emp_001", "payroll": "prl_001"})
    )
    result = _invoke("employees", "get-paystub", "emp_001", "prl_001")
    assert result.exit_code == 0
    data = json.loads(result.output.strip())
    assert data["payroll"] == "prl_001"


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_format_table(respx_mock):
    respx_mock.get("/companies").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [{"id": "com_001", "legal_name": "Acme"}],
                "next": None,
                "previous": None,
            },
        )
    )
    result = _invoke("--format", "table", "companies", "list")
    assert result.exit_code == 0
    assert "ID" in result.output
    assert "com_001" in result.output
    assert "Acme" in result.output


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_format_json_compact(respx_mock):
    respx_mock.get("/companies/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001"})
    )
    result = _invoke("companies", "get", "com_001")
    assert result.exit_code == 0
    # Compact JSON has no extra spaces
    assert result.output.strip() == '{"id":"com_001"}'


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_api_error_returns_exit_code_1(respx_mock):
    respx_mock.get("/companies/com_bad").mock(
        return_value=httpx.Response(404, json={"error": "not_found"})
    )
    result = _invoke("companies", "get", "com_bad")
    assert result.exit_code == 1
    # Error output goes to stderr
    assert "error" in result.stderr


def test_missing_api_key():
    runner = CliRunner()
    result = runner.invoke(cli, ["companies", "list"], env={"CHECK_API_KEY": ""})
    assert result.exit_code == 3
    assert "CHECK_API_KEY" in result.stderr


def test_missing_required_option():
    """create requires --legal-name."""
    result = _invoke("companies", "create")
    assert result.exit_code == 2
    assert "legal-name" in result.output or "legal-name" in result.stderr


# ---------------------------------------------------------------------------
# Environment / --env switching
# ---------------------------------------------------------------------------


@respx.mock(base_url="https://api.checkhq.com", assert_all_called=False)
def test_production_env(respx_mock):
    respx_mock.get("/companies").mock(
        return_value=httpx.Response(
            200, json={"results": [], "next": None, "previous": None}
        )
    )
    result = _invoke("--env", "production", "companies", "list")
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_read_only_hides_write_commands():
    runner = CliRunner()
    result = runner.invoke(cli, ["--read-only", "companies", "--help"])
    assert result.exit_code == 0
    assert "create" not in result.output
    assert "update" not in result.output
    assert "onboard" not in result.output
    assert "list" in result.output
    assert "get" in result.output


def test_toolsets_env_filters_groups():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"], env={"CHECK_TOOLSETS": "companies"})
    assert result.exit_code == 0
    assert "companies" in result.output
    assert "employees" not in result.output


def test_toolsets_env_blocks_access():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["employees", "--help"], env={"CHECK_TOOLSETS": "companies"}
    )
    assert result.exit_code == 2


@respx.mock(base_url=BASE_URL, assert_all_called=False)
def test_read_only_env_blocks_write(respx_mock):
    """CHECK_READ_ONLY=1 should block create commands at runtime."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["companies", "create", "--legal-name", "Nope"],
        env={"CHECK_API_KEY": "sk_test_123", "CHECK_READ_ONLY": "1"},
    )
    # Command should not be found (hidden by filter)
    assert result.exit_code == 2
