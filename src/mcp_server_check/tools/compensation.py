"""Compensation tools for the Check API (pay schedules, benefits, deductions, etc.).

Uses the declarative tool factory for standard CRUD operations,
with manual functions for non-standard endpoints.
"""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.helpers import Ctx, check_api_get
from mcp_server_check.tool_factory import Field, Resource, generate_tools

# ---------------------------------------------------------------------------
# Pay Schedules
# ---------------------------------------------------------------------------

_pay_schedules = Resource(
    name="pay_schedules",
    path="/pay_schedules",
    id_param="pay_schedule_id",
    id_description="The Check pay schedule ID.",
    description="pay schedules",
    list_filters=["company"],
    fields=[
        Field("company", str, required_for="create", doc="The Check company ID."),
        Field(
            "pay_frequency",
            str,
            required_for="create",
            doc='Pay frequency — "weekly", "biweekly", "semimonthly", "monthly", "quarterly", or "annually".',
        ),
        Field(
            "first_payday",
            str,
            required_for="create",
            doc="Payday date of the first payroll on this schedule (YYYY-MM-DD).",
        ),
        Field(
            "first_period_end",
            str,
            required_for="create",
            doc="Period end date of the first payroll on this schedule (YYYY-MM-DD).",
        ),
        Field(
            "second_payday",
            str,
            doc="Second payday date (semimonthly only; must be between one day and one month after first_payday).",
        ),
        Field("name", str, doc="Human-readable name for the pay schedule."),
        Field("metadata", str, doc="Additional JSON metadata string."),
    ],
)
_pay_schedule_tools = generate_tools(_pay_schedules)

list_pay_schedules = _pay_schedule_tools.list_fn
get_pay_schedule = _pay_schedule_tools.get_fn
create_pay_schedule = _pay_schedule_tools.create_fn
update_pay_schedule = _pay_schedule_tools.update_fn
delete_pay_schedule = _pay_schedule_tools.delete_fn


