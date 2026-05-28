"""Hotel search schemas."""

from typing import Any

from pydantic import BaseModel, Field


class RawHotelGeocodeResponse(BaseModel):
    """Raw RideClaw geocode response for hotel search."""

    code: int
    message: str = ""
    data: dict[str, Any] | None = None


class RawHotelSearchResponse(BaseModel):
    """Raw RideClaw hotel search response."""

    code: int
    message: str = ""
    data: Any = Field(default_factory=list)


__all__ = [
    "RawHotelGeocodeResponse",
    "RawHotelSearchResponse",
]
