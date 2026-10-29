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
import contextlib
import inspect
import json
import logging
import math
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

# Standard-library modules the sandbox provides (checked against
# pydantic-monty 1.3). Filesystem and network modules are left out: they
# import but every access is denied.
SANDBOX_MODULES: tuple[str, ...] = (
    "asyncio",
    "base64",
    "bisect",
    "collections",
    "copy",
    "csv",
    "dataclasses",
    "datetime",
    "functools",
    "hashlib",
    "itertools",
    "json",
    "math",
    "random",
    "re",
    "time",
    "typing",
    "unicodedata",
)

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

Make the answer the program's last expression; the server serializes it. The
sandbox's modules are {", ".join(SANDBOX_MODULES)}; json.dumps takes indent
and sort_keys but not default. asyncio has only gather(*coros) and sleep():
no Semaphore, wait_for, or create_task, and the server already caps
concurrent calls and retries throttled ones, so do not throttle. No async
with, async for, generators, class inheritance, or del. Generator
expressions evaluate eagerly to lists here (use next(iter(...))).

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
    max_memory_bytes: int = 256 * 1024 * 1024
    concurrency: int = 8
    max_retries: int = 8
    max_programs: int = 4
    # A Lambda MicroVM image ARN. When set, programs run in CPython in a fresh
    # MicroVM instead of Monty.
    microvm_image: str = ""

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
_FUNCTION_DIAGNOSTIC = re.compile(r"function `(\w+)`")
_MISSING_MEMBER = re.compile(r"Module `" + MODULE_NAME + r"` has no member `(\w+)`")


