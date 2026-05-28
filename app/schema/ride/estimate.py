"""Ride estimate schemas."""

from typing import Any

from pydantic import BaseModel


class RawRideEstimateResponse(BaseModel):
    """Raw RideClaw estimate response."""

    code: int
    message: str = ""
    data: Any = None


__all__ = [
    "RawRideEstimateResponse",
]
