"""RideClaw transport option search MCP tools."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from services.transport.search_service import search_aggregated_transport


def register_search_transport_options_tools(mcp_app) -> None:
    """注册 RideClaw 交通方案搜索 MCP 工具。"""

    @mcp_app.tool(
        name="search_transport_options",
        description="搜索城市间交通方案，返回可选的航班、火车和巴士结果。",
    )
    async def search_transport_options(
        date: Annotated[
            str,
            Field(description='出发日期，格式为 "YYYY-MM-DD"。'),
        ],
        from_name: Annotated[
            str,
            Field(description='出发地名称，例如 "深圳北"。'),
        ],
        to_name: Annotated[
            str,
            Field(description='目的地名称，例如 "广州"。'),
        ],
        is_cn: Annotated[
            bool,
            Field(description="是否为中国境内地址。"),
        ],
        earliest_departure_time: Annotated[
            str | None,
            Field(description='最早出发时间，格式为 "YYYY-MM-DD HH:MM"。'),
        ] = None,
        latest_arrival_time: Annotated[
            str | None,
            Field(description='最晚到达时间，格式为 "YYYY-MM-DD HH:MM"；会在请求后端前往前推 1 小时。'),
        ] = None,
        user_token: Annotated[
            str | None,
            Field(description="用户登录令牌；没有登录态时可为空。"),
        ] = None,
        modes: Annotated[
            Literal["flight", "train", "bus", "all"],
            Field(description="交通方式，可选 flight、train、bus、all；默认 all。"),
        ] = "all",
    ) -> dict[str, object]:
        """搜索交通方案并返回结构化结果。"""

        return await search_aggregated_transport(
            date=date,
            from_name=from_name,
            to_name=to_name,
            is_cn=is_cn,
            earliest_departure_time=earliest_departure_time,
            latest_arrival_time=latest_arrival_time,
            user_token=user_token,
            modes=None if modes == "all" else [modes],
        )


__all__ = [
    "register_search_transport_options_tools",
]
