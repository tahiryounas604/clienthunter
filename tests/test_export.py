import csv
import io

from clienthunter.export import to_csv, to_markdown, write_csv, write_markdown
from clienthunter.models import Business
from clienthunter.scoring import score_all


def sample():
    return score_all([
        Business(name="Ghost Salon", category="shop=hairdresser"),
        Business(name="Modern Bites", category="amenity=restaurant",
                 website="https://m.example.com", phone="1", email="a@b.c",
                 opening_hours="Mo 9-5", address="1 Street"),
    ])


def test_csv_structure_and_values():
    text = to_csv(sample())
    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == 2
    assert rows[0]["name"] == "Ghost Salon"  # highest score first (score_all order)
    assert rows[0]["opportunity_score"] == "100"
    assert rows[0]["opportunity_level"] == "high"
    assert "no website" in rows[0]["reasons"]
    assert rows[1]["opportunity_score"] == "0"


def test_csv_header():
    first = to_csv(sample()).splitlines()[0]
    assert first.startswith("name,category,opportunity_score,opportunity_level")


def test_markdown_report():
    md = to_markdown(sample())
    assert md.startswith("# ClientHunter report")
    assert "Businesses: **2**" in md
    assert "high opportunity: **1**" in md
    assert "Ghost Salon" in md and "Modern Bites" in md
    assert "| 100 | high |" in md


def test_markdown_empty():
    md = to_markdown([])
    assert "No businesses found." in md


def test_markdown_escapes_pipes():
    md = to_markdown(score_all([Business(name="A | B Cafe")]))
    assert "A \\| B Cafe" in md


def test_write_files(tmp_path):
    csv_path = tmp_path / "out.csv"
    md_path = tmp_path / "out.md"
    write_csv(sample(), str(csv_path))
    write_markdown(sample(), str(md_path))
    assert "Ghost Salon" in csv_path.read_text(encoding="utf-8")
    assert "Ghost Salon" in md_path.read_text(encoding="utf-8")
