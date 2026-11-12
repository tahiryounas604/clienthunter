import json
from pathlib import Path

import pytest

from clienthunter.importer import load_places_file, parse_places

FIXTURE = Path(__file__).parent / "fixtures" / "places_fixture.json"


def test_parse_places_fixture():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    businesses = parse_places(data)
    assert len(businesses) == 2  # nameless entry skipped
    pizza = businesses[0]
    assert pizza.name == "Places Pizza"
    assert pizza.lat == 31.51 and pizza.lon == 74.35
    assert pizza.phone == "+92 300 9999999"
    assert pizza.category == "restaurant"
    assert pizza.source == "places"
    assert pizza.source_id == "plc-1"


def test_parse_places_weekday_text_hours():
    businesses = parse_places(json.loads(FIXTURE.read_text(encoding="utf-8")))
    salon = businesses[1]
    assert salon.website == "https://salonpro.example.com"
    assert "Monday: 9 AM" in salon.opening_hours
    assert salon.address  # vicinity / formatted_address fallback present


def test_parse_bare_list_and_businesses_key():
    item = {"name": "Solo Gym", "lat": 1.0, "lng": 2.0, "category": "gym"}
    assert parse_places([item])[0].name == "Solo Gym"
    assert parse_places({"businesses": [item]})[0].lon == 2.0


def test_parse_places_rejects_unknown_shape():
    with pytest.raises(ValueError):
        parse_places({"unexpected": 1})


def test_load_places_file(tmp_path):
    target = tmp_path / "p.json"
    target.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    assert len(load_places_file(str(target))) == 2
