"""Workflow-level composite tools for common multi-step operations.

These tools compose multiple API calls server-side, saving the LLM
3-4 round-trips per operation.
"""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import Ctx, check_api_get, check_api_list


async def get_company_overview(
    ctx: Ctx,
    company_id: str,
    include_employees: bool = True,
    include_payrolls: bool = True,
    include_bank_accounts: bool = True,
    employee_limit: int = 10,
    payroll_limit: int = 5,
) -> dict:
    """Get a comprehensive overview of a company in a single call.

    Returns the company details along with its employees, recent payrolls,
    and bank accounts. This replaces 4 separate API calls.

    Args:
        company_id: The Check company ID (e.g. "com_xxxxx").
        include_employees: Include the company's employees (default true).
        include_payrolls: Include recent payrolls (default true).
        include_bank_accounts: Include bank accounts (default true).
        employee_limit: Max employees to return (default 10).
        payroll_limit: Max payrolls to return (default 5).
    """
    # Always fetch the company
    tasks: dict[str, asyncio.Task] = {}
    async with asyncio.TaskGroup() as tg:
        tasks["company"] = tg.create_task(
            check_api_get(ctx, f"/companies/{company_id}")
        )
        if include_employees:
            tasks["employees"] = tg.create_task(
                check_api_list(
                    ctx,
                    "/employees",
                    params={"company": company_id, "limit": employee_limit},
                )
            )
        if include_payrolls:
            tasks["payrolls"] = tg.create_task(
                check_api_list(
                    ctx,
                    "/payrolls",
                    params={"company": company_id, "limit": payroll_limit},
                )
            )
        if include_bank_accounts:
            tasks["bank_accounts"] = tg.create_task(
                check_api_list(
                    ctx,
                    "/bank_accounts",
                    params={"company": company_id},
                )
            )

    result: dict = {"company": tasks["company"].result()}
    if "employees" in tasks:
        result["employees"] = tasks["employees"].result()
    if "payrolls" in tasks:
        result["payrolls"] = tasks["payrolls"].result()
    if "bank_accounts" in tasks:
        result["bank_accounts"] = tasks["bank_accounts"].result()
    return result


async def get_employee_snapshot(
    ctx: Ctx,
    employee_id: str,
    include_tax_params: bool = True,
    include_paystubs: bool = True,
    paystub_limit: int = 5,
) -> dict:
    """Get a comprehensive snapshot of an employee in a single call.

    Returns employee details along with their tax parameters and recent
    paystubs. This replaces 3 separate API calls.

    Args:
        employee_id: The Check employee ID (e.g. "emp_xxxxx").
        include_tax_params: Include employee tax parameters (default true).
        include_paystubs: Include recent paystubs (default true).
        paystub_limit: Max paystubs to return (default 5).
    """
    tasks: dict[str, asyncio.Task] = {}
    async with asyncio.TaskGroup() as tg:
        tasks["employee"] = tg.create_task(
            check_api_get(ctx, f"/employees/{employee_id}")
        )
        if include_tax_params:
            tasks["tax_params"] = tg.create_task(
                check_api_get(ctx, f"/employee_tax_params/{employee_id}")
            )
        if include_paystubs:
            tasks["paystubs"] = tg.create_task(
                check_api_list(
                    ctx,
                    f"/employees/{employee_id}/paystubs",
                    params={"limit": paystub_limit},
                )
            )

    result: dict = {"employee": tasks["employee"].result()}
    if "tax_params" in tasks:
        result["tax_params"] = tasks["tax_params"].result()
    if "paystubs" in tasks:
        result["paystubs"] = tasks["paystubs"].result()
    return result


async def diagnose_payment(
    ctx: Ctx,
    payment_id: str,
) -> dict:
    """Get a diagnostic view of a payment with its attempts and related payroll item.

    Useful for debugging failed or stuck payments. Returns the payment,
    its payment attempts, and (if linked) the originating payroll item.
    This replaces 3 separate API calls.

    Args:
        payment_id: The Check payment ID (e.g. "pmt_xxxxx").
    """
    tasks: dict[str, asyncio.Task] = {}
    async with asyncio.TaskGroup() as tg:
        tasks["payment"] = tg.create_task(check_api_get(ctx, f"/payments/{payment_id}"))
        tasks["attempts"] = tg.create_task(
            check_api_list(ctx, f"/payments/{payment_id}/payment_attempts")
        )

    payment = tasks["payment"].result()
    result: dict = {
        "payment": payment,
        "payment_attempts": tasks["attempts"].result(),
    }

    # If the payment has a payroll_item, fetch it too
    payroll_item_id = None
    if isinstance(payment, dict) and "error" not in payment:
        payroll_item_id = payment.get("payroll_item")
    if payroll_item_id:
        payroll_item = await check_api_get(ctx, f"/payroll_items/{payroll_item_id}")
        result["payroll_item"] = payroll_item

    return result


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(get_company_overview)
    mcp.add_tool(get_employee_snapshot)
    mcp.add_tool(diagnose_payment)
