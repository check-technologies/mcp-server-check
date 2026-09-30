"""Check Payroll API CLI.

Provides a ``check`` command that exposes the same tool functions used by
the MCP server as a resource-oriented CLI (similar to the Stripe CLI).
"""

from __future__ import annotations

import click

from mcp_server_check import __version__
from .codegen import CSVList, build_command, collect_tools
from .context import resolve_api_key, resolve_base_url
from .groups import ToolsetGroup, build_tool_filter
from .setup import init_command


class _MainCLI(click.Group):
    """Top-level CLI group that hides toolset groups based on ToolFilter.

    Overrides ``format_commands`` to render standalone commands (like
    ``setup``) separately from API toolset groups.
    """

    def __init__(
        self,
        *args,
        toolset_names: dict[str, str] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # cli_group_name -> toolset_name
        self.toolset_names: dict[str, str] = (
            toolset_names if toolset_names is not None else {}
        )

    def list_commands(self, ctx: click.Context) -> list[str]:
        tf = build_tool_filter(ctx)
        commands: list[str] = []
        for name in super().list_commands(ctx):
            toolset = self.toolset_names.get(name)
            # Non-toolset commands always shown
            if toolset is None:
                commands.append(name)
                continue
            if tf.is_toolset_allowed(toolset):
                commands.append(name)
        return commands

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        cmd = super().get_command(ctx, cmd_name)
        if cmd is None:
            return None
        toolset = self.toolset_names.get(cmd_name)
        if toolset is None:
            return cmd
        tf = build_tool_filter(ctx)
        if not tf.is_toolset_allowed(toolset):
            return None
        return cmd

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        visible = self.list_commands(ctx)
        if not visible:
            return

        standalone: list[tuple[str, str]] = []
        toolset_cmds: list[tuple[str, str]] = []

        limit = formatter.width - 6 - max(len(n) for n in visible)

        for name in visible:
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            help_text = cmd.get_short_help_str(limit=limit)
            row = (name, help_text)
            if name in self.toolset_names:
                toolset_cmds.append(row)
            else:
                standalone.append(row)

        if standalone:
            with formatter.section("Commands"):
                formatter.write_dl(standalone)

        if toolset_cmds:
            with formatter.section("API Resources"):
                formatter.write_dl(toolset_cmds)


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
        "--preview-toolsets",
        type=CSVList(),
        default=None,
        help="Comma-separated preview toolsets to enable (or CHECK_PREVIEW_TOOLSETS env var).",
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
        preview_toolsets: list[str] | None,
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

        group = ToolsetGroup(
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

    cli.add_command(init_command, "init")

    return cli


cli = _build_cli()


def main() -> None:
    """Entry point for the ``check`` console script."""
    cli(standalone_mode=True)
