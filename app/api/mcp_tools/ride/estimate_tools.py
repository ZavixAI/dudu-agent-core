"""Ride estimate MCP tools."""

from __future__ import annotations

from typing import Any


def register_estimate_tools(mcp_app) -> None:
    """Register ride estimate tools."""

    @mcp_app.tool(
        name="ride_estimate_price",
        description="Estimate ride price for a planned trip.",
    )
    async def ride_estimate_price(
        origin: str,
        destination: str,
        city: str,
    ) -> dict[str, Any]:
        """Return a placeholder ride estimate response."""
        return {
            "origin": origin,
            "destination": destination,
            "city": city,
            "status": "todo",
            "message": "Ride estimate tool scaffold is ready. Wire service logic next.",
        }
