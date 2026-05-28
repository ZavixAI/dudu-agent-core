"""MCP tool response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class MCPToolResponse(BaseModel):
    """Unified successful response envelope for MCP tools."""

    ok: bool = Field(default=True)
    data: Any = None


__all__ = [
    "MCPToolResponse",
]
