"""End-to-end tests for the RideClaw estimate MCP tool wrapper."""

import asyncio
import importlib
import sys
import types
from unittest.mock import AsyncMock

import pytest

MODULE_NAME = "api.mcp_tools.ride.rideclaw_estimate_price_tools"


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


@pytest.fixture
def tool_module():
    mocked_estimate_ride_price = AsyncMock()
    fake_estimate_service = types.ModuleType("services.ride.estimate_service")
    fake_estimate_service.estimate_ride_price = mocked_estimate_ride_price
    original_estimate_service = sys.modules.get("services.ride.estimate_service")
    original_tool_module = sys.modules.pop(MODULE_NAME, None)
    sys.modules["services.ride.estimate_service"] = fake_estimate_service

    try:
        module = importlib.import_module(MODULE_NAME)
        yield module, mocked_estimate_ride_price
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if original_tool_module is not None:
            sys.modules[MODULE_NAME] = original_tool_module
        if original_estimate_service is None:
            sys.modules.pop("services.ride.estimate_service", None)
        else:
            sys.modules["services.ride.estimate_service"] = original_estimate_service


def test_registers_and_calls_estimate_service(tool_module) -> None:
    module, mocked_estimate_ride_price = tool_module
    mcp_app = FakeMCPApp()
    expected_result = {"estimated_price": 42}
    mocked_estimate_ride_price.return_value = expected_result

    module.register_rideclaw_estimate_price_tools(mcp_app)
    tool = mcp_app.tools["rideclaw_estimate_price"]
    result = asyncio.run(
        tool["func"](
            from_lng="116.397128",
            from_lat="39.916527",
            from_name="天安门",
            to_lng="116.407396",
            to_lat="39.904200",
            to_name="北京站",
            order_type=2,
            booking_time_str="2026-05-04 12:00",
            user_token="user-token",
        )
    )

    assert tool["description"] == "Estimate taxi quote by origin and destination."
    assert result == expected_result
    mocked_estimate_ride_price.assert_awaited_once_with(
        from_lng="116.397128",
        from_lat="39.916527",
        from_name="天安门",
        to_lng="116.407396",
        to_lat="39.904200",
        to_name="北京站",
        order_type=2,
        booking_time_str="2026-05-04 12:00",
        user_token="user-token",
    )


def test_uses_realtime_order_defaults(tool_module) -> None:
    module, mocked_estimate_ride_price = tool_module
    mcp_app = FakeMCPApp()
    expected_result = {"estimated_price": 35}
    mocked_estimate_ride_price.return_value = expected_result

    module.register_rideclaw_estimate_price_tools(mcp_app)
    result = asyncio.run(
        mcp_app.tools["rideclaw_estimate_price"]["func"](
            from_lng="116.397128",
            from_lat="39.916527",
            from_name="天安门",
            to_lng="116.407396",
            to_lat="39.904200",
            to_name="北京站",
        )
    )

    assert result == expected_result
    mocked_estimate_ride_price.assert_awaited_once_with(
        from_lng="116.397128",
        from_lat="39.916527",
        from_name="天安门",
        to_lng="116.407396",
        to_lat="39.904200",
        to_name="北京站",
        order_type=1,
        booking_time_str=None,
        user_token=None,
    )
