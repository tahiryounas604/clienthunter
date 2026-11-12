"""Importer for Places-style JSON.

Accepts the shapes commonly produced by Places APIs / exports:

  {"results": [ {...}, ... ]}          (Google Places style)
  {"businesses": [ {...}, ... ]}
  [ {...}, ... ]                        (bare list)

Per-place fields understood (all optional except a name):
  name, place_id, types / category, formatted_address / address / vicinity,
  geometry.location.lat/lng  (or plain lat/lng / latitude/longitude),
  website, formatted_phone_number / phone, email,
  opening_hours.weekday_text / opening_hours (string) / hours
"""
from __future__ import annotations

import json

from .models import Business


def _extract_list(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("results", "businesses", "places", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("unrecognised Places JSON: expected a list or a dict "
                     "with results/businesses/places")


def _hours(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = value.get("weekday_text") or value.get("text") or []
        if isinstance(text, list):
            return "; ".join(str(t) for t in text)
        return str(text)
    return ""


def parse_places(data) -> list[Business]:
    out: list[Business] = []
    for item in _extract_list(data):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        lat = item.get("lat", item.get("latitude"))
        lon = item.get("lng", item.get("lon", item.get("longitude")))
        geom = item.get("geometry") or {}
        loc = geom.get("location") or {} if isinstance(geom, dict) else {}
        if lat is None and isinstance(loc, dict):
            lat, lon = loc.get("lat"), loc.get("lng", loc.get("lon"))
        types = item.get("types") or []
        category = str(item.get("category") or (types[0] if types else "") or "")
        out.append(Business(
            name=name,
            category=category,
            lat=float(lat) if lat is not None else None,
            lon=float(lon) if lon is not None else None,
            website=str(item.get("website") or "").strip(),
            phone=str(item.get("formatted_phone_number") or item.get("phone") or "").strip(),
            email=str(item.get("email") or "").strip(),
            opening_hours=_hours(item.get("opening_hours", item.get("hours", ""))),
            address=str(item.get("formatted_address") or item.get("address")
                        or item.get("vicinity") or "").strip(),
            city=str(item.get("city") or "").strip(),
            source="places",
            source_id=str(item.get("place_id") or item.get("id") or ""),
        ))
    return out


def load_places_file(path: str) -> list[Business]:
    with open(path, encoding="utf-8") as fh:
        return parse_places(json.load(fh))
