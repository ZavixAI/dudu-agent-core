"""RideClaw estimate price MCP tools."""

from __future__ import annotations

from typing import Any

from services.ride.estimate_service import estimate_ride_price


def register_rideclaw_estimate_price_tools(mcp_app) -> None:
    """Register RideClaw estimate price MCP tools."""

    @mcp_app.tool(
        name="rideclaw_estimate_price",
        description="Estimate taxi quote by origin and destination.",
    )
    async def rideclaw_estimate_price(
        from_lng: str,
        from_lat: str,
        from_name: str,
        to_lng: str,
        to_lat: str,
        to_name: str,
        order_type: int = 1,
        booking_time_str: str | None = None,
        user_token: str | None = None,
    ) -> Any:
        """Estimate taxi price for real-time or scheduled RideClaw orders."""

        return await estimate_ride_price(
            from_lng=from_lng,
            from_lat=from_lat,
            from_name=from_name,
            to_lng=to_lng,
            to_lat=to_lat,
            to_name=to_name,
            order_type=order_type,
            booking_time_str=booking_time_str,
            user_token=user_token,
        )


__all__ = [
    "register_rideclaw_estimate_price_tools",
]