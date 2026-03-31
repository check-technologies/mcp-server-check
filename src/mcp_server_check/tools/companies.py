"""Company tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.types import Address
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
    check_api_put,
)


async def list_companies(
    ctx: Ctx,
    limit: int | None = None,
    active: bool | None = None,
    ids: list[str] | None = None,
    cursor: str | None = None,
) -> dict:
    """List companies in your Check account.

    Args:
        limit: Maximum number of results to return (default 10, max 100).
        active: Filter by active status.
        ids: Filter to specific company IDs.
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/companies",
        params=build_params(limit=limit, active=active, ids=ids, cursor=cursor),
    )


async def get_company(ctx: Ctx, company_id: str) -> dict:
    """Get details for a specific company.

    Args:
        company_id: The Check company ID (e.g. "com_xxxxx").
    """
    return await check_api_get(ctx, f"/companies/{company_id}")


async def create_company(
    ctx: Ctx,
    legal_name: str,
    trade_name: str | None = None,
    other_business_name: str | None = None,
    business_type: str | None = None,
    industry_type: str | None = None,
    website: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: Address | None = None,
    pay_frequency: str | None = None,
    start_date: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new company.

    Args:
        legal_name: The legal name of the company.
        trade_name: Trade name (DBA) of the company.
        other_business_name: Other business name used by the company.
        business_type: One of "sole_proprietorship", "partnership", "c_corporation",
            "s_corporation", or "llc".
        industry_type: Industry classification (e.g. "health_care", "restaurant",
            "financial_services", "general_construction_or_general_contracting", etc.).
        website: Company website URL.
        email: Email of the payroll department or administrator.
        phone: Company phone number.
        address: Address with keys: line1, line2, city, state, postal_code, country.
        pay_frequency: Default pay frequency — "weekly", "biweekly", "semimonthly",
            "monthly", "quarterly", or "annually".
        start_date: Date matching first payday using Check (YYYY-MM-DD).
        metadata: Additional JSON metadata string.
    """
    return await check_api_post(
        ctx,
        "/companies",
        data=build_body(
            {"legal_name": legal_name},
            trade_name=trade_name,
            other_business_name=other_business_name,
            business_type=business_type,
            industry_type=industry_type,
            website=website,
            email=email,
            phone=phone,
            address=address,
            pay_frequency=pay_frequency,
            start_date=start_date,
            metadata=metadata,
        ),
    )


async def update_company(
    ctx: Ctx,
    company_id: str,
    legal_name: str | None = None,
    trade_name: str | None = None,
    other_business_name: str | None = None,
    business_type: str | None = None,
    industry_type: str | None = None,
    website: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: Address | None = None,
    principal_place_of_business: str | None = None,
    pay_frequency: str | None = None,
    processing_period: str | None = None,
    start_date: str | None = None,
    metadata: str | None = None,
    default_bank_account: str | None = None,
) -> dict:
    """Update an existing company.

    Args:
        company_id: The Check company ID.
        legal_name: The legal name of the company.
        trade_name: Trade name (DBA) of the company.
        other_business_name: Other business name used by the company.
        business_type: One of "sole_proprietorship", "partnership", "c_corporation",
            "s_corporation", or "llc".
        industry_type: Industry classification.
        website: Company website URL.
        email: Email of the payroll department or administrator.
        phone: Company phone number.
        address: Address with keys: line1, line2, city, state, postal_code, country.
        principal_place_of_business: Workplace ID whose address prints on paystubs.
        pay_frequency: Default pay frequency — "weekly", "biweekly", "semimonthly",
            "monthly", "quarterly", or "annually".
        processing_period: Processing period — "three_day", "two_day", or "one_day".
        start_date: Date the company will start using Check (YYYY-MM-DD).
        metadata: Additional JSON metadata string.
        default_bank_account: ID of the company's default bank account.
    """
    return await check_api_patch(
        ctx,
        f"/companies/{company_id}",
        data=build_body(
            {},
            legal_name=legal_name,
            trade_name=trade_name,
            other_business_name=other_business_name,
            business_type=business_type,
            industry_type=industry_type,
            website=website,
            email=email,
            phone=phone,
            address=address,
            principal_place_of_business=principal_place_of_business,
            pay_frequency=pay_frequency,
            processing_period=processing_period,
            start_date=start_date,
            metadata=metadata,
            default_bank_account=default_bank_account,
        ),
    )


async def onboard_company(ctx: Ctx, company_id: str) -> dict:
    """Onboard a company, transitioning it to active status.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_post(ctx, f"/companies/{company_id}/onboard")


async def get_company_paydays(
    ctx: Ctx,
    company_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    pay_schedule: str | None = None,
) -> dict:
    """Get upcoming paydays for a company.

    Args:
        company_id: The Check company ID.
        start_date: Start of date range (YYYY-MM-DD).
        end_date: End of date range (YYYY-MM-DD).
        pay_schedule: Filter by pay schedule ID.
    """
    return await check_api_get(
        ctx,
        f"/companies/{company_id}/paydays",
        params=build_params(
            start_date=start_date, end_date=end_date, pay_schedule=pay_schedule
        ),
    )


async def list_company_tax_deposits(
    ctx: Ctx,
    company_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List tax deposits for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        f"/companies/{company_id}/tax_deposits",
        params=build_params(limit=limit, cursor=cursor),
    )


async def get_company_benefit_aggregations(
    ctx: Ctx,
    company_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Get benefit aggregations for a company.

    Args:
        company_id: The Check company ID.
        start_date: Start of date range (YYYY-MM-DD).
        end_date: End of date range (YYYY-MM-DD).
    """
    return await check_api_get(
        ctx,
        f"/companies/{company_id}/benefit_aggregations",
        params=build_params(start_date=start_date, end_date=end_date),
    )


# --- Reports ---

COMPANY_REPORT_TYPES = [
    "payroll_journal",
    "payroll_summary",
    "tax_liabilities",
    "contractor_payments",
    "child_support_payments",
    "w4_exemption_status",
    "applied_for_ids_detailed",
    "w2_preview",
]


async def get_company_report(
    ctx: Ctx,
    company_id: str,
    report_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
    year: str | None = None,
) -> dict:
    """Get a report for a company.

    Args:
        company_id: The Check company ID.
        report_type: One of: "payroll_journal", "payroll_summary", "tax_liabilities",
            "contractor_payments", "child_support_payments", "w4_exemption_status",
            "applied_for_ids_detailed", "w2_preview".
        start_date: Report start date (YYYY-MM-DD). Required for payroll_journal,
            payroll_summary, tax_liabilities, contractor_payments, child_support_payments.
        end_date: Report end date (YYYY-MM-DD). Required for the same reports as start_date.
        year: Tax year (e.g. "2025"). Required for w2_preview.
    """
    if report_type not in COMPANY_REPORT_TYPES:
        return {
            "error": True,
            "detail": (
                f"Unknown report_type: '{report_type}'. "
                f"Valid types: {', '.join(COMPANY_REPORT_TYPES)}."
            ),
        }
    return await check_api_get(
        ctx,
        f"/companies/{company_id}/reports/{report_type}",
        params=build_params(start_date=start_date, end_date=end_date, year=year),
    )


# --- Federal EIN Verifications ---


async def list_federal_ein_verifications(
    ctx: Ctx, company_id: str, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List federal EIN verifications for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        f"/companies/{company_id}/federal_ein_verifications",
        params=build_params(limit=limit, cursor=cursor),
    )


async def get_federal_ein_verification(
    ctx: Ctx, company_id: str, verification_id: str
) -> dict:
    """Get a specific federal EIN verification.

    Args:
        company_id: The Check company ID.
        verification_id: The verification ID.
    """
    return await check_api_get(
        ctx, f"/companies/{company_id}/federal_ein_verifications/{verification_id}"
    )


# --- Signatories ---


async def list_signatories(
    ctx: Ctx, company_id: str, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List signatories for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        f"/companies/{company_id}/signatories",
        params=build_params(limit=limit, cursor=cursor),
    )


async def create_signatory(
    ctx: Ctx,
    company_id: str,
    first_name: str,
    last_name: str,
    title: str,
    email: str,
    middle_name: str | None = None,
) -> dict:
    """Create a signatory for a company.

    Args:
        company_id: The Check company ID.
        first_name: Signatory's first name.
        last_name: Signatory's last name.
        title: Title representing the signer's relationship to the company
            (e.g. "Officer", "Manager").
        email: Signatory's email address.
        middle_name: Signatory's middle name.
    """
    return await check_api_post(
        ctx,
        f"/companies/{company_id}/signatories",
        data=build_body(
            {
                "first_name": first_name,
                "last_name": last_name,
                "title": title,
                "email": email,
            },
            middle_name=middle_name,
        ),
    )


# --- Enrollment Profile ---


async def get_enrollment_profile(ctx: Ctx, company_id: str) -> dict:
    """Get the enrollment profile for a company.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_get(ctx, f"/companies/{company_id}/enrollment_profile")


async def create_enrollment_profile(
    ctx: Ctx,
    company_id: str,
    employee_count: int | None = None,
    contractor_count: int | None = None,
    pay_period_amount: str | None = None,
    previous_payroll_provider: str | None = None,
    previous_payroll_provider_other: str | None = None,
    first_payroll: bool | None = None,
    first_payroll_of_year: bool | None = None,
    user_since: str | None = None,
    expected_first_payday: str | None = None,
    approved_for_payment_processing: bool | None = None,
    existing_payroll_customer_processing_period: str | None = None,
    average_monthly_revenue: float | None = None,
    earliest_known_revenue: str | None = None,
    months_on_previous_payroll_provider: int | None = None,
    social_media: list[str] | None = None,
    products_actively_used: list[str] | None = None,
    account_contacts: list[str] | None = None,
    fraud_score: float | None = None,
    predicted_fraud: bool | None = None,
    paying_user: bool | None = None,
    missed_payments_count: int | None = None,
    payroll_history_access_method: str | None = None,
    implementation_services_submission_comment: str | None = None,
) -> dict:
    """Create the enrollment profile for a company.

    Args:
        company_id: The Check company ID.
        employee_count: Number of W2 employees.
        contractor_count: Number of 1099 contractors.
        pay_period_amount: Estimated total pay per period (e.g. "50000.00").
        previous_payroll_provider: Previous provider (e.g. "gusto", "adp_run", "manual").
        previous_payroll_provider_other: Custom label if provider not in enum.
        first_payroll: Whether the company has ever paid people before.
        first_payroll_of_year: Whether this is the first payroll of the calendar year.
        user_since: Date company joined your platform (YYYY-MM-DD).
        expected_first_payday: Expected first payday on Check (YYYY-MM-DD).
        approved_for_payment_processing: Whether approved for payment processing.
        existing_payroll_customer_processing_period: Current processing period —
            "four_day", "two_day", or "one_day".
        average_monthly_revenue: Average monthly revenue.
        earliest_known_revenue: Earliest revenue date (YYYY-MM-DD).
        months_on_previous_payroll_provider: Months using previous provider.
        social_media: List of social media URLs.
        products_actively_used: Products used — "timetracking", "payments", "scheduling".
        account_contacts: Partner employee emails associated with the company.
        fraud_score: Fraud risk value between 0 and 100.
        predicted_fraud: Whether company is predicted fraudulent.
        paying_user: Whether company pays your platform for services.
        missed_payments_count: Number of failed payments to your platform.
        payroll_history_access_method: One of "authorized_access_to_previous_provider",
            "provided_credentials", or "provided_reports".
        implementation_services_submission_comment: Optional comment for submission.
    """
    return await check_api_put(
        ctx,
        f"/companies/{company_id}/enrollment_profile",
        data=build_body(
            {},
            employee_count=employee_count,
            contractor_count=contractor_count,
            pay_period_amount=pay_period_amount,
            previous_payroll_provider=previous_payroll_provider,
            previous_payroll_provider_other=previous_payroll_provider_other,
            first_payroll=first_payroll,
            first_payroll_of_year=first_payroll_of_year,
            user_since=user_since,
            expected_first_payday=expected_first_payday,
            approved_for_payment_processing=approved_for_payment_processing,
            existing_payroll_customer_processing_period=existing_payroll_customer_processing_period,
            average_monthly_revenue=average_monthly_revenue,
            earliest_known_revenue=earliest_known_revenue,
            months_on_previous_payroll_provider=months_on_previous_payroll_provider,
            social_media=social_media,
            products_actively_used=products_actively_used,
            account_contacts=account_contacts,
            fraud_score=fraud_score,
            predicted_fraud=predicted_fraud,
            paying_user=paying_user,
            missed_payments_count=missed_payments_count,
            payroll_history_access_method=payroll_history_access_method,
            implementation_services_submission_comment=implementation_services_submission_comment,
        ),
    )


async def update_enrollment_profile(
    ctx: Ctx,
    company_id: str,
    employee_count: int | None = None,
    contractor_count: int | None = None,
    pay_period_amount: str | None = None,
    previous_payroll_provider: str | None = None,
    previous_payroll_provider_other: str | None = None,
    first_payroll: bool | None = None,
    first_payroll_of_year: bool | None = None,
    user_since: str | None = None,
    expected_first_payday: str | None = None,
    approved_for_payment_processing: bool | None = None,
    existing_payroll_customer_processing_period: str | None = None,
    average_monthly_revenue: float | None = None,
    earliest_known_revenue: str | None = None,
    months_on_previous_payroll_provider: int | None = None,
    social_media: list[str] | None = None,
    products_actively_used: list[str] | None = None,
    account_contacts: list[str] | None = None,
    fraud_score: float | None = None,
    predicted_fraud: bool | None = None,
    paying_user: bool | None = None,
    missed_payments_count: int | None = None,
    payroll_history_access_method: str | None = None,
    implementation_services_submission_comment: str | None = None,
) -> dict:
    """Update the enrollment profile for a company.

    Args:
        company_id: The Check company ID.
        employee_count: Number of W2 employees.
        contractor_count: Number of 1099 contractors.
        pay_period_amount: Estimated total pay per period.
        previous_payroll_provider: Previous provider name.
        previous_payroll_provider_other: Custom label if provider not in enum.
        first_payroll: Whether the company has ever paid people before.
        first_payroll_of_year: Whether this is the first payroll of the calendar year.
        user_since: Date company joined your platform (YYYY-MM-DD).
        expected_first_payday: Expected first payday on Check (YYYY-MM-DD).
        approved_for_payment_processing: Whether approved for payment processing.
        existing_payroll_customer_processing_period: Current processing period.
        average_monthly_revenue: Average monthly revenue.
        earliest_known_revenue: Earliest revenue date (YYYY-MM-DD).
        months_on_previous_payroll_provider: Months using previous provider.
        social_media: List of social media URLs.
        products_actively_used: Products used — "timetracking", "payments", "scheduling".
        account_contacts: Partner employee emails.
        fraud_score: Fraud risk value between 0 and 100.
        predicted_fraud: Whether company is predicted fraudulent.
        paying_user: Whether company pays your platform for services.
        missed_payments_count: Number of failed payments.
        payroll_history_access_method: One of "authorized_access_to_previous_provider",
            "provided_credentials", or "provided_reports".
        implementation_services_submission_comment: Optional comment.
    """
    return await check_api_patch(
        ctx,
        f"/companies/{company_id}/enrollment_profile",
        data=build_body(
            {},
            employee_count=employee_count,
            contractor_count=contractor_count,
            pay_period_amount=pay_period_amount,
            previous_payroll_provider=previous_payroll_provider,
            previous_payroll_provider_other=previous_payroll_provider_other,
            first_payroll=first_payroll,
            first_payroll_of_year=first_payroll_of_year,
            user_since=user_since,
            expected_first_payday=expected_first_payday,
            approved_for_payment_processing=approved_for_payment_processing,
            existing_payroll_customer_processing_period=existing_payroll_customer_processing_period,
            average_monthly_revenue=average_monthly_revenue,
            earliest_known_revenue=earliest_known_revenue,
            months_on_previous_payroll_provider=months_on_previous_payroll_provider,
            social_media=social_media,
            products_actively_used=products_actively_used,
            account_contacts=account_contacts,
            fraud_score=fraud_score,
            predicted_fraud=predicted_fraud,
            paying_user=paying_user,
            missed_payments_count=missed_payments_count,
            payroll_history_access_method=payroll_history_access_method,
            implementation_services_submission_comment=implementation_services_submission_comment,
        ),
    )


# --- Implementation ---


async def start_implementation(ctx: Ctx, company_id: str) -> dict:
    """Start implementation for a company.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_post(ctx, f"/companies/{company_id}/start_implementation")


async def cancel_implementation(ctx: Ctx, company_id: str) -> dict:
    """Cancel implementation for a company.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_post(ctx, f"/companies/{company_id}/cancel_implementation")


async def request_embedded_setup(ctx: Ctx, company_id: str) -> dict:
    """Request embedded setup for a company.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_post(ctx, f"/companies/{company_id}/request_embedded_setup")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_companies)
    mcp.add_tool(get_company)
    mcp.add_tool(get_company_paydays)
    mcp.add_tool(list_company_tax_deposits)
    mcp.add_tool(get_company_benefit_aggregations)
    mcp.add_tool(get_company_report)
    mcp.add_tool(list_federal_ein_verifications)
    mcp.add_tool(get_federal_ein_verification)
    mcp.add_tool(list_signatories)
    mcp.add_tool(get_enrollment_profile)
    if not read_only:
        mcp.add_tool(create_company)
        mcp.add_tool(update_company)
        mcp.add_tool(onboard_company)
        mcp.add_tool(create_signatory)
        mcp.add_tool(create_enrollment_profile)
        mcp.add_tool(update_enrollment_profile)
        mcp.add_tool(start_implementation)
        mcp.add_tool(cancel_implementation)
        mcp.add_tool(request_embedded_setup)
