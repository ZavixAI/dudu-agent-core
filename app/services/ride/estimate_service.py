"""Ride estimate domain services."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from loguru import logger

from config import constants
from core.http.exceptions import AppHTTPException
from core.infra.http_client import get_http_client
from schema.mcp import MCPToolResponse
from schema.ride import RawRideEstimateResponse


def _booking_time_to_millis(booking_time_str: str) -> int:
    """Convert local booking time string to millisecond timestamp."""

    try:
        booking_time = datetime.strptime(booking_time_str, "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise AppHTTPException(
            status_code=400,
            detail='booking_time_str must match format "YYYY-MM-DD HH:mm"',
            error_code="RIDECLOW_QUOTE_INVALID_BOOKING_TIME",
            error_detail={"booking_time_str": booking_time_str},
        ) from exc

    localized_booking_time = booking_time.replace(
        tzinfo=ZoneInfo(constants.DEFAULT_TIMEZONE)
    )
    return int(localized_booking_time.timestamp() * 1000)


async def estimate_ride_price(
    from_lng: str,
    from_lat: str,
    from_name: str,
    to_lng: str,
    to_lat: str,
    to_name: str,
    order_type: int = 1,
    booking_time_str: str | None = None,
    user_token: str | None = None,
) -> Any:
    """Estimate taxi quote through RideClaw."""

    if order_type == 2 and not booking_time_str:
        raise AppHTTPException(
            status_code=400,
            detail="booking_time_str is required for scheduled ride orders",
            error_code="RIDECLOW_QUOTE_BOOKING_TIME_REQUIRED",
        )

    request_body: dict[str, Any] = {
        "from_lng": from_lng,
        "from_lat": from_lat,
        "from_name": from_name,
        "to_lng": to_lng,
        "to_lat": to_lat,
        "to_name": to_name,
        "order_type": order_type,
    }
    if order_type == 2 and booking_time_str:
        request_body["booking_time"] = _booking_time_to_millis(booking_time_str)

    request_headers = {}
    if user_token:
        request_headers["Authorization"] = f"Bearer {user_token}"

    client = await get_http_client("rideclaw")
    logger.info(
        "RideClaw quote started from_name={} to_name={} order_type={}",
        from_name,
        to_name,
        order_type,
    )

    try:
        response = await client.post(
            "/api/v1/taxi/quote",
            json=request_body,
            headers=request_headers or None,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception(
            "RideClaw quote request failed from_name={} to_name={} order_type={}",
            from_name,
            to_name,
            order_type,
        )
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw quote failed",
            error_code="RIDECLOW_QUOTE_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawRideEstimateResponse(**payload)
    if raw_response.code != 0:
        logger.warning(
            "RideClaw quote returned error from_name={} to_name={} order_type={} code={} message={}",
            from_name,
            to_name,
            order_type,
            raw_response.code,
            raw_response.message,
        )
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw quote returned an error",
            error_code="RIDECLOW_QUOTE_ERROR",
            error_detail=payload,
        )
    if raw_response.data is None:
        logger.info(
            "RideClaw quote returned no data from_name={} to_name={} order_type={}",
            from_name,
            to_name,
            order_type,
        )
        raise AppHTTPException(
            status_code=404,
            detail="RideClaw quote returned no data",
            error_code="RIDECLOW_QUOTE_EMPTY",
            error_detail=payload,
        )

    logger.info(
        "RideClaw quote succeeded from_name={} to_name={} order_type={}",
        from_name,
        to_name,
        order_type,
    )
    return MCPToolResponse(data=raw_response.data).model_dump()


__all__ = [
    "estimate_ride_price",
]
