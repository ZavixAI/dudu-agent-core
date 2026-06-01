"""End-to-end tests for the RideClaw pending-payment taxi order MCP tool."""

import asyncio
import importlib
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[4]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import constants

MODULE_NAME = "api.mcp_tools.ride.create_pending_payment_taxi_order_tools"


class FakeMCPApp:
    """Minimal MCP app test double that captures registered tools."""

    def __init__(self) -> None:
        self.tools = {}

    def tool(self, *, name: str, description: str):
        def decorator(func):
            self.tools[name] = {
                "description": description,
                "func": func,
            }
            return func

        return decorator


def _get_create_pending_payment_taxi_order_tool():
    module = importlib.import_module(MODULE_NAME)
    mcp_app = FakeMCPApp()
    module.register_create_pending_payment_taxi_order_tools(mcp_app)
    return mcp_app.tools["create_pending_payment_taxi_order"]["func"]


def test_create_pending_payment_taxi_order_tool_returns_unified_response() -> None:
    result = asyncio.run(
        _get_create_pending_payment_taxi_order_tool()(
            estimate_trace_id="trace-1",
            standard_car_type="comfort",
            estimated_price=42.5,
            estimated_duration=1800,
            estimated_distance=12000,
            from_name="天安门",
            to_name="北京站",
        )
    )

    assert result == {
        "ok": True,
        "data": {
            "estimate_trace_id": "trace-1",
            "standard_car_type": "comfort",
            "estimated_price": 42.5,
            "estimated_duration": 1800,
            "estimated_distance": 12000,
            "from_name": "天安门",
            "to_name": "北京站",
        },
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_TAXI_ORDER
        ),
    }
