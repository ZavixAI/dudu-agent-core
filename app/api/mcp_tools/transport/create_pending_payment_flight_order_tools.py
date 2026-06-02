"""RideClaw create pending-payment flight order MCP tools."""

from __future__ import annotations

from typing import Annotated, Any, Union

from pydantic import Field

from services.transport.order_service import create_pending_payment_flight_order


def register_create_pending_payment_flight_order_tools(mcp_app) -> None:
    """注册 RideClaw 创建机票待支付订单 MCP 工具。"""

    @mcp_app.tool(
        name="create_pending_payment_flight_order",
        description="根据航班搜索快照定位字段生成机票待支付订单数据。",
    )
    async def create_pending_payment_flight_order_tool(
        search_token: Annotated[
            str,
            Field(description="航班搜索返回的搜索令牌。"),
        ],
        departure_date: Annotated[
            str,
            Field(description='出发日期，格式为 "YYYY-MM-DD"。'),
        ],
        flight_id: Annotated[
            Union[str, int, float],
            Field(description="航班 ID。"),
        ],
        cabin_fare_id: Annotated[
            Union[str, int, float],
            Field(description="舱位票价 ID。"),
        ],
    ) -> Any:
        """从 RideClaw 航班快照中取回待支付订单数据。"""

        return await create_pending_payment_flight_order(
            search_token=search_token,
            departure_date=departure_date,
            flight_id=flight_id,
            cabin_fare_id=cabin_fare_id,
        )


__all__ = [
    "register_create_pending_payment_flight_order_tools",
]
