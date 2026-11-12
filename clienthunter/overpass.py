"""OpenStreetMap Overpass API source.

Free, no API key. Queries are built as Overpass QL; live fetching uses
urllib from the standard library. Parsing is a pure function over the
JSON response, so it is fully testable offline on recorded fixtures.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .models import Business

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Friendly category name -> (OSM key, OSM value). "*" means any value.
CATEGORIES: dict[str, tuple[str, str]] = {
    "restaurant": ("amenity", "restaurant"),
    "cafe": ("amenity", "cafe"),
    "fast-food": ("amenity", "fast_food"),
    "pharmacy": ("amenity", "pharmacy"),
    "dentist": ("amenity", "dentist"),
    "clinic": ("amenity", "clinic"),
    "bar": ("amenity", "bar"),
    "bakery": ("shop", "bakery"),
    "salon": ("shop", "hairdresser"),
    "gym": ("leisure", "fitness_centre"),
    "hotel": ("tourism", "hotel"),
    "shop": ("shop", "*"),
    "craft": ("craft", "*"),
    "office": ("office", "*"),
    "any": ("amenity", "*"),
}


def category_clause(category: str, area_clause: str) -> str:
    key, value = CATEGORIES.get(category.lower(), ("amenity", category.lower()))
    if value == "*":
        filt = f'["{key}"]'
    else:
        filt = f'["{key}"="{value}"]'
    return (
        f"node{filt}{area_clause};"
        f"way{filt}{area_clause};"
    )


def build_query(city: str | None = None, bbox: tuple[float, float, float, float] | None = None,
                category: str = "restaurant", timeout: int = 60) -> str:
    """Build an Overpass QL query.

    Exactly one of ``city`` / ``bbox`` must be given. ``bbox`` is
    (south, west, north, east) as Overpass expects.
    """
    if bool(city) == bool(bbox):
        raise ValueError("give exactly one of city or bbox")
    if city:
        # Resolve the city name to an OSM area, then search inside it.
        area = f'area["name"="{city}"]["boundary"="administrative"]->.searchArea;'
        scope = "(area.searchArea)"
        return (f"[out:json][timeout:{timeout}];\n{area}\n"
                f"({category_clause(category, scope)});\nout center tags;")
    assert bbox is not None
    s, w, n, e = bbox
    scope = f"({s},{w},{n},{e})"
    return (f"[out:json][timeout:{timeout}];\n"
            f"({category_clause(category, scope)});\nout center tags;")


def parse_bbox(text: str) -> tuple[float, float, float, float]:
    parts = [float(p) for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be 'south,west,north,east'")
    return (parts[0], parts[1], parts[2], parts[3])


def _address_from_tags(tags: dict) -> str:
    parts = []
    if tags.get("addr:housenumber"):
        parts.append(tags["addr:housenumber"])
    if tags.get("addr:street"):
        parts.append(tags["addr:street"])
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    if tags.get("addr:postcode"):
        parts.append(tags["addr:postcode"])
    return " ".join(parts).strip()


def _category_from_tags(tags: dict) -> str:
    for key in ("amenity", "shop", "leisure", "tourism", "craft", "office"):
        if tags.get(key):
            return f"{key}={tags[key]}"
    return ""


def parse_overpass(data: dict) -> list[Business]:
    """Parse an Overpass JSON response dict into Business objects."""
    out: list[Business] = []
    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name:
            continue  # unnamed POIs are not usable leads
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None and isinstance(el.get("center"), dict):
            lat = el["center"].get("lat")
            lon = el["center"].get("lon")
        out.append(Business(
            name=name,
            category=_category_from_tags(tags),
            lat=lat, lon=lon,
            website=(tags.get("website") or tags.get("contact:website") or "").strip(),
            phone=(tags.get("phone") or tags.get("contact:phone") or "").strip(),
            email=(tags.get("email") or tags.get("contact:email") or "").strip(),
            opening_hours=(tags.get("opening_hours") or "").strip(),
            address=_address_from_tags(tags),
            city=(tags.get("addr:city") or "").strip(),
            source="overpass",
            source_id=f"{el.get('type', '')}/{el.get('id', '')}",
        ))
    return out


def fetch_overpass(query: str, url: str = OVERPASS_URL, timeout: int = 90) -> dict:
    """POST the query to Overpass and return the parsed JSON dict."""
    body = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"User-Agent": "clienthunter/0.1 (tytechlabs)",
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https host)
        return json.loads(resp.read().decode("utf-8", "replace"))
