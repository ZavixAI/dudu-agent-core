"""Transport MCP tools."""

from api.mcp_tools.transport.rideclaw_create_pending_payment_bus_order_tools import (
    register_rideclaw_create_pending_payment_bus_order_tools,
)
from api.mcp_tools.transport.rideclaw_create_pending_payment_flight_order_tools import (
    register_rideclaw_create_pending_payment_flight_order_tools,
)
from api.mcp_tools.transport.rideclaw_create_pending_payment_train_order_tools import (
    register_rideclaw_create_pending_payment_train_order_tools,
)
from api.mcp_tools.transport.rideclaw_search_bus_options_tools import (
    register_rideclaw_search_bus_options_tools,
)
from api.mcp_tools.transport.rideclaw_search_flight_options_tools import (
    register_rideclaw_search_flight_options_tools,
)
from api.mcp_tools.transport.rideclaw_search_transport_options_tools import (
    register_rideclaw_search_transport_options_tools,
)
from api.mcp_tools.transport.rideclaw_search_train_options_tools import (
    register_rideclaw_search_train_options_tools,
)


def register_transport_tools(mcp_app) -> None:
    """Register all transport MCP tools."""

    register_rideclaw_create_pending_payment_bus_order_tools(mcp_app)
    register_rideclaw_create_pending_payment_flight_order_tools(mcp_app)
    register_rideclaw_create_pending_payment_train_order_tools(mcp_app)
    register_rideclaw_search_bus_options_tools(mcp_app)
    register_rideclaw_search_flight_options_tools(mcp_app)
    register_rideclaw_search_transport_options_tools(mcp_app)
    register_rideclaw_search_train_options_tools(mcp_app)


__all__ = [
    "register_transport_tools",
]
