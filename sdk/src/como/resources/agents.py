"""Research-agents resource — author, link, and run agents over lists.

The single source of truth for the ``/v1/crm/agents`` + ``/v1/crm/agent-batches``
route map. Name/slug resolution stays in the CLI; the SDK deals in ids.
"""

from __future__ import annotations

from typing import Any

from como_core.platform import Agent, AgentBatch

from ._base import AsyncResource, SyncResource

_BASE = "/v1/crm"
_AGENTS = f"{_BASE}/agents"
_BATCHES = f"{_BASE}/agent-batches"


class AgentsResource(SyncResource):
    def list(self) -> list[Agent]:
        body = self._t.get(_AGENTS)
        return [Agent.model_validate(a) for a in body or []]

    def create(self, definition: dict[str, Any]) -> Agent:
        return Agent.model_validate(self._t.post(_AGENTS, json=definition))

    def set_browser_profile(self, agent_id: str, *, profile_id: str | None) -> Agent:
        """Link (or, with ``profile_id=None``, unlink) an agent's browser profile."""
        return Agent.model_validate(self._t.patch(f"{_AGENTS}/{agent_id}", json={"browser_profile_id": profile_id}))

    def delete(self, agent_id: str) -> None:
        self._t.delete(f"{_AGENTS}/{agent_id}")

    def run_batch(self, *, attribute_id: str, list_id: str) -> AgentBatch:
        body = {"attribute_id": attribute_id, "list_id": list_id}
        return AgentBatch.model_validate(self._t.post(_BATCHES, json=body))


class AsyncAgentsResource(AsyncResource):
    async def list(self) -> list[Agent]:
        body = await self._t.get(_AGENTS)
        return [Agent.model_validate(a) for a in body or []]

    async def create(self, definition: dict[str, Any]) -> Agent:
        return Agent.model_validate(await self._t.post(_AGENTS, json=definition))

    async def set_browser_profile(self, agent_id: str, *, profile_id: str | None) -> Agent:
        return Agent.model_validate(
            await self._t.patch(f"{_AGENTS}/{agent_id}", json={"browser_profile_id": profile_id})
        )

    async def delete(self, agent_id: str) -> None:
        await self._t.delete(f"{_AGENTS}/{agent_id}")

    async def run_batch(self, *, attribute_id: str, list_id: str) -> AgentBatch:
        body = {"attribute_id": attribute_id, "list_id": list_id}
        return AgentBatch.model_validate(await self._t.post(_BATCHES, json=body))
