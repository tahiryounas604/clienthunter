"""De-duplication by normalised name + location."""
from __future__ import annotations

import re

from .models import Business

_PUNCT = re.compile(r"[^a-z0-9 ]+")


def normalise_name(name: str) -> str:
    text = _PUNCT.sub(" ", name.lower())
    return re.sub(r"\s+", " ", text).strip()


def dedup_key(biz: Business):
    name = normalise_name(biz.name)
    if biz.lat is not None and biz.lon is not None:
        # ~3 decimal places ~= 111 m grid cell
        return (name, round(float(biz.lat), 3), round(float(biz.lon), 3))
    return (name, (biz.city or biz.address).strip().lower(), None)


def dedup(businesses: list[Business]) -> list[Business]:
    """Collapse duplicates, keeping the most complete record per key."""
    best: dict = {}
    order: list = []
    for biz in businesses:
        key = dedup_key(biz)
        if key not in best:
            best[key] = biz
            order.append(key)
        elif biz.completeness() > best[key].completeness():
            best[key] = biz
    return [best[k] for k in order]
