"""Recovery remedies rendered as check command lines."""

from __future__ import annotations

import json
import shlex
from typing import Any

import click

from mcp_server_check.recovery import Failure, Recovery, recovery

from .groups import ToolsetGroup, build_tool_filter


class CommandLines:
    """Renders remedies as the check commands this invocation can run."""

    def __init__(self, ctx: click.Context, registry: Recovery = recovery) -> None:
        root = ctx.find_root().command
        assert isinstance(root, click.Group), "CommandLines: Expected a click Group"
        self._groups = [
            (name, group)
            for name, group in root.commands.items()
            if isinstance(group, ToolsetGroup)
        ]
        self._tool_filter = build_tool_filter(ctx)
        self._registry = registry

    def recover(
        self, result: dict[str, Any], tool: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Return a failed result listing its remedies as command lines."""
        remedies = self._registry.remedies(
            tool, arguments, Failure.from_payload(result), self.is_available
        )
        if not remedies:
            return result
        return {
            **result,
            "alternatives": [
                {
                    "command": self.command_line(
                        alternative.tool, alternative.arguments
                    ),
                    "description": alternative.description,
                }
                for alternative in remedies.alternatives
            ],
            "hints": [
                {
                    "command": self.command_line(hint.tool, {}),
                    "description": hint.description,
                    "options": self.options(hint.tool, hint.arguments),
                }
                for hint in remedies.hints
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
        for param in command.params:
            value = arguments.get(param.name)
            if value is None:
                continue
            if isinstance(param, click.Argument):
                positional.append(str(value))
            elif isinstance(param, click.Option):
                options.extend(self._option_words(param, value))
        return shlex.join(["check", group_name, command_name, *positional, *options])

    def options(self, tool: str, arguments: tuple[str, ...]) -> list[str]:
        """Return the command line names of the tool's arguments."""
        found = self._find(tool)
        assert found is not None, f"CommandLines.options: {tool} is unavailable"
        params = {param.name: param for param in found[2].params}
        return [
            params[name].opts[0]
            if isinstance(params[name], click.Option)
            else params[name].human_readable_name
            for name in arguments
            if name in params
        ]

    def _find(self, tool: str) -> tuple[str, str, click.Command] | None:
        for group_name, group in self._groups:
            found = group.command_for(tool, self._tool_filter)
            if found is not None:
                return group_name, *found
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
