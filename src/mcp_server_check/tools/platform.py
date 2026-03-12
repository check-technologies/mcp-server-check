"""Platform and admin tools for the Check API."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


# --- Notifications ---


async def list_notifications(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List notifications, optionally filtered by company.

    Args:
        company: Filter to notifications belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/notifications", params=params or None)


async def get_notification(ctx: Ctx, notification_id: str) -> dict:
    """Get a specific notification.

    Args:
        notification_id: The notification ID.
    """
    return await check_api_get(ctx, f"/notifications/{notification_id}")


# --- Communications ---


async def list_communications(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List communications, optionally filtered by company.

    Args:
        company: Filter to communications belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/communications", params=params or None)


async def get_communication(ctx: Ctx, communication_id: str) -> dict:
    """Get a specific communication.

    Args:
        communication_id: The communication ID.
    """
    return await check_api_get(ctx, f"/communications/{communication_id}")


async def create_communication(
    ctx: Ctx,
    company: str,
    type: str | None = None,
    email: dict | None = None,
) -> dict:
    """Create a new communication.

    Args:
        company: The Check company ID the communication is in reference to.
        type: Communication type. Default: "email".
        email: Email details dict with keys: to (list of emails, required),
            from (sender email, required), cc (list of emails), subject (required),
            message (required).
    """
    body: dict = {"company": company}
    if type is not None:
        body["type"] = type
    if email is not None:
        body["email"] = email
    return await check_api_post(ctx, "/communications", data=body)


# --- Usage ---


async def list_usage_summaries(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List usage summaries.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/usage_summaries", params=params or None)


async def list_usage_records(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List usage records.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/usage_records", params=params or None)


# --- Integrations ---


async def list_integration_partners(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List integration partners.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/integration_partners", params=params or None)


async def get_integration_partner(ctx: Ctx, partner_id: str) -> dict:
    """Get a specific integration partner.

    Args:
        partner_id: The integration partner ID.
    """
    return await check_api_get(ctx, f"/integration_partners/{partner_id}")


async def authorize_integration_partner(
    ctx: Ctx, partner_id: str, data: dict | None = None
) -> dict:
    """Authorize an integration partner.

    Args:
        partner_id: The integration partner ID.
        data: Authorization details.
    """
    return await check_api_post(
        ctx, f"/integration_partners/{partner_id}/authorize", data=data
    )


async def list_integration_permissions(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List integration permissions.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, "/integration_permissions", params=params or None
    )


async def get_integration_permission(ctx: Ctx, permission_id: str) -> dict:
    """Get a specific integration permission.

    Args:
        permission_id: The integration permission ID.
    """
    return await check_api_get(ctx, f"/integration_permissions/{permission_id}")


async def list_integration_accesses(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List integration accesses.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/integration_accesses", params=params or None)


# --- Accounting Integrations ---


async def list_accounting_accounts(
    ctx: Ctx, company_id: str, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List accounting accounts for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/companies/{company_id}/accounting_accounts", params=params or None
    )


async def refresh_accounting_accounts(ctx: Ctx, company_id: str) -> dict:
    """Refresh accounting accounts for a company.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_post(
        ctx, f"/companies/{company_id}/accounting_accounts/refresh"
    )


