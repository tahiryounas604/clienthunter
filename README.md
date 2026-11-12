# clienthunter

Business lead discovery for web developers and agencies: find businesses
with **weak or no web presence** — the ones most likely to need a website.

It pulls businesses from OpenStreetMap via the free Overpass API (no API
key), scores each one by how much of its online presence is missing, and
exports a ranked lead list as CSV and Markdown.

## Features

- **Overpass source** — businesses by `--city` name or `--bbox`, in 15
  friendly categories (`restaurant`, `cafe`, `salon`, `gym`, `hotel`,
  `pharmacy`, `dentist`, `shop`, …) mapped to OSM tags. Nodes and ways
  (via `center`) are both parsed; `website`/`contact:website`,
  `phone`/`contact:phone`, `email`/`contact:email`, `opening_hours` and
  `addr:*` tags are all read.
- **Places-style JSON importer** — `{"results": [...]}`,
  `{"businesses": [...]}` or a bare list, with `geometry.location`,
  `formatted_phone_number`, `opening_hours.weekday_text`, etc.
- **Opportunity scoring** — documented formula below; every score carries
  human-readable reasons.
- **De-duplication** — by normalised name + location (~111 m grid), or
  name + city when a business has no coordinates; the most complete
  duplicate record wins.
- **Export** — ranked CSV (15 columns) and a Markdown report with
  high/medium/low counts.
- **Offline-friendly** — `hunt --file saved-overpass.json` replays a
  recorded Overpass response with no network at all.

## Opportunity score

Max 100 points — higher means a better lead (weaker web presence):

| Signal | Points |
|---|---:|
| No website | +50 |
| Website present but http-only (no HTTPS) | +25 |
| Website with HTTPS | +0 |
| No phone listed | +20 |
| No opening hours listed | +15 |
| No email listed | +10 |
| No street address listed | +5 |

Levels: **high** ≥ 70, **medium** 40–69, **low** < 40.

## Install

Python 3.11+ only. No third-party runtime dependencies — standard
library only (pytest is used for the tests).

```bash
git clone https://github.com/tahiryounas604/clienthunter.git
cd clienthunter
# optional: install as a command
pip install --break-system-packages .
```

## Usage

```bash
# Live hunt: cafes in Lahore (Overpass, free, no key)
python3 clienthunter.py hunt --city Lahore --category cafe --out leads.json

# Live hunt by bounding box (south,west,north,east)
python3 clienthunter.py hunt --bbox 31.520,74.355,31.525,74.365 --category restaurant

# Offline: replay a saved Overpass response
python3 clienthunter.py hunt --file tests/fixtures/overpass_fixture.json --out leads.json

# Import Places-style JSON instead
python3 clienthunter.py import places.json --out leads.json
python3 clienthunter.py hunt --places-file places.json --out leads.json

# (Re)score an existing leads file
python3 clienthunter.py score leads.json

# Export ranked leads
python3 clienthunter.py export leads.json --csv leads.csv --md report.md
```

Leads files are plain JSON lists, so the steps compose:
`hunt`/`import` → `score` → `export`.

Example output (from the recorded fixture, fully offline):

```
parsed 5 businesses from tests/fixtures/overpass_fixture.json
dedup: 5 -> 4
wrote 4 scored leads to leads.json
 100  high    Ghost Salon [shop=hairdresser] website=NO
  35  low     Http Cafe [amenity=cafe] website=yes
  25  low     No Website Noodles [amenity=restaurant] website=yes
   0  low     Modern Bites [amenity=restaurant] website=yes
```

## Architecture

```
clienthunter/
├── models.py     Business dataclass (+ completeness used by dedup)
├── overpass.py   category map, Overpass QL builder, response parser, fetcher
├── importer.py   Places-style JSON -> Business
├── scoring.py    the documented opportunity formula + levels
├── dedup.py      normalised name + rounded-location keys
├── export.py     CSV + Markdown writers
└── cli.py        hunt / import / score / export subcommands
clienthunter.py   top-level entry point shim
tests/            offline tests + recorded fixtures (Overpass & Places JSON)
```

## Tests

```bash
python3 -m pytest -q
```

39 tests, all offline: Overpass parsing on a recorded fixture (nodes,
ways with `center`, `contact:*` fallbacks, unnamed POIs skipped), query
building for city and bbox, Places importer shapes, every scoring rule
and level boundary, dedup (including the fixture's duplicate pair),
CSV/Markdown export, and the CLI end to end
(hunt-from-fixture → score → export, plus error paths).

## HONEST LIMITS

- **Scores measure OSM/Places data completeness, not ground truth.** A
  business with no `website` tag in OpenStreetMap may still have a
  website that nobody mapped. Verify a lead before pitching.
- **Coverage is only as good as OpenStreetMap in that area.** Some
  cities are mapped densely, others barely at all; an empty result
  means "not in OSM", not "no businesses".
- **Live Overpass needs network access** to `overpass-api.de` and the
  public instance is rate-limited / can be slow for large areas; keep
  bboxes small. A live smoke in the build environment (small Lahore
  bbox, category `cafe`, 2026-11-12) did succeed — 1 named business
  returned ("Cafe Nataliya", opportunity score 95, no website) — but it
  took ~53 seconds through the egress proxy, so expect slow responses
  and prefer the `--file` replay path for development.
- **City lookup depends on an OSM administrative boundary** with a
  matching `name` tag; if a city name does not resolve, use `--bbox`.
- **No website checking is performed** — clienthunter never fetches a
  business's website, so an http-only site that redirects to HTTPS
  still scores +25, and a dead website still counts as "has website".
- **Dedup is name+location only** — two different branches with the
  same name inside one ~111 m grid cell would collapse; differently
  spelled names for the same business will not.
- Respect OpenStreetMap / Overpass usage policies and local rules on
  contacting businesses (spam laws) — this tool finds leads, it does
  not send outreach.

## Author

Tahir Younas — Tytechlabs — https://www.linkedin.com/in/tahiryounas604

## License

GPL-3.0 — see `LICENSE`.
