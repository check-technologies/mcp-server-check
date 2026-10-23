"""Code mode: run model-written Python against the Check tools in a sandbox.

Instead of one tool call per API request, the model writes a short program.
``import check`` exposes one async function per Check tool; each call proxies
to the same tool function run_tool would run, through the same ToolFilter, and
the program's final value comes back as one result. The program runs in a
Pydantic Monty sandbox: no network, no filesystem, a time and memory budget,
and only ``check.*`` calls leave it. Credentials never enter the sandbox.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import random
import re
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from fastmcp.exceptions import ToolError, ValidationError
from fastmcp.tools import ToolResult
from typing_extensions import is_typeddict

from mcp_server_check import types as check_types
from mcp_server_check.errors import CheckToolError
from mcp_server_check.tool_filter import ToolFilter
from mcp_server_check.tool_index import ToolEntry, ToolIndex

MODULE_NAME = "check"

_CTX_ANNOTATIONS = frozenset({"Ctx", "Context"})

_STUB_HEADER = f'''\
"""The `{MODULE_NAME}` module, already imported in programs run with run_code.

Every function is async: `await {MODULE_NAME}.list_companies(limit=100)`. Use
asyncio.gather for independent calls. A failed Check API call raises
RuntimeError whose message is a JSON object with "status_code" and "detail".
Throttled calls are retried for you. List results carry "results",
"result_count" and "next_cursor"; pass the cursor back to page. Write tools
are marked below and must be named in run_code's `writes` argument before a
program can call them. Generator expressions evaluate eagerly to lists here.
"""

from typing import Any
from typing_extensions import TypedDict
'''

_WRITE_NOTE = "# write tool: name it in run_code(writes=[...]) to call it"


def _install_hint() -> str:
    return (
        "Code mode needs the pydantic-monty package. Install the server with "
        "the 'code' extra: uv sync --extra code (or pip install "
        "'mcp-server-check[code]')."
    )


def _monty():
    try:
        import pydantic_monty
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise CheckToolError({"error": True, "detail": _install_hint()}) from e
    return pydantic_monty


# ---------------------------------------------------------------------------
# Stub rendering
# ---------------------------------------------------------------------------


def _annotation_text(annotation: Any) -> str:
    """Render a parameter annotation as it should read in a stub."""
    if annotation is inspect.Parameter.empty:
        return "Any"
    if isinstance(annotation, str):
        return annotation
    if isinstance(annotation, type):
        return annotation.__name__
    return str(annotation).replace("typing_extensions.", "").replace("typing.", "")


def _is_ctx(param: inspect.Parameter) -> bool:
    annotation = param.annotation
    name = (
        annotation
        if isinstance(annotation, str)
        else getattr(annotation, "__name__", "")
    )
    return param.name == "ctx" or name in _CTX_ANNOTATIONS


def tool_parameters(fn: Any) -> list[inspect.Parameter]:
    """The parameters a program passes to a tool: everything but the context."""
    return [
        p
        for p in inspect.signature(fn).parameters.values()
        if not _is_ctx(p)
        and p.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]


def render_signature(entry: ToolEntry) -> str:
    """One-line ``async def`` signature for a tool."""
    params = []
    for p in tool_parameters(entry.tool.fn):
        text = f"{p.name}: {_annotation_text(p.annotation)}"
        if p.default is not inspect.Parameter.empty:
            text += f" = {p.default!r}"
        params.append(text)
    # Results are untyped JSON; `Any` keeps the type checker on names and
    # arguments, where it catches real mistakes, and off result shapes, where a
    # strict `dict` produced false positives on mixed asyncio.gather results.
    return f"async def {entry.name}({', '.join(params)}) -> Any"


def render_stub(entry: ToolEntry, *, mark_writes: bool = False) -> str:
    """A typed stub for one tool: signature plus its full docstring."""
    doc = inspect.cleandoc(entry.tool.fn.__doc__ or entry.description)
    body = "\n".join(f"    {line}".rstrip() for line in doc.splitlines())
    lines = []
    if mark_writes and entry.is_write:
        lines.append(_WRITE_NOTE)
    lines += [f"{render_signature(entry)}:", '    """', body, '    """', "    ..."]
    return "\n".join(lines) + "\n"


def _render_typed_dicts() -> str:
    """Stub definitions for the TypedDicts tool signatures refer to."""
    out: list[str] = []
    for name, obj in vars(check_types).items():
        if not is_typeddict(obj) or obj.__module__ != check_types.__name__:
            continue
        total = "" if getattr(obj, "__total__", True) else ", total=False"
        out.append(f"class {name}(TypedDict{total}):")
        hints = getattr(obj, "__annotations__", {})
        if not hints:
            out.append("    ...")
        for field_name, hint in hints.items():
            out.append(f"    {field_name}: {_annotation_text(hint)}")
        out.append("")
    return "\n".join(out)


def render_stubs(entries: Iterable[ToolEntry], *, mark_writes: bool = False) -> str:
    """The ``check`` module's stub file for the given tools, grouped by toolset."""
    by_toolset: dict[str, list[ToolEntry]] = {}
    for entry in entries:
        by_toolset.setdefault(entry.toolset, []).append(entry)
    parts = [_STUB_HEADER, _render_typed_dicts()]
    for toolset, toolset_entries in by_toolset.items():
        parts.append(f"# ---- {toolset} ----\n")
        parts.extend(render_stub(e, mark_writes=mark_writes) for e in toolset_entries)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CodeModeSettings:
    """Budgets for one program. Each has a CHECK_CODE_* environment variable."""

    timeout_secs: float = 60.0
    max_calls: int = 200
    max_memory_bytes: int = 256 * 1024 * 1024
    concurrency: int = 8
    max_retries: int = 4

    @classmethod
    def from_env(cls) -> CodeModeSettings:
        env = os.environ
        return cls(
            timeout_secs=float(env.get("CHECK_CODE_TIMEOUT_SECS", cls.timeout_secs)),
            max_calls=int(env.get("CHECK_CODE_MAX_CALLS", cls.max_calls)),
            max_memory_bytes=int(
                float(env.get("CHECK_CODE_MAX_MEMORY_MB", 256)) * 1024 * 1024
            ),
            concurrency=int(env.get("CHECK_CODE_CONCURRENCY", cls.concurrency)),
            max_retries=int(env.get("CHECK_CODE_MAX_RETRIES", cls.max_retries)),
        )


