"""
Convert evaluated CSV exports into appended entries for all_titles.txt.

Behavior:
- Reads an evaluated CSV (e.g., evaluated_legal_acts_YYYY-MM-DD.csv)
- For each row, takes Title and Category
- Groups by Publication Date and appends new sections at the end of all_titles.txt
- Dedupe: Skips titles that already exist in all_titles.txt (commented or not)
- Formatting rules:
  - Section header per date: "# YYYY-MM-DDT00:00:00 (<N> titles)" followed by "#======================================="
  - Each title line uncommented when Category == RELEVANT; otherwise commented with a leading "# "

Usage:
  uv run python service/src/service/evaluation/csv_to_titles.py \
    --csv service/src/service/evaluation/config/evaluated_legal_acts_2025-09-03.csv \
    --out service/src/service/evaluation/config/all_titles.txt
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set


@dataclass(frozen=True)
class CsvRow:
    publication_date: str  # YYYY-MM-DD
    title: str
    category: str  # RELEVANT | NOT_RELEVANT | other


HEADER_UNDERLINE = "#======================================="


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append evaluated CSV into all_titles.txt format"
    )
    parser.add_argument(
        "--csv",
        required=True,
        type=Path,
        help="Path to evaluated CSV (e.g., service/src/service/evaluation/config/evaluated_legal_acts_YYYY-MM-DD.csv)",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Path to all_titles.txt (e.g., service/src/service/evaluation/config/all_titles.txt)",
    )
    return parser.parse_args()


def read_evaluated_csv(csv_path: Path) -> List[CsvRow]:
    rows: List[CsvRow] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r is None:
                continue
            title = (r.get("Title") or "").strip()
            pub_date = (r.get("Publication Date") or "").strip()
            category = (r.get("Category") or "").strip()
            if not title or not pub_date:
                continue
            rows.append(
                CsvRow(publication_date=pub_date, title=title, category=category)
            )
    return rows


def normalize_title(line: str) -> str:
    """
    Normalize a title line by:
    - stripping leading comment marker if present
    - removing trailing inline note starting with ' #' if present
    - trimming whitespace
    """
    s = line.strip()
    if s.startswith("#"):
        # Remove a single leading '#'
        s = s[1:].lstrip()
    # Cut off inline note beginning with ' #'
    hash_pos = s.find(" #")
    if hash_pos != -1:
        s = s[:hash_pos]
    return s.strip()


def is_date_header(line: str) -> bool:
    s = line.strip()
    return (
        s.startswith("# ")
        and len(s) >= 14
        and s[2:12].count("-") == 2
        and "T00:00:00" in s
    )


def is_underline(line: str) -> bool:
    return line.strip().startswith("#=====")


def collect_existing_titles(lines: Iterable[str]) -> Set[str]:
    existing: Set[str] = set()
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if is_date_header(s) or is_underline(s):
            continue
        # Consider anything else as a possible title line
        normalized = normalize_title(s)
        if normalized:
            existing.add(normalized)
    return existing


def group_by_date(rows: Iterable[CsvRow]) -> Dict[str, List[CsvRow]]:
    grouped: Dict[str, List[CsvRow]] = {}
    for r in rows:
        grouped.setdefault(r.publication_date, []).append(r)
    return grouped


def format_section(date_yyyy_mm_dd: str, rows: List[CsvRow]) -> List[str]:
    # Only include distinct titles within this section to avoid intra-file duplicates
    seen: Set[str] = set()
    deduped: List[CsvRow] = []
    for r in rows:
        if r.title not in seen:
            deduped.append(r)
            seen.add(r.title)

    # Header with UTC midnight timestamp and count
    header = f"# {date_yyyy_mm_dd}T00:00:00 ({len(deduped)} titles)"
    out_lines: List[str] = ["", header, HEADER_UNDERLINE]
    for r in deduped:
        if r.category.upper() == "RELEVANT":
            out_lines.append(r.title)
        else:
            out_lines.append(f"# {r.title}")
    return out_lines


def append_sections(out_path: Path, sections: List[List[str]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if out_path.exists() else "w"
    with out_path.open(mode, encoding="utf-8") as f:
        for sec in sections:
            for line in sec:
                f.write(line + "\n")


def main() -> None:
    args = parse_args()

    csv_rows = read_evaluated_csv(args.csv)
    if not csv_rows:
        print(f"No rows found in {args.csv}")
        return

    existing_lines: List[str] = []
    if args.out.exists():
        existing_lines = args.out.read_text(encoding="utf-8").splitlines()

    existing_titles = collect_existing_titles(existing_lines)

    # Filter out titles that already exist anywhere in the file
    new_rows = [r for r in csv_rows if r.title not in existing_titles]
    if not new_rows:
        print("No new titles to append. All entries already present.")
        return

    grouped = group_by_date(new_rows)
    # Build sections per date in ascending date order for determinism
    sections: List[List[str]] = []
    for date_key in sorted(grouped.keys()):
        sections.append(format_section(date_key, grouped[date_key]))

    append_sections(args.out, sections)
    print(
        f"Appended {sum(len(sec) - 3 for sec in sections)} new titles across {len(sections)} date sections to {args.out}"
    )


if __name__ == "__main__":
    main()
