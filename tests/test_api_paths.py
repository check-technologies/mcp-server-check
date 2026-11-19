"""Structural checks for safe Check API path construction."""

from __future__ import annotations

import ast
from pathlib import Path


def test_api_modules_do_not_interpolate_raw_paths():
    package = Path(__file__).parents[1] / "src" / "mcp_server_check"
    modules = [
        *sorted((package / "tools").glob("*.py")),
        package / "tool_factory.py",
        package / "reports.py",
    ]
    violations: list[str] = []

    for module in modules:
        tree = ast.parse(module.read_text(), filename=str(module))
        for node in ast.walk(tree):
            if not isinstance(node, ast.JoinedStr):
                continue
            if any(
                isinstance(part, ast.Constant)
                and isinstance(part.value, str)
                and "/" in part.value
                for part in node.values
            ):
                violations.append(f"{module.relative_to(package)}:{node.lineno}")

    assert not violations, (
        "Build dynamic Check API paths from separate api_path() segments: "
        + ", ".join(violations)
    )
