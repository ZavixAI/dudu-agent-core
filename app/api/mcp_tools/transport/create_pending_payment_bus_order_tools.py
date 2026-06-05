"""RideClaw create pending-payment bus order MCP tools."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from services.transport.order_service import create_pending_payment_bus_order


def register_create_pending_payment_bus_order_tools(mcp_app) -> None:
    """注册 RideClaw 创建巴士待支付订单 MCP 工具。"""

    @mcp_app.tool(
        name="create_pending_payment_bus_order",
        description=(
            "功能：根据聚合交通搜索快照定位字段生成巴士待支付订单数据。"
            "使用场景：适用于已确认具体巴士班次后的支付前环节，"
            "用于创建待支付巴士订单。"
        ),
    )
    async def create_pending_payment_bus_order_tool(
        search_id: Annotated[
            str,
            Field(description="聚合交通搜索返回的搜索 ID。"),
        ],
        gid: Annotated[
            str,
            Field(description="巴士班次 GID。"),
        ],
    ) -> Any:
        """从 RideClaw 巴士快照中取回待支付订单数据。"""

        return await create_pending_payment_bus_order(
            search_id=search_id,
            gid=gid,
        )


__all__ = [
    "register_create_pending_payment_bus_order_tools",
]
