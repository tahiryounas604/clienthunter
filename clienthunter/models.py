"""Core data model for clienthunter."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Business:
    name: str
    category: str = ""
    lat: float | None = None
    lon: float | None = None
    website: str = ""
    phone: str = ""
    email: str = ""
    opening_hours: str = ""
    address: str = ""
    city: str = ""
    source: str = ""          # "overpass" or "places"
    source_id: str = ""       # osm id / place_id
    opportunity_score: int | None = None
    opportunity_level: str = ""
    reasons: list[str] = field(default_factory=list)

    @property
    def has_website(self) -> bool:
        return bool(self.website.strip())

    @property
    def website_is_https(self) -> bool:
        return self.website.strip().lower().startswith("https://")

    def completeness(self) -> int:
        """Number of populated contact/detail fields (used by dedup)."""
        fields = [self.website, self.phone, self.email,
                  self.opening_hours, self.address, self.category]
        return sum(1 for f in fields if str(f).strip())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Business":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})
