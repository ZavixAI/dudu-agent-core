"""RideClaw location search MCP tools."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field
from services.common.location_service import search_location


def register_rideclaw_search_location_tools(mcp_app) -> None:
    """注册 RideClaw 位置搜索 MCP 工具。"""

    @mcp_app.tool(
        name="rideclaw_search_location",
        description="根据关键词、地区和半径搜索候选地点。",
    )
    async def rideclaw_search_location(
        query: Annotated[
            str,
            Field(description="要搜索的地点名称、地址或关键词。"),
        ],
        region: Annotated[
            str,
            Field(description="限定搜索范围的城市、国家或地区。"),
        ],
        radius: Annotated[
            int,
            Field(description="搜索半径，单位为米。"),
        ] = 200,
    ) -> dict[str, Any]:
        """为打车、酒店或行程场景搜索候选地点。"""

        return await search_location(
            query=query,
            region=region,
            radius=radius,
        )


__all__ = [
    "register_rideclaw_search_location_tools",
]
