"""RideClaw create pending-payment hotel order MCP tools."""

from __future__ import annotations

from typing import Annotated, Any, Union

from pydantic import Field

from services.hotel.order_service import create_pending_payment_hotel_order


def register_create_pending_payment_hotel_order_tools(mcp_app) -> None:
    """注册 RideClaw 创建酒店待支付订单 MCP 工具。"""

    @mcp_app.tool(
        name="create_pending_payment_hotel_order",
        description="根据酒店搜索快照定位字段生成用户酒店待支付订单数据。",
    )
    async def create_pending_payment_hotel_order_tool(
        search_id: Annotated[
            str,
            Field(description="酒店搜索返回的搜索 ID。"),
        ],
        hotel_type: Annotated[
            str,
            Field(description="酒店供应商类型。"),
        ],
        hotel_id: Annotated[
            Union[str, int],
            Field(description="酒店 ID。"),
        ],
        product_id: Annotated[
            str,
            Field(description="房型产品 ID。"),
        ],
    ) -> Any:
        """从 RideClaw 酒店快照中取回待支付订单数据。"""

        return await create_pending_payment_hotel_order(
            search_id=search_id,
            hotel_type=hotel_type,
            hotel_id=hotel_id,
            product_id=product_id,
        )


__all__ = [
    "register_create_pending_payment_hotel_order_tools",
]
