from __future__ import annotations

from como_core import Cost, CostMixin

from .._transport import AsyncTransport, SyncTransport


def lift_cost[E: CostMixin](entity: E, body: object) -> E:
    """Carry a sibling top-level ``cost`` from the response envelope onto an
    element-GET entity.

    Element-GET endpoints unwrap ``body["element"]`` and validate only that
    entity, which would otherwise drop the sibling ``cost`` key. The entity
    models declare ``cost`` (via ``CostMixin``), so this sets a typed field.
    """
    if isinstance(body, dict) and body.get("cost") is not None:
        entity.cost = Cost.model_validate(body["cost"])
    return entity


class SyncResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport


class AsyncResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport
