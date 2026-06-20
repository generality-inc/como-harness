"""Cloud-browser resource — ephemeral sessions + persistent profiles.

The single source of truth for the ``/v1/browser`` route map. The Browser Use
key never leaves the platform; callers only ever see ``cdp_url`` / ``live_url``.
"""

from __future__ import annotations

from como_core.platform import BrowserProfile, BrowserSession, ProfileLoginSession

from ._base import AsyncResource, SyncResource

_BASE = "/v1/browser"


def _create_session_body(profile: str | None) -> dict:
    return {"profile": profile} if profile else {}


def _create_profile_body(*, name: str, description: str | None, shared: bool) -> dict:
    return {"name": name, "description": description, "visibility": "shared" if shared else "private"}


class BrowserResource(SyncResource):
    # --- sessions ---------------------------------------------------------
    def create_session(self, *, profile: str | None = None) -> BrowserSession:
        return BrowserSession.model_validate(self._t.post(_BASE, json=_create_session_body(profile)))

    def stop_session(self, browser_id: str) -> None:
        self._t.delete(f"{_BASE}/{browser_id}")

    # --- profiles ---------------------------------------------------------
    def profiles(self) -> list[BrowserProfile]:
        body = self._t.get(f"{_BASE}/profiles")
        return [BrowserProfile.model_validate(p) for p in body or []]

    def create_profile(self, *, name: str, description: str | None = None, shared: bool = False) -> BrowserProfile:
        body = _create_profile_body(name=name, description=description, shared=shared)
        return BrowserProfile.model_validate(self._t.post(f"{_BASE}/profile", json=body))

    def delete_profile(self, profile_id: str) -> None:
        self._t.delete(f"{_BASE}/profile/{profile_id}")

    def start_login(self, profile_id: str, *, login_url: str | None = None) -> ProfileLoginSession:
        body = {"login_url": login_url} if login_url else {}
        return ProfileLoginSession.model_validate(self._t.post(f"{_BASE}/profile/{profile_id}/login", json=body))

    def complete_login(self, profile_id: str) -> BrowserProfile:
        return BrowserProfile.model_validate(self._t.post(f"{_BASE}/profile/{profile_id}/login/complete", json={}))

    def cancel_login(self, profile_id: str) -> None:
        self._t.post(f"{_BASE}/profile/{profile_id}/login/cancel", json={})


class AsyncBrowserResource(AsyncResource):
    async def create_session(self, *, profile: str | None = None) -> BrowserSession:
        return BrowserSession.model_validate(await self._t.post(_BASE, json=_create_session_body(profile)))

    async def stop_session(self, browser_id: str) -> None:
        await self._t.delete(f"{_BASE}/{browser_id}")

    async def profiles(self) -> list[BrowserProfile]:
        body = await self._t.get(f"{_BASE}/profiles")
        return [BrowserProfile.model_validate(p) for p in body or []]

    async def create_profile(
        self, *, name: str, description: str | None = None, shared: bool = False
    ) -> BrowserProfile:
        body = _create_profile_body(name=name, description=description, shared=shared)
        return BrowserProfile.model_validate(await self._t.post(f"{_BASE}/profile", json=body))

    async def delete_profile(self, profile_id: str) -> None:
        await self._t.delete(f"{_BASE}/profile/{profile_id}")

    async def start_login(self, profile_id: str, *, login_url: str | None = None) -> ProfileLoginSession:
        body = {"login_url": login_url} if login_url else {}
        return ProfileLoginSession.model_validate(await self._t.post(f"{_BASE}/profile/{profile_id}/login", json=body))

    async def complete_login(self, profile_id: str) -> BrowserProfile:
        return BrowserProfile.model_validate(
            await self._t.post(f"{_BASE}/profile/{profile_id}/login/complete", json={})
        )

    async def cancel_login(self, profile_id: str) -> None:
        await self._t.post(f"{_BASE}/profile/{profile_id}/login/cancel", json={})
