from __future__ import annotations

from typing import Any

import httpx

from ._config import DEFAULT_TIMEOUT, resolve_api_key, resolve_base_url
from ._version import __version__
from .errors import ComoNetworkError, error_for_status


def _build_headers(api_key: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": f"como-python/{__version__}",
    }
    if extra:
        headers.update(extra)
    return headers


def _parse_body(response: httpx.Response) -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def _handle(response: httpx.Response) -> Any:
    body = _parse_body(response)
    if response.status_code >= 400:
        raise error_for_status(response.status_code, body, response)
    return body


class SyncTransport:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = resolve_base_url(base_url)
        self._api_key = resolve_api_key(api_key)
        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.Client(
                base_url=self._base_url,
                headers=_build_headers(self._api_key),
                timeout=timeout,
            )
            self._owns_client = True

    def get(self, path: str, *, params: dict[str, str] | None = None) -> Any:
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise ComoNetworkError(str(exc)) from exc
        return _handle(response)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> SyncTransport:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncTransport:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = resolve_base_url(base_url)
        self._api_key = resolve_api_key(api_key)
        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=_build_headers(self._api_key),
                timeout=timeout,
            )
            self._owns_client = True

    async def get(self, path: str, *, params: dict[str, str] | None = None) -> Any:
        try:
            response = await self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise ComoNetworkError(str(exc)) from exc
        return _handle(response)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
