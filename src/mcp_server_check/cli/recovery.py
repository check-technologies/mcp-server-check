"""Recovery alternatives rendered as check command lines."""

from __future__ import annotations

import json
import shlex
from typing import Any

import click

from mcp_server_check.recovery import recovery

from .groups import ToolsetGroup


class CommandLines:
    """Maps tool names to the CLI commands the current invocation can run."""

    def __init__(self, ctx: click.Context) -> None:
        self._ctx = ctx
        root = ctx.find_root().command
        assert isinstance(root, click.Group), "CommandLines: Expected a click Group"
        self._groups = [
            (name, group)
            for name, group in root.commands.items()
            if isinstance(group, ToolsetGroup)
        ]

    def recover(
        self, result: dict[str, Any], tool: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Return a failed result with its alternatives as command lines."""
        payload = recovery.enrich(result, tool, arguments, self.is_available)
        if payload is result:
            return result
        return {
            **payload,
            "alternatives": [
                {
                    "command": self.command_line(
                        alternative["tool"], alternative["arguments"]
                    ),
                    "description": alternative["description"],
                }
                for alternative in payload["alternatives"]
            ],
        }

    def is_available(self, tool: str) -> bool:
        return self._find(tool) is not None

    def command_line(self, tool: str, arguments: dict[str, Any]) -> str:
        found = self._find(tool)
        assert found is not None, f"CommandLines.command_line: {tool} is unavailable"
        group_name, command_name, command = found
        positional: list[str] = []
        options: list[str] = []
        params = {param.name: param for param in command.params}
        for name, value in arguments.items():
            param = params.get(name)
            if isinstance(param, click.Argument):
                positional.append(str(value))
            elif isinstance(param, click.Option):
                options.extend(self._option_words(param, value))
        return shlex.join(["check", group_name, command_name, *positional, *options])

    def _find(self, tool: str) -> tuple[str, str, click.Command] | None:
        for group_name, group in self._groups:
            command_name = group.command_name_for(self._ctx, tool)
            if command_name is not None:
                command = group.get_command(self._ctx, command_name)
                assert command is not None, "CommandLines._find: command vanished"
                return group_name, command_name, command
        return None

    @staticmethod
    def _option_words(option: click.Option, value: Any) -> list[str]:
        if isinstance(value, bool):
            flags = option.opts if value else option.secondary_opts
            return flags[:1]
        if isinstance(value, list):
            return [option.opts[0], ",".join(str(item) for item in value)]
        if isinstance(value, dict):
            return [option.opts[0], json.dumps(value)]
        return [option.opts[0], str(value)]
