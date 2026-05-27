"""Ride order MCP tools."""

from __future__ import annotations

from typing import Any


def register_order_tools(mcp_app) -> None:
    """Register ride order tools."""

    @mcp_app.tool(
        name="ride_create_order",
        description="Create a ride order after user confirmation.",
    )
    async def ride_create_order(
        origin: str,
        destination: str,
        city: str,
        passenger_name: str | None = None,
    ) -> dict[str, Any]:
        """Return a placeholder ride order response."""
        return {
            "origin": origin,
            "destination": destination,
            "city": city,
            "passenger_name": passenger_name,
            "status": "todo",
            "message": "Ride order tool scaffold is ready. Wire service logic next.",
        }
