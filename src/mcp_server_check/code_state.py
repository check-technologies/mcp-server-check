"""Values a run_code program saves for later programs in the same conversation.

Every program runs in a fresh MicroVM, so nothing a program computes reaches
the next one unless the model retypes it. Programs can instead call
``await check.save("name", value)`` and, in a later program,
``await check.load("name")``. The calls are host functions like the tools:
the runner in the MicroVM proxies them over its WebSocket the same way, so
the MicroVM image does not change. The values live in an AsyncKeyValue
store on the host (an in-process MemoryStore locally, the hosted server's
DynamoDB table in production), under a scope derived from the conversation.

A scope needs a conversation. Over HTTP the client names it in the
X-MCP-Conversation-Id header, and the scope hashes it together with the
request's credential so one caller cannot read another's values by guessing
an ID. Over stdio, or any transport without an HTTP request, the process
serves one client, so the whole process is one scope.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

CONVERSATION_HEADER = "x-mcp-conversation-id"
COLLECTION = "code_state"
LOCAL_SCOPE = "local"

_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_INDEX_KEY = "__index__"


def _valid_name(name: Any) -> bool:
    # Names starting "__" are reserved, so a program cannot overwrite the index.
    return (
        isinstance(name, str) and bool(_NAME.match(name)) and not name.startswith("__")
    )


class KeyValueStore(Protocol):
    """The part of key_value.aio's AsyncKeyValue this module uses. The hosted
    server's DynamoDBKeyValue and key_value's MemoryStore both satisfy it."""

    async def get(
        self, key: str, *, collection: str | None = None
    ) -> dict[str, Any] | None: ...

    async def put(
        self,
        key: str,
        value: Any,
        *,
        collection: str | None = None,
        ttl: Any = None,
    ) -> None: ...


@dataclass(frozen=True)
class StateLimits:
    """Caps on what one conversation may keep. Each has a CHECK_CODE_STATE_*
    environment variable."""

    # DynamoDB items cap at 400 KB; leave room for the key and attributes.
    max_value_bytes: int = 256 * 1024
    max_total_bytes: int = 2 * 1024 * 1024
    max_keys: int = 50
    # A support conversation rarely runs past a working day.
    ttl_secs: int = 6 * 60 * 60

    @classmethod
    def from_env(cls) -> StateLimits:
        env = os.environ
        return cls(
            max_value_bytes=int(
                env.get("CHECK_CODE_STATE_MAX_VALUE_BYTES", cls.max_value_bytes)
            ),
            max_total_bytes=int(
                env.get("CHECK_CODE_STATE_MAX_TOTAL_BYTES", cls.max_total_bytes)
            ),
            max_keys=int(env.get("CHECK_CODE_STATE_MAX_KEYS", cls.max_keys)),
            ttl_secs=int(env.get("CHECK_CODE_STATE_TTL_SECS", cls.ttl_secs)),
        )


def state_scope(request: Any, *, allow_local: bool = False) -> str | None:
    """The scope a request's saved values live under, or None when it has none.

    ``request`` is the Starlette request of an HTTP call, or None for stdio
    and in-memory transports. A request-less call gets the process-wide
    scope only with ``allow_local``, which a server sets only when it serves
    one client (stdio, local dev); a shared deployment never falls back to a
    scope every caller would share.
    """
    if request is None:
        return LOCAL_SCOPE if allow_local else None
    headers = getattr(request, "headers", None) or {}
    conversation = (headers.get(CONVERSATION_HEADER) or "").strip()
    if not conversation:
        return None
    credential = headers.get("authorization") or headers.get("x-check-token") or ""
    digest = hashlib.sha256(f"{credential}\n{conversation}".encode()).hexdigest()
    return f"c-{digest}"


class ProgramState:
    """save / load / saved for the programs of one scope."""

    def __init__(
        self, store: KeyValueStore, scope: str, limits: StateLimits | None = None
    ) -> None:
        self._store = store
        self._scope = scope
        self._limits = limits or StateLimits()
        # A program that saves inside asyncio.gather would otherwise race on
        # the index's read-modify-write and drop names from it.
        self._lock = asyncio.Lock()

    def _key(self, name: str) -> str:
        return f"{self._scope}:{name}"

    async def _index(self) -> dict[str, int]:
        record = await self._store.get(self._key(_INDEX_KEY), collection=COLLECTION)
        return dict((record or {}).get("sizes") or {})

    async def save(self, name: str, value: Any) -> None:
        if not _valid_name(name):
            raise ValueError(
                f"check.save name must be 1-64 letters, digits, '_', '.' or '-'; "
                f"got {name!r}"
            )
        try:
            encoded = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"check.save({name!r}) needs a JSON-serializable value "
                f"(dict, list, str, number, bool, None): {e}"
            ) from e
        size = len(encoded.encode())
        limits = self._limits
        if size > limits.max_value_bytes:
            raise ValueError(
                f"check.save({name!r}) value is {size} bytes; the limit is "
                f"{limits.max_value_bytes}. Save the IDs or fields you need, "
                "not whole pages."
            )
        async with self._lock:
            sizes = await self._index()
            sizes[name] = size
            if len(sizes) > limits.max_keys:
                raise ValueError(
                    f"check.save({name!r}) would keep {len(sizes)} names; the "
                    f"limit is {limits.max_keys}. Reuse a name."
                )
            total = sum(sizes.values())
            if total > limits.max_total_bytes:
                raise ValueError(
                    f"check.save({name!r}) would keep {total} bytes in this "
                    f"conversation; the limit is {limits.max_total_bytes}."
                )
            ttl = limits.ttl_secs
            await self._store.put(
                self._key(name), {"value": encoded}, collection=COLLECTION, ttl=ttl
            )
            await self._store.put(
                self._key(_INDEX_KEY), {"sizes": sizes}, collection=COLLECTION, ttl=ttl
            )

    async def load(self, name: str, default: Any = None) -> Any:
        if not _valid_name(name):
            raise ValueError(f"check.load name is not a saved name: {name!r}")
        record = await self._store.get(self._key(name), collection=COLLECTION)
        if record is None or "value" not in record:
            return default
        return json.loads(record["value"])

    async def saved(self) -> dict[str, int]:
        """Each saved name and its size in bytes."""
        return await self._index()

    def functions(self) -> dict[str, Callable[..., Awaitable[Any]]]:
        """The host functions a program reaches as check.save / load / saved."""
        return {"save": self.save, "load": self.load, "saved": self.saved}


STATE_FUNCTIONS = frozenset({"save", "load", "saved"})


def unavailable_functions(
    reason: str,
) -> dict[str, Callable[..., Awaitable[Any]]]:
    """Stand-ins that explain why there is nowhere to save this request."""

    async def refuse(*args: Any, **kwargs: Any) -> Any:
        raise ValueError(reason)

    return dict.fromkeys(STATE_FUNCTIONS, refuse)