def missing_member_notes(
    errors: Iterable[str],
    entries: Mapping[str, ToolEntry],
    tool_filter: ToolFilter,
    writes: Iterable[str],
) -> list[str]:
    """Why each tool the type checker could not find is absent from `check`.

    "Module `check` has no member `create_correction`" is true for a tool
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


# Diagnostics that name a tool but judge the type of an argument rather than
# its name. The checker infers those types from untyped JSON, so `cid = None`
# followed by `cid = c["id"]` in a loop is "str | None" to it and the call is
# refused; such lines are reported as warnings instead of blocking the run.
_WARNING_DIAGNOSTICS = ("[invalid-argument-type]",)


def _tool_diagnostics(
    diagnostics: str, tool_names: Iterable[str]
) -> tuple[list[str], list[str]]:
    """Split diagnostics into those worth blocking on and those worth a warning.

    Type checking exists to catch a wrong tool name or argument before any API
    call. Diagnostics about the program's own handling of untyped results
    (unions the checker infers from JSON) are not reliable enough to block on,
    so only lines naming the module or one of its functions count, plus an
    import the sandbox cannot resolve, which would fail at runtime anyway. A
    line naming a function but only doubting an argument's type is a warning.
    """
    names = set(tool_names)
    errors: list[str] = []
    warnings: list[str] = []
    for line in diagnostics.splitlines():
        if "Module `" + MODULE_NAME + "`" in line or "[unresolved-import]" in line:
            errors.append(line)
            continue
        match = _FUNCTION_DIAGNOSTIC.search(line)
        if not match or match.group(1) not in names:
            continue
        if any(code in line for code in _WARNING_DIAGNOSTICS):
            warnings.append(line)
        else:
            errors.append(line)
    return errors, warnings


def signature_errors(diagnostics: str, tool_names: Iterable[str]) -> list[str]:
    """The type-check diagnostics worth blocking on; see _tool_diagnostics."""
    return _tool_diagnostics(diagnostics, tool_names)[0]


def signature_warnings(diagnostics: str, tool_names: Iterable[str]) -> list[str]:
    """Type-check diagnostics about a tool call that do not block the run."""
    return _tool_diagnostics(diagnostics, tool_names)[1]


_MODULE_LIST = ", ".join(SANDBOX_MODULES)
_SANDBOX_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"JSONEncoder\.__init__\(\) got an unexpected keyword argument"),
        "The sandbox's json.dumps takes indent, sort_keys, and ensure_ascii but "
        "not default. Make the data the program's last expression instead of "
        "serializing it: the server turns it into JSON and renders dates and "
        "other objects as strings.",
    ),
    (
        re.compile(
            r"No module named '([^']+)'|Cannot resolve imported module `([^`]+)`"
        ),
        "The sandbox has no {name} module and no third-party packages. Its "
        f"modules are {_MODULE_LIST}.",
    ),
    (
        re.compile(r"'list' object is not an iterator"),
        "Generator expressions evaluate eagerly to lists in the sandbox, so "
        "next() cannot consume one. Use next(iter(...)), index the list, or a "
        "for loop.",
    ),
    (
        re.compile(
            r"does not yet support async context managers"
            r"|module 'asyncio' has no attribute"
            r"|gather\(\) does not yet support keyword arguments"
        ),
        "The sandbox's asyncio has only gather(*coros) and sleep(): no "
        "Semaphore, wait_for, create_task, async with, or gather keyword "
        "arguments. Drop the throttling; the server already caps concurrent "
        "calls and retries throttled ones. For partial failures, catch "
        "RuntimeError inside a helper coroutine instead of "
        "gather(return_exceptions=True).",
    ),
    (
        re.compile(r"does not yet support yield expressions"),
        "The sandbox has no generators, so no yield or async for. Build and "
        "return lists instead.",
    ),
    (
        re.compile(r"does not yet support class inheritance"),
        "The sandbox has no class inheritance: no subclassing, custom "
        "exception classes, TypedDict, or NamedTuple. Use plain classes, "
        "dicts, or dataclasses, and raise built-in exceptions.",
    ),
    (
        re.compile(r"does not yet support the 'del' statement"),
        "The sandbox has no del statement. Use dict.pop(key) or list.pop(i).",
    ),
    (
        re.compile(r"exceptions can only be called with zero or one string argument"),
        "Exceptions in the sandbox take at most one string argument.",
    ),
    (
        re.compile(r"exceeded its budget of (\d+) tool calls"),
        "The program made more than {name} tool calls, and the calls that "
        "succeeded before the limit are lost with it. Split the work across "
        "several run_code programs, or use a composite tool such as "
        "get_company_overview or get_employee_snapshot that bundles several "
        "API calls into one.",
    ),
    (
        # Anything else Monty's parser or runtime reports as unsupported.
        re.compile(r"does not yet support (.+?)(?:\.|$)"),
        "The sandbox does not support {name}. Rewrite the program without it.",
    ),
)


def sandbox_hint(detail: str) -> str | None:
    """Advice for a failure caused by a known limit of the sandbox."""
    for pattern, hint in _SANDBOX_HINTS:
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


def _timeout_detail(timeout: float) -> str:
    return (
        f"The program did not finish within {timeout:g} seconds. "
        "Make fewer or more parallel calls."
    )


MICROVM_PORT = 8080
MICROVM_MAX_MESSAGE_BYTES = 16 * 1024 * 1024


@contextlib.asynccontextmanager
async def launch_microvm(image_arn: str, timeout: float):
    """Run a MicroVM from the runner image; yield its WebSocket URL and headers.

    The MicroVM gets no execution role and no egress connector, so the program
    reaches nothing but this host. It is terminated on exit, and Lambda
    terminates it anyway a minute after the program's time budget.
    """
    try:
        import boto3
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise CheckToolError(
            {
                "error": True,
                "detail": "MicroVM code mode needs boto3: uv sync --extra microvm.",
            }
        ) from e
    region = image_arn.split(":")[3]
    client = boto3.client("lambda-microvms", region_name=region)
    run = await asyncio.to_thread(
        client.run_microvm,
        imageIdentifier=image_arn,
        ingressNetworkConnectors=[
            f"arn:aws:lambda:{region}:aws:network-connector:aws-network-connector:ALL_INGRESS"
        ],
        maximumDurationInSeconds=int(timeout) + 60,
    )
    microvm_id = run["microvmId"]
    try:
        state = run["state"]
        while state == "PENDING":
            await asyncio.sleep(0.1)
            state = (
                await asyncio.to_thread(
                    client.get_microvm, microvmIdentifier=microvm_id
                )
            )["state"]
        if state != "RUNNING":
            raise RuntimeError(f"MicroVM {microvm_id} is {state}, not RUNNING")
        token = await asyncio.to_thread(
            client.create_microvm_auth_token,
            microvmIdentifier=microvm_id,
            expirationInMinutes=max(1, math.ceil(timeout / 60)),
            allowedPorts=[{"port": MICROVM_PORT}],
        )
        yield (
            f"wss://{run['endpoint']}/",
            {"X-aws-proxy-auth": token["authToken"]["X-aws-proxy-auth"]},
        )
    finally:
        try:
            await asyncio.to_thread(
                client.terminate_microvm, microvmIdentifier=microvm_id
            )
        except Exception:
            logger.warning("Could not terminate MicroVM %s", microvm_id, exc_info=True)


class CodeRunner:
    """Runs programs against the tools in a ToolIndex, honoring a ToolFilter."""

    def __init__(
        self, index: ToolIndex, settings: CodeModeSettings | None = None
    ) -> None:
        self._index = index
        self._settings = settings or CodeModeSettings.from_env()
        # Each program holds a Monty worker process; cap them across requests.
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
        while the program runs. Raises CheckToolError, with the trace so far, when the program
        does not type-check, raises, or exhausts a budget. Waiting for a free
        program slot does not count against the time budget.
        """
        run = self._run_microvm if self._settings.microvm_image else self._run
        async with self._programs:
            return await run(code, tool_filter, writes, on_call)

    async def _run(
        self,
        code: str,
        tool_filter: ToolFilter,
        writes: Sequence[str] = (),
        on_call: CallListener | None = None,
    ) -> dict[str, Any]:
        pm = _monty()
        entries = self.callable_entries(tool_filter, writes)
        program = ProgramRun(on_call=on_call)
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
        timeout = self._settings.timeout_secs
        started = time.monotonic()
        deadline = started + timeout

        def failure(kind: str, detail: str) -> CheckToolError:
            return _program_failure(
                kind, detail, printed.output, program.calls, sandbox_hint(detail)
            )

        async def feed(session: Any, source: str, **kwargs: Any) -> Any:
            # One deadline across every feed, so a type-check rerun cannot
            # double the budget.
            remaining = max(deadline - time.monotonic(), 0)
            return await asyncio.wait_for(
                session.feed_run(source, **kwargs), timeout=remaining
            )

        warnings: list[str] = []
        try:
            async with pm.AsyncMonty(min_processes=1, max_processes=1) as pool:
                session = pool.checkout(
                    type_check=True,
                    type_check_format="concise",
                    limits=limits,
                    external_modules={MODULE_NAME: module},
                )
                async with session:
                    # Bind the module up front so programs need no import and
                    # the type checker knows the name; a program's own
                    # `import check` is then a harmless repeat.
                    await feed(session, f"import {MODULE_NAME}")
                    try:
                        value = await feed(session, code, print_callback=printed)
                    except pm.MontyTypingError as e:
                        errors, warnings = _tool_diagnostics(e.display(), module.attrs)
                        if errors:
                            if all("[unresolved-import]" in line for line in errors):
                                what = (
                                    "The program imports a module the sandbox "
                                    "does not have; nothing ran.\n"
                                )
                            else:
                                what = (
                                    "The program does not match the check module's "
                                    "signatures; nothing ran. Use get_stubs to see "
                                    "them.\n"
                                )
                            notes = missing_member_notes(
                                errors, self._index.entries, tool_filter, writes
                            )
                            raise failure(
                                "type_check_failed",
                                what + "\n".join([*errors, *notes]),
                            ) from e
                        # Diagnostics about the program's own data handling:
                        # run it anyway.
                        value = await feed(
                            session, code, print_callback=printed, skip_type_check=True
                        )
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
            raise failure("timeout", _timeout_detail(timeout)) from e
        except pm.MontyError as e:
            raise failure("sandbox_error", str(e)) from e
        finally:
            # Whatever ended the program, nothing it started may outlive it:
            # a call still in flight would otherwise finish in the background
            # and report progress to a request that has already answered.
            program.close()

        result = {
            "result": value,
            "logs": printed.output,
            "calls": [c.to_dict() for c in program.calls],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
        if warnings:
            result["warnings"] = warnings
        return result

    async def _run_microvm(
        self,
        code: str,
        tool_filter: ToolFilter,
        writes: Sequence[str] = (),
        on_call: CallListener | None = None,
    ) -> dict[str, Any]:
        """Run the program in CPython in a fresh Lambda MicroVM.

        The runner in the MicroVM (microvm_runner.py) sends each check.* call
        back over the WebSocket, and the same host functions Monty uses answer
        it, so the ToolFilter, writes, budgets, and retries apply unchanged.
        """
        # shortcut: no type check before the run, so a wrong tool name fails
        # at runtime; run ty on the host against render_stubs(entries) to
        # restore type_check_failed.
        from websockets.asyncio.client import connect

        entries = self.callable_entries(tool_filter, writes)
        program = ProgramRun(on_call=on_call)
        semaphore = asyncio.Semaphore(self._settings.concurrency)
        functions = {
            entry.name: self._host_function(entry, tool_filter, semaphore, program)
            for entry in entries
        }
        timeout = self._settings.timeout_secs
        started = time.monotonic()
        answers: set[asyncio.Task] = set()

        async def answer(ws: Any, call: dict[str, Any]) -> None:
            reply: dict[str, Any] = {"id": call.get("id")}
            try:
                fn = functions.get(call.get("tool"))
                if fn is None:
                    raise ValueError(f"Tool {call.get('tool')!r} is not callable")
                value = await fn(*call.get("args", ()), **call.get("kwargs", {}))
                reply.update(type="result", value=value)
            except Exception as e:
                reply.update(type="error", error_type=type(e).__name__, message=str(e))
            await ws.send(json.dumps(reply, default=str))

        async def converse() -> dict[str, Any]:
            async with launch_microvm(self._settings.microvm_image, timeout) as (
                url,
                headers,
            ):
                async with connect(
                    url,
                    additional_headers=headers,
                    max_size=MICROVM_MAX_MESSAGE_BYTES,
                ) as ws:
                    request = {
                        "type": "execute",
                        "code": code,
                        "tools": list(functions),
                    }
                    await ws.send(json.dumps(request))
                    async for raw in ws:
                        message = json.loads(raw)
                        if message.get("type") != "call":
                            return message
                        task = asyncio.create_task(answer(ws, message))
                        answers.add(task)
                        task.add_done_callback(answers.discard)
            raise RuntimeError("The MicroVM closed the connection without a result")

        try:
            reply = await asyncio.wait_for(converse(), timeout=timeout)
        except asyncio.TimeoutError as e:
            raise _program_failure(
                "timeout", _timeout_detail(timeout), "", program.calls
            ) from e
        except CheckToolError:
            raise
        except Exception as e:
            raise _program_failure(
                "sandbox_error", f"{type(e).__name__}: {e}", "", program.calls
            ) from e
        finally:
            # As in the Monty path: no call may outlive the program.
            program.close()
            for task in answers:
                task.cancel()

        if reply.get("type") != "done":
            raise _program_failure(
                str(reply.get("kind", "runtime_error")),
                str(reply.get("detail", "")),
                str(reply.get("logs", "")),
                program.calls,
            )
        return {
            "result": reply.get("value"),
            "logs": reply.get("logs", ""),
            "calls": [c.to_dict() for c in program.calls],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
