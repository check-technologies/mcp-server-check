"""Embedded UI component tools for the Check API.

Uses factory functions to generate tools for the uniform component pattern:
POST /{entity_type}/{entity_id}/components/{component_type}
"""

from __future__ import annotations

from typing import Callable

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import Ctx, check_api_post

# Component definitions: (entity_type, entity_prefix, component_name)
_COMPANY_COMPONENTS = [
    "previous_provider_access",
    "accounting_integration",
    "authorization_documents",
    "business_details",
    "checklist",
    "company_reports",
    "connect_bank_account",
    "details",
    "early_enrollment",
    "employee_setup",
    "filing_authorization",
    "filing_preview",
    "full_service_setup_submission",
    "integrations",
    "integrations_authorize",
    "pay_history",
    "payment_setup",
    "progress_tracker",
    "run_payroll",
    "signatory_agreements",
    "tax_documents",
    "tax_setup",
    "team_setup",
    "terms_of_service",
    "verification_documents",
]

_EMPLOYEE_COMPONENTS = [
    "benefits",
    "payment_setup",
    "paystubs",
    "post_tax_deductions",
    "profile",
    "ssn_setup",
    "tax_documents",
    "tax_setup",
    "withholdings_setup",
]

_CONTRACTOR_COMPONENTS = [
    "tax_documents",
]


def _make_component_tool(
    entity_type: str,
    entity_label: str,
    component_name: str,
) -> Callable:
    """Factory to create a component tool function."""
    tool_name = f"create_{entity_label}_{component_name}_component"
    entity_id_param = f"{entity_label}_id"

    async def component_tool(ctx: Ctx, entity_id: str, data: dict | None = None) -> dict:
        return await check_api_post(
            ctx,
            f"/{entity_type}/{entity_id}/components/{component_name}",
            data=data,
        )

    component_tool.__name__ = tool_name
    component_tool.__qualname__ = tool_name
    component_tool.__doc__ = (
        f"Create a {component_name.replace('_', ' ')} component for a {entity_label}.\n\n"
        f"Args:\n"
        f"    entity_id: The Check {entity_label} ID.\n"
        f"    data: Optional component configuration."
    )

    # Fix the parameter name in annotations for better tool schema
    component_tool.__annotations__ = {
        "ctx": Ctx,
        "entity_id": str,
        "data": "dict | None",
        "return": dict,
    }

    return component_tool


def _build_tools() -> list[Callable]:
    """Build all component tool functions."""
    tools = []
    for name in _COMPANY_COMPONENTS:
        tools.append(_make_component_tool("companies", "company", name))
    for name in _EMPLOYEE_COMPONENTS:
        tools.append(_make_component_tool("employees", "employee", name))
    for name in _CONTRACTOR_COMPONENTS:
        tools.append(_make_component_tool("contractors", "contractor", name))
    return tools


_ALL_TOOLS = _build_tools()


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    if read_only:
        return
    for tool in _ALL_TOOLS:
        mcp.add_tool(tool)
