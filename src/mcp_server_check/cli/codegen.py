"""Auto-generate click commands from tool function signatures."""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
import types
import typing
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable

import click
import httpx

from mcp_server_check.helpers import CheckContext
from mcp_server_check.tools import collect_all_tools

from .context import CLIContext
from .output import output_result


# ---------------------------------------------------------------------------
# Custom click parameter types
# ---------------------------------------------------------------------------


class JSONParam(click.ParamType):
    """Click parameter type for JSON values.

    Accepts inline JSON strings or ``@filename`` (use ``@-`` for stdin).
    """

    name = "JSON"

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str) and value.startswith("@"):
            path = value[1:]
            try:
                if path == "-":
                    content = sys.stdin.read()
                else:
                    with open(path) as f:
                        content = f.read()
                return json.loads(content)
            except (OSError, json.JSONDecodeError) as e:
                self.fail(f"Failed to read JSON from {path}: {e}", param, ctx)
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON: {e}", param, ctx)


class CSVList(click.ParamType):
    """Click parameter type for comma-separated string lists."""

    name = "CSV"

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> Any:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return [s.strip() for s in value.split(",") if s.strip()]


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------


def _singularize(word: str) -> str:
    """Naive singularization: companies->company, accounts->account."""
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _make_command_name(func_name: str, toolset_name: str) -> str:
    """Derive a CLI command name from a tool function name and its toolset.

    Algorithm: find the toolset's plural or singular form as a contiguous
    subsequence of the function-name parts and remove it, then join with ``-``.

    Examples::

        list_companies, companies   -> list
        get_company, companies      -> get
        get_company_paydays, companies -> get-paydays
        list_employee_paystubs, employees -> list-paystubs
        simulate_start_processing, payrolls -> simulate-start-processing
        list_bank_accounts, bank_accounts -> list
    """
    parts = func_name.split("_")
    ts_plural = toolset_name.split("_")
    ts_singular = ts_plural[:-1] + [_singularize(ts_plural[-1])]

    for needle in (ts_plural, ts_singular):
        n = len(needle)
        for i in range(len(parts) - n + 1):
            if parts[i : i + n] == needle:
                remaining = parts[:i] + parts[i + n :]
                if remaining:
                    return "-".join(remaining)
                # Entire name was the toolset name (shouldn't happen in practice)
                break

    # No toolset component found – use the full name
    return "-".join(parts)


# ---------------------------------------------------------------------------
# Type introspection
# ---------------------------------------------------------------------------


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    """Unwrap ``X | None`` → ``(X, True)``.  Non-optional → ``(X, False)``."""
    if isinstance(annotation, types.UnionType):
        args = [a for a in annotation.__args__ if a is not type(None)]
        if len(args) == 1:
            return args[0], True
        return annotation, False
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0], True
        return annotation, False
    return annotation, False


def _is_id_param(name: str) -> bool:
    """Return True if a parameter name looks like a resource ID."""
    return name.endswith("_id")


def _get_param_help(func: Callable, param_name: str) -> str | None:
    """Extract a parameter's help text from the function's docstring."""
    doc = func.__doc__
    if not doc:
        return None
    for line in doc.split("\n"):
        stripped = line.strip()
        if stripped.startswith(f"{param_name}:"):
            return stripped[len(param_name) + 1 :].strip()
    return None


# ---------------------------------------------------------------------------
# Parameter builder
# ---------------------------------------------------------------------------


