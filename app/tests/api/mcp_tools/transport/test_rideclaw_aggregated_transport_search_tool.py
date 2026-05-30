"""End-to-end tests for the RideClaw aggregated transport search MCP tool."""

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
from services.transport import search_service

MODULE_NAME = "api.mcp_tools.transport.rideclaw_search_transport_options_tools"


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


def _get_transport_search_tool():
    module = importlib.import_module(MODULE_NAME)
    mcp_app = FakeMCPApp()
    module.register_rideclaw_search_transport_options_tools(mcp_app)
    return mcp_app.tools["search_transport_options"]["func"]


def test_aggregated_transport_search_tool_returns_unified_response(monkeypatch) -> None:
    raw_data = {
        "from_city": "深圳",
        "to_city": "广州",
        "date": "2026-06-01",
        "search_id": "search-1",
        "debug": "hidden",
        "errors": [{"mode": "flight", "error": "未找到航班", "extra": "hidden"}],
        "train_data": {
            "trains": [
                {
                    "trainCode": "G1",
                    "trainNo": "240000G10A",
                    "fromStation": "深圳北",
                    "toStation": "广州南",
                    "fromDateTime": "2026-06-01 08:00",
                    "toDateTime": "2026-06-01 08:30",
                    "arrive_days": "0",
                    "runTime": "00:30",
                    "trainsTypeName": "高铁",
                    "hidden": "hidden",
                    "Seats": [
                        {
                            "seatTypeName": "二等座",
                            "ticketPrice": 75,
                            "leftTicketNum": 10,
                            "hidden": "hidden",
                        }
                    ],
                }
            ]
        },
        "flight_data": {
            "search_token": "token-1",
            "hidden": "hidden",
            "flights": [
                {
                    "flightId": "flight-1",
                    "hidden": "hidden",
                    "trips": [
                        {
                            "depAirportCode": "SZX",
                            "arrAirportCode": "CAN",
                            "hidden": "hidden",
                            "segments": [
                                {
                                    "airlineName": "南方航空",
                                    "airlineCode": "CZ",
                                    "flightNumber": "CZ1234",
                                    "aircraft": "320",
                                    "depCityName": "深圳",
                                    "depAirportName": "宝安机场",
                                    "depTerminal": "T3",
                                    "depDate": "2026-06-01",
                                    "depTime": "09:00",
                                    "arrCityName": "广州",
                                    "arrAirportName": "白云机场",
                                    "arrTerminal": "T2",
                                    "arrDate": "2026-06-01",
                                    "arrTime": "10:00",
                                    "stopCount": 1,
                                    "hidden": "hidden",
                                    "stopInfos": [
                                        {
                                            "city_name": "珠海",
                                            "stop_time": "20分钟",
                                            "hidden": "hidden",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                    "cabinFares": [
                        {
                            "cabinFareId": "fare-1",
                            "cabin": "Y",
                            "cabinName": "经济舱",
                            "bookingClass": "Y",
                            "seat": "A",
                            "hidden": "hidden",
                            "passengerFares": [
                                {
                                    "passengerType": "ADT",
                                    "total": 500,
                                    "baseFare": 420,
                                    "airportTax": 50,
                                    "oilTax": 30,
                                    "hidden": "hidden",
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        "bus_data": {
            "buses": [
                {
                    "line_name": f"线路{i}",
                    "start_station_name": "深圳汽车站",
                    "start_city_name": "深圳",
                    "start_addr": "深圳地址",
                    "end_station_name": "广州汽车站",
                    "end_city_name": "广州",
                    "end_addr": "广州地址",
                    "start_distance_text": "距起点1公里",
                    "end_distance_text": "距终点2公里",
                    "hidden": "hidden",
                    "class_day_list": [
                        {
                            "gid": f"gid-{i}",
                            "class_time": "08:00",
                            "price": "80.00",
                            "discount_price": "70.00",
                            "avail_seat_count": 20,
                            "duration": 90,
                            "distance": 120,
                            "hidden": "hidden",
                        }
                    ],
                }
                for i in range(6)
            ]
        },
    }
    expected_data = {
        "from_city": "深圳",
        "to_city": "广州",
        "date": "2026-06-01",
        "search_id": "search-1",
        "errors": [{"mode": "flight", "error": "未找到航班"}],
        "train_data": {
            "trains": [
                {
                    "trainCode": "G1",
                    "trainNo": "240000G10A",
                    "fromStation": "深圳北",
                    "toStation": "广州南",
                    "fromDateTime": "2026-06-01 08:00",
                    "toDateTime": "2026-06-01 08:30",
                    "arrive_days": "0",
                    "runTime": "00:30",
                    "trainsTypeName": "高铁",
                    "Seats": [
                        {
                            "seatTypeName": "二等座",
                            "ticketPrice": 75,
                            "leftTicketNum": 10,
                        }
                    ],
                }
            ]
        },
        "flight_data": {
            "search_token": "token-1",
            "flights": [
                {
                    "flightId": "flight-1",
                    "trips": [
                        {
                            "depAirportCode": "SZX",
                            "arrAirportCode": "CAN",
                            "segments": [
                                {
                                    "airlineName": "南方航空",
                                    "airlineCode": "CZ",
                                    "flightNumber": "CZ1234",
                                    "aircraft": "320",
                                    "depCityName": "深圳",
                                    "depAirportName": "宝安机场",
                                    "depTerminal": "T3",
                                    "depDate": "2026-06-01",
                                    "depTime": "09:00",
                                    "arrCityName": "广州",
                                    "arrAirportName": "白云机场",
                                    "arrTerminal": "T2",
                                    "arrDate": "2026-06-01",
                                    "arrTime": "10:00",
                                    "stopCount": 1,
                                    "stopInfos": [{"city_name": "珠海", "stop_time": "20分钟"}],
                                }
                            ],
                        }
                    ],
                    "cabinFares": [
                        {
                            "cabinFareId": "fare-1",
                            "cabin": "Y",
                            "cabinName": "经济舱",
                            "bookingClass": "Y",
                            "seat": "A",
                            "passengerFares": [
                                {
                                    "passengerType": "ADT",
                                    "total": 500,
                                    "baseFare": 420,
                                    "airportTax": 50,
                                    "oilTax": 30,
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        "bus_data": {
            "buses": [
                {
                    "line_name": f"线路{i}",
                    "start_station_name": "深圳汽车站",
                    "start_city_name": "深圳",
                    "start_addr": "深圳地址",
                    "end_station_name": "广州汽车站",
                    "end_city_name": "广州",
                    "end_addr": "广州地址",
                    "start_distance_text": "距起点1公里",
                    "end_distance_text": "距终点2公里",
                    "class_day_list": [
                        {
                            "gid": f"gid-{i}",
                            "class_time": "08:00",
                            "price": "80.00",
                            "discount_price": "70.00",
                            "avail_seat_count": 20,
                            "duration": 90,
                            "distance": 120,
                        }
                    ],
                }
                for i in range(5)
            ]
        },
    }
    fake_client = FakeHTTPClient(
        [
            {
                "code": 0,
                "message": "success",
                "data": {
                    "lng": 114.0297,
                    "lat": 22.6099,
                    "formatted_address": "深圳北",
                },
            },
            {
                "code": 0,
                "message": "success",
                "data": {
                    "lng": 113.2644,
                    "lat": 23.1291,
                    "formatted_address": "广州",
                },
            },
            {"code": 0, "message": "success", "data": raw_data},
        ]
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_transport_search_tool()(
            date="2026-06-01",
            from_name="深圳北",
            to_name="广州",
            is_cn=True,
            earliest_departure_time="2026-06-01 08:00",
            latest_arrival_time="2026-06-01 20:00",
            user_token="user-token",
            modes="all",
        )
    )

    assert result == {"ok": True, "data": expected_data}
    assert fake_client.posts[0] == {
        "url": "/apitest/v1/tool/geocode",
        "json": {"address": "深圳北", "is_cn": True},
        "headers": {"Authorization": "Bearer user-token"},
    }
    assert fake_client.posts[1] == {
        "url": "/apitest/v1/tool/geocode",
        "json": {"address": "广州", "is_cn": True},
        "headers": {"Authorization": "Bearer user-token"},
    }
    assert fake_client.posts[2] == {
        "url": "/apitest/v1/transport/search",
        "json": {
            "date": "2026-06-01",
            "from_lat": "22.6099",
            "from_lng": "114.0297",
            "from_name": "深圳北",
            "to_lat": "23.1291",
            "is_cn": True,
            "to_lng": "113.2644",
            "to_name": "广州",
            "modes": ["flight", "train", "bus"],
            "earliest_departure_time": "2026-06-01 08:00",
            "latest_arrival_time": "2026-06-01 19:00",
        },
        "headers": {"Authorization": "Bearer user-token"},
    }


def test_aggregated_transport_search_tool_accepts_single_mode_enum(monkeypatch) -> None:
    fake_client = FakeHTTPClient(
        [
            {"code": 0, "message": "success", "data": {"lng": 1, "lat": 2}},
            {"code": 0, "message": "success", "data": {"lng": 3, "lat": 4}},
            {"code": 0, "message": "success", "data": {"train_data": {"trains": []}}},
        ]
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    result = asyncio.run(
        _get_transport_search_tool()(
            date="2026-06-01",
            from_name="深圳北",
            to_name="广州",
            is_cn=True,
            modes="train",
        )
    )

    assert result == {"ok": True, "data": {"train_data": {"trains": []}}}
    assert fake_client.posts[2]["json"]["modes"] == ["train"]


@pytest.mark.parametrize(
    ("payload", "error_code"),
    [
        ({"code": 1001, "message": "invalid address", "data": None}, "RIDECLOW_TRANSPORT_GEOCODE_ERROR"),
        ({"code": 0, "message": "success", "data": {"lng": None, "lat": 22.6099}}, "RIDECLOW_TRANSPORT_GEOCODE_INVALID"),
    ],
)
def test_aggregated_transport_search_tool_raises_for_failed_geocode(
    monkeypatch,
    payload,
    error_code,
) -> None:
    fake_client = FakeHTTPClient([payload, payload])

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_transport_search_tool()(
                date="2026-06-01",
                from_name="深圳北",
                to_name="广州",
                is_cn=True,
            )
        )

    assert exc_info.value.error_code == error_code


def test_aggregated_transport_search_tool_raises_for_failed_search(monkeypatch) -> None:
    fake_client = FakeHTTPClient(
        [
            {"code": 0, "message": "success", "data": {"lng": 1, "lat": 2}},
            {"code": 0, "message": "success", "data": {"lng": 3, "lat": 4}},
            {"code": 1001, "message": "invalid search", "data": None},
        ]
    )

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return fake_client

    monkeypatch.setattr(search_service, "get_http_client", fake_get_http_client)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            _get_transport_search_tool()(
                date="2026-06-01",
                from_name="深圳北",
                to_name="广州",
                is_cn=True,
            )
        )

    assert exc_info.value.error_code == "RIDECLOW_TRANSPORT_SEARCH_ERROR"


