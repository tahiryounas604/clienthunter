import json
from pathlib import Path

from clienthunter.dedup import dedup, dedup_key, normalise_name
from clienthunter.models import Business
from clienthunter.overpass import parse_overpass

FIXTURE = Path(__file__).parent / "fixtures" / "overpass_fixture.json"


def test_normalise_name():
    assert normalise_name("  Joe's Pizza!! ") == "joe s pizza"
    assert normalise_name("CAFE   Mocha") == "cafe mocha"


def test_dedup_same_name_and_location():
    a = Business(name="Cafe Mocha", lat=31.52041, lon=74.35871)
    b = Business(name="cafe mocha!", lat=31.52044, lon=74.35874,
                 website="https://mocha.example.com")
    result = dedup([a, b])
    assert len(result) == 1
    assert result[0].website == "https://mocha.example.com"  # more complete kept


def test_dedup_different_location_kept():
    a = Business(name="Cafe Mocha", lat=31.52, lon=74.35)
    b = Business(name="Cafe Mocha", lat=32.50, lon=74.50)
    assert len(dedup([a, b])) == 2


def test_dedup_no_coords_uses_city():
    a = Business(name="Gym X", city="Lahore")
    b = Business(name="Gym X", city="Lahore", phone="123")
    c = Business(name="Gym X", city="Karachi")
    result = dedup([a, b, c])
    assert len(result) == 2


def test_dedup_fixture_duplicate_pair():
    businesses = parse_overpass(json.loads(FIXTURE.read_text(encoding="utf-8")))
    result = dedup(businesses)
    # two "No Website Noodles" records at the same spot collapse to one
    assert len(result) == 4
    kept = [b for b in result if b.name == "No Website Noodles"][0]
    # the richer duplicate (website+email+hours) wins
    assert kept.website == "http://nowebsitenoodles.example.com"


def test_dedup_key_rounding():
    a = Business(name="X", lat=31.52041, lon=74.35871)
    b = Business(name="X", lat=31.52044, lon=74.35874)
    assert dedup_key(a) == dedup_key(b)
