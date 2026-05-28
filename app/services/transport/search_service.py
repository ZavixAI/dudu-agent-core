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


def _filter_train_data(train_data: dict[str, Any]) -> dict[str, Any]:
    trains = train_data.get("trains") or []
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
    return {"trains": filtered_trains}


def _filter_flight_data(flight_data: dict[str, Any]) -> dict[str, Any]:
    filtered_data = _pick_fields(flight_data, ["search_token"])
    filtered_flights = []
    for flight in flight_data.get("flights") or []:
        if not isinstance(flight, dict):
            continue
        filtered_flight = _pick_fields(flight, ["flightId"])
        filtered_trips = []
        for trip in flight.get("trips") or []:
            if not isinstance(trip, dict):
                continue
            filtered_trip = _pick_fields(trip, ["depAirportCode", "arrAirportCode"])
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
                        "depCityCode",
                        "depAirportName",
                        "depAirportCode",
                        "depTerminal",
                        "depDate",
                        "depTime",
                        "arrCityName",
                        "arrCityCode",
                        "arrAirportName",
                        "arrAirportCode",
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

        cabin_fares = []
        for fare in flight.get("cabinFares") or []:
            if not isinstance(fare, dict):
                continue
            filtered_fare = _pick_fields(
                fare,
                ["cabinFareId", "cabin", "cabinName", "bookingClass", "seat"],
            )
            passenger_fares = fare.get("passengerFares") or []
            if passenger_fares:
                filtered_fare["passengerFares"] = [
                    _pick_fields(
                        passenger_fare,
                        ["passengerType", "total", "baseFare", "airportTax", "oilTax"],
                    )
                    for passenger_fare in passenger_fares
                    if isinstance(passenger_fare, dict)
                ]
            cabin_fares.append(filtered_fare)
        filtered_flight["cabinFares"] = cabin_fares
        filtered_flights.append(filtered_flight)
    filtered_data["flights"] = filtered_flights
    return filtered_data


def _filter_bus_data(bus_data: dict[str, Any]) -> dict[str, Any]:
    filtered_buses = []
    for bus in (bus_data.get("buses") or [])[:5]:
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
                        "duration",
                        "distance",
                    ],
                )
                for schedule in class_day_list
                if isinstance(schedule, dict)
            ]
        filtered_buses.append(filtered_bus)
    return {"buses": filtered_buses}


def _filter_errors(errors: Any) -> list[dict[str, Any]]:
    if not isinstance(errors, list):
        return []
    return [
        _pick_fields(error, ["mode", "error"])
        for error in errors
        if isinstance(error, dict)
    ]


def _filter_aggregated_transport_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    filtered_data = _pick_fields(data, ["from_city", "to_city", "date", "search_id"])
    errors = _filter_errors(data.get("errors"))
    if errors:
        filtered_data["errors"] = errors

    train_data = data.get("train_data")
    if isinstance(train_data, dict):
        filtered_data["train_data"] = _filter_train_data(train_data)
    flight_data = data.get("flight_data")
    if isinstance(flight_data, dict):
        filtered_data["flight_data"] = _filter_flight_data(flight_data)
    bus_data = data.get("bus_data")
    if isinstance(bus_data, dict):
        filtered_data["bus_data"] = _filter_bus_data(bus_data)
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
    return MCPToolResponse(data=_filter_aggregated_transport_data(raw_response.data)).model_dump()


__all__ = [
    "search_aggregated_transport",
]
