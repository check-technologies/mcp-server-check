"""Guards against tool-classification drift.

The Anthropic directory deployment relies on ``CHECK_EXCLUDE_MONEY_MOVEMENT``
and ``CHECK_EXCLUDE_DESTRUCTIVE`` to keep fund-moving tools off that endpoint.
Both flags classify tools by name, so a new tool with an unanticipated name
would ship unclassified and reach the directory endpoint. These tests fail
instead, forcing an explicit decision.
"""

from __future__ import annotations

import inspect
import re

import pytest
from mcp_server_check.tool_filter import (
    _MONEY_MOVEMENT_EXACT,
    is_destructive_tool,
    is_money_movement_tool,
)
from mcp_server_check.tools import collect_all_tools

# Mutating Check API calls, e.g. ``check_api_post(ctx, f"/payments/{id}/retry")``.
_MUTATING_CALL = re.compile(r"check_api_(post|patch|delete)\(")
_LITERAL_PATH = re.compile(r'check_api_(?:post|patch|delete)\(\s*ctx,\s*f?"(/[^"]+)"')

# API paths where a mutation moves funds or repoints where funds go.
_MONEY_PATH = re.compile(r"^/(payments|bank_accounts)(/|$)")

# Mutating money-path tools deliberately left available on every deployment.
# Adding a name here is a policy decision, not a formality.
_REVIEWED_AVAILABLE: frozenset[str] = frozenset()


def _mutating_paths(fn) -> list[str]:
    """Return the API paths a tool mutates, or [] if it only reads.

    Hand-written tools carry the path as a literal in the call. Tools built by
    ``generate_tools`` share a generic body, so the path arrives as a closure
    cell instead.
    """
    try:
        source = inspect.getsource(fn)
    except (OSError, TypeError):  # pragma: no cover - source always available
        return []
    if not _MUTATING_CALL.search(source):
        return []
    paths = _LITERAL_PATH.findall(source)
    if not paths and fn.__closure__:
        paths = [
            cell.cell_contents
            for cell in fn.__closure__
            if isinstance(cell.cell_contents, str)
            and cell.cell_contents.startswith("/")
        ]
    return paths


def _all_tool_functions() -> list:
    return [fn for fns in collect_all_tools().values() for fn in fns]


def test_money_path_mutations_are_classified():
    """Every tool that mutates a payments/bank-account endpoint is classified."""
    unclassified = [
        fn.__name__
        for fn in _all_tool_functions()
        if any(_MONEY_PATH.match(p) for p in _mutating_paths(fn))
        and not is_money_movement_tool(fn.__name__)
        and not is_destructive_tool(fn.__name__)
        and fn.__name__ not in _REVIEWED_AVAILABLE
    ]
    assert not unclassified, (
        "These tools mutate a money-related endpoint but are excluded by neither "
        f"CHECK_EXCLUDE_MONEY_MOVEMENT nor CHECK_EXCLUDE_DESTRUCTIVE: {unclassified}. "
        "Add them to _MONEY_MOVEMENT_EXACT, or to _REVIEWED_AVAILABLE with a rationale."
    )


def test_path_detection_finds_known_money_tools():
    """The source-introspection above actually resolves paths (guards the guard)."""
    detected = {
        fn.__name__
        for fn in _all_tool_functions()
        if any(_MONEY_PATH.match(p) for p in _mutating_paths(fn))
    }
    assert {
        "retry_payment",
        "refund_payment",
        "cancel_payment",
        "create_bank_account",
        "update_bank_account",
        "delete_bank_account",
    } <= detected


def test_no_mutating_tool_has_an_unresolvable_path():
    """A tool whose path can't be read would silently bypass the drift check."""
    unresolvable = [
        fn.__name__
        for fn in _all_tool_functions()
        if _MUTATING_CALL.search(inspect.getsource(fn)) and not _mutating_paths(fn)
    ]
    assert not unresolvable, (
        "Could not determine which endpoint these tools mutate, so the money-path "
        f"drift check cannot see them: {unresolvable}"
    )


@pytest.mark.parametrize("name", sorted(_MONEY_MOVEMENT_EXACT))
def test_money_movement_names_still_exist(name):
    """A rename would silently empty the exclusion set."""
    registered = {fn.__name__ for fn in _all_tool_functions()}
    assert name in registered, (
        f"'{name}' is in _MONEY_MOVEMENT_EXACT but no longer registered — it was "
        "renamed or removed, and the exclusion no longer covers it."
    )


def test_approve_payroll_is_covered_despite_non_money_path():
    """approve_payroll disburses funds but posts to /payrolls, not /payments.

    The path heuristic cannot see it, which is why the exact set (guarded by
    the rename test above) is the real protection.
    """
    assert is_money_movement_tool("approve_payroll")
