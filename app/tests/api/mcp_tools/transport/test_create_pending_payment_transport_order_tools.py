"""End-to-end tests for RideClaw pending-payment transport order MCP tools."""

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
from services.transport import order_service


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


def _get_tool(module_name: str, register_name: str, tool_name: str):
    module = importlib.import_module(module_name)
    mcp_app = FakeMCPApp()
    getattr(module, register_name)(mcp_app)
    return mcp_app.tools[tool_name]["func"]


def test_create_pending_payment_flight_order_tool_returns_snapshot(monkeypatch) -> None:
    expected_data = {"flight_id": "flight-1", "cabin_fare_id": "fare-1", "total_price": 880}
    fake_client = FakeHTTPClient({"code": 0, "message": "success", "data": expected_data})

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(order_service, "get_http_client", fake_get_http_client)
    tool = _get_tool(
        "api.mcp_tools.transport.create_pending_payment_flight_order_tools",
        "register_create_pending_payment_flight_order_tools",
        "create_pending_payment_flight_order",
    )

    result = asyncio.run(
        tool(
            search_token="token-1",
            departure_date="2026-06-01",
            flight_id=123,
            cabin_fare_id=456,
        )
    )

    assert result == {
        "ok": True,
        "data": expected_data,
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTIONS["transport"]["pending_payment_flight_order"]
        ),
    }
    assert fake_client.posts == [
        {
            "url": "/apitest/v1/flight/snapshot/lookup",
            "json": {
                "search_token": "token-1",
                "departure_date": "2026-06-01",
                "flight_id": "123",
                "cabin_fare_id": "456",
            },
        }
    ]


def test_create_pending_payment_train_order_tool_returns_normalized_snapshot(monkeypatch) -> None:
    fake_client = FakeHTTPClient(
        {
            "code": 0,
            "message": "success",
            "data": {
                "transport_type": "train",
                "train_code": "G1025",
                "train_no": "24000G102500",
                "from_station": "深圳北",
                "to_station": "广州南",
                "from_datetime": "2026-06-01 08:00",
                "to_datetime": "2026-06-01 08:30",
                "arrive_days": "0",
                "run_time": "00:30",
                "trains_type_name": "高铁",
                "seat_type_name": "二等座",
                "ticket_price": "75.5",
                "from_city": "深圳",
                "to_city": "广州",
                "hidden": "ignored",
            },
        }
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(order_service, "get_http_client", fake_get_http_client)
    tool = _get_tool(
        "api.mcp_tools.transport.create_pending_payment_train_order_tools",
        "register_create_pending_payment_train_order_tools",
        "create_pending_payment_train_order",
    )

    result = asyncio.run(
        tool(
            search_id="search-1",
            train_no="24000G102500",
            seat_type_name="二等座",
            date="2026-06-01",
        )
    )

    assert result == {
        "ok": True,
        "data": {
            "search_id": "search-1",
            "transport_type": "train",
            "train_code": "G1025",
            "train_no": "24000G102500",
            "from_station": "深圳北",
            "to_station": "广州南",
            "from_datetime": "2026-06-01 08:00",
            "to_datetime": "2026-06-01 08:30",
            "arrive_days": "0",
            "run_time": "00:30",
            "trains_type_name": "高铁",
            "seat_type_name": "二等座",
            "ticket_price": 75.5,
            "from_city": "深圳",
            "to_city": "广州",
        },
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTIONS["transport"]["pending_payment_train_order"]
        ),
    }
    assert fake_client.posts[0] == {
        "url": "/apitest/v1/train/snapshot/lookup",
        "json": {
            "search_id": "search-1",
            "train_no": "24000G102500",
            "date": "2026-06-01",
            "seat_type_name": "二等座",
        },
    }


