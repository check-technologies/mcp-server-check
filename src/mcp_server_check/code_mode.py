"""Code mode: run model-written Python against the Check tools in a sandbox.

Instead of one tool call per API request, the model writes a short program.
``import check`` exposes one async function per Check tool; each call proxies
to the same tool function run_tool would run, through the same ToolFilter, and
the program's final value comes back as one result. Each program runs in
CPython in a fresh Lambda MicroVM (microvm_host.py), so code mode is available
only when CHECK_CODE_MICROVM_IMAGE names an image. The host functions here
answer every ``check.*`` call, and credentials never enter the MicroVM.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import random
import re
import time
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from fastmcp.exceptions import ToolError, ValidationError
from fastmcp.tools import ToolResult
from typing_extensions import is_typeddict

from mcp_server_check import types as check_types
from mcp_server_check.errors import CheckToolError
from mcp_server_check.tool_filter import PREVIEW_TOOLSETS, ToolFilter
from mcp_server_check.tool_index import ToolEntry, ToolIndex

logger = logging.getLogger(__name__)

MODULE_NAME = "check"

_CTX_ANNOTATIONS = frozenset({"Ctx", "Context"})

_STUB_HEADER = f'''\
"""The `{MODULE_NAME}` module, already imported in programs run with run_code.

Every function is async: `await {MODULE_NAME}.list_companies(limit=100)`. Use
asyncio.gather for independent calls. A failed Check API call raises
RuntimeError whose message is a JSON object with "status_code" and "detail".
Throttled calls, and reads whose connection dropped, are retried for you. List
results carry "results",
"result_count" and "next_cursor"; pass the cursor back to page. Write tools
are marked below and must be named in run_code's `writes` argument before a
program can call them.

Make the answer the program's last expression; the server serializes it.
Programs run in CPython 3.13 with the standard library and no third-party
packages. The server already caps concurrent calls and retries throttled
ones, so do not throttle.

List results are summaries: each record keeps only the fields below, by ID
prefix. Call the matching get_* tool for a full record.
{{summary_fields}}
"""

from typing import Any
from typing_extensions import TypedDict
'''


def _summary_field_lines() -> str:
    from mcp_server_check.helpers import _SUMMARY_FIELDS

    return "\n".join(
        f"  {prefix}* -> {', '.join(fields)}"
        for prefix, fields in sorted(_SUMMARY_FIELDS.items())
    )


_WRITE_NOTE = "# write tool: name it in run_code(writes=[...]) to call it"


def _microvm():
    try:
        from mcp_server_check import microvm_host
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        detail = "Code mode needs the code extra: uv sync --extra code."
        raise CheckToolError({"error": True, "detail": detail}) from e
    return microvm_host


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
    # Results are untyped JSON.
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


def render_catalog(
    entries: Iterable[ToolEntry], descriptions: Mapping[str, str]
) -> str:
    """The toolsets of the `check` module and their tool names, for get_stubs().

    A few hundred names cost far fewer tokens than their stubs, so this is the
    starting point: pick names, then fetch signatures for just those.
    """
    by_toolset: dict[str, list[ToolEntry]] = {}
    for entry in entries:
        by_toolset.setdefault(entry.toolset, []).append(entry)
    lines = [
        f'"""Toolsets of the `{MODULE_NAME}` module. `*` marks a write tool, which',
        "run_code's writes argument must name. For signatures call",
        "get_stubs(tools=[...]), get_stubs(toolset=...), or get_stubs(query=...).",
        '"""',
    ]
    for toolset, group in sorted(by_toolset.items()):
        lines.append("")
        lines.append(f"# ---- {toolset} ({len(group)} tools) ----")
        description = descriptions.get(toolset)
        if description:
            lines.append(f"# {description}")
        names = ", ".join(e.name + ("*" if e.is_write else "") for e in group)
        lines.append(f"# {names}")
    return "\n".join(lines) + "\n"


