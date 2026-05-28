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

from core.http.exceptions import AppHTTPException
from services.ride import estimate_service

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
    module.register_rideclaw_estimate_price_tools(mcp_app)
    return mcp_app.tools["estimate_price"]["func"]


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

    assert result == {"ok": True, "data": expected_data}


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
