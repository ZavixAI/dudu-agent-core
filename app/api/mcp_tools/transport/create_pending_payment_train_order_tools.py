"""RideClaw create pending-payment train order MCP tools."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from services.transport.order_service import create_pending_payment_train_order


def register_create_pending_payment_train_order_tools(mcp_app) -> None:
    """注册 RideClaw 创建火车待支付订单 MCP 工具。"""

    @mcp_app.tool(
        name="create_pending_payment_train_order",
        description=(
            "功能：根据聚合交通搜索快照定位字段生成火车待支付订单数据。"
            "使用场景：适用于已确认具体车次、席别和出发日期后的支付前环节，"
            "用于创建待支付火车订单。"
        ),
    )
    async def create_pending_payment_train_order_tool(
        search_id: Annotated[
            str,
            Field(description="聚合交通搜索返回的搜索 ID。"),
        ],
        train_no: Annotated[
            str,
            Field(description='车次编号，例如 "24000G102500"。'),
        ],
        seat_type_name: Annotated[
            str,
            Field(description='席别名称，例如 "二等座"、"一等座"、"商务座"。'),
        ],
        date: Annotated[
            str,
            Field(description='出发日期，格式为 "YYYY-MM-DD"。'),
        ],
    ) -> Any:
        """从 RideClaw 火车快照中取回待支付订单数据。"""

        return await create_pending_payment_train_order(
            search_id=search_id,
            train_no=train_no,
            seat_type_name=seat_type_name,
            date=date,
        )


__all__ = [
    "register_create_pending_payment_train_order_tools",
]
