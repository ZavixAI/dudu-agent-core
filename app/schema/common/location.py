"""Location-related schemas."""

from typing import Any

from pydantic import BaseModel, Field


class LocationCandidate(BaseModel):
    """A place candidate normalized for display and downstream tool use."""

    name: str = Field(description="Place name.")
    address: str = Field(default="", description="Place address.")
    province: str = Field(default="", description="Province name.")
    city: str = Field(default="", description="City name.")
    area: str = Field(default="", description="District or county name.")
    lng: float = Field(description="Longitude.")
    lat: float = Field(description="Latitude.")
    adcode: str = Field(default="", description="Administrative division code.")

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "LocationCandidate":
        """Keep only the fields needed by the location display format."""

        return cls(
            name=raw.get("name", ""),
            address=raw.get("address", ""),
            province=raw.get("province", ""),
            city=raw.get("city", ""),
            area=raw.get("area", ""),
            lng=raw.get("lng"),
            lat=raw.get("lat"),
            adcode=raw.get("adcode", ""),
        )

    @property
    def region_text(self) -> str:
        """Return province/city/area as a slash-separated region string."""

        return "/".join(part for part in (self.province, self.city, self.area) if part)

    def to_display_text(self, index: int) -> str:
        """Render one candidate in the user-facing location format."""

        lines = [f"{index}. {self.name}"]
        if self.address:
            lines.append(f"   地址: {self.address}")
        if self.region_text:
            lines.append(f"   区域: {self.region_text}")
        lines.append(f"   坐标: {self.lng},{self.lat}")
        if self.adcode:
            lines.append(f"   行政区划代码: {self.adcode}")
        return "\n".join(lines)


class LocationSearchResult(BaseModel):
    """Normalized location search result."""

    locations: list[LocationCandidate] = Field(default_factory=list)

    @classmethod
    def from_raw_response(cls, response: "RawLocationSearchResponse") -> "LocationSearchResult":
        """Build a normalized result from the raw RideClaw response."""

        return cls(locations=[LocationCandidate.from_raw(item) for item in response.data])

    def to_display_text(self) -> str:
        """Render all candidates in a readable numbered list."""

        lines = [f"找到 {len(self.locations)} 个地点:", "-" * 60]
        for index, location in enumerate(self.locations[:10], start=1):
            lines.append(location.to_display_text(index))
            lines.append("")
        return "\n".join(lines).strip()


class RawLocationSearchResponse(BaseModel):
    """Raw RideClaw location search response."""

    code: int
    message: str = ""
    data: list[dict[str, Any]] = Field(default_factory=list)
