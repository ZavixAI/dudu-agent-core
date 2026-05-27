"""Request-scoped context helpers."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_request_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "request_context",
    default=None,
)


def clear_request_context() -> None:
    """Clear request-local context."""

    _request_context.set({})


def set_request_context(request_id: str, request_logger: Any | None = None) -> None:
    """Store request metadata for logging and tracing."""

    _request_context.set(
        {
            "request_id": request_id,
            "logger": request_logger,
        }
    )


def get_request_context() -> dict[str, Any]:
    """Return a copy of the current request context."""

    return dict(_request_context.get() or {})


def get_request_id() -> str:
    """Return the current request id or a fallback value."""

    return str(get_request_context().get("request_id") or "background")
