"""Command line interface.

  hunt   --city NAME | --bbox S,W,N,E  [--category CAT] [--out leads.json]
         [--file overpass.json] [--places-file places.json]
  score  leads.json [--out scored.json]
  export leads.json [--csv leads.csv] [--md report.md]
  import places.json [--out leads.json]      (Places-style JSON -> leads file)

Leads files are plain JSON lists of Business dicts, so the three steps
compose: hunt/import -> score -> export.
"""
from __future__ import annotations

import argparse
import json
import sys

from .dedup import dedup
from .export import write_csv, write_markdown
from .importer import load_places_file
from .models import Business
from .overpass import build_query, fetch_overpass, parse_bbox, parse_overpass
from .scoring import score_all


def _load_leads(path: str) -> list[Business]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON list of leads")
    return [Business.from_dict(d) for d in data]


def _save_leads(businesses: list[Business], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([b.to_dict() for b in businesses], fh, indent=2, ensure_ascii=False)


def _print_table(businesses: list[Business]) -> None:
    for b in businesses:
        score = b.opportunity_score if b.opportunity_score is not None else "-"
        print(f"{score:>4}  {b.opportunity_level or '-':<6}  {b.name} "
              f"[{b.category or '?'}] website={'yes' if b.has_website else 'NO'}")


def cmd_hunt(args) -> int:
    businesses: list[Business] = []
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            businesses = parse_overpass(json.load(fh))
        print(f"parsed {len(businesses)} businesses from {args.file}")
    elif args.places_file:
        businesses = load_places_file(args.places_file)
        print(f"imported {len(businesses)} businesses from {args.places_file}")
    else:
        if not args.city and not args.bbox:
            print("error: hunt needs --city or --bbox (or --file/--places-file offline)",
                  file=sys.stderr)
            return 2
        bbox = parse_bbox(args.bbox) if args.bbox else None
        query = build_query(city=args.city, bbox=bbox, category=args.category)
        print(f"querying Overpass for category={args.category} "
              f"({'city=' + args.city if args.city else 'bbox=' + args.bbox}) ...")
        try:
            data = fetch_overpass(query, timeout=args.timeout)
        except Exception as exc:  # network/proxy failures are common; be honest
            print(f"error: Overpass request failed: {exc}", file=sys.stderr)
            return 1
        businesses = parse_overpass(data)
        print(f"Overpass returned {len(businesses)} named businesses")
    before = len(businesses)
    businesses = dedup(businesses)
    if len(businesses) != before:
        print(f"dedup: {before} -> {len(businesses)}")
    businesses = score_all(businesses)
    _save_leads(businesses, args.out)
    print(f"wrote {len(businesses)} scored leads to {args.out}")
    _print_table(businesses[: args.limit])
    return 0


def cmd_import(args) -> int:
    businesses = score_all(dedup(load_places_file(args.places_file)))
    _save_leads(businesses, args.out)
    print(f"imported {len(businesses)} scored leads to {args.out}")
    _print_table(businesses[: args.limit])
    return 0


def cmd_score(args) -> int:
    businesses = score_all(_load_leads(args.leads))
    out = args.out or args.leads
    _save_leads(businesses, out)
    print(f"scored {len(businesses)} leads -> {out}")
    _print_table(businesses[: args.limit])
    return 0


def cmd_export(args) -> int:
    businesses = _load_leads(args.leads)
    if any(b.opportunity_score is None for b in businesses):
        businesses = score_all(businesses)
    else:
        businesses = sorted(businesses,
                              key=lambda b: (-(b.opportunity_score or 0), b.name.lower()))
    wrote = []
    if args.csv:
        write_csv(businesses, args.csv)
        wrote.append(args.csv)
    if args.md:
        write_markdown(businesses, args.md)
        wrote.append(args.md)
    if not wrote:
        print("error: export needs --csv and/or --md", file=sys.stderr)
        return 2
    print(f"exported {len(businesses)} leads to {', '.join(wrote)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="clienthunter",
                                description="Find businesses with weak/no web presence.")
    sub = p.add_subparsers(dest="command", required=True)

    h = sub.add_parser("hunt", help="fetch businesses from Overpass (or an offline file)")
    h.add_argument("--city")
    h.add_argument("--bbox", help="south,west,north,east")
    h.add_argument("--category", default="restaurant")
    h.add_argument("--file", help="offline: parse a saved Overpass JSON response")
    h.add_argument("--places-file", help="offline: import Places-style JSON instead")
    h.add_argument("--out", default="leads.json")
    h.add_argument("--timeout", type=int, default=90)
    h.add_argument("--limit", type=int, default=20)
    h.set_defaults(func=cmd_hunt)

    i = sub.add_parser("import", help="import Places-style JSON into a leads file")
    i.add_argument("places_file")
    i.add_argument("--out", default="leads.json")
    i.add_argument("--limit", type=int, default=20)
    i.set_defaults(func=cmd_import)

    s = sub.add_parser("score", help="(re)score a leads file")
    s.add_argument("leads")
    s.add_argument("--out")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_score)

    e = sub.add_parser("export", help="export a leads file to CSV / Markdown")
    e.add_argument("leads")
    e.add_argument("--csv")
    e.add_argument("--md")
    e.set_defaults(func=cmd_export)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
