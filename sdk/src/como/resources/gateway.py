"""LLM-gateway resource — mint a short-lived, budget-capped inference key.

The provider key never leaves the platform; the caller gets a virtual key + the
base URL to route the Anthropic/OpenAI SDKs through (see ``como run``).
"""

from __future__ import annotations

from como_core.platform import GatewayKey

from ._base import AsyncResource, SyncResource

_PATH = "/v1/llm-gateway/key"


class GatewayResource(SyncResource):
    def create_key(self) -> GatewayKey:
        return GatewayKey.model_validate(self._t.post(_PATH))


class AsyncGatewayResource(AsyncResource):
    async def create_key(self) -> GatewayKey:
        return GatewayKey.model_validate(await self._t.post(_PATH))
