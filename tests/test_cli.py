import csv
import io
import json
from pathlib import Path

from clienthunter.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_hunt_offline_fixture_score_export(tmp_path, capsys):
    leads = tmp_path / "leads.json"
    rc = main(["hunt", "--file", str(FIXTURES / "overpass_fixture.json"),
               "--out", str(leads)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dedup: 5 -> 4" in out
    data = json.loads(leads.read_text(encoding="utf-8"))
    assert len(data) == 4
    assert all(d["opportunity_score"] is not None for d in data)
    # best lead first
    assert data[0]["name"] == "Ghost Salon"
    assert data[0]["opportunity_score"] == 100

    csv_path = tmp_path / "leads.csv"
    md_path = tmp_path / "report.md"
    rc = main(["export", str(leads), "--csv", str(csv_path), "--md", str(md_path)])
    assert rc == 0
    rows = list(csv.DictReader(io.StringIO(csv_path.read_text(encoding="utf-8"))))
    assert len(rows) == 4
    assert "Ghost Salon" in md_path.read_text(encoding="utf-8")


def test_cli_import_places(tmp_path, capsys):
    leads = tmp_path / "leads.json"
    rc = main(["import", str(FIXTURES / "places_fixture.json"), "--out", str(leads)])
    assert rc == 0
    data = json.loads(leads.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert {d["name"] for d in data} == {"Places Pizza", "Places Salon Pro"}


def test_cli_hunt_places_file(tmp_path):
    leads = tmp_path / "leads.json"
    rc = main(["hunt", "--places-file", str(FIXTURES / "places_fixture.json"),
               "--out", str(leads)])
    assert rc == 0
    assert len(json.loads(leads.read_text(encoding="utf-8"))) == 2


def test_cli_score_rescores(tmp_path):
    leads = tmp_path / "leads.json"
    leads.write_text(json.dumps([{"name": "Bare Bones"}]), encoding="utf-8")
    rc = main(["score", str(leads)])
    assert rc == 0
    data = json.loads(leads.read_text(encoding="utf-8"))
    assert data[0]["opportunity_score"] == 100
    assert data[0]["opportunity_level"] == "high"


def test_cli_hunt_requires_scope(capsys):
    rc = main(["hunt", "--out", "unused.json"])
    assert rc == 2
    assert "needs --city or --bbox" in capsys.readouterr().err


def test_cli_export_requires_format(tmp_path):
    leads = tmp_path / "leads.json"
    leads.write_text("[]", encoding="utf-8")
    rc = main(["export", str(leads)])
    assert rc == 2
