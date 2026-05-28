"""Ride-related MCP tools."""

from api.mcp_tools.ride.rideclaw_create_pending_payment_taxi_order_tools import (
    register_rideclaw_create_pending_payment_taxi_order_tools,
)
from api.mcp_tools.ride.rideclaw_estimate_price_tools import (
    register_rideclaw_estimate_price_tools,
)


def register_ride_tools(mcp_app) -> None:
    """Register all ride-related MCP tools."""

    register_rideclaw_estimate_price_tools(mcp_app)
    register_rideclaw_create_pending_payment_taxi_order_tools(mcp_app)


__all__ = [
    "register_ride_tools",
]
