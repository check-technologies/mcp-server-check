"""Tool modules for the Check MCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import (
    bank_accounts,
    companies,
    compensation,
    components,
    contractor_payments,
    contractors,
    documents,
    employees,
    external_payrolls,
    forms,
    payments,
    payroll_items,
    payrolls,
    platform,
    tax,
    webhooks,
    workplaces,
)

_MODULES = [
    bank_accounts,
    companies,
    compensation,
    components,
    contractor_payments,
    contractors,
    documents,
    employees,
    external_payrolls,
    forms,
    payroll_items,
    payrolls,
    payments,
    platform,
    tax,
    webhooks,
    workplaces,
]


def register_all(mcp: FastMCP, *, read_only: bool = False) -> None:
    """Register tools from every module.

    Args:
        read_only: When True, only register read-only tools (list/get/download/preview).
            Write, update, delete, and other mutating tools are skipped.
    """
    for mod in _MODULES:
        mod.register(mcp, read_only=read_only)
