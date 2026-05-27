"""MCP application wiring."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

mcp = FastMCP(name="Dudu Agent Core Demo MCP")
mcp_http = mcp.http_app("/mcp")

__all__ = [
    "echo",
    "mcp",
    "mcp_http",
]


@mcp.tool(
    name="echo",
    description="Demo tool that returns the provided message.",
)
async def echo(message: str) -> dict[str, Any]:
    """Return the input message for MCP integration smoke tests."""
    return {
        "message": message,
    }
