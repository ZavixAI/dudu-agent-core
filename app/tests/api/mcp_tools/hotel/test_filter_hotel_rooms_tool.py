"""End-to-end tests for the RideClaw hotel room filter MCP tool."""

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
from services.hotel import room_service

MODULE_NAME = "api.mcp_tools.hotel.filter_hotel_rooms_tools"


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


def _get_filter_rooms_tool():
    module = importlib.import_module(MODULE_NAME)
    mcp_app = FakeMCPApp()
    module.register_filter_hotel_rooms_tools(mcp_app)
    return mcp_app.tools["filter_hotel_rooms"]["func"]


def test_filter_hotel_rooms_tool_returns_unified_response(monkeypatch) -> None:
    raw_room_groups = [
        {
            "room_type_info": {
                "room_id": "room-1",
                "room_name": "大床房",
                "room_name_en": "King Room",
                "bed_type_tag": "大床",
                "bed_desc": "1张1.8米大床",
                "window_type_tag": "有窗",
                "area_min": 20,
                "area_max": 25,
                "floor_info": "5-8层",
                "max_occupancy": 2,
                "has_wifi": True,
                "allow_extra_bed": False,
                "smoke_policy": "禁烟",
                "main_picture": "https://example.com/room.jpg",
                "extra_room_field": "ignored",
            },
            "price_range": {"min": 18800, "max": 28800, "extra_price_field": "ignored"},
            "product_count": 2,
            "products": [
                {
                    "product_id": "product-expensive",
                    "room_id": "room-1",
                    "product_name": "含早",
                    "price": 28800,
                    "inventory": 1,
                    "breakfast": "双早",
                    "cancel_rule_type": "N",
                    "cancel_rule_desc": "不可取消",
                    "is_refundable": False,
                    "pay_type": 0,
                    "extra_product_field": "ignored",
                },
                {
                    "product_id": "product-cheap",
                    "room_id": "room-1",
                    "product_name": "无早",
                    "price": 18800,
                    "inventory": 3,
                    "breakfast": "无早",
                    "cancel_rule_type": "Y",
                    "cancel_rule_desc": "入住前可免费取消",
                    "is_refundable": True,
                    "pay_type": 1,
                    "extra_product_field": "ignored",
                },
            ],
            "extra_group_field": "ignored",
        }
    ]
    expected_data = {
        "search_id": "search-1",
        "supplier": "meituan",
        "hotel_type": "meituan",
        "hotel_id": "hotel-1",
        "hotel_name": "三里屯酒店",
        "hotel_main_picture": "https://example.com/hotel.jpg",
        "currency": "CNY",
        "total_count": 2,
        "total_group_count": 1,
        "room_groups": [
            {
                "room_type_info": {
                    "room_id": "room-1",
                    "room_name": "大床房",
                    "room_name_en": "King Room",
                    "bed_type_tag": "大床",
                    "bed_desc": "1张1.8米大床",
                    "window_type_tag": "有窗",
                    "area_min": 20,
                    "area_max": 25,
                    "floor_info": "5-8层",
                    "max_occupancy": 2,
                    "has_wifi": True,
                    "allow_extra_bed": False,
                    "smoke_policy": "禁烟",
                    "main_picture": "https://example.com/room.jpg",
                },
                "price_range": {"min": 18800, "max": 28800},
                "product_count": 2,
                "recommended_product": {
                    "product_id": "product-cheap",
                    "room_id": "room-1",
                    "product_name": "无早",
                    "price": 18800,
                    "inventory": 3,
                    "breakfast": "无早",
                    "cancel_rule_type": "Y",
                    "cancel_rule_desc": "入住前可免费取消",
                    "is_refundable": True,
                    "pay_type": 1,
                },
                "other_product_count": 1,
            }
        ],
    }
    fake_client = FakeHTTPClient(
        {
            "code": 0,
            "message": "success",
            "data": {
                "search_id": "search-1",
                "supplier": "meituan",
                "hotel_id": "hotel-1",
                "hotel_name": "三里屯酒店",
                "hotel_main_picture": "https://example.com/hotel.jpg",
                "currency": "CNY",
                "room_groups": raw_room_groups,
                "extra_top_field": "ignored",
            },
        }
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(room_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_filter_rooms_tool()(
            hotel_type="meituan",
            hotel_id="hotel-1",
            check_in="2026-06-01",
            check_out="2026-06-02",
            search_id="search-1",
            room_count=1,
            adult_count=2,
            child_count=2,
            child_ages="3,7",
            min_price="10000",
            max_price="20000",
            product_type=3,
            user_token="user-token",
        )
    )

    assert result == {
        "ok": True,
        "data": expected_data,
        "assistant_response_instruction": (
            constants.ASSISTANT_RESPONSE_INSTRUCTION_FOR_HOTEL_ROOMS
        ),
        "next_action_suggestions": (
            constants.NEXT_ACTION_SUGGESTIONS_FOR_HOTEL_ROOM_FILTER
        ),
    }
    assert fake_client.posts == [
        {
            "url": "/apitest/v1/hotel/filter-rooms",
            "json": {
                "hotel_type": "meituan",
                "hotel_id": "hotel-1",
                "check_in": "2026-06-01",
                "check_out": "2026-06-02",
                "room_count": 1,
                "adult_count": 2,
                "child_count": 2,
                "child_ages": [3, 7],
                "product_type": 3,
                "need_detail": True,
                "search_id": "search-1",
                "min_price": 10000,
                "max_price": 20000,
            },
            "headers": {"Authorization": "Bearer user-token"},
        }
    ]


def test_filter_hotel_rooms_tool_limits_room_groups(monkeypatch) -> None:
    room_groups = [
        {
            "room_type_info": {"room_id": f"room-{index}", "room_name": f"房型{index}"},
            "products": [{"product_id": f"product-{index}", "price": index}],
        }
        for index in range(13)
    ]
    fake_client = FakeHTTPClient(
        {
            "code": 0,
            "message": "success",
            "data": {
                "hotel_id": "hotel-1",
                "hotel_type": "meituan",
                "room_groups": room_groups,
            },
        }
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(room_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_filter_rooms_tool()(
            hotel_type="meituan",
            hotel_id="hotel-1",
            check_in="2026-06-01",
            check_out="2026-06-02",
        )
    )

    assert (
        result["assistant_response_instruction"]
        == constants.ASSISTANT_RESPONSE_INSTRUCTION_FOR_HOTEL_ROOMS
    )
    assert (
        result["next_action_suggestions"]
        == constants.NEXT_ACTION_SUGGESTIONS_FOR_HOTEL_ROOM_FILTER
    )
    assert result["data"]["total_group_count"] == 13
    assert len(result["data"]["room_groups"]) == 12
    assert result["data"]["room_groups"][-1]["room_type_info"]["room_id"] == "room-11"


def test_filter_hotel_rooms_tool_raises_for_failed_filter(monkeypatch) -> None:
    fake_client = FakeHTTPClient({"code": 1001, "message": "invalid hotel", "data": None})

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(room_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_filter_rooms_tool()(
                hotel_type="meituan",
                hotel_id="hotel-1",
                check_in="2026-06-01",
                check_out="2026-06-02",
            )
        )

    assert exc_info.value.error_code == "RIDECLOW_HOTEL_ROOM_FILTER_ERROR"


@pytest.mark.parametrize(
    ("hotel_type", "hotel_id", "error_code"),
    [
        ("", "hotel-1", "RIDECLOW_HOTEL_ROOM_TYPE_REQUIRED"),
        ("meituan", "", "RIDECLOW_HOTEL_ROOM_ID_REQUIRED"),
    ],
)
def test_filter_hotel_rooms_tool_validates_required_fields(
    hotel_type,
    hotel_id,
    error_code,
) -> None:
    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_filter_rooms_tool()(
                hotel_type=hotel_type,
                hotel_id=hotel_id,
                check_in="2026-06-01",
                check_out="2026-06-02",
            )
        )

    assert exc_info.value.error_code == error_code
