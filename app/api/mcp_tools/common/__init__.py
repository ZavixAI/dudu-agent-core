"""Common MCP tools."""

from api.mcp_tools.common.search_location_tools import (
    register_search_location_tools,
)


def register_common_tools(mcp_app) -> None:
    """Register all common MCP tools."""

    register_search_location_tools(mcp_app)


__all__ = [
    "register_common_tools",
]
