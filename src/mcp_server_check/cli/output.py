"""Output formatters for the Check CLI."""

from __future__ import annotations

import json
import sys


def format_json(data: dict | list) -> str:
    """Format data as compact JSON (pipe-friendly)."""
    return json.dumps(data, separators=(",", ":"))


def format_table(data: dict | list) -> str:
    """Format data as a human-readable table."""
    if isinstance(data, dict) and "results" in data:
        rows = data["results"]
        if not rows:
            return "No results."
        parts = [_format_rows(rows)]
        if data.get("next_cursor"):
            parts.append(f"\nNext cursor: {data['next_cursor']}")
        return "\n".join(parts)

    if isinstance(data, list):
        if not data:
            return "No results."
        return _format_rows(data)

    if isinstance(data, dict):
        return _format_object(data)

    return str(data)


def _format_rows(rows: list[dict]) -> str:
    """Format a list of dicts as aligned columns."""
    if not rows:
        return ""
    columns = list(rows[0].keys())
    widths: dict[str, int] = {}
    for col in columns:
        values = [str(row.get(col, "")) for row in rows]
        widths[col] = min(max(len(col), max((len(v) for v in values), default=0)), 40)

    header = "  ".join(col.upper().ljust(widths[col]) for col in columns)
    separator = "  ".join("-" * widths[col] for col in columns)
    lines = [header, separator]
    for row in rows:
        line = "  ".join(
            str(row.get(col, ""))[:widths[col]].ljust(widths[col]) for col in columns
        )
        lines.append(line)
    return "\n".join(lines)


def _format_object(obj: dict) -> str:
    """Format a single dict as key-value pairs."""
    if not obj:
        return "{}"
    max_key_len = max(len(str(k)) for k in obj)
    lines = []
    for key, value in obj.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, indent=2)
        lines.append(f"{str(key).ljust(max_key_len)}  {value}")
    return "\n".join(lines)


def output_result(data: dict | list, fmt: str, file: object | None = None) -> None:
    """Print formatted output to *file* (default stdout)."""
    if file is None:
        file = sys.stdout
    if fmt == "table":
        print(format_table(data), file=file)
    else:
        print(format_json(data), file=file)