async def get_accounting_mappings(ctx: Ctx, company_id: str) -> dict:
    """Get accounting mappings for a company.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_get(ctx, f"/companies/{company_id}/accounting_mappings")


async def update_accounting_mappings(
    ctx: Ctx, company_id: str, data: dict
) -> dict:
    """Update accounting mappings for a company.

    The payload is a complex structure — pass the full request body as a dict.

    Args:
        company_id: The Check company ID.
        data: Mapping fields to update.
    """
    return await check_api_patch(
        ctx, f"/companies/{company_id}/accounting_mappings", data=data
    )


async def toggle_accounting_mappings(
    ctx: Ctx, company_id: str, data: dict
) -> dict:
    """Toggle accounting mappings for a company.

    The payload is a complex structure — pass the full request body as a dict.

    Args:
        company_id: The Check company ID.
        data: Toggle configuration.
    """
    return await check_api_post(
        ctx, f"/companies/{company_id}/accounting_mappings/toggle", data=data
    )


async def sync_accounting(ctx: Ctx, company_id: str, data: dict | None = None) -> dict:
    """Trigger an accounting sync for a company.

    Args:
        company_id: The Check company ID.
        data: Sync configuration.
    """
    return await check_api_post(
        ctx, f"/companies/{company_id}/accounting_sync", data=data
    )


async def list_accounting_sync_attempts(
    ctx: Ctx, company_id: str, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List accounting sync attempts for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/companies/{company_id}/accounting_sync_attempts", params=params or None
    )


# --- Company Groups ---


async def list_company_groups(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List company groups.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/company_groups", params=params or None)


async def create_company_group(
    ctx: Ctx,
    name: str | None = None,
    companies: list[dict] | None = None,
) -> dict:
    """Create a new company group.

    Args:
        name: Name of the company group.
        companies: List of company dicts, each with an "id" key (the company ID).
    """
    body: dict = {}
    if name is not None:
        body["name"] = name
    if companies is not None:
        body["companies"] = companies
    return await check_api_post(ctx, "/company_groups", data=body)


async def update_company_group(
    ctx: Ctx,
    group_id: str,
    name: str | None = None,
    companies: list[dict] | None = None,
) -> dict:
    """Update a company group.

    Args:
        group_id: The company group ID.
        name: Name of the company group.
        companies: List of company dicts, each with an "id" key (the company ID).
    """
    body: dict = {}
    if name is not None:
        body["name"] = name
    if companies is not None:
        body["companies"] = companies
    return await check_api_patch(ctx, f"/company_groups/{group_id}", data=body)


# --- Addresses ---


async def validate_address(
    ctx: Ctx,
    line1: str,
    city: str,
    state: str,
    postal_code: str,
    line2: str | None = None,
    country: str | None = None,
) -> dict:
    """Validate an address.

    Args:
        line1: Street address or PO Box.
        city: City, district, suburb, town, or village.
        state: 2-digit state code.
        postal_code: 5-digit postal code or zip code.
        line2: Apartment, suite, unit, or building.
        country: Country code. Default: "US".
    """
    body: dict = {
        "line1": line1,
        "city": city,
        "state": state,
        "postal_code": postal_code,
    }
    if line2 is not None:
        body["line2"] = line2
    if country is not None:
        body["country"] = country
    return await check_api_post(ctx, "/addresses/validate", data=body)


# --- Setups ---


async def list_setups(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List setups, optionally filtered by company.

    Args:
        company: Filter to setups belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/setups", params=params or None)


async def get_setup(ctx: Ctx, setup_id: str) -> dict:
    """Get a specific setup.

    Args:
        setup_id: The setup ID.
    """
    return await check_api_get(ctx, f"/setups/{setup_id}")


# --- Requirements ---


async def list_requirements(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List requirements, optionally filtered by company.

    Args:
        company: Filter to requirements belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/requirements", params=params or None)


async def get_requirement(ctx: Ctx, requirement_id: str) -> dict:
    """Get a specific requirement.

    Args:
        requirement_id: The requirement ID.
    """
    return await check_api_get(ctx, f"/requirements/{requirement_id}")


# --- Reports ---


async def get_applied_for_ids_report(ctx: Ctx) -> dict:
    """Get the applied-for IDs report across all companies."""
    return await check_api_get(ctx, "/reports/applied_for_ids")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    # Notifications
    mcp.add_tool(list_notifications)
    mcp.add_tool(get_notification)
    # Communications
    mcp.add_tool(list_communications)
    mcp.add_tool(get_communication)
    # Usage
    mcp.add_tool(list_usage_summaries)
    mcp.add_tool(list_usage_records)
    # Integrations
    mcp.add_tool(list_integration_partners)
    mcp.add_tool(get_integration_partner)
    mcp.add_tool(list_integration_permissions)
    mcp.add_tool(get_integration_permission)
    mcp.add_tool(list_integration_accesses)
    # Accounting Integrations
    mcp.add_tool(list_accounting_accounts)
    mcp.add_tool(get_accounting_mappings)
    mcp.add_tool(list_accounting_sync_attempts)
    # Company Groups
    mcp.add_tool(list_company_groups)
    # Addresses
    mcp.add_tool(validate_address)
    # Setups
    mcp.add_tool(list_setups)
    mcp.add_tool(get_setup)
    # Requirements
    mcp.add_tool(list_requirements)
    mcp.add_tool(get_requirement)
    # Reports
    mcp.add_tool(get_applied_for_ids_report)
    if not read_only:
        mcp.add_tool(create_communication)
        mcp.add_tool(authorize_integration_partner)
        mcp.add_tool(refresh_accounting_accounts)
        mcp.add_tool(update_accounting_mappings)
        mcp.add_tool(toggle_accounting_mappings)
        mcp.add_tool(sync_accounting)
        mcp.add_tool(create_company_group)
        mcp.add_tool(update_company_group)
