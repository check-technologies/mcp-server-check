"""Check Payroll API CLI.

Provides a ``check`` command that exposes the same tool functions used by
the MCP server as a resource-oriented CLI (similar to the Stripe CLI).
"""

from __future__ import annotations

import click

from mcp_server_check import __version__
from mcp_server_check.tool_filter import ToolFilter

from .codegen import build_command, collect_tools
from .context import resolve_api_key, resolve_base_url


# ---------------------------------------------------------------------------
# Filtered click groups
# ---------------------------------------------------------------------------


def _build_filter(ctx: click.Context) -> ToolFilter:
    """Build a ToolFilter by merging env vars with the ``--read-only`` flag."""
    root = ctx
    while root.parent:
        root = root.parent
    read_only = root.params.get("read_only", False) if root.params else False
    env_filter = ToolFilter.from_env()
    if read_only and not env_filter.read_only:
        return ToolFilter(
            toolsets=env_filter.toolsets,
            tools=env_filter.tools,
            exclude_tools=env_filter.exclude_tools,
            read_only=True,
        )
    return env_filter


class _FilteredGroup(click.Group):
    """Click group that hides commands rejected by :class:`ToolFilter`."""

    def __init__(
        self,
        *args,
        toolset_name: str = "",
        tool_map: dict[str, str] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.toolset_name = toolset_name
        # command_cli_name -> tool_function_name
        self.tool_map: dict[str, str] = tool_map if tool_map is not None else {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        tf = _build_filter(ctx)
        return sorted(
            name
            for name in super().list_commands(ctx)
            if name in self.tool_map
            and tf.is_tool_allowed(self.tool_map[name], self.toolset_name)
        )

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        cmd = super().get_command(ctx, cmd_name)
        if cmd is None:
            return None
        func_name = self.tool_map.get(cmd_name)
        if func_name is None:
            return cmd
        tf = _build_filter(ctx)
        if not tf.is_tool_allowed(func_name, self.toolset_name):
            return None
        return cmd


class _MainCLI(click.Group):
    """Top-level CLI group that hides toolset groups based on ToolFilter."""

    def __init__(
        self,
        *args,
        toolset_names: dict[str, str] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # cli_group_name -> toolset_name
        self.toolset_names: dict[str, str] = toolset_names if toolset_names is not None else {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        tf = _build_filter(ctx)
        commands: list[str] = []
        for name in super().list_commands(ctx):
            toolset = self.toolset_names.get(name)
            # Non-toolset commands (shouldn't exist, but be safe) always shown
            if toolset is None:
                commands.append(name)
                continue
            if tf.toolsets is None or toolset in tf.toolsets:
                commands.append(name)
        return commands

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        cmd = super().get_command(ctx, cmd_name)
        if cmd is None:
            return None
        toolset = self.toolset_names.get(cmd_name)
        if toolset is None:
            return cmd
        tf = _build_filter(ctx)
        if tf.toolsets is not None and toolset not in tf.toolsets:
            return None
        return cmd


# ---------------------------------------------------------------------------
# CLI construction
# ---------------------------------------------------------------------------


def _build_cli() -> click.Group:
    """Build the full CLI application with all auto-generated commands."""
    toolset_names: dict[str, str] = {}

    @click.group(cls=_MainCLI, toolset_names=toolset_names)
    @click.option(
        "--api-key",
        envvar="CHECK_API_KEY",
        default=None,
        help="Check API key (or CHECK_API_KEY env var).",
    )
    @click.option(
        "--env",
        "environment",
        type=click.Choice(["sandbox", "production"]),
        default=None,
        help="API environment (default: sandbox; or CHECK_ENV env var).",
    )
    @click.option(
        "--format",
        "fmt",
        type=click.Choice(["json", "table"]),
        default="json",
        help="Output format (default: json).",
    )
    @click.option(
        "--read-only",
        is_flag=True,
        default=False,
        help="Block write operations (or CHECK_READ_ONLY env var).",
    )
    @click.option(
        "--verbose",
        is_flag=True,
        default=False,
        help="Print request details to stderr.",
    )
    @click.version_option(version=__version__, prog_name="check")
    @click.pass_context
    def cli(
        ctx: click.Context,
        api_key: str | None,
        environment: str | None,
        fmt: str,
        read_only: bool,
        verbose: bool,
    ) -> None:
        """Check Payroll API CLI."""
        ctx.ensure_object(dict)
        ctx.obj["api_key"] = resolve_api_key(api_key)
        ctx.obj["base_url"] = resolve_base_url(environment)
        ctx.obj["format"] = fmt
        ctx.obj["read_only"] = read_only
        ctx.obj["verbose"] = verbose

    # Register toolset groups ------------------------------------------------
    all_tools = collect_tools()
    for toolset_name, functions in all_tools.items():
        group_name = toolset_name.replace("_", "-")
        tool_map: dict[str, str] = {}

        group = _FilteredGroup(
            name=group_name,
            toolset_name=toolset_name,
            tool_map=tool_map,
            help=f"Commands for {toolset_name.replace('_', ' ')}.",
        )

        for func in functions:
            cmd_name, cmd, func_name = build_command(func, toolset_name)
            tool_map[cmd_name] = func_name
            group.add_command(cmd, cmd_name)

        toolset_names[group_name] = toolset_name
        cli.add_command(group, group_name)

    return cli


cli = _build_cli()


def main() -> None:
    """Entry point for the ``check`` console script."""
    cli(standalone_mode=True)