def render_stubs(entries: Iterable[ToolEntry], *, mark_writes: bool = False) -> str:
    """The ``check`` module's stub file for the given tools, grouped by toolset."""
    by_toolset: dict[str, list[ToolEntry]] = {}
    for entry in entries:
        by_toolset.setdefault(entry.toolset, []).append(entry)
    header = _STUB_HEADER.replace("{summary_fields}", _summary_field_lines())
    parts = [header, _render_typed_dicts()]
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
    concurrency: int = 8
    max_retries: int = 8
    max_programs: int = 4
    # The Lambda MicroVM image programs run in; code mode is off without one.
    microvm_image: str = ""

    @classmethod
    def from_env(cls) -> CodeModeSettings:
        env = os.environ
        return cls(
            timeout_secs=float(env.get("CHECK_CODE_TIMEOUT_SECS", cls.timeout_secs)),
            max_calls=int(env.get("CHECK_CODE_MAX_CALLS", cls.max_calls)),
            concurrency=int(env.get("CHECK_CODE_CONCURRENCY", cls.concurrency)),
            max_retries=int(env.get("CHECK_CODE_MAX_RETRIES", cls.max_retries)),
            max_programs=int(env.get("CHECK_CODE_MAX_PROGRAMS", cls.max_programs)),
            microvm_image=env.get("CHECK_CODE_MICROVM_IMAGE", ""),
        )


@dataclass
class CallRecord:
    """One tool call a program made, for the trace returned with the result."""

    tool: str
    arguments: dict[str, Any]
    # "pending" until the tool returns, so a timeout trace shows calls that
    # had not finished (and, for writes, may still land).
    status: str = "pending"
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

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> CallRecord:
        """The inverse of to_dict."""
        return cls(**{k: v for k, v in record.items() if k in cls.__dataclass_fields__})

    def summary(self, max_args_chars: int = 120) -> str:
        """One line for a progress message or trace: the call and its outcome."""
        args = ", ".join(f"{k}={v!r}" for k, v in self.arguments.items())
        if len(args) > max_args_chars:
            args = args[: max_args_chars - 1] + "…"
        line = f"{self.tool}({args}) {self.status}"
        if self.status != "pending":
            line += f" {self.duration_ms}ms"
        if self.retries:
            line += f" after {self.retries} retr{'y' if self.retries == 1 else 'ies'}"
        if self.error is not None:
            line += f": {_error_summary(self.error)}"
        return line


def _error_summary(error: Any) -> str:
    """The status code and detail of a call's error, on one short line."""
    if isinstance(error, dict):
        parts = [str(error[k]) for k in ("status_code", "detail") if k in error]
        text = " ".join(parts) or json.dumps(error)
    else:
        text = str(error)
    text = " ".join(text.split())
    return text if len(text) <= 160 else text[:159] + "…"


def render_trace(calls: Sequence[CallRecord], duration_ms: int | None = None) -> str:
    """The calls a program made, as text for the client and the user.

    Returned beside the JSON result so the record of what ran is not buried
    inside it, and the model can repeat it to the user.
    """
    if not calls:
        return "Tool calls: none"
    header = f"Tool calls: {len(calls)}"
    if duration_ms is not None:
        header += f" in {duration_ms}ms"
    lines = [f"{i}. {call.summary()}" for i, call in enumerate(calls, 1)]
    return "\n".join([header, *lines])


CallListener = Callable[[CallRecord, int], Awaitable[None]]


_THROTTLE_HINT = re.compile(r"available in (\d+(?:\.\d+)?) second")
_MISSING_MEMBER = re.compile(r"module '" + MODULE_NAME + r"' has no attribute '(\w+)'")


