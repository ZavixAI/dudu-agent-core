"""Hotel order schemas."""

from typing import Any

from pydantic import BaseModel


class RawHotelOrderSnapshotResponse(BaseModel):
    """Raw RideClaw hotel order snapshot response."""

    code: int
    message: str = ""
    data: Any = None


__all__ = [
    "RawHotelOrderSnapshotResponse",
]
