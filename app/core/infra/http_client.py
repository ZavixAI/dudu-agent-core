"""Shared async HTTP client helpers."""

import asyncio
from typing import Any

import httpx

from config.settings import AppConfig, get_app_config

_HTTP_CLIENT_LOCK = asyncio.Lock()
_HTTP_CLIENTS: dict[str, httpx.AsyncClient] = {}
DEFAULT_HTTP_TIMEOUT_SECONDS = 10.0


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _build_http_client_configs(cfg: AppConfig) -> dict[str, dict[str, Any]]:
    """Build per-service HTTP client configuration."""

    return {
        "rideclaw": {
            "base_url": _normalize_base_url(cfg.rideclaw_base_url),
            "headers": {"Content-Type": "application/json"},
        },
    }


async def init_http_clients(cfg: AppConfig | None = None) -> dict[str, httpx.AsyncClient]:
    """Initialize the shared HTTP clients registry."""

    resolved_cfg = cfg or get_app_config()
    client_configs = _build_http_client_configs(resolved_cfg)

    async with _HTTP_CLIENT_LOCK:
        for service_name, service_config in client_configs.items():
            if service_name in _HTTP_CLIENTS:
                continue

            _HTTP_CLIENTS[service_name] = httpx.AsyncClient(
                base_url=service_config["base_url"],
                timeout=httpx.Timeout(DEFAULT_HTTP_TIMEOUT_SECONDS),
                headers=dict(service_config.get("headers") or {}),
            )

    return dict(_HTTP_CLIENTS)


async def get_http_client(service_name: str) -> httpx.AsyncClient:
    """Return the shared HTTP client for a named downstream service."""

    if service_name not in _HTTP_CLIENTS:
        await init_http_clients()

    client = _HTTP_CLIENTS.get(service_name)
    if client is None:
        raise ValueError(f"Unknown HTTP client service: {service_name}")
    return client


async def close_http_clients() -> None:
    """Close all shared HTTP clients."""

    async with _HTTP_CLIENT_LOCK:
        clients = list(_HTTP_CLIENTS.values())
        _HTTP_CLIENTS.clear()

    for client in clients:
        await client.aclose()


__all__ = [
    "close_http_clients",
    "get_http_client",
    "init_http_clients",
]
