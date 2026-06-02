"""RideClaw hotel search MCP tools."""

from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from services.hotel.search_service import search_hotels as search_hotels_service


def register_search_hotels_tools(mcp_app) -> None:
    """注册 RideClaw 酒店搜索 MCP 工具。"""

    @mcp_app.tool(
        name="hotel_search",
        description="根据目的地和入住日期搜索酒店，支持价格、星级、评分、距离、品牌和设施筛选。",
    )
    async def search_hotels(
        destination: Annotated[
            str,
            Field(description='目的地地址文本，例如 "北京市朝阳区三里屯"。'),
        ],
        check_in: Annotated[
            str,
            Field(description='入住日期，格式为 "YYYY-MM-DD"。'),
        ],
        check_out: Annotated[
            str,
            Field(description='退房日期，格式为 "YYYY-MM-DD"。'),
        ],
        room_count: Annotated[
            int,
            Field(description="房间数量。"),
        ] = 1,
        adult_count: Annotated[
            int,
            Field(description="成人数量。"),
        ] = 2,
        sort_by: Annotated[
            str | None,
            Field(description="排序方式，可选 best、price、rating、star、distance。"),
        ] = None,
        min_price: Annotated[
            Union[float, str, None],
            Field(description="最低价格，单位元。"),
        ] = None,
        max_price: Annotated[
            Union[float, str, None],
            Field(description="最高价格，单位元。"),
        ] = None,
        star_levels: Annotated[
            str | list[int] | None,
            Field(description='星级筛选，支持逗号分隔字符串或数组，例如 "4,5"。'),
        ] = None,
        hotel_types: Annotated[
            str | list[str] | None,
            Field(description='供应商筛选，支持逗号分隔字符串或数组，例如 "qiantao"。'),
        ] = None,
        hotel_brand: Annotated[
            str | None,
            Field(description='酒店品牌筛选，例如 "万豪酒店"。'),
        ] = None,
        min_review_score: Annotated[
            Union[float, str, None],
            Field(description="最低评分，例如 4.3。"),
        ] = None,
        max_distance_km: Annotated[
            Union[float, str, None],
            Field(description="最大距离，单位公里，例如 10。"),
        ] = None,
        tags: Annotated[
            str | list[str] | None,
            Field(
                description=(
                    "设施/服务筛选标签，支持逗号分隔字符串或数组；可选 has_wifi、"
                    "has_parking、has_swimming_pool、has_gymnasium、has_dining_room、"
                    "has_board_room、has_spa、has_airport_shuttle、has_child_facility、"
                    "has_business_center、has_laundry、has_24h_front_desk、"
                    "has_ev_charging、has_bar。"
                )
            ),
        ] = None,
        page: Annotated[
            int,
            Field(description="页码。"),
        ] = 1,
        page_size: Annotated[
            int,
            Field(description="每页数量。"),
        ] = 10,
        is_cn: Annotated[
            bool,
            Field(description="是否按国内地址进行地理编码。"),
        ] = True,
        user_token: Annotated[
            str | None,
            Field(description="用户登录令牌；没有登录态时可为空。"),
        ] = None,
    ) -> dict[str, object]:
        """搜索酒店并返回结构化聚合结果。"""

        return await search_hotels_service(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            room_count=room_count,
            adult_count=adult_count,
            sort_by=sort_by,
            min_price=min_price,
            max_price=max_price,
            star_levels=star_levels,
            hotel_types=hotel_types,
            hotel_brand=hotel_brand,
            min_review_score=min_review_score,
            max_distance_km=max_distance_km,
            tags=tags,
            page=page,
            page_size=page_size,
            is_cn=is_cn,
            user_token=user_token,
        )


__all__ = [
    "register_search_hotels_tools",
]
