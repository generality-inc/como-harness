from __future__ import annotations

from .._transport import AsyncTransport, SyncTransport


class SyncResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport


class AsyncResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport
