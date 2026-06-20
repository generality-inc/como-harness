"""Platform models — first-party Como objects that aren't CRM rows: cloud
browsers, browser profiles, research agents, the LLM gateway, and the
authenticated account. Like the CRM models these are snake_case on the wire and
keep unknown fields (``extra="allow"``)."""

from __future__ import annotations

from typing import Any

from .crm import CrmBaseModel as _Base


class BrowserSession(_Base):
    """An ephemeral cloud browser. Attach a CDP driver to ``cdp_url``; watch via
    ``live_url``; tear down by id."""

    id: str | None = None
    cdp_url: str | None = None
    live_url: str | None = None


class BrowserProfile(_Base):
    """A persistent, logged-in browser identity (cookies/localStorage)."""

    id: str | None = None
    name: str | None = None
    status: str | None = None
    visibility: str | None = None
    description: str | None = None
    cookie_domains: list[str] = []
    has_linkedin: bool | None = None


class ProfileLoginSession(_Base):
    """The live browser opened so a human can sign a profile in once."""

    browser_id: str | None = None
    cdp_url: str | None = None
    live_url: str | None = None
    login_url: str | None = None
    expires_at: str | None = None


class Agent(_Base):
    """A research-agent definition. ``output_fields`` (derived from the
    ``output_schema``) maps onto CRM columns."""

    id: str | None = None
    workspace_id: str | None = None
    slug: str | None = None
    name: str | None = None
    description: str | None = None
    mission: str | None = None
    input_fields: list[str] = []
    output_schema: dict[str, Any] = {}
    output_fields: dict[str, Any] = {}
    budget_usd: Any | None = None
    model: str | None = None
    tools: list[str] = []
    browser_profile_id: str | None = None
    is_archived: bool | None = None
    created_at: str | None = None


class AgentBatch(_Base):
    """One run of an agent-bound column over a list (one sandboxed run per record)."""

    id: str | None = None
    workspace_id: str | None = None
    agent_id: str | None = None
    attribute_id: str | None = None
    object_id: str | None = None
    list_id: str | None = None
    status: str | None = None
    total_runs: int | None = None
    succeeded_runs: int | None = None
    failed_runs: int | None = None
    cost_ceiling_usd: Any | None = None
    cost_spent_usd: Any | None = None
    error_message: str | None = None
    completed_at: str | None = None
    created_at: str | None = None


class GatewayKey(_Base):
    """A short-lived, budget-capped LLM-gateway key + the base URL to call it."""

    base_url: str | None = None
    api_key: str | None = None
    models: list[str] = []
    expires: Any | None = None


class Me(_Base):
    """The user + workspace the current credentials authenticate as."""

    user: dict[str, Any] = {}
    workspace: dict[str, Any] = {}


class CliKey(_Base):
    """A CLI/SDK API key issued to a device."""

    id: str | None = None
    prefix: str | None = None


class ViewColumn(_Base):
    """A column on a view — an attribute, its position, and display overrides."""

    id: str | None = None
    view_id: str | None = None
    attribute_id: str | None = None
    position: int | None = None
    label_override: str | None = None
    width_px: int | None = None


class ViewSort(_Base):
    """A sort rule on a view: an attribute and a direction (``asc``/``desc``)."""

    id: str | None = None
    view_id: str | None = None
    attribute_id: str | None = None
    position: int | None = None
    direction: str | None = None


class View(_Base):
    """A saved table/kanban view over an object or a list — its columns, sorts,
    filter tree, and (for kanban) layout config."""

    id: str | None = None
    workspace_id: str | None = None
    object_id: str | None = None
    list_id: str | None = None
    slug: str | None = None
    name: str | None = None
    description: str | None = None
    view_type: str | None = None
    is_system: bool | None = None
    is_default: bool | None = None
    filter: dict[str, Any] | None = None
    kanban_config: dict[str, Any] | None = None
    created_by_member_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    columns: list[ViewColumn] = []
    sorts: list[ViewSort] = []
