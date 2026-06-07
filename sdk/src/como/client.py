from __future__ import annotations

from typing import Any

import httpx

from ._config import DEFAULT_TIMEOUT
from ._transport import AsyncTransport, SyncTransport
from .resources.ads import AdsResource, AsyncAdsResource
from .resources.company import AsyncCompanyResource, CompanyResource
from .resources.geo import AsyncGeoResource, GeoResource
from .resources.group import AsyncGroupResource, GroupResource
from .resources.job import AsyncJobResource, JobResource
from .resources.leads import AsyncLeadsResource, LeadsResource
from .resources.post import AsyncPostResource, PostResource
from .resources.profile import AsyncProfileResource, ProfileResource
from .resources.service import AsyncServiceResource, ServiceResource


class Como:
    """Synchronous Como client.

    Reads `COMO_API_KEY` and `COMO_API_BASE_URL` from the environment if not provided.
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
        self.ads = AdsResource(self._transport)
        self.company = CompanyResource(self._transport)
        self.geo = GeoResource(self._transport)
        self.group = GroupResource(self._transport)
        self.job = JobResource(self._transport)
        self.leads = LeadsResource(self._transport)
        self.post = PostResource(self._transport)
        self.profile = ProfileResource(self._transport)
        self.service = ServiceResource(self._transport)

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
        self.ads = AsyncAdsResource(self._transport)
        self.company = AsyncCompanyResource(self._transport)
        self.geo = AsyncGeoResource(self._transport)
        self.group = AsyncGroupResource(self._transport)
        self.job = AsyncJobResource(self._transport)
        self.leads = AsyncLeadsResource(self._transport)
        self.post = AsyncPostResource(self._transport)
        self.profile = AsyncProfileResource(self._transport)
        self.service = AsyncServiceResource(self._transport)

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> AsyncComo:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
