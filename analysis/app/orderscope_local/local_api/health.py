"""Localhost-only health surface for the Local Corporate Intelligence service."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI

from orderscope_local.contracts import ContractViolation


LOCALHOST_BIND_HOST = "127.0.0.1"
LOCAL_HEALTH_SCHEMA_VERSION = "local-health-v0.1"


@dataclass(frozen=True, slots=True)
class LocalServerBinding:
    """Validated bind configuration for the local HTTP process.

    v0.1 deliberately accepts only the literal IPv4 loopback address. Hostname
    aliases, wildcard binds, IPv6, LAN addresses, and externally routable
    addresses are rejected rather than resolved or guessed.
    """

    host: str = LOCALHOST_BIND_HOST

    def __post_init__(self) -> None:
        if not isinstance(self.host, str) or self.host != LOCALHOST_BIND_HOST:
            raise ContractViolation("local HTTP service must bind exactly to 127.0.0.1")


def create_health_app(*, binding: LocalServerBinding | None = None) -> FastAPI:
    """Create the read-only health application after validating its bind policy."""

    effective = binding or LocalServerBinding()
    if not isinstance(effective, LocalServerBinding):
        raise ContractViolation("binding must be LocalServerBinding")

    app = FastAPI(title="OrderScope Local", version="0.1.0")
    app.state.local_binding = effective

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "schema_version": LOCAL_HEALTH_SCHEMA_VERSION,
            "bind_host": effective.host,
        }

    return app
