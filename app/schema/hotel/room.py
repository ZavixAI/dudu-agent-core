"""Hotel room schemas."""

from typing import Any

from pydantic import BaseModel


class RawHotelRoomFilterResponse(BaseModel):
    """Raw RideClaw hotel room filter response."""

    code: int
    message: str = ""
    data: Any = None


__all__ = [
    "RawHotelRoomFilterResponse",
]
