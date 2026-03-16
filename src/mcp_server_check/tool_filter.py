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


def is_write_tool(name: str) -> bool:
    """Return True if the tool name matches a write/mutating pattern."""
    return any(name.startswith(p) for p in _WRITE_PREFIXES) or any(
        name.startswith(k) for k in _WRITE_KEYWORDS
    )


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

    @classmethod
    def from_env(cls) -> ToolFilter:
        """Build a ToolFilter from environment variables."""
        return cls(
            toolsets=_parse_comma_set(os.environ.get("CHECK_TOOLSETS")),
            tools=_parse_comma_set(os.environ.get("CHECK_TOOLS")),
            exclude_tools=_parse_comma_set(os.environ.get("CHECK_EXCLUDE_TOOLS"))
            or frozenset(),
            read_only=_parse_bool(os.environ.get("CHECK_READ_ONLY")),
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
        )
