"""RideClaw create taxi order MCP tools."""

from __future__ import annotations

from typing import Union
from uuid import uuid4


def register_rideclaw_create_taxi_order_tools(mcp_app) -> None:
    """Register RideClaw create taxi order MCP tools."""

    @mcp_app.tool(
        name="create_taxi_order",
        description="Create a taxi order from the user's selected quote option.",
    )
    async def create_taxi_order(
        estimate_trace_id: str,
        standard_car_type: str,
        estimated_price: Union[float, int, str],
        estimated_duration: Union[int, str, float],
        estimated_distance: Union[int, str, float],
        from_name: str,
        to_name: str,
    ) -> dict[str, object]:
        """Create mocked taxi order information from the user's selected option."""

        return {
            "order_id": f"mock_taxi_order_{uuid4().hex}",
            "estimate_trace_id": estimate_trace_id,
            "standard_car_type": standard_car_type,
            "estimated_price": estimated_price,
            "estimated_duration": estimated_duration,
            "estimated_distance": estimated_distance,
            "from_name": from_name,
            "to_name": to_name,
            "status": "mock_created",
        }


__all__ = [
    "register_rideclaw_create_taxi_order_tools",
]