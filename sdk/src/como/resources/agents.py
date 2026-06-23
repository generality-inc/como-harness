"""Research-agents resource — author, link, and run agents over lists.

The single source of truth for the ``/v1/crm/agents`` + ``/v1/crm/agent-batches``
route map. Name/slug resolution stays in the CLI; the SDK deals in ids.
"""

from __future__ import annotations

from typing import Any

from como_core.crm import CrmBaseModel
from como_core.platform import Agent, AgentBatch

from .._params import clean_params
from ._base import AsyncResource, SyncResource

_BASE = "/v1/crm"
_AGENTS = f"{_BASE}/agents"
_BATCHES = f"{_BASE}/agent-batches"


class AgentRun(CrmBaseModel):
    """One per-record run within a batch — the per-record audit row (status, the
    value written, cost, whether it was reused, error, timestamps)."""

    id: str | None = None
    record_id: str | None = None
    record_name: str | None = None
    attribute_slug: str | None = None
    status: str | None = None
    agent_version: int | None = None
    mapped_value: dict[str, Any] | None = None
    cost_usd: Any | None = None
    reused: bool | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None


def _active_params(*, attribute_id: str, list_id: str) -> dict[str, str]:
    return clean_params({"attribute_id": attribute_id, "list_id": list_id})


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

    def list_batches(self, agent_id: str) -> list[AgentBatch]:
        """An agent's run history — its batches, newest first."""
        body = self._t.get(f"{_AGENTS}/{agent_id}/batches")
        return [AgentBatch.model_validate(b) for b in body or []]

    def get_batch(self, batch_id: str) -> AgentBatch:
        """One batch's progress — status, counters, and spend."""
        return AgentBatch.model_validate(self._t.get(f"{_BATCHES}/{batch_id}"))

    def list_runs(self, batch_id: str) -> list[AgentRun]:
        """The per-record runs of a batch — the per-record audit rows."""
        body = self._t.get(f"{_BATCHES}/{batch_id}/runs")
        return [AgentRun.model_validate(r) for r in body or []]

    def active_batch(self, *, attribute_id: str, list_id: str) -> AgentBatch | None:
        """The active (pending/running) batch for a column+list, or ``None``."""
        body = self._t.get(f"{_BATCHES}/active", params=_active_params(attribute_id=attribute_id, list_id=list_id))
        return AgentBatch.model_validate(body) if body else None


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

    async def list_batches(self, agent_id: str) -> list[AgentBatch]:
        body = await self._t.get(f"{_AGENTS}/{agent_id}/batches")
        return [AgentBatch.model_validate(b) for b in body or []]

    async def get_batch(self, batch_id: str) -> AgentBatch:
        return AgentBatch.model_validate(await self._t.get(f"{_BATCHES}/{batch_id}"))

    async def list_runs(self, batch_id: str) -> list[AgentRun]:
        body = await self._t.get(f"{_BATCHES}/{batch_id}/runs")
        return [AgentRun.model_validate(r) for r in body or []]

    async def active_batch(self, *, attribute_id: str, list_id: str) -> AgentBatch | None:
        body = await self._t.get(
            f"{_BATCHES}/active", params=_active_params(attribute_id=attribute_id, list_id=list_id)
        )
        return AgentBatch.model_validate(body) if body else None
