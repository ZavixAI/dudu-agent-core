"""MCP application wiring."""

from __future__ import annotations

from api.mcp_tools.registry import register_all_mcp_tools
from fastmcp import FastMCP


def create_mcp_app() -> FastMCP:
    """Create and configure the MCP application."""

    mcp_app = FastMCP(name="Dudu Agent Core Demo MCP")
    register_all_mcp_tools(mcp_app)
    return mcp_app


mcp = create_mcp_app()
mcp_http = mcp.http_app("/mcp")

__all__ = [
    "create_mcp_app",
    "mcp",
    "mcp_http",
]
