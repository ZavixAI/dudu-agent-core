"""Hotel MCP tools."""

from api.mcp_tools.hotel.rideclaw_create_pending_payment_hotel_order_tools import (
    register_rideclaw_create_pending_payment_hotel_order_tools,
)
from api.mcp_tools.hotel.rideclaw_filter_hotel_rooms_tools import (
    register_rideclaw_filter_hotel_rooms_tools,
)
from api.mcp_tools.hotel.rideclaw_search_hotels_tools import (
    register_rideclaw_search_hotels_tools,
)


def register_hotel_tools(mcp_app) -> None:
    """Register all hotel MCP tools."""

    register_rideclaw_create_pending_payment_hotel_order_tools(mcp_app)
    register_rideclaw_filter_hotel_rooms_tools(mcp_app)
    register_rideclaw_search_hotels_tools(mcp_app)


__all__ = [
    "register_hotel_tools",
]
