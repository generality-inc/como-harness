"""``como run -- <cmd>`` — run a command with the como LLM gateway injected.

Mints a short-lived gateway key (``POST /v1/llm-gateway/key``, authed by the
stored ``como_live_`` key) and execs ``<cmd>`` with the Anthropic/OpenAI SDK env
(``*_BASE_URL`` + ``*_API_KEY``) set **for that child process only**. So code the
agent writes — ``anthropic.Anthropic().messages.create(...)``,
``openai.OpenAI()...`` — routes through the gateway with **no provider key on the
machine**, and nothing leaks into the user's shell or their normal Anthropic use.

``como claude`` is sugar for ``como run -- claude`` (route Claude Code's own
inference through the gateway too).
"""

from __future__ import annotations

import os
import subprocess

import typer

from ..client import Como
from ..errors import ComoError


def _gateway_env() -> dict[str, str]:
    """Mint a fresh gateway key and return the SDK env to inject. The key is
    short-lived + budget-capped and scoped to the caller's workspace team."""
    try:
        with Como() as client:
            key = client.gateway.create_key()
    except ComoError as exc:
        typer.secho(f"Couldn't get a gateway key: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    gw = str(key.base_url).rstrip("/")
    sk = str(key.api_key)
    return {
        # Anthropic SDK (and Claude Code, which reads AUTH_TOKEN).
        "ANTHROPIC_BASE_URL": gw,
        "ANTHROPIC_API_KEY": sk,
        "ANTHROPIC_AUTH_TOKEN": sk,
        # OpenAI SDK (LiteLLM serves the OpenAI API under /v1).
        "OPENAI_BASE_URL": f"{gw}/v1",
        "OPENAI_API_KEY": sk,
    }


def _exec(cmd: list[str]) -> None:
    """Run ``cmd`` with the gateway env injected into the child only, and exit
    with the child's status."""
    if not cmd:
        typer.secho("Usage: como run -- <command> [args…]", fg="yellow", err=True)
        raise typer.Exit(code=2)
    env = {**os.environ, **_gateway_env()}
    proc = subprocess.run(cmd, env=env)
    raise typer.Exit(code=proc.returncode)


def run(ctx: typer.Context) -> None:
    """Run any command with the LLM gateway env injected (process-scoped)."""
    _exec(list(ctx.args))


def claude(ctx: typer.Context) -> None:
    """Launch Claude Code with its inference routed through the como gateway."""
    _exec(["claude", *ctx.args])
