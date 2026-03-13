"""CLI context and authentication for the Check CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass

from mcp_server_check.helpers import CheckContext

SANDBOX_URL = "https://sandbox.checkhq.com"
PRODUCTION_URL = "https://api.checkhq.com"


@dataclass
class _RequestContext:
    lifespan_context: CheckContext


class CLIContext:
    """Minimal context matching the interface expected by tool functions.

    Mirrors the structure of ``mcp.server.fastmcp.Context`` so that existing
    async tool functions can be called without modification:

        ctx.request_context.lifespan_context -> CheckContext
    """

    def __init__(self, check_ctx: CheckContext) -> None:
        self.request_context = _RequestContext(lifespan_context=check_ctx)


def resolve_base_url(env: str | None = None) -> str:
    """Resolve the API base URL from --env flag or CHECK_API_BASE_URL."""
    explicit = os.environ.get("CHECK_API_BASE_URL")
    if explicit:
        return explicit.rstrip("/")
    env = env or os.environ.get("CHECK_ENV", "sandbox")
    if env == "production":
        return PRODUCTION_URL
    return SANDBOX_URL


def resolve_api_key(api_key: str | None = None) -> str | None:
    """Resolve API key from --api-key flag or CHECK_API_KEY env var."""
    return api_key or os.environ.get("CHECK_API_KEY")
