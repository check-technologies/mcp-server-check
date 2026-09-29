"""Click groups that show only the commands the active ToolFilter allows."""

from __future__ import annotations

import click

from mcp_server_check.tool_filter import ToolFilter


def build_tool_filter(ctx: click.Context) -> ToolFilter:
    """Build a ToolFilter by merging env vars with the --read-only flag."""
    root = ctx.find_root()
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
        # command_cli_name -> tool_function_name
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

    def command_name_for(self, ctx: click.Context, tool: str) -> str | None:
        """Return the name of the allowed command that runs tool, if any."""
        for name, func_name in self.tool_map.items():
            if func_name == tool and self.get_command(ctx, name) is not None:
                return name
        return None
