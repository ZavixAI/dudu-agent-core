"""End-to-end tests for the RideClaw location MCP tool wrapper."""

import asyncio
import importlib
import sys
import types
from unittest.mock import AsyncMock

import pytest

MODULE_NAME = "api.mcp_tools.common.rideclaw_search_location_tools"


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
    mocked_search_location = AsyncMock()
    fake_location_service = types.ModuleType("services.common.location_service")
    fake_location_service.search_location = mocked_search_location
    original_location_service = sys.modules.get("services.common.location_service")
    original_tool_module = sys.modules.pop(MODULE_NAME, None)
    sys.modules["services.common.location_service"] = fake_location_service

    try:
        module = importlib.import_module(MODULE_NAME)
        yield module, mocked_search_location
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if original_tool_module is not None:
            sys.modules[MODULE_NAME] = original_tool_module
        if original_location_service is None:
            sys.modules.pop("services.common.location_service", None)
        else:
            sys.modules["services.common.location_service"] = original_location_service


def test_registers_and_calls_search_location_service(tool_module) -> None:
    module, mocked_search_location = tool_module
    mcp_app = FakeMCPApp()
    expected_result = {
        "formatted_text": (
            "找到 1 个地点:\n"
            "------------------------------------------------------------\n"
            "1. 天安门\n"
            "   地址: 北京市东城区长安街\n"
            "   坐标: 116.39759,39.908776"
        )
    }
    mocked_search_location.return_value = expected_result

    module.register_rideclaw_search_location_tools(mcp_app)
    tool = mcp_app.tools["rideclaw_search_location"]
    result = asyncio.run(tool["func"](query="天安门", region="北京", radius=200))

    assert tool["description"] == "Search candidate places by query, region, and radius."
    assert result == expected_result
    mocked_search_location.assert_awaited_once_with(
        query="天安门",
        region="北京",
        radius=200,
    )


def test_uses_default_radius(tool_module) -> None:
    module, mocked_search_location = tool_module
    mcp_app = FakeMCPApp()
    expected_result = {"formatted_text": "找到 1 个地点"}
    mocked_search_location.return_value = expected_result

    module.register_rideclaw_search_location_tools(mcp_app)
    result = asyncio.run(
        mcp_app.tools["rideclaw_search_location"]["func"](
            query="天安门",
            region="北京",
        )
    )

    assert result == expected_result
    mocked_search_location.assert_awaited_once_with(
        query="天安门",
        region="北京",
        radius=200,
    )
