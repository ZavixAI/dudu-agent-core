"""Transport search schemas."""

from typing import Any

from pydantic import BaseModel, Field


class RawTransportGeocodeResponse(BaseModel):
    """Raw RideClaw geocode response for transport search."""

    code: int
    message: str = ""
    data: dict[str, Any] | None = None


class RawAggregatedTransportSearchResponse(BaseModel):
    """Raw RideClaw aggregated transport search response."""

    code: int
    message: str = ""
    data: Any = Field(default_factory=dict)


__all__ = [
    "RawAggregatedTransportSearchResponse",
    "RawTransportGeocodeResponse",
]
