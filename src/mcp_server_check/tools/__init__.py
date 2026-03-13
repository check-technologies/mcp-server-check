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

_TOOLSETS = {
    "bank_accounts": bank_accounts,
    "companies": companies,
    "compensation": compensation,
    "components": components,
    "contractor_payments": contractor_payments,
    "contractors": contractors,
    "documents": documents,
    "employees": employees,
    "external_payrolls": external_payrolls,
    "forms": forms,
    "payroll_items": payroll_items,
    "payrolls": payrolls,
    "payments": payments,
    "platform": platform,
    "tax": tax,
    "webhooks": webhooks,
    "workplaces": workplaces,
}


def register_all(mcp: FastMCP, registry: dict[str, str]) -> None:
    """Register tools from every module, recording tool-to-toolset mappings.

    All tools are always registered (no read_only filtering at registration time).
    Filtering happens at request time via ToolFilter.

    Args:
        registry: Dict to populate with tool_name -> toolset_name mappings.
    """
    original_add_tool = mcp.add_tool

    current_toolset: list[str] = []

    def tracking_add_tool(fn, **kwargs):
        original_add_tool(fn, **kwargs)
        tool_name = kwargs.get("name") or fn.__name__
        registry[tool_name] = current_toolset[0]

    try:
        mcp.add_tool = tracking_add_tool  # type: ignore[assignment]
        for toolset_name, mod in _TOOLSETS.items():
            current_toolset.clear()
            current_toolset.append(toolset_name)
            mod.register(mcp, read_only=False)
    finally:
        mcp.add_tool = original_add_tool  # type: ignore[assignment]
