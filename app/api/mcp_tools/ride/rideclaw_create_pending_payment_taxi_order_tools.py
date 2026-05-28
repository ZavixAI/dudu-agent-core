"""RideClaw create pending-payment taxi order MCP tools."""

from typing import Annotated, Union

from pydantic import Field


def register_rideclaw_create_pending_payment_taxi_order_tools(mcp_app) -> None:
    """注册 RideClaw 创建打车待支付订单 MCP 工具。"""

    @mcp_app.tool(
        name="create_pending_payment_taxi_order",
        description="根据用户选择的报价方案生成打车待支付订单数据。",
    )
    async def create_pending_payment_taxi_order(
        estimate_trace_id: Annotated[
            str,
            Field(description="价格预估接口返回的追踪 ID，用于关联本次报价。"),
        ],
        standard_car_type: Annotated[
            str,
            Field(description="用户选择的标准车型。"),
        ],
        estimated_price: Annotated[
            Union[float, int, str],
            Field(description="用户选择方案的预估价格。"),
        ],
        estimated_duration: Annotated[
            Union[int, str, float],
            Field(description="用户选择方案的预估行程时长。"),
        ],
        estimated_distance: Annotated[
            Union[int, str, float],
            Field(description="用户选择方案的预估行程距离。"),
        ],
        from_name: Annotated[
            str,
            Field(description="出发地点名称。"),
        ],
        to_name: Annotated[
            str,
            Field(description="目的地点名称。"),
        ],
    ) -> dict[str, object]:
        """根据用户选择的方案生成待支付打车订单信息。"""

        return {
            "ok": True,
            "data": {
                "estimate_trace_id": estimate_trace_id,
                "standard_car_type": standard_car_type,
                "estimated_price": estimated_price,
                "estimated_duration": estimated_duration,
                "estimated_distance": estimated_distance,
                "from_name": from_name,
                "to_name": to_name,
            },
        }


__all__ = [
    "register_rideclaw_create_pending_payment_taxi_order_tools",
]
