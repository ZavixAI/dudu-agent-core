"""End-to-end tests for the RideClaw location MCP tool."""

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
from services.common import location_service

MODULE_NAME = "api.mcp_tools.common.search_location_tools"


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


def _get_search_tool():
    module = importlib.import_module(MODULE_NAME)
    mcp_app = FakeMCPApp()
    module.register_search_location_tools(mcp_app)
    return mcp_app.tools["location_search"]["func"]


def test_search_location_tool_returns_unified_response(monkeypatch) -> None:
    raw_location = {
        "name": "天安门",
        "address": "北京市东城区长安街",
        "province": "北京市",
        "city": "北京市",
        "area": "东城区",
        "lng": 116.39759,
        "lat": 39.908776,
        "adcode": "110101",
        "extra": "ignored",
    }

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return FakeHTTPClient({"code": 0, "message": "success", "data": [raw_location]})

    monkeypatch.setattr(location_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_search_tool()(
            query="天安门",
            region="北京",
            radius=200,
        )
    )

    assert result == {
        "ok": True,
        "data": [
            {
                "name": "天安门",
                "address": "北京市东城区长安街",
                "province": "北京市",
                "city": "北京市",
                "area": "东城区",
                "lng": 116.39759,
                "lat": 39.908776,
                "adcode": "110101",
            }
        ],
        "next_action_suggestions": (
            constants.NEXT_ACTION_SUGGESTIONS["location_search"]
        ),
    }


@pytest.mark.parametrize(
    ("payload", "error_code"),
    [
        ({"code": 1001, "message": "invalid query", "data": []}, "RIDECLOW_LOCATION_SEARCH_ERROR"),
        ({"code": 0, "message": "success", "data": []}, "RIDECLOW_LOCATION_SEARCH_EMPTY"),
    ],
)
def test_search_location_tool_raises_for_failed_search(monkeypatch, payload, error_code) -> None:
    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return FakeHTTPClient(payload)

    monkeypatch.setattr(location_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(_get_search_tool()(query="天安门", region="北京", radius=200))

    assert exc_info.value.error_code == error_code
