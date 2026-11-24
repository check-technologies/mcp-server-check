"""Structural checks for safe Check API path construction."""

from __future__ import annotations

import ast
from pathlib import Path


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def test_api_modules_do_not_construct_or_send_raw_paths():
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
            if isinstance(node, ast.JoinedStr) and any(
                isinstance(part, ast.Constant)
                and isinstance(part.value, str)
                and "/" in part.value
                for part in node.values
            ):
                violations.append(f"{module.relative_to(package)}:{node.lineno}")
                continue
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if (
                name
                and name.startswith("check_api_")
                and len(node.args) >= 2
                and isinstance(node.args[1], (ast.Constant, ast.JoinedStr))
            ):
                violations.append(f"{module.relative_to(package)}:{node.lineno}")
            if name == "Resource" and any(
                keyword.arg == "path"
                and isinstance(keyword.value, (ast.Constant, ast.JoinedStr))
                for keyword in node.keywords
            ):
                violations.append(f"{module.relative_to(package)}:{node.lineno}")

    assert not violations, "Build every Check API path with api_path(): " + ", ".join(
        violations
    )
