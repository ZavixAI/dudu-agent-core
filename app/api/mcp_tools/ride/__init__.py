"""Ride-related MCP tools."""

from api.mcp_tools.ride.estimate_tools import register_estimate_tools
from api.mcp_tools.ride.order_tools import register_order_tools


def register_ride_tools(mcp_app) -> None:
    """Register all ride-related MCP tools."""

    register_estimate_tools(mcp_app)
    register_order_tools(mcp_app)


__all__ = [
    "register_ride_tools",
]
