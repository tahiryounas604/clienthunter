"""CSV and Markdown report export."""
from __future__ import annotations

import csv
import io

from .models import Business

CSV_FIELDS = ["name", "category", "opportunity_score", "opportunity_level",
              "website", "phone", "email", "opening_hours", "address",
              "city", "lat", "lon", "source", "source_id", "reasons"]


def to_csv(businesses: list[Business]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for biz in businesses:
        row = biz.to_dict()
        row["reasons"] = "; ".join(biz.reasons)
        writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})
    return buf.getvalue()


def write_csv(businesses: list[Business], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(to_csv(businesses))


def to_markdown(businesses: list[Business], title: str = "ClientHunter report") -> str:
    high = sum(1 for b in businesses if b.opportunity_level == "high")
    med = sum(1 for b in businesses if b.opportunity_level == "medium")
    low = sum(1 for b in businesses if b.opportunity_level == "low")
    lines = [f"# {title}", "",
             f"Businesses: **{len(businesses)}** — high opportunity: **{high}**, "
             f"medium: **{med}**, low: **{low}**.", ""]
    if not businesses:
        lines.append("No businesses found.")
        return "\n".join(lines) + "\n"
    lines += ["| Score | Level | Name | Category | Website | Phone | Why |",
              "|------:|-------|------|----------|---------|-------|-----|"]
    for b in businesses:
        why = "; ".join(b.reasons)
        def esc(s) -> str:
            return str(s or "").replace("|", "\\|")
        lines.append(f"| {b.opportunity_score if b.opportunity_score is not None else ''} "
                     f"| {esc(b.opportunity_level)} | {esc(b.name)} | {esc(b.category)} "
                     f"| {esc(b.website)} | {esc(b.phone)} | {esc(why)} |")
    lines.append("")
    return "\n".join(lines)


def write_markdown(businesses: list[Business], path: str,
                   title: str = "ClientHunter report") -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(to_markdown(businesses, title=title))
