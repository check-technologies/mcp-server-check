"""Embedded UI component tools for the Check API.

Replaces 35 individual component tools with 2 generic tools:
- list_component_types: discover available component types per entity
- create_component: create any component with entity_type + component_type
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import Ctx, check_api_post

COMPANY_COMPONENTS = [
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

EMPLOYEE_COMPONENTS = [
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

CONTRACTOR_COMPONENTS = [
    "tax_documents",
]

_ENTITY_COMPONENTS: dict[str, list[str]] = {
    "company": COMPANY_COMPONENTS,
    "employee": EMPLOYEE_COMPONENTS,
    "contractor": CONTRACTOR_COMPONENTS,
}

_ENTITY_PATH: dict[str, str] = {
    "company": "companies",
    "employee": "employees",
    "contractor": "contractors",
}


async def list_component_types(ctx: Ctx, entity_type: str | None = None) -> dict:
    """List available embedded UI component types.

    Returns the component types that can be created for each entity type.
    Use this to discover valid component_type values for create_component.

    Args:
        entity_type: Filter to a specific entity type ("company", "employee",
            or "contractor"). Omit to see all.
    """
    if entity_type is not None:
        components = _ENTITY_COMPONENTS.get(entity_type)
        if components is None:
            return {
                "error": True,
                "detail": (
                    f"Unknown entity_type: '{entity_type}'. "
                    f"Must be one of: {', '.join(sorted(_ENTITY_COMPONENTS))}."
                ),
            }
        return {"entity_type": entity_type, "component_types": components}
    return {
        entity: {"component_types": comps}
        for entity, comps in _ENTITY_COMPONENTS.items()
    }


async def create_component(
    ctx: Ctx,
    entity_type: str,
    entity_id: str,
    component_type: str,
    data: dict | None = None,
) -> dict:
    """Create an embedded UI component URL for a company, employee, or contractor.

    Returns a URL that can be embedded in an iframe to render the component.

    Args:
        entity_type: One of "company", "employee", or "contractor".
        entity_id: The Check entity ID (e.g. "com_xxxxx", "emp_xxxxx", "ctr_xxxxx").
        component_type: The component to create. Use list_component_types to see
            valid values (e.g. "tax_setup", "payment_setup", "run_payroll").
        data: Optional component configuration.
    """
    path_prefix = _ENTITY_PATH.get(entity_type)
    if path_prefix is None:
        return {
            "error": True,
            "detail": (
                f"Unknown entity_type: '{entity_type}'. "
                f"Must be one of: {', '.join(sorted(_ENTITY_PATH))}."
            ),
        }
    valid_types = _ENTITY_COMPONENTS.get(entity_type, [])
    if component_type not in valid_types:
        return {
            "error": True,
            "detail": (
                f"Unknown component_type '{component_type}' for {entity_type}. "
                f"Valid types: {', '.join(valid_types)}."
            ),
        }
    return await check_api_post(
        ctx,
        f"/{path_prefix}/{entity_id}/components/{component_type}",
        data=data,
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_component_types)
    if not read_only:
        mcp.add_tool(create_component)
