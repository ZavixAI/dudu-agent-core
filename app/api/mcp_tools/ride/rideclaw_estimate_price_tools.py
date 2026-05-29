"""RideClaw estimate price MCP tools."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field
from services.ride.estimate_service import estimate_ride_price


def register_rideclaw_estimate_price_tools(mcp_app) -> None:
    """注册 RideClaw 打车价格预估 MCP 工具。"""

    @mcp_app.tool(
        name="ride_estimate_price",
        description="根据出发地和目的地预估打车报价。",
    )
    async def rideclaw_estimate_price(
        from_lng: Annotated[
            str,
            Field(description="出发地经度。"),
        ],
        from_lat: Annotated[
            str,
            Field(description="出发地纬度。"),
        ],
        from_name: Annotated[
            str,
            Field(description="出发地点名称。"),
        ],
        to_lng: Annotated[
            str,
            Field(description="目的地经度。"),
        ],
        to_lat: Annotated[
            str,
            Field(description="目的地纬度。"),
        ],
        to_name: Annotated[
            str,
            Field(description="目的地点名称。"),
        ],
        order_type: Annotated[
            int,
            Field(description="订单类型，1 表示实时叫车，2 表示预约用车。"),
        ] = 1,
        booking_time_str: Annotated[
            str | None,
            Field(
                description='乘车日期时间，格式为 "YYYY-MM-DD HH:mm"，例如 "2026-05-04 12:00"；选填，不传则为实时单，order_type=2 时必填。'
            ),
        ] = None,
        user_token: Annotated[
            str | None,
            Field(description="用户登录令牌；没有登录态时可为空。"),
        ] = None,
    ) -> Any:
        """为实时或预约 RideClaw 打车订单预估价格。"""

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