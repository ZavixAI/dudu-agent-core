"""Transport order schemas."""

from typing import Any

from pydantic import BaseModel


class RawTransportOrderSnapshotResponse(BaseModel):
    """Raw RideClaw transport order snapshot response."""

    code: int
    message: str = ""
    data: Any = None


__all__ = [
    "RawTransportOrderSnapshotResponse",
]
