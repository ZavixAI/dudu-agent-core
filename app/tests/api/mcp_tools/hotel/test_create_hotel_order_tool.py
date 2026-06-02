"""End-to-end tests for the RideClaw pending-payment hotel order MCP tool."""

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
from services.hotel import order_service

MODULE_NAME = "api.mcp_tools.hotel.create_pending_payment_hotel_order_tools"


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
        self.posts: list[dict[str, Any]] = []

    async def post(self, url: str, **kwargs) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse(self.payload)


def _get_create_pending_payment_hotel_order_tool():
    module = importlib.import_module(MODULE_NAME)
    mcp_app = FakeMCPApp()
    module.register_create_pending_payment_hotel_order_tools(mcp_app)
    return mcp_app.tools["create_pending_payment_hotel_order"]["func"]


def test_create_pending_payment_hotel_order_tool_returns_snapshot_dict(monkeypatch) -> None:
    expected_data = {
        "hotel_type": "meituan",
        "hotel_id": "hotel-1",
        "product_id": "product-1",
        "total_price": 18800,
    }
    fake_client = FakeHTTPClient({"code": 0, "message": "success", "data": expected_data})

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(order_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_create_pending_payment_hotel_order_tool()(
            search_id="search-1",
            hotel_type="meituan",
            hotel_id=123,
            product_id="product-1",
        )
    )

    assert result == {
        "ok": True,
        "data": expected_data,
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTIONS["hotel"]["pending_payment_order"]
        ),
    }
    assert fake_client.posts == [
        {
            "url": "/apitest/v1/hotel/snapshot/lookup",
            "json": {
                "search_id": "search-1",
                "hotel_type": "meituan",
                "hotel_id": "123",
                "product_id": "product-1",
            },
        }
    ]


def test_create_pending_payment_hotel_order_tool_parses_snapshot_json_string(monkeypatch) -> None:
    fake_client = FakeHTTPClient(
        {
            "code": 0,
            "message": "success",
            "data": '{"hotel_id": "hotel-1", "product_id": "product-1"}',
        }
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(order_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_create_pending_payment_hotel_order_tool()(
            search_id="search-1",
            hotel_type="meituan",
            hotel_id="hotel-1",
            product_id="product-1",
        )
    )

    assert result == {
        "ok": True,
        "data": {"hotel_id": "hotel-1", "product_id": "product-1"},
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTIONS["hotel"]["pending_payment_order"]
        ),
    }


def test_create_hotel_order_tool_raises_for_failed_snapshot(monkeypatch) -> None:
    fake_client = FakeHTTPClient({"code": 1001, "message": "snapshot missing", "data": None})

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(order_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_create_pending_payment_hotel_order_tool()(
                search_id="search-1",
                hotel_type="meituan",
                hotel_id="hotel-1",
                product_id="product-1",
            )
        )

    assert exc_info.value.error_code == "RIDECLOW_HOTEL_ORDER_SNAPSHOT_ERROR"


@pytest.mark.parametrize(
    ("search_id", "hotel_type", "hotel_id", "product_id", "error_code"),
    [
        ("", "meituan", "hotel-1", "product-1", "RIDECLOW_HOTEL_ORDER_SEARCH_ID_REQUIRED"),
        ("search-1", "", "hotel-1", "product-1", "RIDECLOW_HOTEL_ORDER_TYPE_REQUIRED"),
        ("search-1", "meituan", "", "product-1", "RIDECLOW_HOTEL_ORDER_ID_REQUIRED"),
        ("search-1", "meituan", "hotel-1", "", "RIDECLOW_HOTEL_ORDER_PRODUCT_ID_REQUIRED"),
    ],
)
def test_create_pending_payment_hotel_order_tool_validates_required_fields(
    search_id,
    hotel_type,
    hotel_id,
    product_id,
    error_code,
) -> None:
    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_create_pending_payment_hotel_order_tool()(
                search_id=search_id,
                hotel_type=hotel_type,
                hotel_id=hotel_id,
                product_id=product_id,
            )
        )

    assert exc_info.value.error_code == error_code
