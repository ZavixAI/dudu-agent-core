"""Hotel search services."""

import json
from typing import Any

import httpx
from loguru import logger

from config import constants
from core.http.exceptions import AppHTTPException
from core.infra.http_client import get_http_client
from schema.hotel import RawHotelGeocodeResponse, RawHotelSearchResponse
from schema.mcp import MCPToolResponse

NULL_STRINGS = {"none", "null", "undefined"}
HOTEL_FILTER_TAGS = {
    "has_wifi",
    "has_parking",
    "has_swimming_pool",
    "has_gymnasium",
    "has_dining_room",
    "has_board_room",
    "has_spa",
    "has_airport_shuttle",
    "has_child_facility",
    "has_business_center",
    "has_laundry",
    "has_24h_front_desk",
    "has_ev_charging",
    "has_bar",
}


def _is_nullish(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        return not text or text.lower() in NULL_STRINGS
    return False


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
            logger.warning("Ignored invalid hotel star level value={}", item)
    return result or None


def _parse_optional_str_list(value: Any) -> list[str] | None:
    if _is_nullish(value):
        return None
    if isinstance(value, list):
        result = [str(item).strip() for item in value if not _is_nullish(item)]
        return result or None

    text = str(value).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                result = [str(item).strip() for item in parsed if not _is_nullish(item)]
                return result or None
        except json.JSONDecodeError:
            logger.warning("Failed to parse string list JSON, fallback to comma split value={}", text)
    result = [item.strip() for item in text.split(",") if not _is_nullish(item)]
    return result or None


def _parse_tags(tags: Any) -> list[str] | None:
    parsed_tags = _parse_optional_str_list(tags)
    if not parsed_tags:
        return None
    return [tag for tag in parsed_tags if tag in HOTEL_FILTER_TAGS] or None


def _auth_headers(user_token: str | None) -> dict[str, str] | None:
    token = str(user_token or "").strip()
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def _build_hotel_filters(
    min_price: float | None,
    max_price: float | None,
    star_levels: list[int] | None,
    hotel_brand: str | None,
    min_review_score: float | None,
    max_distance_km: float | None,
    tags: list[str] | None,
) -> dict[str, Any] | None:
    filters: dict[str, Any] = {}
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if star_levels:
        filters["star_levels"] = star_levels
    if hotel_brand:
        filters["hotel_brand"] = hotel_brand
    if min_review_score is not None:
        filters["min_review_score"] = min_review_score
    if max_distance_km is not None:
        filters["max_distance_km"] = max_distance_km
    for tag in tags or []:
        filters[tag] = True
    return filters or None


def _compact_hotel_location(location: Any) -> dict[str, Any] | None:
    if not isinstance(location, dict):
        return None

    latitude = location.get("latitude") or location.get("lat")
    longitude = location.get("longitude") or location.get("lng")
    result = {}
    if not _is_nullish(latitude):
        result["latitude"] = latitude
    if not _is_nullish(longitude):
        result["longitude"] = longitude
    return result or None


def _compact_hotel_item(hotel: Any) -> dict[str, Any]:
    if not isinstance(hotel, dict):
        return {}

    supplier = hotel.get("supplier") or hotel.get("source")
    compact = {
        "hotel_id": hotel.get("hotel_id", ""),
        "supplier": supplier or "",
        "source": hotel.get("source") or supplier or "",
        "hotel_name": hotel.get("hotel_name", ""),
        "brand_name": hotel.get("brand_name", ""),
        "address": hotel.get("address", ""),
        "district": hotel.get("district", ""),
        "business_zone": hotel.get("business_zone", ""),
        "star_rating": hotel.get("star_rating", 0),
        "review_score": hotel.get("review_score", 0),
        "review_count": hotel.get("review_count", 0),
        "min_price": hotel.get("min_price", 0),
        "currency": hotel.get("currency", "CNY"),
        "main_picture": hotel.get("main_picture", ""),
        "phone": hotel.get("phone", ""),
        "has_wifi": hotel.get("has_wifi"),
        "has_parking": hotel.get("has_parking"),
        "has_restaurant": hotel.get("has_restaurant"),
        "has_breakfast": hotel.get("has_breakfast"),
    }

    location = _compact_hotel_location(hotel.get("location"))
    if location:
        compact["location"] = location

    description = hotel.get("description", "")
    if description and len(str(description)) <= 100:
        compact["description"] = description

    return compact


def _compact_search_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    hotels = data.get("hotels")
    if hotels is None:
        hotels = data.get("content", [])
    if not isinstance(hotels, list):
        hotels = []

    return {
        "search_id": data.get("search_id", ""),
        "total_count": data.get("total_count", data.get("total", len(hotels))),
        "hotels": [_compact_hotel_item(hotel) for hotel in hotels],
    }


async def _geocode_destination(
    destination: str,
    is_cn: bool,
    user_token: str | None,
) -> dict[str, Any]:
    client = await get_http_client("rideclaw")
    try:
        response = await client.post(
            "/apitest/v1/tool/geocode",
            json={"address": destination, "is_cn": is_cn},
            headers=_auth_headers(user_token),
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("RideClaw hotel geocode request failed destination={}", destination)
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel geocode failed",
            error_code="RIDECLOW_HOTEL_GEOCODE_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawHotelGeocodeResponse(**payload)
    if raw_response.code != 0:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel geocode returned an error",
            error_code="RIDECLOW_HOTEL_GEOCODE_ERROR",
            error_detail=payload,
        )
    if not raw_response.data:
        raise AppHTTPException(
            status_code=404,
            detail="RideClaw hotel geocode returned no data",
            error_code="RIDECLOW_HOTEL_GEOCODE_EMPTY",
            error_detail=payload,
        )

    lng = raw_response.data.get("lng")
    lat = raw_response.data.get("lat")
    if _is_nullish(lng) or _is_nullish(lat):
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel geocode returned invalid coordinates",
            error_code="RIDECLOW_HOTEL_GEOCODE_INVALID",
            error_detail=payload,
        )

    return raw_response.data