def test_create_pending_payment_bus_order_tool_returns_normalized_snapshot(monkeypatch) -> None:
    fake_client = FakeHTTPClient(
        {
            "code": 0,
            "message": "success",
            "data": {
                "line_gid": "line-1",
                "line_name": "深圳到广州",
                "gid": "gid-1",
                "start_station_name": "深圳站",
                "end_station_name": "广州站",
                "class_date": "2026-06-01",
                "class_time": "09:00",
                "class_name": "上午班",
                "price": "88.5",
                "duration": "120",
                "distance": "130.2",
                "from_city": "深圳",
                "to_city": "广州",
                "search_id": "search-1",
                "hidden": "ignored",
            },
        }
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(order_service, "get_http_client", fake_get_http_client)
    tool = _get_tool(
        "api.mcp_tools.transport.create_pending_payment_bus_order_tools",
        "register_create_pending_payment_bus_order_tools",
        "create_pending_payment_bus_order",
    )

    result = asyncio.run(tool(search_id="search-1", gid="gid-1"))

    assert result == {
        "ok": True,
        "data": {
            "transport_type": "bus",
            "line_gid": "line-1",
            "line_name": "深圳到广州",
            "gid": "gid-1",
            "start_station_name": "深圳站",
            "end_station_name": "广州站",
            "class_date": "2026-06-01",
            "class_time": "09:00",
            "class_name": "上午班",
            "price": 88.5,
            "duration": 120,
            "distance": 130,
            "from_city": "深圳",
            "to_city": "广州",
            "search_id": "search-1",
        },
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTIONS["transport"]["pending_payment_bus_order"]
        ),
    }
    assert fake_client.posts[0] == {
        "url": "/apitest/v1/bus/snapshot/lookup",
        "json": {"search_id": "search-1", "gid": "gid-1"},
    }


def test_create_pending_payment_transport_order_raises_for_snapshot_error(monkeypatch) -> None:
    fake_client = FakeHTTPClient({"code": 1001, "message": "snapshot missing", "data": None})

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(order_service, "get_http_client", fake_get_http_client)
    tool = _get_tool(
        "api.mcp_tools.transport.create_pending_payment_bus_order_tools",
        "register_create_pending_payment_bus_order_tools",
        "create_pending_payment_bus_order",
    )

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(tool(search_id="search-1", gid="gid-1"))

    assert exc_info.value.error_code == "RIDECLOW_BUS_ORDER_SNAPSHOT_ERROR"


@pytest.mark.parametrize(
    ("kwargs", "error_code"),
    [
        (
            {
                "search_token": "",
                "departure_date": "2026-06-01",
                "flight_id": "flight-1",
                "cabin_fare_id": "fare-1",
            },
            "RIDECLOW_FLIGHT_ORDER_SEARCH_TOKEN_REQUIRED",
        ),
        (
            {
                "search_token": "token-1",
                "departure_date": "",
                "flight_id": "flight-1",
                "cabin_fare_id": "fare-1",
            },
            "RIDECLOW_FLIGHT_ORDER_DEPARTURE_DATE_REQUIRED",
        ),
        (
            {
                "search_token": "token-1",
                "departure_date": "2026-06-01",
                "flight_id": "",
                "cabin_fare_id": "fare-1",
            },
            "RIDECLOW_FLIGHT_ORDER_FLIGHT_ID_REQUIRED",
        ),
        (
            {
                "search_token": "token-1",
                "departure_date": "2026-06-01",
                "flight_id": "flight-1",
                "cabin_fare_id": "",
            },
            "RIDECLOW_FLIGHT_ORDER_CABIN_FARE_ID_REQUIRED",
        ),
    ],
)
def test_create_pending_payment_flight_order_validates_required_fields(kwargs, error_code) -> None:
    tool = _get_tool(
        "api.mcp_tools.transport.create_pending_payment_flight_order_tools",
        "register_create_pending_payment_flight_order_tools",
        "create_pending_payment_flight_order",
    )

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(tool(**kwargs))

    assert exc_info.value.error_code == error_code
