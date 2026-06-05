"""RideClaw train option search MCP tools."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from services.transport.search_service import search_aggregated_transport


def register_search_train_options_tools(mcp_app) -> None:
    """注册 RideClaw 火车方案搜索 MCP 工具。"""

    @mcp_app.tool(
        name="search_train_options",
        description=(
            "功能：搜索城市间火车方案，返回可选车次、席别、余票和价格信息。"
            "使用场景：适用于火车、高铁、动车或铁路出行方案查询，"
            "并按出发到达站点、日期、时间范围筛选车次。"
        ),
    )
    async def search_train_options(
        date: Annotated[str, Field(description='出发日期，格式为 "YYYY-MM-DD"。')],
        from_name: Annotated[str, Field(description='出发地名称，例如 "深圳北"。')],
        to_name: Annotated[str, Field(description='目的地名称，例如 "广州南"。')],
        is_cn: Annotated[bool, Field(description="是否为中国境内地址。")],
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
        page: Annotated[
            int,
            Field(description="页码，从 1 开始；默认 1。"),
        ] = 1,
        page_size: Annotated[
            int,
            Field(description="每页数量，默认 10，最大 20。"),
        ] = 10,
    ) -> dict[str, object]:
        """搜索火车方案。"""

        return await search_aggregated_transport(
            date=date,
            from_name=from_name,
            to_name=to_name,
            is_cn=is_cn,
            earliest_departure_time=earliest_departure_time,
            latest_arrival_time=latest_arrival_time,
            user_token=user_token,
            modes=["train"],
            page=page,
            page_size=page_size,
        )


__all__ = [
    "register_search_train_options_tools",
]
