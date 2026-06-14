"""
Aggregate the TOP500 supercomputer list into per-country system counts (indicator I4).

The TOP500 project (https://www.top500.org/) publishes, twice a year, the 500 most
powerful non-distributed computer systems, with each system's installation country. The
full list for the 66th edition (November 2025) is downloadable as an Excel workbook at
https://www.top500.org/lists/top500/2025/11/download/TOP500_202511.xlsx and is bundled at
data/raw/top500_2025_11.xlsx. This script counts the installed systems per country
(hosting/installation country, not vendor or owner country), maps each to ISO3, and writes
a clean CSV. The count is M-PAPI indicator I4 (TOP500 compute), the dedicated compute
measure on the Compute-and-Infrastructure-Posture axis; it is hosting-attributed and so is
distinct from C2 (training compute, attributed to the model's organisation country).

Run:  python extract_top500.py
Produces: data/raw/top500_2025.csv  (cols: economy_name, iso3, top500_count, year)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from iso_map import to_iso3

ROOT = Path(__file__).parent
XLSX = ROOT / "data" / "raw" / "top500_2025_11.xlsx"
OUT = ROOT / "data" / "raw" / "top500_2025.csv"
LIST_YEAR = 2025  # data vintage: 66th TOP500 list, November 2025

# Manual ISO3 mapping for TOP500 country labels that pycountry does not resolve cleanly.
ISO3_OVERRIDES = {
    "United States": "USA",
    "South Korea": "KOR",
    "Taiwan": "TWN",
    "Russia": "RUS",
    "Czechia": "CZE",
    "Czech Republic": "CZE",
    "Slovakia": "SVK",
    "Hong Kong": "HKG",
    "United Arab Emirates": "ARE",
    "Turkey": "TUR",
}



def parse() -> pd.DataFrame:
    if not XLSX.exists():
        raise FileNotFoundError(
            f"{XLSX} not found. Download the TOP500 November 2025 list from "
            "https://www.top500.org/lists/top500/2025/11/download/TOP500_202511.xlsx "
            "to that path first (the notebook §4 also fetches it automatically)."
        )
    df = pd.read_excel(XLSX)  # requires openpyxl
    if "Country" not in df.columns:
        raise RuntimeError(
            f"TOP500 workbook has no 'Country' column (found {list(df.columns)[:6]}...); "
            "the export schema likely changed."
        )
    counts = df["Country"].value_counts()
    rows = []
    for name, n in counts.items():
        iso3 = to_iso3(str(name).strip(), ISO3_OVERRIDES)
        if iso3 is None:
            print(f"[WARN] No ISO3 mapping for TOP500 country: {name}", file=sys.stderr)
        rows.append(
            {
                "economy_name": str(name).strip(),
                "iso3": iso3,
                "top500_count": int(n),
                "year": LIST_YEAR,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    df = parse()
    total = int(df["top500_count"].sum())
    print(f"Parsed {len(df)} countries; {total} systems total.")
    _TOP500_TOTAL = 500
    if total != _TOP500_TOTAL:
        raise RuntimeError(
            f"TOP500 extractor aggregated {total} systems but the list has exactly "
            f"{_TOP500_TOTAL}. The workbook or its 'Country' column likely changed; "
            f"refusing to overwrite {OUT} with a partial/incorrect extract."
        )
    unmapped = df[df["iso3"].isna()]
    if len(unmapped):
        raise RuntimeError(
            f"{len(unmapped)} TOP500 country label(s) did not map to ISO3 "
            f"({unmapped['economy_name'].tolist()}); add them to ISO3_OVERRIDES before "
            "writing, so the EU-member sum and per-country counts stay complete."
        )
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Wrote {OUT}")
    # Coverage check against the 13 standalone middle powers ITU/TOP500 report at the
    # economy level (EU is built in the notebook §5.2 as the sum of member states).
    target = [
        "GBR", "CAN", "FRA", "DEU", "JPN", "IND", "ISR",
        "SGP", "KOR", "SWE", "SAU", "ARE", "TWN",
    ]
    s = df.set_index("iso3")["top500_count"]
    print("\nMiddle-power TOP500 system counts (Nov 2025):")
    for iso3 in target:
        print(f"  {iso3}: {int(s.get(iso3, 0))}")


if __name__ == "__main__":
    main()
