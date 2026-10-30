"""Host side of the MicroVM code-mode backend.

Each program runs in CPython in a fresh Lambda MicroVM started from an image
of microvm_runner.py. The runner sends each ``check.*`` call back over a
WebSocket, and the host functions code_mode builds answer it, so the
ToolFilter, writes, budgets, and retries apply to every call. Needs the
``code`` extra; code_mode imports this module only when a program runs.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import json
import logging
import math
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import boto3
from websockets.asyncio.client import connect

from mcp_server_check.code_mode import ProgramFailed, timeout_detail
from mcp_server_check.microvm_runner import MAX_MESSAGE_BYTES, PORT

logger = logging.getLogger(__name__)

# A MicroVM takes about 1.4s to start, and each poll interval past RUNNING is
# added to every run. botocore retries a throttled GetMicrovm on its own.
POLL_SECS = 0.05

# The failure kinds the runner reports. The program can write to the runner's
# socket, so any other kind it claims is reported as a runtime error.
_RUNNER_FAILURES = frozenset({"syntax_error", "runtime_error"})


@functools.cache
def _client(region: str) -> Any:
    """One boto3 client per region for the life of the process.

    Building a client loads the service model, which took about 300ms on a
    cold Lambda; boto3 clients are safe to share across threads.
    """
    return boto3.client("lambda-microvms", region_name=region)


@contextlib.asynccontextmanager
async def launch_microvm(image_arn: str, timeout: float):
    """Run a MicroVM from the runner image; yield its WebSocket URL and headers.

    The MicroVM gets no execution role, so the program holds no AWS
    credentials. It is terminated on exit, and Lambda ends it anyway shortly
    after the program's time budget.
    """
    region = image_arn.split(":")[3]
    client = _client(region)
    # Shielded: a run cancelled while RunMicrovm is in flight still gets a
    # MicroVM, and only the ID in the response lets us terminate it.
    starting = asyncio.ensure_future(
        asyncio.to_thread(
            client.run_microvm,
            imageIdentifier=image_arn,
            ingressNetworkConnectors=[
                f"arn:aws:lambda:{region}:aws:network-connector:aws-network-connector:ALL_INGRESS"
            ],
            maximumDurationInSeconds=int(timeout) + 15,
        )
    )
    try:
        run = await asyncio.shield(starting)
    except asyncio.CancelledError:
        with contextlib.suppress(Exception):
            started = await starting
            await asyncio.to_thread(
                client.terminate_microvm, microvmIdentifier=started["microvmId"]
            )
        raise
    microvm_id = run["microvmId"]
    try:
        state = run["state"]
        while state == "PENDING":
            await asyncio.sleep(POLL_SECS)
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
            allowedPorts=[{"port": PORT}],
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


async def execute(
    code: str,
    functions: Mapping[str, Callable[..., Awaitable[Any]]],
    image_arn: str,
    timeout: float,
) -> tuple[Any, str]:
    """Run a program in a fresh MicroVM; return its value and printed output.

    Raises ProgramFailed when the program fails, the MicroVM cannot be
    reached, or the time budget runs out.
    """
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
        async with launch_microvm(image_arn, timeout) as (url, headers):
            async with connect(
                url, additional_headers=headers, max_size=MAX_MESSAGE_BYTES
            ) as ws:
                request = {"type": "execute", "code": code, "tools": list(functions)}
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
        raise ProgramFailed("timeout", timeout_detail(timeout)) from e
    except Exception as e:
        raise ProgramFailed("sandbox_error", f"{type(e).__name__}: {e}") from e
    finally:
        for task in answers:
            task.cancel()

    logs = str(reply.get("logs", ""))
    if reply.get("type") == "done":
        return reply.get("value"), logs
    kind = reply.get("kind")
    raise ProgramFailed(
        kind if kind in _RUNNER_FAILURES else "runtime_error",
        str(reply.get("detail", "")),
        logs,
    )
