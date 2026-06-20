"""Account resource — the authenticated identity + CLI key management.

Covers the API calls that have a key (``GET /v1/me`` and the
``/v1/cli/keys`` management used by ``como auth whoami`` / ``logout``). The
keyless device-code login handshake stays in the CLI — it bootstraps the key
this resource needs and so can't go through the authenticated client.
"""

from __future__ import annotations

from como_core.platform import CliKey, Me

from ._base import AsyncResource, SyncResource


class AccountResource(SyncResource):
    def me(self) -> Me:
        return Me.model_validate(self._t.get("/v1/me"))

    def list_keys(self) -> list[CliKey]:
        body = self._t.get("/v1/cli/keys")
        return [CliKey.model_validate(k) for k in body or []]

    def delete_key(self, key_id: str) -> None:
        self._t.delete(f"/v1/cli/keys/{key_id}")


class AsyncAccountResource(AsyncResource):
    async def me(self) -> Me:
        return Me.model_validate(await self._t.get("/v1/me"))

    async def list_keys(self) -> list[CliKey]:
        body = await self._t.get("/v1/cli/keys")
        return [CliKey.model_validate(k) for k in body or []]

    async def delete_key(self, key_id: str) -> None:
        await self._t.delete(f"/v1/cli/keys/{key_id}")
