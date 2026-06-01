"""Hotel order services."""

from __future__ import annotations

import json
from typing import Any

import httpx
from loguru import logger

from config import constants
from core.http.exceptions import AppHTTPException
from core.infra.http_client import get_http_client
from schema.hotel import RawHotelOrderSnapshotResponse
from schema.mcp import MCPToolResponse


def _parse_snapshot_data(data: Any) -> Any:
    if isinstance(data, str):
        text = data.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return data


async def create_pending_payment_hotel_order(
    search_id: str,
    hotel_type: str,
    hotel_id: str | int,
    product_id: str,
) -> dict[str, Any]:
    """Create pending-payment hotel order payload by looking up the RideClaw snapshot."""

    clean_search_id = str(search_id or "").strip()
    clean_hotel_type = str(hotel_type or "").strip()
    clean_hotel_id = str(hotel_id or "").strip()
    clean_product_id = str(product_id or "").strip()
    if not clean_search_id:
        raise AppHTTPException(
            status_code=400,
            detail="search_id cannot be empty",
            error_code="RIDECLOW_HOTEL_ORDER_SEARCH_ID_REQUIRED",
        )
    if not clean_hotel_type:
        raise AppHTTPException(
            status_code=400,
            detail="hotel_type cannot be empty",
            error_code="RIDECLOW_HOTEL_ORDER_TYPE_REQUIRED",
        )
    if not clean_hotel_id:
        raise AppHTTPException(
            status_code=400,
            detail="hotel_id cannot be empty",
            error_code="RIDECLOW_HOTEL_ORDER_ID_REQUIRED",
        )
    if not clean_product_id:
        raise AppHTTPException(
            status_code=400,
            detail="product_id cannot be empty",
            error_code="RIDECLOW_HOTEL_ORDER_PRODUCT_ID_REQUIRED",
        )

    request_body = {
        "search_id": clean_search_id,
        "hotel_type": clean_hotel_type,
        "hotel_id": clean_hotel_id,
        "product_id": clean_product_id,
    }

    client = await get_http_client("rideclaw")
    logger.info(
        "RideClaw hotel order snapshot lookup started search_id={} hotel_type={} hotel_id={} product_id={}",
        clean_search_id,
        clean_hotel_type,
        clean_hotel_id,
        clean_product_id,
    )
    try:
        response = await client.post(
            "/apitest/v1/hotel/snapshot/lookup",
            json=request_body,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception(
            "RideClaw hotel order snapshot lookup failed search_id={} hotel_type={} hotel_id={} product_id={}",
            clean_search_id,
            clean_hotel_type,
            clean_hotel_id,
            clean_product_id,
        )
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel order snapshot lookup failed",
            error_code="RIDECLOW_HOTEL_ORDER_SNAPSHOT_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawHotelOrderSnapshotResponse(**payload)
    if raw_response.code != 0:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel order snapshot lookup returned an error",
            error_code="RIDECLOW_HOTEL_ORDER_SNAPSHOT_ERROR",
            error_detail=payload,
        )

    parsed_data = _parse_snapshot_data(raw_response.data)
    if parsed_data is None:
        raise AppHTTPException(
            status_code=404,
            detail="RideClaw hotel order snapshot data is empty or invalid",
            error_code="RIDECLOW_HOTEL_ORDER_SNAPSHOT_EMPTY",
            error_detail=payload,
        )

    logger.info(
        "RideClaw hotel order snapshot lookup succeeded search_id={} hotel_type={} hotel_id={} product_id={}",
        clean_search_id,
        clean_hotel_type,
        clean_hotel_id,
        clean_product_id,
    )
    response_payload = MCPToolResponse(data=parsed_data).model_dump()
    response_payload["assistant_response_instruction"] = (
        constants.ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_HOTEL_ORDER
    )
    return response_payload


__all__ = [
    "create_pending_payment_hotel_order",
]