def missing_member_notes(
    errors: Iterable[str],
    entries: Mapping[str, ToolEntry],
    tool_filter: ToolFilter,
    writes: Iterable[str],
) -> list[str]:
    """Why each tool a program could not find is absent from `check`.

    "module 'check' has no attribute 'create_correction'" is true for a tool
    that does not exist, one hidden by the server's configuration, and a
    write the program did not declare, and the fix is different for each.
    """
    declared = set(writes)
    notes: list[str] = []
    seen: set[str] = set()
    for line in errors:
        match = _MISSING_MEMBER.search(line)
        if not match or match.group(1) in seen:
            continue
        name = match.group(1)
        seen.add(name)
        entry = entries.get(name)
        if entry is None:
            notes.append(
                f"{name}: no such tool. Call get_stubs(query='{name}') to find "
                "the right name."
            )
        elif not tool_filter.is_tool_allowed(name, entry.toolset):
            if (
                entry.toolset in PREVIEW_TOOLSETS
                and entry.toolset not in tool_filter.preview_toolsets
            ):
                notes.append(
                    f"{name}: in the preview toolset '{entry.toolset}', which "
                    "this connection has not opted into."
                )
            else:
                notes.append(
                    f"{name}: hidden by the server's configuration (read-only "
                    "mode, toolset selection, or an exclusion)."
                )
        elif entry.is_write and name not in declared:
            notes.append(
                f"{name}: a write tool; name it in run_code's writes argument "
                "to call it."
            )
    return notes


_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"exceeded its budget of (\d+) tool calls"),
        "The program made more than {name} tool calls, and the calls that "
        "succeeded before the limit are lost with it. Split the work across "
        "several run_code programs, or use a composite tool such as "
        "get_company_overview or get_employee_snapshot that bundles several "
        "API calls into one.",
    ),
)


def sandbox_hint(detail: str) -> str | None:
    """Advice for a failure caused by a known limit of code mode."""
    for pattern, hint in _HINTS:
        match = pattern.search(detail)
        if match:
            name = next((g for g in match.groups() if g), "")
            return hint.format(name=name)
    return None


def _is_throttled(payload: dict[str, Any]) -> bool:
    return payload.get("status_code") == 429


def _is_transient(payload: dict[str, Any], *, is_write: bool) -> bool:
    """Whether a failed call is worth retrying.

    A throttled call always is. A transport error (the connection dropped
    before a response arrived) is for a read; a write may already have
    landed, so it is reported instead.
    """
    if _is_throttled(payload):
        return True
    return bool(payload.get("transport_error")) and not is_write


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
    # Told about each call as it finishes, with how many have finished. That
    # count, not the call's position, keeps progress increasing when parallel
    # calls finish out of order.
    on_call: CallListener | None = None
    finished_count: int = 0
    # Monotonic time before which no call may be sent. One throttled call
    # pauses every call of the program, so a gather stops hammering the API
    # the moment it says to wait instead of each call finding out for itself.
    resume_at: float = 0.0
    # The tasks running host calls, so calls still in flight when the program
    # ends can be cancelled rather than left to finish in the background.
    tasks: set[asyncio.Task[Any]] = field(default_factory=set)
    closed: bool = False

    def throttle(self, delay: float) -> None:
        self.resume_at = max(self.resume_at, time.monotonic() + delay)

    async def wait_for_window(self) -> None:
        """Sleep until the program may send a call again."""
        while (delay := self.resume_at - time.monotonic()) > 0:
            await asyncio.sleep(delay)

    def close(self) -> None:
        """Stop reporting calls and cancel those still in flight."""
        self.closed = True
        for task in list(self.tasks):
            task.cancel()
        self.tasks.clear()

    async def finished(self, record: CallRecord) -> None:
        if self.closed:
            return
        self.finished_count += 1
        if self.on_call is None:
            return
        try:
            await self.on_call(record, self.finished_count)
        except Exception:
            # Reporting a call must never fail the program that made it.
            logger.warning("run_code call listener failed", exc_info=True)


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


def _program_failure(
    kind: str,
    detail: str,
    logs: str,
    calls: Sequence[CallRecord],
    hint: str | None = None,
) -> CheckToolError:
    if any(c.status == "pending" for c in calls):
        detail += (
            " Calls marked pending were still in flight when the"
            " program ended and were cancelled; a pending write may"
            " still have landed, so check before retrying it."
        )
    payload: dict[str, Any] = {
        "error": True,
        "kind": kind,
        "detail": detail,
        "logs": logs,
        "calls": [c.to_dict() for c in calls],
    }
    if hint:
        payload["hint"] = hint
    return CheckToolError(payload)


