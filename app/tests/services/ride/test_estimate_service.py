"""Tests for RideClaw estimate service."""

import sys
from pathlib import Path
from typing import Any

import pytest

APP_DIR = Path(__file__).resolve().parents[3]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.ride import estimate_service


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
        self.post_calls: list[dict[str, Any]] = []

    async def post(
        self,
        url: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> FakeResponse:
        self.post_calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
            }
        )
        return FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_estimate_ride_price_posts_realtime_quote(monkeypatch) -> None:
    expected_data = {"estimated_price": 35, "currency": "CNY"}
    client = FakeHTTPClient({"code": 0, "message": "success", "data": expected_data})

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return client

    monkeypatch.setattr(estimate_service, "get_http_client", fake_get_http_client)

    result = await estimate_service.estimate_ride_price(
        from_lng="116.397128",
        from_lat="39.916527",
        from_name="天安门",
        to_lng="116.407396",
        to_lat="39.904200",
        to_name="北京站",
    )

    assert result == expected_data
    assert client.post_calls == [
        {
            "url": "/api/v1/taxi/quote",
            "json": {
                "from_lng": "116.397128",
                "from_lat": "39.916527",
                "from_name": "天安门",
                "to_lng": "116.407396",
                "to_lat": "39.904200",
                "to_name": "北京站",
                "order_type": 1,
            },
            "headers": None,
        }
    ]


@pytest.mark.asyncio
async def test_estimate_ride_price_posts_scheduled_quote(monkeypatch) -> None:
    expected_data = {"estimated_price": 48, "currency": "CNY"}
    client = FakeHTTPClient({"code": 0, "message": "success", "data": expected_data})

    async def fake_get_http_client(service_name: str) -> FakeHTTPClient:
        assert service_name == "rideclaw"
        return client

    monkeypatch.setattr(estimate_service, "get_http_client", fake_get_http_client)

    result = await estimate_service.estimate_ride_price(
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

    assert result == expected_data
    assert client.post_calls == [
        {
            "url": "/api/v1/taxi/quote",
            "json": {
                "from_lng": "116.397128",
                "from_lat": "39.916527",
                "from_name": "天安门",
                "to_lng": "116.407396",
                "to_lat": "39.904200",
                "to_name": "北京站",
                "order_type": 2,
                "booking_time": 1777867200000,
            },
            "headers": {"Authorization": "Bearer user-token"},
        }
    ]
