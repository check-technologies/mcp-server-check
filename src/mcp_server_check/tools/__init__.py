"""Tool modules for the Check MCP server."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

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
    workflows,
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
    "workflows": workflows,
    "workplaces": workplaces,
}


def collect_all_tools() -> dict[str, list[Callable]]:
    """Return {toolset_name: [fn, ...]} for all toolsets.

    Calls each module's register() with a collector to capture tool functions.
    The collector advertises kwargs support so ``add_annotated_tool`` passes the
    raw function rather than a wrapped Tool object — the index needs the
    function for introspection and to derive Tool instances itself.
    """
    result: dict[str, list[Callable]] = {}
    for name, module in _TOOLSETS.items():
        functions: list[Callable] = []

        class _Collector:
            # Tells add_annotated_tool to pass the raw function so we can
            # introspect it during indexing.
            _annotated_tool_supports_kwargs = True

            @staticmethod
            def add_tool(fn: Callable, **kwargs: Any) -> None:
                functions.append(fn)

        module.register(_Collector(), read_only=False)
        result[name] = functions
    return result


def register_all(mcp: FastMCP, registry: dict[str, str]) -> None:
    """Register tools from every module, recording tool-to-toolset mappings.

    All tools are always registered (no read_only filtering at registration time).
    Filtering happens at request time via ToolFilter.

    Args:
        registry: Dict to populate with tool_name -> toolset_name mappings.
    """
    original_add_tool = mcp.add_tool

    current_toolset: list[str] = []

    def tracking_add_tool(tool, **kwargs):
        # ``tool`` may be a FunctionTool (the new annotated path) or a raw
        # callable (legacy / direct callers). Resolve the public tool name
        # from whichever shape was supplied.
        result = original_add_tool(tool, **kwargs)
        if hasattr(tool, "name"):
            tool_name = tool.name
        else:
            tool_name = kwargs.get("name") or tool.__name__
        registry[tool_name] = current_toolset[0]
        return result

    try:
        mcp.add_tool = tracking_add_tool  # type: ignore[assignment]
        for toolset_name, mod in _TOOLSETS.items():
            current_toolset.clear()
            current_toolset.append(toolset_name)
            mod.register(mcp, read_only=False)
    finally:
        mcp.add_tool = original_add_tool  # type: ignore[assignment]
