"""Transport order services."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from config import constants
from core.http.exceptions import AppHTTPException
from core.infra.http_client import get_http_client
from schema.mcp import MCPToolResponse
from schema.transport import RawTransportOrderSnapshotResponse


def _to_float(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _to_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _require_text(value: object, field_name: str, error_code: str) -> str:
    text = str(value or "").strip()
    if text:
        return text
    raise AppHTTPException(
        status_code=400,
        detail=f"{field_name} cannot be empty",
        error_code=error_code,
    )


async def _lookup_snapshot(
    endpoint: str,
    request_body: dict[str, Any],
    error_prefix: str,
) -> dict[str, Any]:
    client = await get_http_client("rideclaw")
    try:
        response = await client.post(endpoint, json=request_body)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("RideClaw transport order snapshot lookup failed endpoint={}", endpoint)
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw transport order snapshot lookup failed",
            error_code=f"{error_prefix}_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawTransportOrderSnapshotResponse(**payload)
    if raw_response.code != 0:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw transport order snapshot lookup returned an error",
            error_code=f"{error_prefix}_ERROR",
            error_detail=payload,
        )
    if not isinstance(raw_response.data, dict):
        raise AppHTTPException(
            status_code=404,
            detail="RideClaw transport order snapshot data is empty or invalid",
            error_code=f"{error_prefix}_EMPTY",
            error_detail=payload,
        )
    return raw_response.data


async def create_pending_payment_flight_order(
    search_token: str,
    departure_date: str,
    flight_id: str | int | float,
    cabin_fare_id: str | int | float,
) -> dict[str, Any]:
    """Create pending-payment flight order data from a RideClaw snapshot."""

    clean_search_token = _require_text(
        search_token,
        "search_token",
        "RIDECLOW_FLIGHT_ORDER_SEARCH_TOKEN_REQUIRED",
    )
    clean_departure_date = _require_text(
        departure_date,
        "departure_date",
        "RIDECLOW_FLIGHT_ORDER_DEPARTURE_DATE_REQUIRED",
    )
    clean_flight_id = _require_text(
        flight_id,
        "flight_id",
        "RIDECLOW_FLIGHT_ORDER_FLIGHT_ID_REQUIRED",
    )
    clean_cabin_fare_id = _require_text(
        cabin_fare_id,
        "cabin_fare_id",
        "RIDECLOW_FLIGHT_ORDER_CABIN_FARE_ID_REQUIRED",
    )
    request_body = {
        "search_token": clean_search_token,
        "departure_date": clean_departure_date,
        "flight_id": clean_flight_id,
        "cabin_fare_id": clean_cabin_fare_id,
    }
    data = await _lookup_snapshot(
        "/apitest/v1/flight/snapshot/lookup",
        request_body,
        "RIDECLOW_FLIGHT_ORDER_SNAPSHOT",
    )
    response_payload = MCPToolResponse(data=data).model_dump()
    response_payload["assistant_response_instruction"] = (
        constants.ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_ORDER
    )
    return response_payload


async def create_pending_payment_train_order(
    search_id: str,
    train_no: str,
    seat_type_name: str,
    date: str,
) -> dict[str, Any]:
    """Create pending-payment train order data from a RideClaw snapshot."""

    clean_search_id = _require_text(
        search_id,
        "search_id",
        "RIDECLOW_TRAIN_ORDER_SEARCH_ID_REQUIRED",
    )
    clean_train_no = _require_text(
        train_no,
        "train_no",
        "RIDECLOW_TRAIN_ORDER_TRAIN_NO_REQUIRED",
    )
    clean_seat_type_name = _require_text(
        seat_type_name,
        "seat_type_name",
        "RIDECLOW_TRAIN_ORDER_SEAT_TYPE_REQUIRED",
    )
    clean_date = _require_text(date, "date", "RIDECLOW_TRAIN_ORDER_DATE_REQUIRED")
    request_body = {
        "search_id": clean_search_id,
        "train_no": clean_train_no,
        "date": clean_date,
        "seat_type_name": clean_seat_type_name,
    }
    item = await _lookup_snapshot(
        "/apitest/v1/train/snapshot/lookup",
        request_body,
        "RIDECLOW_TRAIN_ORDER_SNAPSHOT",
    )
    result_payload = {
        "search_id": clean_search_id,
        "transport_type": item.get("transport_type", "train"),
        "train_code": item.get("train_code", ""),
        "train_no": item.get("train_no", clean_train_no),
        "from_station": item.get("from_station", ""),
        "to_station": item.get("to_station", ""),
        "from_datetime": item.get("from_datetime", ""),
        "to_datetime": item.get("to_datetime", ""),
        "arrive_days": item.get("arrive_days", ""),
        "run_time": item.get("run_time", ""),
        "trains_type_name": item.get("trains_type_name", ""),
        "seat_type_name": item.get("seat_type_name", clean_seat_type_name),
        "ticket_price": _to_float(item.get("ticket_price")),
        "from_city": item.get("from_city", ""),
        "to_city": item.get("to_city", ""),
    }
    response_payload = MCPToolResponse(data=result_payload).model_dump()
    response_payload["assistant_response_instruction"] = (
        constants.ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_TRAIN_ORDER
    )
    return response_payload


async def create_pending_payment_bus_order(
    search_id: str,
    gid: str,
) -> dict[str, Any]:
    """Create pending-payment bus order data from a RideClaw snapshot."""

    clean_search_id = _require_text(
        search_id,
        "search_id",
        "RIDECLOW_BUS_ORDER_SEARCH_ID_REQUIRED",
    )
    clean_gid = _require_text(gid, "gid", "RIDECLOW_BUS_ORDER_GID_REQUIRED")
    request_body = {
        "search_id": clean_search_id,
        "gid": clean_gid,
    }
    item = await _lookup_snapshot(
        "/apitest/v1/bus/snapshot/lookup",
        request_body,
        "RIDECLOW_BUS_ORDER_SNAPSHOT",
    )
    result_payload = {
        "transport_type": "bus",
        "line_gid": item.get("line_gid", ""),
        "line_name": item.get("line_name", ""),
        "gid": item.get("gid", clean_gid),
        "start_station_name": item.get("start_station_name", ""),
        "end_station_name": item.get("end_station_name", ""),
        "class_date": item.get("class_date", ""),
        "class_time": item.get("class_time", ""),
        "class_name": item.get("class_name", ""),
        "price": _to_float(item.get("price")),
        "duration": _to_int(item.get("duration")),
        "distance": _to_int(item.get("distance")),
        "from_city": item.get("from_city", ""),
        "to_city": item.get("to_city", ""),
        "search_id": item.get("search_id", clean_search_id),
    }
    response_payload = MCPToolResponse(data=result_payload).model_dump()
    response_payload["assistant_response_instruction"] = (
        constants.ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_ORDER
    )
    return response_payload


__all__ = [
    "create_pending_payment_bus_order",
    "create_pending_payment_flight_order",
    "create_pending_payment_train_order",
]
