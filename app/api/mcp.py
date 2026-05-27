"""MCP application wiring."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

mcp = FastMCP(name="Dudu Agent Core Demo MCP")
mcp_http = mcp.http_app("/mcp")

__all__ = [
    "echo",
    "hello_world",
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


@mcp.tool(
    name="hello_world",
    description="Demo tool that returns a hello world message.",
)
async def hello_world() -> dict[str, str]:
    """Return a static message for MCP build and smoke tests."""
    return {
        "message": "Hello, world!",
    }
