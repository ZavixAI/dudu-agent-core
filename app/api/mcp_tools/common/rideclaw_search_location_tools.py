"""RideClaw location search MCP tools."""

from __future__ import annotations

from typing import Any

from services.common.location_service import search_location


def register_rideclaw_search_location_tools(mcp_app) -> None:
    """Register RideClaw location search MCP tools."""

    @mcp_app.tool(
        name="rideclaw_search_location",
        description="Search candidate places by query, region, and radius.",
    )
    async def rideclaw_search_location(
        query: str,
        region: str,
        radius: int = 200,
    ) -> dict[str, Any]:
        """Search place candidates for ride, hotel, or itinerary flows."""

        return await search_location(
            query=query,
            region=region,
            radius=radius,
        )


__all__ = [
    "register_rideclaw_search_location_tools",
]
