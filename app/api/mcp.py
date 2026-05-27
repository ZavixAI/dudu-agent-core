"""MCP application wiring."""

from __future__ import annotations

from api.mcp_tools import register_all_mcp_tools
from fastmcp import FastMCP

mcp = FastMCP(name="Dudu Agent Core Demo MCP")
mcp_http = mcp.http_app("/mcp")


def register_tool_groups() -> None:
    """Register all MCP tool groups."""

    register_all_mcp_tools(mcp)


register_tool_groups()

__all__ = [
    "mcp",
    "mcp_http",
    "register_tool_groups",
]