async def search_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    room_count: int = 1,
    adult_count: int = 2,
    sort_by: str | None = None,
    min_price: float | str | None = None,
    max_price: float | str | None = None,
    star_levels: str | list[int] | None = None,
    hotel_types: str | list[str] | None = None,
    hotel_brand: str | None = None,
    min_review_score: float | str | None = None,
    max_distance_km: float | str | None = None,
    tags: str | list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    is_cn: bool = True,
    user_token: str | None = None,
) -> dict[str, Any]:
    """Search hotels through RideClaw aggregated hotel APIs."""

    clean_destination = str(destination or "").strip()
    if not clean_destination:
        raise AppHTTPException(
            status_code=400,
            detail="destination cannot be empty",
            error_code="RIDECLOW_HOTEL_SEARCH_DESTINATION_REQUIRED",
        )

    geocode_data = await _geocode_destination(
        destination=clean_destination,
        is_cn=is_cn,
        user_token=user_token,
    )
    parsed_tags = _parse_tags(tags)
    filters = _build_hotel_filters(
        min_price=_parse_optional_float(min_price),
        max_price=_parse_optional_float(max_price),
        star_levels=_parse_optional_int_list(star_levels),
        hotel_brand=str(hotel_brand).strip() if not _is_nullish(hotel_brand) else None,
        min_review_score=_parse_optional_float(min_review_score),
        max_distance_km=_parse_optional_float(max_distance_km),
        tags=parsed_tags,
    )

    request_body: dict[str, Any] = {
        "destination": geocode_data.get("formatted_address") or clean_destination,
        "longitude": _parse_optional_float(geocode_data.get("lng")),
        "latitude": _parse_optional_float(geocode_data.get("lat")),
        "check_in": check_in,
        "check_out": check_out,
        "room_count": _parse_int(room_count, 1),
        "adult_count": _parse_int(adult_count, 2),
        "page": _parse_int(page, 1),
        "page_size": _parse_int(page_size, 10),
    }
    adcode = geocode_data.get("adcode")
    if not _is_nullish(adcode):
        request_body["adcode"] = str(adcode).strip()
    if sort_by:
        request_body["sort_by"] = sort_by
    parsed_hotel_types = _parse_optional_str_list(hotel_types)
    if parsed_hotel_types:
        request_body["hotel_types"] = parsed_hotel_types
    if filters:
        request_body["filters"] = filters

    client = await get_http_client("rideclaw")
    logger.info(
        "RideClaw hotel search started destination={} check_in={} check_out={}",
        clean_destination,
        check_in,
        check_out,
    )
    try:
        response = await client.post(
            "/apitest/v1/hotel/search-aggregated",
            json=request_body,
            headers=_auth_headers(user_token),
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("RideClaw hotel search request failed destination={}", clean_destination)
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel search failed",
            error_code="RIDECLOW_HOTEL_SEARCH_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawHotelSearchResponse(**payload)
    if raw_response.code != 0:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw hotel search returned an error",
            error_code="RIDECLOW_HOTEL_SEARCH_ERROR",
            error_detail=payload,
        )

    logger.info("RideClaw hotel search succeeded destination={}", clean_destination)
    response_payload = MCPToolResponse(data=_compact_search_data(raw_response.data)).model_dump()
    response_payload["next_action_suggestions"] = (
        constants.NEXT_ACTION_SUGGESTIONS_FOR_HOTEL_SEARCH
    )
    return response_payload


__all__ = [
    "search_hotels",
]