class ProgramFailed(Exception):
    """A program that did not finish, as a backend reports it to CodeRunner.run."""

    def __init__(self, kind: str, detail: str, logs: str = "") -> None:
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
        self.logs = logs


def timeout_detail(timeout: float) -> str:
    return (
        f"The program did not finish within {timeout:g} seconds. "
        "Make fewer or more parallel calls."
    )


class CodeRunner:
    """Runs programs against the tools in a ToolIndex, honoring a ToolFilter."""

    def __init__(
        self, index: ToolIndex, settings: CodeModeSettings | None = None
    ) -> None:
        self._index = index
        self._settings = settings or CodeModeSettings.from_env()
        # Each program holds a MicroVM; cap them across requests.
        self._programs = asyncio.Semaphore(self._settings.max_programs)

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
            task = asyncio.current_task()
            if task is not None:
                run.tasks.add(task)
            started = time.monotonic()
            try:
                while True:
                    try:
                        async with semaphore:
                            # Waiting inside the semaphore keeps the burst
                            # after a pause no larger than the concurrency cap.
                            await run.wait_for_window()
                            result = await self._index.run(
                                entry.name, arguments, tool_filter
                            )
                        break
                    except CheckToolError as e:
                        # Throttled calls, and dropped connections on reads,
                        # are retried here so a program's gather does not
                        # have to know about rate limits. Retrying outside
                        # the semaphore puts the call at the back of the
                        # queue behind calls that have not had a turn.
                        if (
                            not _is_transient(e.payload, is_write=entry.is_write)
                            or record.retries >= max_retries
                        ):
                            raise
                        delay = _retry_delay(e.payload, record.retries)
                        record.retries += 1
                        if _is_throttled(e.payload):
                            run.throttle(delay)
                        else:
                            await asyncio.sleep(delay)
            except CheckToolError as e:
                record.status = "error"
                record.error = e.payload
                raise RuntimeError(json.dumps(e.payload)) from e
            except (ToolError, ValidationError, ValueError) as e:
                record.status = "error"
                record.error = str(e)
                raise ValueError(str(e)) from e
            else:
                record.status = "ok"
            finally:
                if task is not None:
                    run.tasks.discard(task)
                record.duration_ms = int((time.monotonic() - started) * 1000)
                await run.finished(record)
            return _decode(result)

        call.__name__ = entry.name
        call.__qualname__ = entry.name
        return call

    async def run(
        self,
        code: str,
        tool_filter: ToolFilter,
        writes: Sequence[str] = (),
        on_call: CallListener | None = None,
    ) -> dict[str, Any]:
        """Run a program and return its value, printed output, and call trace.

        on_call is awaited after each tool call finishes, with its record and
        the number of calls finished so far, so the caller can report progress
        while the program runs. Raises CheckToolError, with the trace so far,
        when the program raises or exhausts a budget. Waiting for a free
        program slot does not count against the time budget.
        """
        entries = self.callable_entries(tool_filter, writes)
        program = ProgramRun(on_call=on_call)
        semaphore = asyncio.Semaphore(self._settings.concurrency)
        functions = {
            entry.name: self._host_function(entry, tool_filter, semaphore, program)
            for entry in entries
        }
        async with self._programs:
            started = time.monotonic()
            try:
                value, logs = await _microvm().execute(
                    code,
                    functions,
                    self._settings.microvm_image,
                    self._settings.timeout_secs,
                )
            except ProgramFailed as e:
                notes = missing_member_notes(
                    [e.detail], self._index.entries, tool_filter, writes
                )
                raise _program_failure(
                    e.kind,
                    "\n".join([e.detail, *notes]),
                    e.logs,
                    program.calls,
                    sandbox_hint(e.detail),
                ) from e
            finally:
                # Whatever ended the program, nothing it started may outlive
                # it: a call still in flight would otherwise finish in the
                # background and report progress to a request that has
                # already answered.
                program.close()

        return {
            "result": value,
            "logs": logs,
            "calls": [c.to_dict() for c in program.calls],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
