"""Click groups that show only the commands the active ToolFilter allows."""

from __future__ import annotations

from dataclasses import replace

import click

from mcp_server_check.tool_filter import ToolFilter


def build_tool_filter(ctx: click.Context) -> ToolFilter:
    """Build a ToolFilter by merging env vars with the --read-only and
    --preview-toolsets flags."""
    root = ctx.find_root()
    params = root.params or {}
    tool_filter = ToolFilter.from_env()
    if params.get("read_only"):
        tool_filter = replace(tool_filter, read_only=True)
    preview_toolsets = params.get("preview_toolsets")
    if preview_toolsets:
        tool_filter = tool_filter.merge(
            ToolFilter(preview_toolsets=frozenset(preview_toolsets))
        )
    return tool_filter


class ToolsetGroup(click.Group):
    """The commands of one toolset, hiding those rejected by ToolFilter."""

    def __init__(
        self,
        *args,
        toolset_name: str = "",
        tool_map: dict[str, str] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.toolset_name = toolset_name
        self.tool_map: dict[str, str] = tool_map if tool_map is not None else {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        tf = build_tool_filter(ctx)
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
        tf = build_tool_filter(ctx)
        if not tf.is_tool_allowed(func_name, self.toolset_name):
            return None
        return cmd

    def command_for(
        self, tool: str, tool_filter: ToolFilter
    ) -> tuple[str, click.Command] | None:
        """Return the name and command that run tool, if tool_filter allows it."""
        if not tool_filter.is_tool_allowed(tool, self.toolset_name):
            return None
        for name, func_name in self.tool_map.items():
            if func_name == tool:
                return name, self.commands[name]
        return None
