"""Location domain services."""
from typing import Any

import httpx

from core.http.exceptions import AppHTTPException
from core.infra.http_client import get_http_client
from loguru import logger
from schema.mcp import MCPToolResponse
from schema.common.location import LocationSearchResult, RawLocationSearchResponse

async def search_location(
    query: str,
    region: str,
    radius: int = 200,
) -> dict[str, Any]:
    """Search locations through the shared RideClaw HTTP client."""

    client = await get_http_client("rideclaw")
    logger.info(
        "RideClaw location search started query={} region={} radius={}",
        query,
        region,
        radius,
    )

    try:
        response = await client.post(
            "/api/v1/tool/place/search",
            json={
                "query": query,
                "region": region,
                "radius": radius,
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception(
            "RideClaw location search request failed query={} region={} radius={}",
            query,
            region,
            radius,
        )
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw location search failed",
            error_code="RIDECLOW_LOCATION_SEARCH_FAILED",
            error_detail=str(exc),
        ) from exc

    payload = response.json()
    raw_response = RawLocationSearchResponse(**payload)
    if raw_response.code != 0:
        logger.warning(
            "RideClaw location search returned error query={} region={} radius={} code={} message={}",
            query,
            region,
            radius,
            raw_response.code,
            raw_response.message,
        )
        raise AppHTTPException(
            status_code=502,
            detail="RideClaw location search returned an error",
            error_code="RIDECLOW_LOCATION_SEARCH_ERROR",
            error_detail=payload,
        )
    if not raw_response.data:
        logger.info(
            "RideClaw location search returned no data query={} region={} radius={}",
            query,
            region,
            radius,
        )
        raise AppHTTPException(
            status_code=404,
            detail="RideClaw location search returned no data",
            error_code="RIDECLOW_LOCATION_SEARCH_EMPTY",
            error_detail=payload,
        )

    result = LocationSearchResult.from_raw_response(raw_response)
    logger.info(
        "RideClaw location search succeeded query={} region={} radius={} count={}",
        query,
        region,
        radius,
        len(result.locations),
    )

    return MCPToolResponse(
        data=[location.model_dump() for location in result.locations],
    ).model_dump()


__all__ = [
    "search_location",
]
