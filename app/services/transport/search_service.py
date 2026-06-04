"""Transport search services."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

import httpx
from loguru import logger

from core.http.exceptions import AppHTTPException
from core.infra.http_client import get_http_client
from schema.mcp import MCPToolResponse
from schema.transport import (
    RawAggregatedTransportSearchResponse,
    RawTransportGeocodeResponse,
)

DEFAULT_TRANSPORT_MODES = ["flight", "train", "bus"]
VALID_TRANSPORT_MODES = set(DEFAULT_TRANSPORT_MODES)
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 20
ALL_MODE_HINT = (
    "all 模式返回聚合概览，不支持分页；如需查看更多某类交通结果，"
    "请使用 modes='flight'、modes='train' 或 modes='bus' 单独查询。"
)


def _auth_headers(user_token: str | None) -> dict[str, str] | None:
    token = str(user_token or "").strip()
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def _normalize_modes(modes: str | list[str] | None) -> list[str]:
    if modes is None:
        values: list[Any] = list(DEFAULT_TRANSPORT_MODES)
    elif isinstance(modes, str):
        text = modes.strip()
        if not text:
            values = list(DEFAULT_TRANSPORT_MODES)
        elif text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise AppHTTPException(
                    status_code=400,
                    detail="modes must be a JSON array or a list",
                    error_code="RIDECLOW_TRANSPORT_SEARCH_INVALID_MODES",
                    error_detail={"modes": modes},
                ) from exc
            values = parsed
        else:
            values = [item.strip() for item in text.split(",")]
    else:
        values = modes

    if not values:
        raise AppHTTPException(
            status_code=400,
            detail="modes cannot be empty",
            error_code="RIDECLOW_TRANSPORT_SEARCH_EMPTY_MODES",
        )

    normalized: list[str] = []
    invalid: list[Any] = []
    for value in values:
        if not isinstance(value, str):
            invalid.append(value)
            continue
        mode = value.strip()
        if mode not in VALID_TRANSPORT_MODES:
            invalid.append(value)
            continue
        if mode not in normalized:
            normalized.append(mode)

    if invalid:
        raise AppHTTPException(
            status_code=400,
            detail="modes only supports flight, train, bus",
            error_code="RIDECLOW_TRANSPORT_SEARCH_INVALID_MODES",
            error_detail={"invalid_modes": invalid},
        )
    return normalized


def _normalize_page(value: int | str | None) -> int:
    try:
        page = int(value) if value is not None else DEFAULT_PAGE
    except (TypeError, ValueError):
        return DEFAULT_PAGE
    return max(page, 1)


def _normalize_page_size(value: int | str | None) -> int:
    try:
        page_size = int(value) if value is not None else DEFAULT_PAGE_SIZE
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE
    if page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


def _paginate_items(
    items: list[Any],
    page: int,
    page_size: int,
) -> tuple[list[Any], dict[str, Any]]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paged_items = items[start:end]
    return paged_items, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "returned": len(paged_items),
        "has_more": end < total,
    }


def _adjust_latest_arrival_time(latest_arrival_time: str | None) -> str | None:
    if not latest_arrival_time:
        return None
    try:
        arrival_time = datetime.strptime(latest_arrival_time.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        logger.warning("Invalid latest_arrival_time format, passing through value={}", latest_arrival_time)
        return latest_arrival_time
    adjusted_time = arrival_time - timedelta(hours=1)
    return adjusted_time.strftime("%Y-%m-%d %H:%M")


def _pick_fields(source: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: source.get(field) for field in fields if field in source}


def _filter_train_data(
    train_data: dict[str, Any],
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    trains = train_data.get("trains") or []
    page_meta = None
    if page is not None and page_size is not None:
        trains, page_meta = _paginate_items(trains, page, page_size)
    filtered_trains = []
    for train in trains:
        if not isinstance(train, dict):
            continue
        filtered_train = _pick_fields(
            train,
            [
                "trainCode",
                "trainNo",
                "fromStation",
                "toStation",
                "fromDateTime",
                "toDateTime",
                "arrive_days",
                "runTime",
                "trainsTypeName",
            ],
        )
        seats = train.get("Seats") or []
        if seats:
            filtered_train["Seats"] = [
                _pick_fields(seat, ["seatTypeName", "ticketPrice", "leftTicketNum"])
                for seat in seats
                if isinstance(seat, dict)
            ]
        filtered_trains.append(filtered_train)
    return {"trains": filtered_trains}, page_meta


def _filter_flight_data(
    flight_data: dict[str, Any],
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    filtered_data = _pick_fields(flight_data, ["search_token"])
    flights = flight_data.get("flights") or []
    page_meta = None
    if page is not None and page_size is not None:
        flights, page_meta = _paginate_items(flights, page, page_size)
    filtered_flights = []
    for flight in flights:
        if not isinstance(flight, dict):
            continue
        filtered_flight = _pick_fields(flight, ["flightId"])
        filtered_trips = []
        for trip in flight.get("trips") or []:
            if not isinstance(trip, dict):
                continue
            filtered_trip: dict[str, Any] = {}
            filtered_segments = []
            for segment in trip.get("segments") or []:
                if not isinstance(segment, dict):
                    continue
                filtered_segment = _pick_fields(
                    segment,
                    [
                        "airlineName",
                        "airlineCode",
                        "flightNumber",
                        "aircraft",
                        "depCityName",
                        "depAirportName",
                        "depTerminal",
                        "depDate",
                        "depTime",
                        "arrCityName",
                        "arrAirportName",
                        "arrTerminal",
                        "arrDate",
                        "arrTime",
                        "stopCount",
                    ],
                )
                stop_infos = segment.get("stopInfos") or []
                if stop_infos:
                    filtered_segment["stopInfos"] = [
                        _pick_fields(stop, ["city_name", "stop_time"])
                        if isinstance(stop, dict)
                        else stop
                        for stop in stop_infos
                    ]
                filtered_segments.append(filtered_segment)
            filtered_trip["segments"] = filtered_segments
            filtered_trips.append(filtered_trip)
        filtered_flight["trips"] = filtered_trips

        fare_summaries = []
        for fare in flight.get("cabinFares") or []:
            if not isinstance(fare, dict):
                continue
            cabin_fare_id = fare.get("cabinFareId", "")
            cabin_name = fare.get("cabinName", "")
            cabin = fare.get("cabin", "")
            booking_class = fare.get("bookingClass", "")
            seat = fare.get("seat", "")
            fare_line = f"cabin_fare_id={cabin_fare_id}, 舱位={cabin_name}({cabin})"
            if booking_class:
                fare_line += f" 订座级别={booking_class}"
            if seat:
                fare_line += f" 余座={seat}"

            passenger_fare_parts = []
            for passenger_fare in fare.get("passengerFares") or []:
                if not isinstance(passenger_fare, dict):
                    continue
                passenger_type = passenger_fare.get("passengerType", "")
                total = passenger_fare.get("total", 0)
                base_fare = passenger_fare.get("baseFare", 0)
                airport_tax = passenger_fare.get("airportTax", 0)
                oil_tax = passenger_fare.get("oilTax", 0)
                passenger_fare_parts.append(
                    f"{passenger_type}: 总价¥{total} (票面¥{base_fare}+机建¥{airport_tax}+燃油¥{oil_tax})"
                )
            if passenger_fare_parts:
                fare_line += " | " + "; ".join(passenger_fare_parts)
            fare_summaries.append(fare_line)
        if fare_summaries:
            filtered_flight["fare_summary"] = fare_summaries
        filtered_flights.append(filtered_flight)
    filtered_data["flights"] = filtered_flights
    return filtered_data, page_meta


def _filter_bus_data(
    bus_data: dict[str, Any],
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    buses = bus_data.get("buses") or []
    page_meta = None
    if page is not None and page_size is not None:
        buses, page_meta = _paginate_items(buses, page, page_size)
    filtered_buses = []
    for bus in buses:
        if not isinstance(bus, dict):
            continue
        filtered_bus = _pick_fields(
            bus,
            [
                "line_name",
                "start_station_name",
                "start_city_name",
                "start_addr",
                "end_station_name",
                "end_city_name",
                "end_addr",
                "start_distance_text",
                "end_distance_text",
            ],
        )
        class_day_list = bus.get("class_day_list") or []
        if class_day_list:
            filtered_bus["class_day_list"] = [
                _pick_fields(
                    schedule,
                    [
                        "gid",
                        "class_time",
                        "price",
                        "discount_price",
                        "avail_seat_count",
                    ],
                )
                for schedule in class_day_list
                if isinstance(schedule, dict)
            ]
        filtered_buses.append(filtered_bus)
    return {"buses": filtered_buses}, page_meta


def _filter_errors(errors: Any) -> list[dict[str, Any]]:
    if not isinstance(errors, list):
        return []
    return [
        _pick_fields(error, ["mode", "error"])
        for error in errors
        if isinstance(error, dict)
    ]


def _filter_aggregated_transport_data(
    data: Any,
    requested_modes: list[str] | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> Any:
    if not isinstance(data, dict):
        return data

    filtered_data = _pick_fields(data, ["from_city", "to_city", "date", "search_id"])
    requested_modes = requested_modes or list(DEFAULT_TRANSPORT_MODES)
    should_paginate = len(requested_modes) == 1
    normalized_page = _normalize_page(page)
    normalized_page_size = _normalize_page_size(page_size)
    errors = _filter_errors(data.get("errors"))
    if errors:
        filtered_data["errors"] = errors

    train_data = data.get("train_data")
    if "train" in requested_modes and isinstance(train_data, dict):
        filtered_data["train_data"], train_page_meta = _filter_train_data(
            train_data,
            normalized_page if should_paginate else None,
            normalized_page_size if should_paginate else None,
        )
        if train_page_meta is not None:
            filtered_data["pagination"] = {"mode": "train", **train_page_meta}
    flight_data = data.get("flight_data")
    if "flight" in requested_modes and isinstance(flight_data, dict):
        filtered_data["flight_data"], flight_page_meta = _filter_flight_data(
            flight_data,
            normalized_page if should_paginate else None,
            normalized_page_size if should_paginate else None,
        )
        if flight_page_meta is not None:
            filtered_data["pagination"] = {"mode": "flight", **flight_page_meta}
    bus_data = data.get("bus_data")
    if "bus" in requested_modes and isinstance(bus_data, dict):
        filtered_data["bus_data"], bus_page_meta = _filter_bus_data(
            bus_data,
            normalized_page if should_paginate else None,
            normalized_page_size if should_paginate else None,
        )
        if bus_page_meta is not None:
            filtered_data["pagination"] = {"mode": "bus", **bus_page_meta}
    if not should_paginate:
        filtered_data["hints"] = [ALL_MODE_HINT]
    return filtered_data


async def _geocode_address(
    address: str,
    is_cn: bool,
    field_name: str,
    user_token: str | None,
) -> dict[str, Any]:
    clean_address = str(address or "").strip()
    if not clean_address:
        raise AppHTTPException(
            status_code=400,
            detail=f"{field_name} cannot be empty",
            error_code="RIDECLOW_TRANSPORT_GEOCODE_ADDRESS_REQUIRED",
            error_detail={"field_name": field_name},
        )

    client = await get_http_client("rideclaw")
    try:
        response = await client.post(
            "/apitest/v1/tool/geocode",
            json={"address": clean_address, "is_cn": is_cn},
            headers=_auth_headers(user_token),
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("RideClaw transport geocode request failed field={} address={}", field_name, clean_address)
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw transport geocode failed",
            error_code="RIDECLOW_TRANSPORT_GEOCODE_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawTransportGeocodeResponse(**payload)
    if raw_response.code != 0:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw transport geocode returned an error",
            error_code="RIDECLOW_TRANSPORT_GEOCODE_ERROR",
            error_detail=payload,
        )
    if not raw_response.data:
        raise AppHTTPException(
            status_code=404,
            detail="RideClaw transport geocode returned no data",
            error_code="RIDECLOW_TRANSPORT_GEOCODE_EMPTY",
            error_detail=payload,
        )
    if raw_response.data.get("lng") is None or raw_response.data.get("lat") is None:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw transport geocode returned invalid coordinates",
            error_code="RIDECLOW_TRANSPORT_GEOCODE_INVALID",
            error_detail=payload,
        )
    return raw_response.data


async def search_aggregated_transport(
    date: str,
    from_name: str,
    to_name: str,
    is_cn: bool,
    earliest_departure_time: str | None = None,
    latest_arrival_time: str | None = None,
    user_token: str | None = None,
    modes: str | list[str] | None = None,
    page: int | str | None = None,
    page_size: int | str | None = None,
) -> dict[str, Any]:
    """Search aggregated transport options through RideClaw."""

    from_point, to_point = await asyncio.gather(
        _geocode_address(
            address=from_name,
            is_cn=is_cn,
            field_name="from_name",
            user_token=user_token,
        ),
        _geocode_address(
            address=to_name,
            is_cn=is_cn,
            field_name="to_name",
            user_token=user_token,
        ),
    )

    request_body: dict[str, Any] = {
        "date": date,
        "from_lat": str(from_point.get("lat")),
        "from_lng": str(from_point.get("lng")),
        "from_name": str(from_point.get("formatted_address") or from_name).strip(),
        "to_lat": str(to_point.get("lat")),
        "is_cn": is_cn,
        "to_lng": str(to_point.get("lng")),
        "to_name": str(to_point.get("formatted_address") or to_name).strip(),
        "modes": _normalize_modes(modes),
    }
    if earliest_departure_time:
        request_body["earliest_departure_time"] = earliest_departure_time
    adjusted_latest_arrival_time = _adjust_latest_arrival_time(latest_arrival_time)
    if adjusted_latest_arrival_time:
        request_body["latest_arrival_time"] = adjusted_latest_arrival_time

    client = await get_http_client("rideclaw")
    logger.info(
        "RideClaw aggregated transport search started date={} from_name={} to_name={}",
        date,
        from_name,
        to_name,
    )
    try:
        response = await client.post(
            "/apitest/v1/transport/search",
            json=request_body,
            headers=_auth_headers(user_token),
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception(
            "RideClaw aggregated transport search failed date={} from_name={} to_name={}",
            date,
            from_name,
            to_name,
        )
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw aggregated transport search failed",
            error_code="RIDECLOW_TRANSPORT_SEARCH_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawAggregatedTransportSearchResponse(**payload)
    if raw_response.code != 0:
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw aggregated transport search returned an error",
            error_code="RIDECLOW_TRANSPORT_SEARCH_ERROR",
            error_detail=payload,
        )

    logger.info(
        "RideClaw aggregated transport search succeeded date={} from_name={} to_name={}",
        date,
        from_name,
        to_name,
    )
    return MCPToolResponse(
        data=_filter_aggregated_transport_data(
            raw_response.data,
            requested_modes=request_body["modes"],
            page=_normalize_page(page),
            page_size=_normalize_page_size(page_size),
        )
    ).model_dump()


__all__ = [
    "search_aggregated_transport",
]
