"""Runs one code-mode program inside a Lambda MicroVM.

The host connects over a WebSocket and sends ``{"type": "execute", "code",
"tools"}``. Each ``check.<tool>(...)`` the program awaits goes back to the host
as ``{"type": "call"}`` and resolves when the host answers with ``result`` or
``error``. The runner ends with ``done`` or ``failed``. It holds no
credentials and enforces nothing: the host applies the ToolFilter, budgets,
and retries to every call. Standard library plus websockets only, so the
MicroVM image needs nothing from this package.
"""

from __future__ import annotations

import ast
import asyncio
import builtins
import contextlib
import io
import itertools
import json
import sys
import traceback
import types

FILENAME = "<program>"
PORT = 8080
MAX_MESSAGE_BYTES = 16 * 1024 * 1024

# Exception types the host may name in an error reply; anything else is raised
# as RuntimeError so a program's `except RuntimeError` keeps working. A reply
# of kind "APIError" carries the failed call's payload and is rebuilt as
# APIError below.
_HOST_ERRORS = {"RuntimeError", "ValueError", "TypeError"}


def api_error_type(payload: dict) -> str | None:
    """The Check API's error type in a failed call's payload, when it named one.

    The API answers a failed request with ``{"error": {"type": "not_found",
    "message": ...}}``, which the tool keeps under ``detail``.
    """
    detail = payload.get("detail")
    error = detail.get("error") if isinstance(detail, dict) else None
    kind = error.get("type") if isinstance(error, dict) else None
    return kind if isinstance(kind, str) else None


class APIError(RuntimeError):
    """A failed Check API call, raised inside a program as ``check.APIError``.

    ``str(e)`` is the JSON error payload, as it was when a failed call raised
    a bare RuntimeError, so code that parses the message still works; the
    attributes save parsing it. One uncaught failure ends the whole program
    and throws away every other call's result, so a program catches this
    around the one call that may fail, or gathers with ``return_exceptions``.
    """

    # The class lives on the `check` module inside a program, so a traceback
    # reads "check.APIError: ..." rather than naming this file.
    __module__ = "check"

    def __init__(self, payload: dict) -> None:
        super().__init__(json.dumps(payload))
        self.payload = payload
        self.status_code = payload.get("status_code")
        self.type = api_error_type(payload)
        self.detail = payload.get("detail")


def host_error(reply: dict) -> BaseException:
    """The exception an error reply from the host stands for.

    An "APIError" reply without its payload, from a host older than this
    runner, falls back to today's RuntimeError with the JSON message.
    """
    kind = reply.get("error_type")
    if kind == "APIError" and isinstance(reply.get("payload"), dict):
        return APIError(reply["payload"])
    error = getattr(builtins, kind if kind in _HOST_ERRORS else "RuntimeError")
    return error(reply["message"])


def compile_program(code: str) -> types.CodeType:
    """Compile a program whose last expression becomes ``__result__``."""
    tree = ast.parse(code, FILENAME)
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last = tree.body[-1]
        tree.body[-1] = ast.copy_location(
            ast.Assign(
                targets=[ast.Name(id="__result__", ctx=ast.Store())], value=last.value
            ),
            last,
        )
        ast.fix_missing_locations(tree)
    return compile(tree, FILENAME, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)


def _program_traceback(error: BaseException) -> str:
    """The traceback limited to the program's own frames."""
    frames = [
        f for f in traceback.extract_tb(error.__traceback__) if f.filename == FILENAME
    ]
    lines = [f'  File "{FILENAME}", line {f.lineno}, in {f.name}\n' for f in frames]
    if lines:
        lines.insert(0, "Traceback (most recent call last):\n")
    return "".join(lines + traceback.format_exception_only(type(error), error))


async def run_program(ws, code: str, tools: list[str]) -> dict:
    """Run one program, answering its check.* calls over ``ws``."""
    loop = asyncio.get_running_loop()
    pending: dict[int, asyncio.Future] = {}
    ids = itertools.count(1)

    def tool(name: str):
        async def call(*args, **kwargs):
            call_id = next(ids)
            future = loop.create_future()
            pending[call_id] = future
            message = {
                "type": "call",
                "id": call_id,
                "tool": name,
                "args": args,
                "kwargs": kwargs,
            }
            await ws.send(json.dumps(message, default=str))
            return await future

        call.__name__ = call.__qualname__ = name
        return call

    module = types.ModuleType("check")
    for name in tools:
        setattr(module, name, tool(name))
    module.APIError = APIError
    sys.modules["check"] = module

    async def read_replies() -> None:
        async for raw in ws:
            reply = json.loads(raw)
            future = pending.pop(reply.get("id"), None)
            if future is None or future.done():
                continue
            if reply["type"] == "result":
                future.set_result(reply["value"])
            else:
                future.set_exception(host_error(reply))

    reader = asyncio.create_task(read_replies())
    out = io.StringIO()
    # The stub header tells programs to use asyncio.gather and to return
    # values the server serializes, so both modules are in scope from the
    # start: a program that forgets `import asyncio` otherwise dies on its
    # first gather before making a single call.
    namespace = {
        "__name__": "__main__",
        "check": module,
        "asyncio": asyncio,
        "json": json,
    }
    try:
        with contextlib.redirect_stdout(out):
            program = compile_program(code)
            awaitable = eval(program, namespace)
            if awaitable is not None:
                await awaitable
    except SyntaxError as e:
        detail = "".join(traceback.format_exception_only(type(e), e))
        return {
            "type": "failed",
            "kind": "syntax_error",
            "detail": detail,
            "logs": out.getvalue(),
        }
    # SystemExit too: sys.exit() in a program is a failure to report, not a
    # reason to drop the connection and its output.
    except (Exception, SystemExit) as e:
        return {
            "type": "failed",
            "kind": "runtime_error",
            "detail": _program_traceback(e),
            "logs": out.getvalue(),
        }
    finally:
        reader.cancel()
    return {
        "type": "done",
        "value": namespace.get("__result__"),
        "logs": out.getvalue(),
    }


async def handle(ws) -> None:
    """One connection runs one program."""
    request = json.loads(await ws.recv())
    reply = await run_program(ws, request["code"], request["tools"])
    await ws.send(json.dumps(reply, default=str))


async def serve(host: str = "0.0.0.0", port: int = PORT) -> None:
    from websockets.asyncio.server import serve as ws_serve

    async with ws_serve(handle, host, port, max_size=MAX_MESSAGE_BYTES) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(serve())
