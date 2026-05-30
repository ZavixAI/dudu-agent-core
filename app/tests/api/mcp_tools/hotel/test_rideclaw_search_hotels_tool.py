"""End-to-end tests for the RideClaw hotel search MCP tool."""

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
from services.hotel import search_service

MODULE_NAME = "api.mcp_tools.hotel.rideclaw_search_hotels_tools"


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


def _get_search_hotels_tool():
    module = importlib.import_module(MODULE_NAME)
    mcp_app = FakeMCPApp()
    module.register_rideclaw_search_hotels_tools(mcp_app)
    return mcp_app.tools["hotel_search"]["func"]


def test_search_hotels_tool_returns_unified_response(monkeypatch) -> None:
    expected_data = {
        "search_id": "search-1",
        "total_count": 1,
        "hotels": [
            {
                "hotel_id": "hotel-1",
                "hotel_name": "三里屯酒店",
                "supplier": "qiantao",
                "source": "qiantao",
                "brand_name": "",
                "address": "",
                "district": "",
                "business_zone": "",
                "star_rating": 0,
                "review_score": 0,
                "review_count": 0,
                "min_price": 0,
                "currency": "CNY",
                "main_picture": "",
                "phone": "",
                "has_wifi": None,
                "has_parking": None,
                "has_restaurant": None,
                "has_breakfast": None,
            }
        ],
    }
    fake_client = FakeHTTPClient(
        [
            {
                "code": 0,
                "message": "success",
                "data": {
                    "lng": 116.4551,
                    "lat": 39.9346,
                    "adcode": "110105",
                    "formatted_address": "北京市朝阳区三里屯",
                },
            },
            {
                "code": 0,
                "message": "success",
                "data": {
                    "search_id": "search-1",
                    "total_count": 1,
                    "hotels": [
                        {
                            "hotel_id": "hotel-1",
                            "hotel_name": "三里屯酒店",
                            "supplier": "qiantao",
                            "secret_field": "ignored",
                        }
                    ],
                    "raw_debug": "ignored",
                },
            },
        ]
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_search_hotels_tool()(
            destination="北京市朝阳区三里屯",
            check_in="2026-06-01",
            check_out="2026-06-02",
            room_count=1,
            adult_count=2,
            sort_by="best",
            min_price="200",
            max_price="800",
            star_levels="4,5",
            hotel_types="qiantao",
            hotel_brand="万豪酒店",
            min_review_score="4.3",
            max_distance_km="10",
            tags="has_wifi,has_parking,unknown_tag",
            page=1,
            page_size=10,
            is_cn=True,
            user_token="user-token",
        )
    )

    assert result == {
        "ok": True,
        "data": expected_data,
        "next_action_suggestions": constants.NEXT_ACTION_SUGGESTIONS_FOR_HOTEL_SEARCH,
    }
    assert fake_client.posts[0] == {
        "url": "/apitest/v1/tool/geocode",
        "json": {"address": "北京市朝阳区三里屯", "is_cn": True},
        "headers": {"Authorization": "Bearer user-token"},
    }
    assert fake_client.posts[1] == {
        "url": "/apitest/v1/hotel/search-aggregated",
        "json": {
            "destination": "北京市朝阳区三里屯",
            "longitude": 116.4551,
            "latitude": 39.9346,
            "check_in": "2026-06-01",
            "check_out": "2026-06-02",
            "room_count": 1,
            "adult_count": 2,
            "page": 1,
            "page_size": 10,
            "adcode": "110105",
            "sort_by": "best",
            "hotel_types": ["qiantao"],
            "filters": {
                "min_price": 200.0,
                "max_price": 800.0,
                "star_levels": [4, 5],
                "hotel_brand": "万豪酒店",
                "min_review_score": 4.3,
                "max_distance_km": 10.0,
                "has_wifi": True,
                "has_parking": True,
            },
        },
        "headers": {"Authorization": "Bearer user-token"},
    }


def test_search_hotels_tool_compacts_content_hotels(monkeypatch) -> None:
    fake_client = FakeHTTPClient(
        [
            {
                "code": 0,
                "message": "success",
                "data": {"lng": 116.4551, "lat": 39.9346, "adcode": "110105"},
            },
            {
                "code": 0,
                "message": "success",
                "data": {
                    "search_id": "search-1",
                    "total_count": 1,
                    "content": [
                        {
                            "hotel_id": "hotel-1",
                            "source": "meituan",
                            "hotel_name": "三里屯酒店",
                            "description": "市中心酒店",
                            "location": {"latitude": 39.9346, "longitude": 116.4551},
                            "extra": "ignored",
                        }
                    ],
                },
            },
        ]
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_search_hotels_tool()(
            destination="北京市朝阳区三里屯",
            check_in="2026-06-01",
            check_out="2026-06-02",
        )
    )

    assert result["data"]["search_id"] == "search-1"
    assert (
        result["next_action_suggestions"]
        == constants.NEXT_ACTION_SUGGESTIONS_FOR_HOTEL_SEARCH
    )
    assert result["data"]["total_count"] == 1
    assert result["data"]["hotels"][0]["hotel_id"] == "hotel-1"
    assert result["data"]["hotels"][0]["supplier"] == "meituan"
    assert result["data"]["hotels"][0]["description"] == "市中心酒店"
    assert result["data"]["hotels"][0]["location"] == {
        "latitude": 39.9346,
        "longitude": 116.4551,
    }
    assert "content" not in result["data"]
    assert "extra" not in result["data"]["hotels"][0]


@pytest.mark.parametrize(
    ("payload", "error_code"),
    [
        ({"code": 1001, "message": "invalid address", "data": None}, "RIDECLOW_HOTEL_GEOCODE_ERROR"),
        ({"code": 0, "message": "success", "data": {"lng": None, "lat": 39.9346}}, "RIDECLOW_HOTEL_GEOCODE_INVALID"),
    ],
)
def test_search_hotels_tool_raises_for_failed_geocode(monkeypatch, payload, error_code) -> None:
    fake_client = FakeHTTPClient([payload])

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_search_hotels_tool()(
                destination="北京市朝阳区三里屯",
                check_in="2026-06-01",
                check_out="2026-06-02",
            )
        )

    assert exc_info.value.error_code == error_code


def test_search_hotels_tool_raises_for_failed_search(monkeypatch) -> None:
    fake_client = FakeHTTPClient(
        [
            {
                "code": 0,
                "message": "success",
                "data": {"lng": 116.4551, "lat": 39.9346, "adcode": "110105"},
            },
            {"code": 1001, "message": "invalid search", "data": None},
        ]
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_search_hotels_tool()(
                destination="北京市朝阳区三里屯",
                check_in="2026-06-01",
                check_out="2026-06-02",
            )
        )

    assert exc_info.value.error_code == "RIDECLOW_HOTEL_SEARCH_ERROR"
