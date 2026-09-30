"""Shared types for the Check MCP server."""

from __future__ import annotations

from typing_extensions import TypedDict


class Address(TypedDict, total=False):
    """A US mailing address. All keys are optional at the type level; the API
    will enforce which ones are required for each endpoint."""

    line1: str
    """Street address or PO Box."""

    line2: str
    """Apartment, suite, unit, or building."""

    city: str
    """City, district, suburb, town, or village."""

    state: str
    """2-letter state code (e.g. "CA")."""

    postal_code: str
    """5-digit ZIP / postal code (e.g. "94105"). Do NOT use 'zip'."""

    country: str
    """2-letter country code. Defaults to "US" if omitted."""


class FormParameter(TypedDict):
    """A single name/value pair for a form submission."""

    name: str
    """Form field name."""

    value: str | int | bool
    """Form field value."""


class OffCycleOptions(TypedDict, total=False):
    """Options for an off-cycle payroll."""

    force_supplemental_withholding: bool
    """Whether to use supplemental withholding rates."""

    apply_benefits: bool
    """Whether to apply benefit deductions."""

    apply_post_tax_deductions: bool
    """Whether to apply post-tax deductions."""


class VoidSubset(TypedDict, total=False):
    """The part of a payroll to void. At least one list must be non-empty."""

    payroll_items: list[str]
    """IDs of the payroll items to void (e.g. "itm_xxxxx")."""

    contractor_payments: list[str]
    """IDs of the contractor payments to void (e.g. "cpa_xxxxx")."""


class TaxParamUpdate(TypedDict, total=False):
    """A single tax parameter update entry."""

    id: str
    """The tax parameter ID (e.g. "spa_xxxxx")."""

    value: str
    """The new value for the tax parameter."""

    applied_for: bool
    """Whether this is an applied-for value."""

    effective_start: str
    """Effective start date (YYYY-MM-DD)."""


class EmailDetails(TypedDict, total=False):
    """Email details for a communication."""

    to: list[str]
    """List of recipient email addresses (required)."""

    sender: str
    """Sender email address (required). Named 'sender' to avoid shadowing."""

    cc: list[str]
    """List of CC email addresses."""

    subject: str
    """Email subject line (required)."""

    message: str
    """Email body message (required)."""
