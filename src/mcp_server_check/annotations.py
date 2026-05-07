"""Helpers for deriving MCP tool titles and ToolAnnotations from function names.

Centralises the classification logic so that every Check API tool is registered
with a consistent, accurate set of MCP hints (``readOnlyHint``,
``destructiveHint``, ``idempotentHint``, ``openWorldHint``) and a human-readable
``title``. The Check API is a closed-world domain so ``openWorldHint`` is
always ``False`` for these tools.

Classification rules consume :mod:`mcp_server_check.tool_filter` as the source
of truth for write/destructive detection — no parallel taxonomy.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from fastmcp.tools import FunctionTool, Tool
from mcp.types import ToolAnnotations

from mcp_server_check.tool_filter import is_destructive_tool, is_write_tool

# Acronyms that should remain uppercase in the human-readable title.
_ACRONYMS: frozenset[str] = frozenset(
    {
        "ssn",
        "ein",
        "ach",
        "irs",
        "w2",
        "w4",
        "url",
        "id",
        "pdf",
        "csv",
    }
)

# Word-level overrides that don't fit the simple Title-Case rule.
_WORD_OVERRIDES: dict[str, str] = {
    "w2": "W-2",
    "w4": "W-4",
    "ids": "IDs",
}

# Lowercase joining words (skipped only when they appear in the middle of a
# title — the first word is always capitalised).
_LOWERCASE_JOINERS: frozenset[str] = frozenset(
    {"and", "or", "for", "of", "to", "the", "a", "an"}
)

# Tool-name prefixes that imply an idempotent mutating call (PUT/DELETE).
# Idempotent means: calling repeatedly with the same arguments has no
# additional effect beyond the first call.
_IDEMPOTENT_WRITE_PREFIXES: tuple[str, ...] = (
    "update_",
    "bulk_update_",
    "delete_",
    "bulk_delete_",
)

# Sandbox-only mutating tools — flagged with a "(Sandbox)" suffix in the title
# so users can tell them apart from production-state operations.
_SANDBOX_PREFIXES: tuple[str, ...] = ("simulate_",)


def _humanize_word(word: str, *, is_first: bool = False) -> str:
    """Convert a single snake_case token into its title-cased form.

    ``is_first`` keeps the very first word capitalised even when it would
    otherwise be a lowercase joiner (e.g. "of", "and").
    """
    lower = word.lower()
    if lower in _WORD_OVERRIDES:
        return _WORD_OVERRIDES[lower]
    if lower in _ACRONYMS:
        return lower.upper()
    if not is_first and lower in _LOWERCASE_JOINERS:
        return lower
    return word.capitalize()


def derive_title(fn_name: str) -> str:
    """Return a human-readable title for a tool given its function name.

    Examples:
        list_companies -> "List Companies"
        get_employee_paystub -> "Get Employee Paystub"
        reveal_employee_ssn -> "Reveal Employee SSN"
        simulate_complete_funding -> "Simulate Complete Funding (Sandbox)"
        sign_and_submit_employee_form -> "Sign and Submit Employee Form"
    """
    parts = [p for p in re.split(r"_+", fn_name) if p]
    title = " ".join(_humanize_word(p, is_first=(i == 0)) for i, p in enumerate(parts))
    if any(fn_name.startswith(p) for p in _SANDBOX_PREFIXES):
        title += " (Sandbox)"
    return title


def derive_annotations(fn_name: str) -> ToolAnnotations:
    """Derive a ToolAnnotations from the tool name.

    Classification:
      * Read-only: anything not flagged by ``is_write_tool``.
      * Destructive: anything flagged by ``is_destructive_tool``
        (delete/cancel/refund/approve/simulate, etc.).
      * Idempotent: read-only calls, plus update_/delete_ style writes.
      * Open-world: always ``False`` (Check API is a closed domain).
    """
    title = derive_title(fn_name)
    write = is_write_tool(fn_name)
    destructive = is_destructive_tool(fn_name)

    if not write:
        return ToolAnnotations(
            title=title,
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )

    idempotent = any(fn_name.startswith(p) for p in _IDEMPOTENT_WRITE_PREFIXES)
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=False,
    )


def build_tool(fn: Callable[..., Any]) -> FunctionTool:
    """Wrap a plain function in a FunctionTool with derived title and annotations."""
    title = derive_title(fn.__name__)
    annotations = derive_annotations(fn.__name__)
    return Tool.from_function(fn, title=title, annotations=annotations)


def add_annotated_tool(mcp: Any, fn: Callable[..., Any]) -> None:
    """Register ``fn`` on ``mcp`` with a derived title and ToolAnnotations.

    Designed to be a drop-in replacement for ``mcp.add_tool(fn)`` at every
    registration site. Works against both real :class:`FastMCP` instances
    (which require a :class:`Tool` object) and the lightweight collectors
    used during indexing (which accept the raw function).
    """
    title = derive_title(fn.__name__)
    annotations = derive_annotations(fn.__name__)
    accepts_kwargs = getattr(mcp, "_annotated_tool_supports_kwargs", False)
    if accepts_kwargs:
        mcp.add_tool(fn, title=title, annotations=annotations)
        return
    tool = Tool.from_function(fn, title=title, annotations=annotations)
    mcp.add_tool(tool)
