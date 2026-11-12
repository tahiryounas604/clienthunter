import json
from pathlib import Path

import pytest

from clienthunter.overpass import build_query, parse_bbox, parse_overpass

FIXTURE = Path(__file__).parent / "fixtures" / "overpass_fixture.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_parse_fixture_count_named_only():
    businesses = parse_overpass(load_fixture())
    # 5 named elements; the unnamed restaurant node is skipped
    assert len(businesses) == 5
    assert all(b.name for b in businesses)


def test_parse_node_fields():
    businesses = {b.name: b for b in parse_overpass(load_fixture())}
    modern = businesses["Modern Bites"]
    assert modern.website == "https://modernbites.example.com"
    assert modern.phone == "+92 300 3333333"
    assert modern.email == "hi@modernbites.example.com"
    assert modern.opening_hours == "Mo-Su 09:00-23:00"
    assert modern.category == "amenity=restaurant"
    assert modern.source == "overpass"
    assert modern.source_id == "node/103"
    assert "MM Alam Road" in modern.address
    assert modern.city == "Lahore"


def test_parse_contact_fallback_tags():
    businesses = {b.name: b for b in parse_overpass(load_fixture())}
    cafe = businesses["Http Cafe"]
    assert cafe.phone == "+92 300 2222222"       # contact:phone
    assert cafe.website == "http://httpcafe.example.com"


def test_parse_way_uses_center():
    businesses = {b.name: b for b in parse_overpass(load_fixture())}
    salon = businesses["Ghost Salon"]
    assert salon.lat == 31.53 and salon.lon == 74.35
    assert salon.category == "shop=hairdresser"
    assert salon.website == "" and salon.phone == ""


def test_parse_empty_response():
    assert parse_overpass({"elements": []}) == []
    assert parse_overpass({}) == []


def test_build_query_bbox():
    q = build_query(bbox=(31.4, 74.2, 31.6, 74.5), category="cafe")
    assert "[out:json]" in q
    assert '"amenity"="cafe"' in q
    assert "(31.4,74.2,31.6,74.5)" in q
    assert "out center tags;" in q


def test_build_query_city():
    q = build_query(city="Lahore", category="salon")
    assert 'area["name"="Lahore"]' in q
    assert '"shop"="hairdresser"' in q
    assert "area.searchArea" in q


def test_build_query_wildcard_category():
    q = build_query(bbox=(0, 0, 1, 1), category="shop")
    assert '["shop"]' in q


def test_build_query_requires_exactly_one_scope():
    with pytest.raises(ValueError):
        build_query()
    with pytest.raises(ValueError):
        build_query(city="Lahore", bbox=(0, 0, 1, 1))


def test_parse_bbox():
    assert parse_bbox("31.4,74.2,31.6,74.5") == (31.4, 74.2, 31.6, 74.5)
    with pytest.raises(ValueError):
        parse_bbox("31.4,74.2")
