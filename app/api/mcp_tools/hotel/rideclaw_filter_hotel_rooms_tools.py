"""RideClaw hotel room filter MCP tools."""

from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from services.hotel.room_service import filter_hotel_rooms


def register_rideclaw_filter_hotel_rooms_tools(mcp_app) -> None:
    """注册 RideClaw 酒店房型筛选 MCP 工具。"""

    @mcp_app.tool(
        name="filter_hotel_rooms",
        description="根据酒店供应商、酒店 ID 和入住日期查询可用房型及价格。",
    )
    async def rideclaw_filter_hotel_rooms(
        hotel_type: Annotated[
            str,
            Field(description='供应商类型，从酒店搜索结果的 supplier 字段获取，例如 "meituan"。'),
        ],
        hotel_id: Annotated[
            str,
            Field(description="酒店 ID，从酒店搜索结果的 hotel_id 字段获取。"),
        ],
        check_in: Annotated[
            str,
            Field(description='入住日期，格式为 "YYYY-MM-DD"。'),
        ],
        check_out: Annotated[
            str,
            Field(description='退房日期，格式为 "YYYY-MM-DD"。'),
        ],
        search_id: Annotated[
            str | None,
            Field(description="酒店搜索返回的搜索 ID；传入后可稳定生成下单快照。"),
        ] = None,
        room_count: Annotated[
            int,
            Field(description="房间数量。"),
        ] = 1,
        adult_count: Annotated[
            int,
            Field(description="成人数量。"),
        ] = 2,
        child_count: Annotated[
            int,
            Field(description="儿童数量。"),
        ] = 0,
        child_ages: Annotated[
            str | list[int] | None,
            Field(description='儿童年龄列表，支持逗号分隔字符串或数组，例如 "3,7"。'),
        ] = None,
        min_price: Annotated[
            Union[str, int, float, None],
            Field(description="最低价格，单位分，例如 10000 表示 100 元。"),
        ] = None,
        max_price: Annotated[
            Union[str, int, float, None],
            Field(description="最高价格，单位分，例如 20000 表示 200 元。"),
        ] = None,
        product_type: Annotated[
            int,
            Field(description="产品类型，1=全日房，2=钟点房，3=全部。"),
        ] = 3,
        user_token: Annotated[
            str | None,
            Field(description="用户登录令牌；没有登录态时可为空。"),
        ] = None,
    ) -> dict[str, object]:
        """查询指定酒店的可用房型及价格。"""

        return await filter_hotel_rooms(
            hotel_type=hotel_type,
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            search_id=search_id,
            room_count=room_count,
            adult_count=adult_count,
            child_count=child_count,
            child_ages=child_ages,
            min_price=min_price,
            max_price=max_price,
            product_type=product_type,
            user_token=user_token,
        )


__all__ = [
    "register_rideclaw_filter_hotel_rooms_tools",
]
