"""Hotel-related schemas."""

from schema.hotel.order import RawHotelOrderSnapshotResponse
from schema.hotel.room import RawHotelRoomFilterResponse
from schema.hotel.search import RawHotelGeocodeResponse, RawHotelSearchResponse

__all__ = [
    "RawHotelOrderSnapshotResponse",
    "RawHotelRoomFilterResponse",
    "RawHotelGeocodeResponse",
    "RawHotelSearchResponse",
]
