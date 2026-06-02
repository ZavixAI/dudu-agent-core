"""Hotel room services."""

from __future__ import annotations

import json
from typing import Any

import httpx
from loguru import logger

from config import constants
from core.http.exceptions import AppHTTPException
from core.infra.http_client import get_http_client
from schema.hotel import RawHotelRoomFilterResponse
from schema.mcp import MCPToolResponse

NULL_STRINGS = {"none", "null", "undefined"}


def _is_nullish(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        return not text or text.lower() in NULL_STRINGS
    return False


def _parse_optional_str(value: Any) -> str | None:
    if _is_nullish(value):
        return None
    text = str(value).strip()
    return text or None


def _parse_optional_float(value: Any) -> float | None:
    if _is_nullish(value):
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_int(value: Any, default: int) -> int:
    if _is_nullish(value):
        return default
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _parse_optional_int_list(value: Any) -> list[int] | None:
    if _is_nullish(value):
        return None
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                value = text
        else:
            value = [item.strip() for item in text.split(",")]
    elif not isinstance(value, list):
        value = [value]

    result = []
    for item in value:
        if _is_nullish(item):
            continue
        try:
            result.append(int(float(str(item).strip())))
        except ValueError:
            logger.warning("Ignored invalid hotel child age value={}", item)
    return result or None


def _auth_headers(user_token: str | None) -> dict[str, str] | None:
    token = str(user_token or "").strip()
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _price_value(product: dict[str, Any]) -> float:
    try:
        return float(product.get("price"))
    except (TypeError, ValueError):
        return float("inf")


def _choose_recommended_product(products: list[Any]) -> dict[str, Any]:
    valid_products = [product for product in products if isinstance(product, dict)]
    if not valid_products:
        return {}
    return min(valid_products, key=_price_value)


def _compact_room_info(room_info: Any) -> dict[str, Any]:
    if not isinstance(room_info, dict):
        return {}
    return {
        "room_id": room_info.get("room_id", ""),
        "room_name": room_info.get("room_name", ""),
        "room_name_en": room_info.get("room_name_en", ""),
        "bed_type_tag": room_info.get("bed_type_tag", ""),
        "bed_desc": room_info.get("bed_desc", ""),
        "window_type_tag": room_info.get("window_type_tag", ""),
        "area_min": room_info.get("area_min"),
        "area_max": room_info.get("area_max"),
        "floor_info": room_info.get("floor_info", ""),
        "max_occupancy": room_info.get("max_occupancy"),
        "has_wifi": room_info.get("has_wifi"),
        "allow_extra_bed": room_info.get("allow_extra_bed"),
        "smoke_policy": room_info.get("smoke_policy", ""),
        "main_picture": room_info.get("main_picture", ""),
    }


def _compact_price_range(price_range: Any) -> dict[str, Any]:
    if not isinstance(price_range, dict):
        return {}
    return {
        "min": price_range.get("min"),
        "max": price_range.get("max"),
    }


def _compact_product(product: dict[str, Any], fallback_room_id: Any) -> dict[str, Any]:
    return {
        "product_id": product.get("product_id", ""),
        "room_id": product.get("room_id") or fallback_room_id,
        "product_name": product.get("product_name", ""),
        "price": product.get("price", 0),
        "inventory": product.get("inventory", 0),
        "breakfast": product.get("breakfast", ""),
        "cancel_rule_type": product.get("cancel_rule_type"),
        "cancel_rule_desc": product.get("cancel_rule_desc", ""),
        "is_refundable": product.get("is_refundable"),
        "pay_type": product.get("pay_type"),
    }


def _compact_room_group(group: Any) -> dict[str, Any]:
    if not isinstance(group, dict):
        return {}

    room_info = _compact_room_info(group.get("room_type_info"))
    price_range = _compact_price_range(group.get("price_range"))
    products = group.get("products") or []
    if not isinstance(products, list):
        products = []
    product_count = group.get("product_count")
    if product_count is None:
        product_count = len(products)
    product_count_num = _to_int(product_count, len(products))
    recommended_product = _choose_recommended_product(products)

    compact: dict[str, Any] = {
        "room_type_info": room_info,
        "price_range": price_range,
        "product_count": product_count,
    }
    if recommended_product:
        compact["recommended_product"] = _compact_product(
            recommended_product,
            room_info.get("room_id", ""),
        )
        compact["other_product_count"] = max(product_count_num - 1, 0)
    return compact


def _compact_room_filter_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    room_groups = data.get("room_groups") or []
    if not isinstance(room_groups, list):
        room_groups = []

    total_count = data.get("total_count")
    if _is_nullish(total_count):
        total_count = sum(
            _to_int(group.get("product_count"), len(group.get("products") or []))
            for group in room_groups
            if isinstance(group, dict)
        )

    return {
        "search_id": data.get("search_id", ""),
        "supplier": data.get("supplier") or data.get("hotel_type", ""),
        "hotel_type": data.get("hotel_type") or data.get("supplier", ""),
        "hotel_id": data.get("hotel_id", ""),
        "hotel_name": data.get("hotel_name", ""),
        "hotel_main_picture": data.get("hotel_main_picture") or data.get("main_picture", ""),
        "currency": data.get("currency", "CNY"),
        "total_count": total_count,
        "total_group_count": len(room_groups),
        "room_groups": [_compact_room_group(group) for group in room_groups[:12]],
    }


async def filter_hotel_rooms(
    hotel_type: str,
    hotel_id: str,
    check_in: str,
    check_out: str,
    search_id: str | None = None,
    room_count: int = 1,
    adult_count: int = 2,
    child_count: int = 0,
    child_ages: str | list[int] | None = None,
    min_price: str | int | float | None = None,
    max_price: str | int | float | None = None,
    product_type: int = 3,
    user_token: str | None = None,
) -> dict[str, Any]:
    """Filter available hotel rooms through RideClaw."""

    clean_hotel_type = str(hotel_type or "").strip()
    clean_hotel_id = str(hotel_id or "").strip()
    if not clean_hotel_type:
        raise AppHTTPException(
            status_code=400,
            detail="hotel_type cannot be empty",
            error_code="RIDECLOW_HOTEL_ROOM_TYPE_REQUIRED",
        )
    if not clean_hotel_id:
        raise AppHTTPException(
            status_code=400,
            detail="hotel_id cannot be empty",
            error_code="RIDECLOW_HOTEL_ROOM_ID_REQUIRED",
        )

    parsed_min = _parse_optional_float(min_price)
    parsed_max = _parse_optional_float(max_price)
    request_body: dict[str, Any] = {
        "hotel_type": clean_hotel_type,
        "hotel_id": clean_hotel_id,
        "check_in": check_in,
        "check_out": check_out,
        "room_count": _parse_int(room_count, 1),
        "adult_count": _parse_int(adult_count, 2),
        "child_count": _parse_int(child_count, 0),
        "child_ages": _parse_optional_int_list(child_ages) or [],
        "product_type": _parse_int(product_type, 3),
        "need_detail": True,
    }
    parsed_search_id = _parse_optional_str(search_id)
    if parsed_search_id:
        request_body["search_id"] = parsed_search_id
    if parsed_min is not None:
        request_body["min_price"] = int(parsed_min)
    if parsed_max is not None:
        request_body["max_price"] = int(parsed_max)

    client = await get_http_client("rideclaw")
    logger.info(
        "RideClaw hotel room filter started hotel_type={} hotel_id={}",
        clean_hotel_type,
        clean_hotel_id,
    )
    try:
        response = await client.post(
            "/apitest/v1/hotel/filter-rooms",
            json=request_body,
            headers=_auth_headers(user_token),
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception(
            "RideClaw hotel room filter request failed hotel_type={} hotel_id={}",
            clean_hotel_type,
            clean_hotel_id,
        )
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel room filter failed",
            error_code="RIDECLOW_HOTEL_ROOM_FILTER_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawHotelRoomFilterResponse(**payload)
    if raw_response.code != 0:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel room filter returned an error",
            error_code="RIDECLOW_HOTEL_ROOM_FILTER_ERROR",
            error_detail=payload,
        )

    logger.info(
        "RideClaw hotel room filter succeeded hotel_type={} hotel_id={}",
        clean_hotel_type,
        clean_hotel_id,
    )
    return MCPToolResponse(data=_compact_room_filter_data(raw_response.data)).model_dump()


__all__ = [
    "filter_hotel_rooms",
]