# Custom: get_pay_schedule_paydays is not a standard CRUD endpoint
async def get_pay_schedule_paydays(
    ctx: Ctx,
    pay_schedule_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Get paydays for a pay schedule.

    Args:
        pay_schedule_id: The Check pay schedule ID.
        start_date: Start of date range (YYYY-MM-DD).
        end_date: End of date range (YYYY-MM-DD).
    """
    params: dict = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await check_api_get(
        ctx, f"/pay_schedules/{pay_schedule_id}/paydays", params=params or None
    )


# ---------------------------------------------------------------------------
# Benefits (employee-level)
# ---------------------------------------------------------------------------

_benefits = Resource(
    name="benefits",
    path="/benefits",
    id_param="benefit_id",
    id_description="The Check benefit ID.",
    description="employee benefits",
    list_filters=["company", "employee", "include_external"],
    default_limit=500,
    fields=[
        Field("employee", str, required_for="create", doc="The Check employee ID."),
        Field(
            "company_benefit",
            str,
            required_for="create",
            doc="The Check company benefit ID.",
            create_only=True,
        ),
        Field(
            "include_external",
            bool,
            doc="Include external benefits. Defaults to false.",
        ),
        Field("benefit", str, doc="Type of supported benefit."),
        Field(
            "period",
            str,
            doc='Period over which a period amount is distributed — "monthly" or null.',
        ),
        Field(
            "description",
            str,
            doc="Description to distinguish the benefit within a plan (max 255 chars).",
        ),
        Field(
            "company_contribution_amount",
            str,
            doc="Company contribution amount per payroll.",
        ),
        Field(
            "company_contribution_percent",
            float,
            doc="Company contribution as percent of gross pay (0-100).",
        ),
        Field(
            "company_period_amount", str, doc="Company contribution over the period."
        ),
        Field(
            "employee_contribution_amount",
            str,
            doc="Employee contribution amount per payroll.",
        ),
        Field(
            "employee_contribution_percent",
            float,
            doc="Employee contribution as percent of gross pay (0-100).",
        ),
        Field(
            "employee_period_amount", str, doc="Employee contribution over the period."
        ),
        Field("effective_start", str, doc="Start date for the benefit (YYYY-MM-DD)."),
        Field("effective_end", str, doc="End date for the benefit (YYYY-MM-DD)."),
        Field("hsa_contribution_limit", str, doc="HSA contribution limit."),
        Field("metadata", str, doc="Additional JSON metadata string."),
    ],
)
_benefit_tools = generate_tools(_benefits)

list_benefits = _benefit_tools.list_fn
get_benefit = _benefit_tools.get_fn
create_benefit = _benefit_tools.create_fn
update_benefit = _benefit_tools.update_fn
delete_benefit = _benefit_tools.delete_fn


# ---------------------------------------------------------------------------
# Post-Tax Deductions
# ---------------------------------------------------------------------------

_post_tax_deductions = Resource(
    name="post_tax_deductions",
    path="/post_tax_deductions",
    id_param="deduction_id",
    id_description="The Check post-tax deduction ID.",
    description="post-tax deductions",
    list_filters=["company", "employee", "include_external"],
    default_limit=500,
    fields=[
        Field("employee", str, required_for="create", doc="The Check employee ID."),
        Field(
            "type",
            str,
            required_for="create",
            doc='Deduction type — "miscellaneous", "child_support", or "miscellaneous_garnishment".',
            create_only=True,
        ),
        Field(
            "description",
            str,
            required_for="create",
            doc="Description of the deduction (max 255 chars).",
        ),
        Field(
            "effective_start",
            str,
            required_for="create",
            doc="Start date for the deduction (YYYY-MM-DD).",
        ),
        Field("effective_end", str, doc="End date for the deduction (YYYY-MM-DD)."),
        Field(
            "miscellaneous",
            dict,
            doc="Config dict for miscellaneous type with keys: total_amount, amount, percent, annual_limit.",
        ),
        Field(
            "child_support",
            dict,
            doc="Config dict for child_support type with keys: external_id, agency, fips_code, issue_date, amount, max_percent.",
        ),
        Field(
            "miscellaneous_garnishment",
            dict,
            doc="Config dict for miscellaneous_garnishment type with keys: amount, percent, total_amount, annual_limit, priority, max_percent.",
        ),
        Field("metadata", str, doc="Additional JSON metadata string."),
        Field(
            "managed",
            bool,
            doc="Whether the deduction should be remitted by Check (child support only).",
        ),
        Field(
            "include_external",
            bool,
            doc="Include external deductions. Defaults to false.",
        ),
    ],
)
_post_tax_deduction_tools = generate_tools(_post_tax_deductions)

list_post_tax_deductions = _post_tax_deduction_tools.list_fn
get_post_tax_deduction = _post_tax_deduction_tools.get_fn
create_post_tax_deduction = _post_tax_deduction_tools.create_fn
update_post_tax_deduction = _post_tax_deduction_tools.update_fn
delete_post_tax_deduction = _post_tax_deduction_tools.delete_fn


# ---------------------------------------------------------------------------
# Company Benefits
# ---------------------------------------------------------------------------

_company_benefits = Resource(
    name="company_benefits",
    path="/company_benefits",
    id_param="company_benefit_id",
    id_description="The Check company benefit ID.",
    description="company-level benefits",
    list_filters=["company"],
    default_limit=500,
    fields=[
        Field(
            "company",
            str,
            required_for="create",
            doc="The Check company ID.",
            create_only=True,
        ),
        Field("benefit", str, required_for="create", doc="Type of supported benefit."),
        Field(
            "description",
            str,
            required_for="create",
            doc="Description to distinguish the benefit (max 255 chars).",
        ),
        Field(
            "period",
            str,
            doc='Period over which a period amount is distributed — "monthly" or null.',
        ),
        Field(
            "company_contribution_amount",
            str,
            doc="Default company contribution per payroll.",
        ),
        Field(
            "company_contribution_percent",
            str,
            doc="Default company contribution as percent of gross (0-100).",
        ),
        Field(
            "company_period_amount",
            str,
            doc="Default company contribution over the period.",
        ),
        Field(
            "employee_contribution_amount",
            str,
            doc="Default employee contribution per payroll.",
        ),
        Field(
            "employee_contribution_percent",
            str,
            doc="Default employee contribution as percent of gross (0-100).",
        ),
        Field(
            "employee_period_amount",
            str,
            doc="Default employee contribution over the period.",
        ),
        Field("effective_start", str, doc="Start date for the benefit (YYYY-MM-DD)."),
        Field("effective_end", str, doc="End date for the benefit (YYYY-MM-DD)."),
        Field("metadata", str, doc="Additional JSON metadata string."),
    ],
)
_company_benefit_tools = generate_tools(_company_benefits)

list_company_benefits = _company_benefit_tools.list_fn
get_company_benefit = _company_benefit_tools.get_fn
create_company_benefit = _company_benefit_tools.create_fn
update_company_benefit = _company_benefit_tools.update_fn
delete_company_benefit = _company_benefit_tools.delete_fn


# ---------------------------------------------------------------------------
# Earning Rates
# ---------------------------------------------------------------------------

_earning_rates = Resource(
    name="earning_rates",
    path="/earning_rates",
    id_param="earning_rate_id",
    id_description="The Check earning rate ID.",
    description="earning rates",
    list_filters=["company", "employee", "active"],
    has_delete=False,
    default_limit=500,
    fields=[
        Field(
            "employee",
            str,
            required_for="create",
            doc="The Check employee ID.",
            create_only=True,
        ),
        Field(
            "amount",
            str,
            required_for="create",
            doc='The earning rate amount (e.g. "25.00" or "52000.00").',
            create_only=True,
        ),
        Field(
            "period",
            str,
            required_for="create",
            doc='Period type — "hourly", "annually", or "piece".',
            create_only=True,
        ),
        Field("name", str, doc="Name of the earning rate."),
        Field(
            "workweek_hours",
            float,
            doc="Hours per week the employee works. Default: 40.",
            create_only=True,
        ),
        Field(
            "active", bool, doc="Whether the earning rate is active.", update_only=True
        ),
        Field(
            "metadata", str, doc="Additional JSON metadata string.", update_only=True
        ),
    ],
)
_earning_rate_tools = generate_tools(_earning_rates)

list_earning_rates = _earning_rate_tools.list_fn
get_earning_rate = _earning_rate_tools.get_fn
create_earning_rate = _earning_rate_tools.create_fn
update_earning_rate = _earning_rate_tools.update_fn


# ---------------------------------------------------------------------------
# Earning Codes
# ---------------------------------------------------------------------------

_earning_codes = Resource(
    name="earning_codes",
    path="/earning_codes",
    id_param="earning_code_id",
    id_description="The Check earning code ID.",
    description="earning codes",
    list_filters=["company"],
    has_delete=False,
    fields=[
        Field(
            "company",
            str,
            required_for="create",
            doc="The Check company ID.",
            create_only=True,
        ),
        Field(
            "name",
            str,
            required_for="create",
            doc="Name of the earning code.",
            create_only=True,
        ),
        Field(
            "type",
            str,
            required_for="create",
            doc="Type of earning code.",
            create_only=True,
        ),
        Field("active", bool, doc="Whether the code is active."),
        Field(
            "calculation_overrides",
            dict,
            doc='Tax calculation overrides dict. May include "wa_risk_class_code" (format "####-##" for WA L&I).',
            create_only=True,
        ),
        Field("metadata", str, doc="Additional JSON metadata string."),
    ],
)
_earning_code_tools = generate_tools(_earning_codes)

list_earning_codes = _earning_code_tools.list_fn
get_earning_code = _earning_code_tools.get_fn
create_earning_code = _earning_code_tools.create_fn
update_earning_code = _earning_code_tools.update_fn


# ---------------------------------------------------------------------------
# Net Pay Splits
# ---------------------------------------------------------------------------

_net_pay_splits = Resource(
    name="net_pay_splits",
    path="/net_pay_splits",
    id_param="net_pay_split_id",
    id_description="The Check net pay split ID.",
    description="net pay splits",
    list_filters=["company", "employee", "contractor"],
    has_delete=False,
    default_limit=500,
    fields=[
        Field(
            "splits",
            list,
            required_for="create",
            doc='Prioritized list of split dicts. Each may include "bank_account", "priority" (int), "amount", "percentage".',
        ),
        Field("employee", str, doc="The Check employee ID."),
        Field("contractor", str, doc="The Check contractor ID."),
        Field("is_default", bool, doc="Whether this is the default net pay split."),
    ],
)
_net_pay_split_tools = generate_tools(_net_pay_splits)

list_net_pay_splits = _net_pay_split_tools.list_fn
get_net_pay_split = _net_pay_split_tools.get_fn
create_net_pay_split = _net_pay_split_tools.create_fn


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    # Pay Schedules
    mcp.add_tool(list_pay_schedules)
    mcp.add_tool(get_pay_schedule)
    mcp.add_tool(get_pay_schedule_paydays)
    # Benefits
    mcp.add_tool(list_benefits)
    mcp.add_tool(get_benefit)
    # Post-Tax Deductions
    mcp.add_tool(list_post_tax_deductions)
    mcp.add_tool(get_post_tax_deduction)
    # Company Benefits
    mcp.add_tool(list_company_benefits)
    mcp.add_tool(get_company_benefit)
    # Earning Rates
    mcp.add_tool(list_earning_rates)
    mcp.add_tool(get_earning_rate)
    # Earning Codes
    mcp.add_tool(list_earning_codes)
    mcp.add_tool(get_earning_code)
    # Net Pay Splits
    mcp.add_tool(list_net_pay_splits)
    mcp.add_tool(get_net_pay_split)
    if not read_only:
        # Pay Schedules
        mcp.add_tool(create_pay_schedule)
        mcp.add_tool(update_pay_schedule)
        mcp.add_tool(delete_pay_schedule)
        # Benefits
        mcp.add_tool(create_benefit)
        mcp.add_tool(update_benefit)
        mcp.add_tool(delete_benefit)
        # Post-Tax Deductions
        mcp.add_tool(create_post_tax_deduction)
        mcp.add_tool(update_post_tax_deduction)
        mcp.add_tool(delete_post_tax_deduction)
        # Company Benefits
        mcp.add_tool(create_company_benefit)
        mcp.add_tool(update_company_benefit)
        mcp.add_tool(delete_company_benefit)
        # Earning Rates
        mcp.add_tool(create_earning_rate)
        mcp.add_tool(update_earning_rate)
        # Earning Codes
        mcp.add_tool(create_earning_code)
        mcp.add_tool(update_earning_code)
        # Net Pay Splits
        mcp.add_tool(create_net_pay_split)