def _build_params(func: Callable) -> list[click.Parameter]:
    """Build a list of click parameters from *func*'s signature."""
    sig = inspect.signature(func)
    hints = typing.get_type_hints(func)
    params: list[click.Parameter] = []

    for name, param in sig.parameters.items():
        if name == "ctx":
            continue
        annotation = hints.get(name, str)
        base_type, is_optional = _unwrap_optional(annotation)
        has_default = param.default is not inspect.Parameter.empty
        is_required = not is_optional and not has_default
        cli_name = name.replace("_", "-")
        help_text = _get_param_help(func, name)

        # Positional argument for required ID strings
        if base_type is str and _is_id_param(name) and not has_default:
            params.append(click.Argument([name], type=click.STRING))
            continue

        # Boolean flag  (--flag / --no-flag, default None)
        if base_type is bool:
            params.append(
                click.Option(
                    [f"--{cli_name}/--no-{cli_name}"],
                    default=None,
                    help=help_text,
                )
            )
            continue

        # Common option kwargs — only set default=None for optional params
        # (setting default on a required option prevents click from enforcing it)
        opt_kwargs: dict[str, Any] = {"required": is_required, "help": help_text}
        if not is_required:
            opt_kwargs["default"] = None

        # Dict / TypedDict or list[dict] → JSON param
        _is_dict = isinstance(base_type, type) and issubclass(base_type, dict)
        if _is_dict or (
            typing.get_origin(base_type) is list
            and typing.get_args(base_type)
            and isinstance(typing.get_args(base_type)[0], type)
            and issubclass(typing.get_args(base_type)[0], dict)
        ):
            params.append(
                click.Option([f"--{cli_name}"], type=JSONParam(), **opt_kwargs)
            )
            continue

        # list[str] → CSV list
        if typing.get_origin(base_type) is list:
            params.append(click.Option([f"--{cli_name}"], type=CSVList(), **opt_kwargs))
            continue

        # int
        if base_type is int:
            params.append(click.Option([f"--{cli_name}"], type=click.INT, **opt_kwargs))
            continue

        # float
        if base_type is float:
            params.append(
                click.Option([f"--{cli_name}"], type=click.FLOAT, **opt_kwargs)
            )
            continue

        # Default: string
        params.append(click.Option([f"--{cli_name}"], type=click.STRING, **opt_kwargs))

    return params


# ---------------------------------------------------------------------------
# Callback factory
# ---------------------------------------------------------------------------


def _make_callback(func: Callable) -> Callable:
    """Create a sync click callback that runs the async tool function."""

    def callback(**kwargs: Any) -> None:
        ctx = click.get_current_context()
        api_key: str = ctx.obj["api_key"]
        base_url: str = ctx.obj["base_url"]
        fmt: str = ctx.obj["format"]

        if not api_key:
            click.echo(
                "Error: CHECK_API_KEY is required. "
                "Set it via --api-key or the CHECK_API_KEY env var.",
                err=True,
            )
            ctx.exit(3)
            return

        # Strip None values so tool functions use their own defaults
        call_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        async def _run() -> dict:
            try:
                pkg_version = version("mcp-server-check")
            except PackageNotFoundError:
                pkg_version = "dev"
            async with httpx.AsyncClient(
                base_url=base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": f"check-cli/{pkg_version}",
                },
                timeout=30.0,
            ) as client:
                check_ctx = CheckContext(client=client, base_url=base_url)
                cli_ctx = CLIContext(check_ctx)
                return await func(cli_ctx, **call_kwargs)

        try:
            result = asyncio.run(_run())
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
            return

        if isinstance(result, dict) and result.get("error"):
            output_result(result, fmt, file=sys.stderr)
            ctx.exit(1)
        else:
            output_result(result, fmt)

    return callback


# ---------------------------------------------------------------------------
# Command builder
# ---------------------------------------------------------------------------


def build_command(func: Callable, toolset_name: str) -> tuple[str, click.Command, str]:
    """Build a click Command from *func*.

    Returns ``(command_name, click_command, tool_function_name)``.
    """
    cmd_name = _make_command_name(func.__name__, toolset_name)
    params = _build_params(func)
    cb = _make_callback(func)

    # Use first line of docstring as short help
    help_text = None
    if func.__doc__:
        help_text = func.__doc__.strip().split("\n")[0]

    cmd = click.Command(name=cmd_name, params=params, callback=cb, help=help_text)
    return cmd_name, cmd, func.__name__


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------


# Re-export for backwards compatibility and CLI usage
collect_tools = collect_all_tools
