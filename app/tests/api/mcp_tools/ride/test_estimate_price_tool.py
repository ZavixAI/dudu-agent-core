"""End-to-end tests for the RideClaw estimate MCP tool."""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

APP_DIR = Path(__file__).resolve().parents[4]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import constants
from core.http.exceptions import AppHTTPException
from services.ride import estimate_service

MODULE_NAME = "api.mcp_tools.ride.estimate_price_tools"


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


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeHTTPClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    async def post(self, *args, **kwargs) -> FakeResponse:
        return FakeResponse(self.payload)


def _get_estimate_tool():
    module = importlib.import_module(MODULE_NAME)
    mcp_app = FakeMCPApp()
    module.register_estimate_price_tools(mcp_app)
    return mcp_app.tools["ride_estimate_price"]["func"]


def test_estimate_tool_returns_unified_response(monkeypatch) -> None:
    expected_data = {"estimated_price": 42, "currency": "CNY"}

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return FakeHTTPClient({"code": 0, "message": "success", "data": expected_data})

    monkeypatch.setattr(estimate_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_estimate_tool()(
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

    assert result == {
        "ok": True,
        "data": expected_data,
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTIONS["ride"]["estimate_price"]
        ),
    }


def test_estimate_tool_filters_selected_car_type(monkeypatch) -> None:
    expected_data = {
        "economy": {
            "available": True,
            "estimated_price": 18.21,
        },
        "premium": {
            "available": True,
            "estimated_price": 27.97,
        },
        "business": {
            "available": True,
            "estimated_price": 42.72,
        },
        "luxury": {
            "available": True,
            "estimated_price": 98,
        },
        "estimate_trace_id": "AGG_trace_1",
    }

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return FakeHTTPClient({"code": 0, "message": "success", "data": expected_data})

    monkeypatch.setattr(estimate_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_estimate_tool()(
            from_lng="116.397128",
            from_lat="39.916527",
            from_name="天安门",
            to_lng="116.407396",
            to_lat="39.904200",
            to_name="北京站",
            standard_car_type="premium",
        )
    )

    assert result == {
        "ok": True,
        "data": {
            "premium": {
                "available": True,
                "estimated_price": 27.97,
            },
            "estimate_trace_id": "AGG_trace_1",
        },
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTIONS["ride"]["estimate_price"]
        ),
    }


def test_estimate_tool_returns_unsupported_route_message(monkeypatch) -> None:
    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return FakeHTTPClient(
            {
                "code": -1,
                "message": "行程超过 150 公里，暂不支持预估",
                "data": None,
            }
        )

    monkeypatch.setattr(estimate_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_estimate_tool()(
            from_lng="116.407526",
            from_lat="39.904030",
            from_name="北京",
            to_lng="114.057868",
            to_lat="22.543099",
            to_name="深圳",
        )
    )

    assert result == {
        "ok": True,
        "data": {
            "reason": "行程超过 150 公里，暂不支持预估",
            "available": False,
        },
    }


@pytest.mark.parametrize(
    ("payload", "error_code"),
    [
        ({"code": 1001, "message": "invalid route", "data": None}, "RIDECLOW_QUOTE_ERROR"),
        ({"code": 0, "message": "success", "data": None}, "RIDECLOW_QUOTE_EMPTY"),
    ],
)
def test_estimate_tool_raises_for_failed_quote(monkeypatch, payload, error_code) -> None:
    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return FakeHTTPClient(payload)

    monkeypatch.setattr(estimate_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_estimate_tool()(
                from_lng="116.397128",
                from_lat="39.916527",
                from_name="天安门",
                to_lng="116.407396",
                to_lat="39.904200",
                to_name="北京站",
            )
        )

    assert exc_info.value.error_code == error_code
