"""Toolset-based tool filtering for the Check MCP server.

Supports filtering via HTTP headers (remote) or environment variables (local),
following the GitHub MCP Server configuration pattern.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

TOOLSETS: frozenset[str] = frozenset(
    {
        "agencies",
        "bank_accounts",
        "companies",
        "compensation",
        "components",
        "contractor_payments",
        "contractors",
        "corrections",
        "documents",
        "employees",
        "external_payrolls",
        "forms",
        "logs",
        "payments",
        "payroll_items",
        "payrolls",
        "platform",
        "report_runs",
        "tax",
        "webhooks",
        "workflows",
        "workplaces",
    }
)

# Hidden until the caller opts in through preview_toolsets.
PREVIEW_TOOLSETS: frozenset[str] = frozenset({"corrections"})

_WRITE_PREFIXES = (
    "create_",
    "update_",
    "delete_",
    "bulk_update_",
    "bulk_delete_",
)
_WRITE_KEYWORDS = (
    "approve_",
    "reopen_",
    "onboard_",
    "submit_",
    "sign_and_submit_",
    "authorize_",
    "simulate_",
    "retry_",
    "refund_",
    "cancel_",
    "start_implementation",
    "cancel_implementation",
    "request_embedded_setup",
    "ping_",
    "refresh_",
    "toggle_",
    "sync_",
    "upload_",
    "add_",
    "remove_",
    "void_",
)
# Writes whose names read like reads: preview_payroll is a GET, but
# preview_correction starts a dry run and changes the correction's state.
_WRITE_EXACT = frozenset({"preview_correction"})

# Tools that trigger irreversible real-world effects (deletion, approval, refunds).
# CHECK_EXCLUDE_DESTRUCTIVE removes these from a deployment entirely.
_DESTRUCTIVE_PREFIXES = (
    "approve_",
    "delete_",
    "bulk_delete_",
    "simulate_",
    "refund_",
    "cancel_",
)
_DESTRUCTIVE_EXACT = frozenset(
    {
        "start_implementation",
        "cancel_implementation",
        # Posts journal entries into a partner's accounting system; Check
        # cannot recall them.
        "sync_accounting",
        # Cancels an approval that is about to move money.
        "reopen_correction",
    }
)

# Tools that move funds or change where funds are drawn from / sent to.
# CHECK_EXCLUDE_MONEY_MOVEMENT removes these from a deployment entirely.
#
# Matched by exact name rather than prefix: prefixes would sweep in unrelated
# tools (retry_webhook_delivery) and read-only ones (list_payments), while
# missing approve_payroll's real significance. tests/test_tool_drift.py asserts
# every name here still exists and that no new money-path tool escapes
# classification.
_MONEY_MOVEMENT_EXACT = frozenset(
    {
        # Disburses a payroll: debits the company, credits workers.
        "approve_payroll",
        # Re-initiates, reverses, or halts an existing transfer.
        "retry_payment",
        "refund_payment",
        "cancel_payment",
        # Funding/payout destinations: adding or repointing a bank account
        # reroutes where pay is drawn from or sent to.
        "create_bank_account",
        "update_bank_account",
        "delete_bank_account",
    }
)


def is_write_tool(name: str) -> bool:
    """Return True if the tool name matches a write/mutating pattern."""
    if name in _WRITE_EXACT:
        return True
    return any(name.startswith(p) for p in _WRITE_PREFIXES) or any(
        name.startswith(k) for k in _WRITE_KEYWORDS
    )


def is_destructive_tool(name: str) -> bool:
    """Return True if the tool triggers irreversible effects (deletion, approval).

    Also drives the ``destructiveHint`` MCP annotation (see annotations.py),
    so changes here are visible to clients.
    """
    if name in _DESTRUCTIVE_EXACT:
        return True
    return any(name.startswith(p) for p in _DESTRUCTIVE_PREFIXES)


def is_money_movement_tool(name: str) -> bool:
    """Return True if the tool moves funds or changes a funding/payout destination."""
    return name in _MONEY_MOVEMENT_EXACT


def _parse_comma_set(value: str | None) -> frozenset[str] | None:
    """Parse a comma-separated string into a frozenset, or None if empty."""
    if not value:
        return None
    items = frozenset(s.strip() for s in value.split(",") if s.strip())
    return items if items else None


def _parse_bool(value: str | None) -> bool:
    """Parse a string as a boolean flag."""
    return (value or "").lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class ToolFilter:
    """Immutable filter configuration for tool visibility.

    Filtering precedence: exclude_tools > exclusion flags > preview_toolsets
    > read_only > tools > toolsets.
    - exclude_tools always wins (tool is hidden).
    - exclude_money_movement / exclude_destructive hide whole categories, and
      apply even to tools named in the ``tools`` allowlist.
    - A tool in a preview toolset is hidden unless preview_toolsets names it,
      even when tools or toolsets name it.
    - read_only hides write/mutating tools.
    - tools, when set, acts as an allowlist independent of toolsets.
    - toolsets, when set, limits tools to those in the named toolsets.

    code_mode is not a visibility rule for Check tools: it exposes the
    run_code and get_stubs meta-tools in dynamic mode. Like preview_toolsets
    it is an opt-in, so a request header can turn it on.
    """

    toolsets: frozenset[str] | None = None
    tools: frozenset[str] | None = None
    exclude_tools: frozenset[str] = frozenset()
    read_only: bool = False
    exclude_money_movement: bool = False
    exclude_destructive: bool = False
    preview_toolsets: frozenset[str] = frozenset()
    code_mode: bool = False

    def __post_init__(self) -> None:
        if self.toolsets is not None:
            invalid = self.toolsets - TOOLSETS
            if invalid:
                logger.warning(
                    "Ignoring unknown toolset(s): %s", ", ".join(sorted(invalid))
                )
                object.__setattr__(self, "toolsets", self.toolsets & TOOLSETS)
        invalid_preview = self.preview_toolsets - PREVIEW_TOOLSETS
        if invalid_preview:
            logger.warning(
                "Ignoring unknown preview toolset(s): %s",
                ", ".join(sorted(invalid_preview)),
            )
            object.__setattr__(
                self, "preview_toolsets", self.preview_toolsets & PREVIEW_TOOLSETS
            )

    def is_preview_enabled(self, toolset_name: str) -> bool:
        """Return False only for a preview toolset the caller has not opted into."""
        return (
            toolset_name not in PREVIEW_TOOLSETS
            or toolset_name in self.preview_toolsets
        )

    def is_toolset_allowed(self, toolset_name: str) -> bool:
        """Determine whether a toolset as a whole should be visible."""
        if not self.is_preview_enabled(toolset_name):
            return False
        return self.toolsets is None or toolset_name in self.toolsets

    def is_tool_allowed(self, tool_name: str, toolset_name: str) -> bool:
        """Determine whether a tool should be visible given this filter."""
        # Exclude always wins
        if tool_name in self.exclude_tools:
            return False

        # Category exclusions act as a policy floor: they are checked before
        # the `tools` allowlist below, so an allowlisted tool stays hidden.
        if self.exclude_money_movement and is_money_movement_tool(tool_name):
            return False

        if self.exclude_destructive and is_destructive_tool(tool_name):
            return False

        if not self.is_preview_enabled(toolset_name):
            return False

        # Read-only hides write tools
        if self.read_only and is_write_tool(tool_name):
            return False

        # Individual tool allowlist (independent of toolsets)
        if self.tools is not None:
            return tool_name in self.tools

        # Toolset allowlist
        if self.toolsets is not None:
            return toolset_name in self.toolsets

        return True

    def merge(self, other: ToolFilter) -> ToolFilter:
        """Merge two filters, taking the most restrictive value for each field.

        Used to combine a server-side policy (env vars) with a per-request
        override (HTTP headers) so that the policy acts as a floor that
        cannot be relaxed by the client.

        preview_toolsets and code_mode are the exceptions: they are opt-ins,
        so either side can enable them. A server that must keep a preview
        toolset hidden can still do so with toolsets or exclude_tools, and one
        that must keep code mode off can exclude run_code and get_stubs.
        """
        # toolsets: intersect when both set; keep the one that's set if only one is
        if self.toolsets is not None and other.toolsets is not None:
            merged_toolsets = self.toolsets & other.toolsets
        elif self.toolsets is not None:
            merged_toolsets = self.toolsets
        elif other.toolsets is not None:
            merged_toolsets = other.toolsets
        else:
            merged_toolsets = None

        # tools: intersect when both set; keep the one that's set if only one is
        if self.tools is not None and other.tools is not None:
            merged_tools = self.tools & other.tools
        elif self.tools is not None:
            merged_tools = self.tools
        elif other.tools is not None:
            merged_tools = other.tools
        else:
            merged_tools = None

        return ToolFilter(
            toolsets=merged_toolsets,
            tools=merged_tools,
            exclude_tools=self.exclude_tools | other.exclude_tools,
            read_only=self.read_only or other.read_only,
            exclude_money_movement=self.exclude_money_movement
            or other.exclude_money_movement,
            exclude_destructive=self.exclude_destructive or other.exclude_destructive,
            preview_toolsets=self.preview_toolsets | other.preview_toolsets,
            code_mode=self.code_mode or other.code_mode,
        )

    @classmethod
    def from_env(cls) -> ToolFilter:
        """Build a ToolFilter from environment variables."""
        return cls(
            toolsets=_parse_comma_set(os.environ.get("CHECK_TOOLSETS")),
            tools=_parse_comma_set(os.environ.get("CHECK_TOOLS")),
            exclude_tools=_parse_comma_set(os.environ.get("CHECK_EXCLUDE_TOOLS"))
            or frozenset(),
            read_only=_parse_bool(os.environ.get("CHECK_READ_ONLY")),
            exclude_money_movement=_parse_bool(
                os.environ.get("CHECK_EXCLUDE_MONEY_MOVEMENT")
            ),
            exclude_destructive=_parse_bool(
                os.environ.get("CHECK_EXCLUDE_DESTRUCTIVE")
            ),
            preview_toolsets=_parse_comma_set(os.environ.get("CHECK_PREVIEW_TOOLSETS"))
            or frozenset(),
            code_mode=_parse_bool(os.environ.get("CHECK_CODE_MODE")),
        )

    @classmethod
    def from_headers(cls, headers: dict[str, str] | object) -> ToolFilter:
        """Build a ToolFilter from HTTP request headers.

        Args:
            headers: A dict-like object (e.g. Starlette Headers) supporting .get().
        """
        get = getattr(headers, "get", None)
        if get is None:
            return cls()
        return cls(
            toolsets=_parse_comma_set(get("x-mcp-toolsets")),
            tools=_parse_comma_set(get("x-mcp-tools")),
            exclude_tools=_parse_comma_set(get("x-mcp-exclude-tools")) or frozenset(),
            read_only=_parse_bool(get("x-mcp-readonly")),
            exclude_money_movement=_parse_bool(get("x-mcp-exclude-money-movement")),
            exclude_destructive=_parse_bool(get("x-mcp-exclude-destructive")),
            preview_toolsets=_parse_comma_set(get("x-mcp-preview-toolsets"))
            or frozenset(),
            code_mode=_parse_bool(get("x-mcp-code-mode")),
        )

    @classmethod
    def from_query_params(cls, query_params: dict[str, str] | object) -> ToolFilter:
        """Build a ToolFilter from URL query parameters.

        Supports ``read_only``, ``preview_toolsets``, and ``code_mode``, for
        clients that can only be configured with a URL.

        Args:
            query_params: A dict-like object (e.g. Starlette QueryParams)
                          supporting .get().
        """
        get = getattr(query_params, "get", None)
        if get is None:
            return cls()
        return cls(
            read_only=_parse_bool(get("read_only")),
            preview_toolsets=_parse_comma_set(get("preview_toolsets")) or frozenset(),
            code_mode=_parse_bool(get("code_mode")),
        )