@dataclass
class CallRecord:
    """One tool call a program made, for the trace returned with the result."""

    tool: str
    arguments: dict[str, Any]
    status: str = "ok"
    duration_ms: int = 0
    retries: int = 0
    error: Any = None

    def to_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "tool": self.tool,
            "arguments": self.arguments,
            "status": self.status,
            "duration_ms": self.duration_ms,
        }
        if self.retries:
            record["retries"] = self.retries
        if self.error is not None:
            record["error"] = self.error
        return record


_THROTTLE_HINT = re.compile(r"available in (\d+(?:\.\d+)?) second")


def _is_throttled(payload: dict[str, Any]) -> bool:
    return payload.get("status_code") == 429


def _retry_delay(payload: dict[str, Any], attempt: int) -> float:
    """Seconds to wait before retrying a throttled call.

    Honors the wait the Check API names ("Expected available in N second"),
    otherwise backs off exponentially from one second; jitter spreads a
    gather's retries apart.
    """
    match = _THROTTLE_HINT.search(json.dumps(payload.get("detail")))
    base = float(match.group(1)) if match else float(min(2**attempt, 8))
    return base + random.uniform(0, 0.25 * base)


@dataclass
class ProgramRun:
    """Bookkeeping shared by the host functions of one program."""

    calls: list[CallRecord] = field(default_factory=list)


def _decode(result: ToolResult) -> Any:
    """Turn a tool's MCP result back into the Python value the tool returned."""
    values: list[Any] = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text is None:
            values.append(block.model_dump())
            continue
        try:
            values.append(json.loads(text))
        except ValueError:
            values.append(text)
    if len(values) == 1:
        return values[0]
    return values


class CodeRunner:
    """Runs programs against the tools in a ToolIndex, honoring a ToolFilter."""

    def __init__(
        self, index: ToolIndex, settings: CodeModeSettings | None = None
    ) -> None:
        self._index = index
        self._settings = settings or CodeModeSettings.from_env()

    @property
    def settings(self) -> CodeModeSettings:
        return self._settings

    def visible_entries(
        self,
        tool_filter: ToolFilter,
        *,
        toolset: str | None = None,
        tools: Sequence[str] | None = None,
    ) -> list[ToolEntry]:
        """Tools the caller may see, for get_stubs."""
        wanted = set(tools) if tools else None
        return [
            entry
            for entry in self._index.entries.values()
            if tool_filter.is_tool_allowed(entry.name, entry.toolset)
            and (toolset is None or entry.toolset == toolset)
            and (wanted is None or entry.name in wanted)
        ]

    def callable_entries(
        self, tool_filter: ToolFilter, writes: Sequence[str] = ()
    ) -> list[ToolEntry]:
        """Tools a program may call: every allowed read tool plus the declared writes."""
        declared = set(writes)
        unknown = declared - set(self._index.entries)
        if unknown:
            raise CheckToolError(
                {
                    "error": True,
                    "detail": f"Unknown tool(s) in writes: {', '.join(sorted(unknown))}",
                }
            )
        entries: list[ToolEntry] = []
        for entry in self._index.entries.values():
            if not tool_filter.is_tool_allowed(entry.name, entry.toolset):
                if entry.name in declared:
                    raise CheckToolError(
                        {
                            "error": True,
                            "detail": (
                                f"Tool '{entry.name}' is not available in the "
                                "current configuration"
                            ),
                        }
                    )
                continue
            if entry.is_write and entry.name not in declared:
                continue
            entries.append(entry)
        return entries

    def _host_function(
        self,
        entry: ToolEntry,
        tool_filter: ToolFilter,
        semaphore: asyncio.Semaphore,
        run: ProgramRun,
    ):
        names = [p.name for p in tool_parameters(entry.tool.fn)]
        max_calls = self._settings.max_calls
        max_retries = self._settings.max_retries

        async def call(*args: Any, **kwargs: Any) -> Any:
            if len(args) > len(names):
                raise TypeError(
                    f"{entry.name}() takes at most {len(names)} positional "
                    f"arguments ({len(args)} given)"
                )
            arguments = {**dict(zip(names, args)), **kwargs}
            if len(run.calls) >= max_calls:
                raise RuntimeError(
                    json.dumps(
                        {
                            "error": True,
                            "detail": f"Program exceeded its budget of {max_calls} tool calls.",
                        }
                    )
                )
            record = CallRecord(tool=entry.name, arguments=arguments)
            run.calls.append(record)
            started = time.monotonic()
            try:
                while True:
                    try:
                        async with semaphore:
                            result = await self._index.run(
                                entry.name, arguments, tool_filter
                            )
                        break
                    except CheckToolError as e:
                        # A throttled call is retried here, outside the
                        # semaphore, so a program's gather does not have to
                        # know about rate limits.
                        if (
                            not _is_throttled(e.payload)
                            or record.retries >= max_retries
                        ):
                            raise
                        delay = _retry_delay(e.payload, record.retries)
                        record.retries += 1
                        await asyncio.sleep(delay)
            except CheckToolError as e:
                record.status = "error"
                record.error = e.payload
                raise RuntimeError(json.dumps(e.payload)) from e
            except (ToolError, ValidationError, ValueError) as e:
                record.status = "error"
                record.error = str(e)
                raise ValueError(str(e)) from e
            finally:
                record.duration_ms = int((time.monotonic() - started) * 1000)
            return _decode(result)

        call.__name__ = entry.name
        call.__qualname__ = entry.name
        return call

    async def run(
        self, code: str, tool_filter: ToolFilter, writes: Sequence[str] = ()
    ) -> dict[str, Any]:
        """Run a program and return its value, printed output, and call trace.

        Raises CheckToolError, with the trace so far, when the program does not
        type-check, raises, or exhausts a budget.
        """
        pm = _monty()
        entries = self.callable_entries(tool_filter, writes)
        program = ProgramRun()
        semaphore = asyncio.Semaphore(self._settings.concurrency)
        module = pm.ExternalModule(
            {
                entry.name: self._host_function(entry, tool_filter, semaphore, program)
                for entry in entries
            },
            stubs=render_stubs(entries),
        )
        printed = pm.CollectString()
        limits = pm.ResourceLimits(
            max_feed_duration_secs=self._settings.timeout_secs,
            max_memory=self._settings.max_memory_bytes,
            # Backstop for the call budget enforced in the host functions;
            # gathers and name lookups count here too.
            max_suspensions=self._settings.max_calls * 4 + 64,
        )
        started = time.monotonic()

        def failure(kind: str, detail: str) -> CheckToolError:
            return CheckToolError(
                {
                    "error": True,
                    "kind": kind,
                    "detail": detail,
                    "logs": printed.output,
                    "calls": [c.to_dict() for c in program.calls],
                }
            )

        try:
            async with pm.AsyncMonty(min_processes=1, max_processes=1) as pool:
                session = pool.checkout(
                    type_check=True,
                    limits=limits,
                    external_modules={MODULE_NAME: module},
                )
                async with session:
                    # Bind the module up front so programs need no import and
                    # the type checker knows the name; a program's own
                    # `import check` is then a harmless repeat.
                    await session.feed_run(f"import {MODULE_NAME}")
                    value = await asyncio.wait_for(
                        session.feed_run(code, print_callback=printed),
                        timeout=self._settings.timeout_secs,
                    )
        except pm.MontyTypingError as e:
            raise failure(
                "type_check_failed",
                "The program does not match the check module's signatures; "
                "nothing ran. Use get_stubs or search_tools to see them.\n"
                + e.display(),
            ) from e
        except pm.MontySyntaxError as e:
            raise failure("syntax_error", e.display()) from e
        except pm.MontyRuntimeError as e:
            kind = (
                "timeout"
                if isinstance(e.exception(), TimeoutError)
                else "runtime_error"
            )
            raise failure(kind, e.display()) from e
        except asyncio.TimeoutError as e:
            raise failure(
                "timeout",
                f"The program did not finish within {self._settings.timeout_secs:g} "
                "seconds. Make fewer or more parallel calls.",
            ) from e
        except pm.MontyError as e:
            raise failure("sandbox_error", str(e)) from e

        return {
            "result": value,
            "logs": printed.output,
            "calls": [c.to_dict() for c in program.calls],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
