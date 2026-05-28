"""MCP tool registry."""

from api.mcp_tools.common import register_common_tools
from api.mcp_tools.hotel import register_hotel_tools
from api.mcp_tools.planning import register_planning_tools
from api.mcp_tools.ride import register_ride_tools
from api.mcp_tools.transport import register_transport_tools


def register_all_mcp_tools(mcp_app) -> None:
    """Register all MCP tool groups."""

    register_common_tools(mcp_app)
    register_hotel_tools(mcp_app)
    register_planning_tools(mcp_app)
    register_ride_tools(mcp_app)
    register_transport_tools(mcp_app)


__all__ = [
    "register_all_mcp_tools",
]
