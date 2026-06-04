"""Tests for single-mode RideClaw transport search MCP tools."""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[4]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.transport import search_service


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
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = payloads
        self.posts: list[dict[str, Any]] = []

    async def post(self, url: str, **kwargs) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse(self.payloads.pop(0))


def _get_tool(module_name: str, register_name: str, tool_name: str):
    module = importlib.import_module(module_name)
    mcp_app = FakeMCPApp()
    getattr(module, register_name)(mcp_app)
    return mcp_app.tools[tool_name]["func"]


def _transport_payload() -> dict[str, Any]:
    return {
        "from_city": "深圳",
        "to_city": "广州",
        "date": "2026-06-01",
        "search_id": "search-1",
        "errors": [
            {"mode": "flight", "error": "flight error"},
            {"mode": "train", "error": "train error"},
            {"mode": "bus", "error": "bus error"},
        ],
        "train_data": {"trains": [{"trainCode": "G1"}]},
        "flight_data": {
            "search_token": "token-1",
            "flights": [{"flightId": "flight-1", "trips": []}],
        },
        "bus_data": {"buses": [{"line_name": "bus-1"}]},
    }


def _fake_client() -> FakeHTTPClient:
    return FakeHTTPClient(
        [
            {"code": 0, "message": "success", "data": {"lng": 1, "lat": 2}},
            {"code": 0, "message": "success", "data": {"lng": 3, "lat": 4}},
            {"code": 0, "message": "success", "data": _transport_payload()},
        ]
    )


def test_search_train_options_tool_uses_train_mode(monkeypatch) -> None:
    fake_client = _fake_client()

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_tool(
            "api.mcp_tools.transport.search_train_options_tools",
            "register_search_train_options_tools",
            "search_train_options",
        )(
            date="2026-06-01",
            from_name="深圳北",
            to_name="广州南",
            is_cn=True,
        )
    )

    assert fake_client.posts[2]["json"]["modes"] == ["train"]
    assert result["data"]["train_data"] == {"trains": [{"trainCode": "G1"}]}
    assert result["data"]["pagination"] == {
        "mode": "train",
        "page": 1,
        "page_size": 10,
        "total": 1,
        "returned": 1,
        "has_more": False,
    }


def test_search_flight_options_tool_uses_flight_mode(monkeypatch) -> None:
    fake_client = _fake_client()

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_tool(
            "api.mcp_tools.transport.search_flight_options_tools",
            "register_search_flight_options_tools",
            "search_flight_options",
        )(
            date="2026-06-01",
            from_name="深圳",
            to_name="广州",
            is_cn=True,
        )
    )

    assert fake_client.posts[2]["json"]["modes"] == ["flight"]
    assert result["data"]["flight_data"] == {
        "search_token": "token-1",
        "flights": [{"flightId": "flight-1", "trips": []}],
    }
    assert result["data"]["pagination"] == {
        "mode": "flight",
        "page": 1,
        "page_size": 10,
        "total": 1,
        "returned": 1,
        "has_more": False,
    }


def test_search_bus_options_tool_uses_bus_mode(monkeypatch) -> None:
    fake_client = _fake_client()

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_tool(
            "api.mcp_tools.transport.search_bus_options_tools",
            "register_search_bus_options_tools",
            "search_bus_options",
        )(
            date="2026-06-01",
            from_name="深圳",
            to_name="广州",
            is_cn=True,
        )
    )

    assert fake_client.posts[2]["json"]["modes"] == ["bus"]
    assert result["data"]["bus_data"] == {"buses": [{"line_name": "bus-1"}]}
    assert result["data"]["pagination"] == {
        "mode": "bus",
        "page": 1,
        "page_size": 10,
        "total": 1,
        "returned": 1,
        "has_more": False,
    }
