from __future__ import annotations

from typing import Any

import httpx

from ._config import DEFAULT_TIMEOUT
from ._transport import AsyncTransport, SyncTransport
from .resources.account import AccountResource, AsyncAccountResource
from .resources.ads import AdsResource, AsyncAdsResource
from .resources.agents import AgentsResource, AsyncAgentsResource
from .resources.attributes import AsyncAttributesResource, AttributesResource
from .resources.browser import AsyncBrowserResource, BrowserResource
from .resources.company import AsyncCompanyResource, CompanyResource
from .resources.gateway import AsyncGatewayResource, GatewayResource
from .resources.geo import AsyncGeoResource, GeoResource
from .resources.group import AsyncGroupResource, GroupResource
from .resources.job import AsyncJobResource, JobResource
from .resources.leads import AsyncLeadsResource, LeadsResource
from .resources.lists import AsyncListsResource, ListsResource
from .resources.objects import AsyncObjectsResource, ObjectsResource
from .resources.post import AsyncPostResource, PostResource
from .resources.profile import AsyncProfileResource, ProfileResource
from .resources.records import AsyncRecordsResource, RecordsResource
from .resources.service import AsyncServiceResource, ServiceResource
from .resources.views import AsyncViewsResource, ViewsResource


class Como:
    """Synchronous Como client.

    Reads `COMO_API_KEY` and `COMO_BASE_URL` from the environment if not provided.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._transport = SyncTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            http_client=http_client,
        )
        self.account = AccountResource(self._transport)
        self.ads = AdsResource(self._transport)
        self.agents = AgentsResource(self._transport)
        self.attributes = AttributesResource(self._transport)
        self.browser = BrowserResource(self._transport)
        self.company = CompanyResource(self._transport)
        self.gateway = GatewayResource(self._transport)
        self.geo = GeoResource(self._transport)
        self.group = GroupResource(self._transport)
        self.job = JobResource(self._transport)
        self.leads = LeadsResource(self._transport)
        self.lists = ListsResource(self._transport)
        self.objects = ObjectsResource(self._transport)
        self.post = PostResource(self._transport)
        self.profile = ProfileResource(self._transport)
        self.records = RecordsResource(self._transport)
        self.service = ServiceResource(self._transport)
        self.views = ViewsResource(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Como:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncComo:
    """Asynchronous Como client."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._transport = AsyncTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            http_client=http_client,
        )
        self.account = AsyncAccountResource(self._transport)
        self.ads = AsyncAdsResource(self._transport)
        self.agents = AsyncAgentsResource(self._transport)
        self.attributes = AsyncAttributesResource(self._transport)
        self.browser = AsyncBrowserResource(self._transport)
        self.company = AsyncCompanyResource(self._transport)
        self.gateway = AsyncGatewayResource(self._transport)
        self.geo = AsyncGeoResource(self._transport)
        self.group = AsyncGroupResource(self._transport)
        self.job = AsyncJobResource(self._transport)
        self.leads = AsyncLeadsResource(self._transport)
        self.lists = AsyncListsResource(self._transport)
        self.objects = AsyncObjectsResource(self._transport)
        self.post = AsyncPostResource(self._transport)
        self.profile = AsyncProfileResource(self._transport)
        self.records = AsyncRecordsResource(self._transport)
        self.service = AsyncServiceResource(self._transport)
        self.views = AsyncViewsResource(self._transport)

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> AsyncComo:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
