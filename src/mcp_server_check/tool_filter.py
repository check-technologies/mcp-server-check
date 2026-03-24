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
        "bank_accounts",
        "companies",
        "compensation",
        "components",
        "contractor_payments",
        "contractors",
        "documents",
        "employees",
        "external_payrolls",
        "forms",
        "payments",
        "payroll_items",
        "payrolls",
        "platform",
        "tax",
        "webhooks",
        "workflows",
        "workplaces",
    }
)

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
    "request_tax_",
)

# Tools that trigger irreversible real-world effects (money movement, deletion).
# These require explicit confirmation when CHECK_CONFIRM_DESTRUCTIVE is enabled.
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
    }
)


def is_write_tool(name: str) -> bool:
    """Return True if the tool name matches a write/mutating pattern."""
    return any(name.startswith(p) for p in _WRITE_PREFIXES) or any(
        name.startswith(k) for k in _WRITE_KEYWORDS
    )


def is_destructive_tool(name: str) -> bool:
    """Return True if the tool triggers irreversible effects (money movement, deletion).

    These tools should require explicit confirmation when the confirmation
    tier is enabled.
    """
    if name in _DESTRUCTIVE_EXACT:
        return True
    return any(name.startswith(p) for p in _DESTRUCTIVE_PREFIXES)


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

    Filtering precedence: exclude_tools > read_only > tools > toolsets.
    - exclude_tools always wins (tool is hidden).
    - read_only hides write/mutating tools.
    - tools, when set, acts as an allowlist independent of toolsets.
    - toolsets, when set, limits tools to those in the named toolsets.
    """

    toolsets: frozenset[str] | None = None
    tools: frozenset[str] | None = None
    exclude_tools: frozenset[str] = frozenset()
    read_only: bool = False
    confirm_destructive: bool = False

    def __post_init__(self) -> None:
        if self.toolsets is not None:
            invalid = self.toolsets - TOOLSETS
            if invalid:
                logger.warning(
                    "Ignoring unknown toolset(s): %s", ", ".join(sorted(invalid))
                )
                object.__setattr__(self, "toolsets", self.toolsets & TOOLSETS)

    def is_tool_allowed(self, tool_name: str, toolset_name: str) -> bool:
        """Determine whether a tool should be visible given this filter."""
        # Exclude always wins
        if tool_name in self.exclude_tools:
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
            confirm_destructive=self.confirm_destructive or other.confirm_destructive,
        )

    def requires_confirmation(self, tool_name: str) -> bool:
        """Return True if this tool requires explicit confirmation before execution."""
        return self.confirm_destructive and is_destructive_tool(tool_name)

    @classmethod
    def from_env(cls) -> ToolFilter:
        """Build a ToolFilter from environment variables."""
        return cls(
            toolsets=_parse_comma_set(os.environ.get("CHECK_TOOLSETS")),
            tools=_parse_comma_set(os.environ.get("CHECK_TOOLS")),
            exclude_tools=_parse_comma_set(os.environ.get("CHECK_EXCLUDE_TOOLS"))
            or frozenset(),
            read_only=_parse_bool(os.environ.get("CHECK_READ_ONLY")),
            confirm_destructive=_parse_bool(
                os.environ.get("CHECK_CONFIRM_DESTRUCTIVE")
            ),
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
            confirm_destructive=_parse_bool(get("x-mcp-confirm-destructive")),
        )
