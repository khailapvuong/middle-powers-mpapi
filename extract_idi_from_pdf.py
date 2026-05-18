"""
Parse ITU IDI 2024 country scores from the public IDI 2024 report PDF (Table 1).

The official Excel at itu.int/.../IDIDataset.xlsx is auth-gated, but the full report
PDF at https://www.itu.int/dms_pub/itu-d/opb/ind/d-ind-ict_mdd-2024-3-pdf-e.pdf is public
and contains the country scores in Table 1.

This script reads the pdftotext-extracted .txt and writes a clean CSV with columns
(economy_name, iso3, idi_score, idi_2023, year, region, income_group). The notebook's
loader (§4.5 of M-PAPI.ipynb) reads this CSV when the auth-gated official URL fails.

Prerequisite: run `pdftotext -layout data/raw/itu_idi_2024_report.pdf data/raw/itu_idi_2024_report.txt`
first. The notebook also calls this script directly when the report PDF is freshly downloaded.

Run: python extract_idi_from_pdf.py
Produces: data/raw/itu_idi_2024.csv
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pycountry

ROOT = Path(__file__).parent
TXT = ROOT / "data" / "raw" / "itu_idi_2024_report.txt"
OUT = ROOT / "data" / "raw" / "itu_idi_2024.csv"

# Table 1 row pattern. Region code is one of {AFR, AMS, ARB, ASP, CIS, EUR}.
# Income code is one of {HI, UMI, LMI, LI, n.a.}.
# Scores: float "NN.N" or literal "n.a.". A dash or +/-N% trails.
ROW_RE = re.compile(
    r"^(?P<economy>.+?)\s+"
    r"(?P<region>AFR|AMS|ARB|ASP|CIS|EUR)\s+"
    r"(?P<income>HI|UMI|LMI|LI|n\.a\.)\s+"
    r"(?P<idi_2023>n\.a\.|\d+\.\d+)\s+"
    r"(?P<idi_2024>\d+\.\d+)"
)

# Manual ISO3 mapping for ITU economy names that pycountry doesn't resolve cleanly.
ISO3_OVERRIDES = {
    "Bolivia (Plurinational State of)": "BOL",
    "Côte d'Ivoire": "CIV",
    "Czech Republic": "CZE",
    "Dem. Rep. of the Congo": "COD",
    "Congo (Rep. of the)": "COG",
    "Hong Kong, China": "HKG",
    "Iran (Islamic Republic of)": "IRN",
    "Korea (Rep. of)": "KOR",
    "Lao P.D.R.": "LAO",
    "Macao, China": "MAC",
    "Moldova": "MDA",
    "Netherlands (Kingdom of the)": "NLD",
    "North Macedonia": "MKD",
    "Russian Federation": "RUS",
    "Sao Tome and Principe": "STP",
    "Syrian Arab Republic": "SYR",
    "Tanzania": "TZA",
    "Türkiye": "TUR",
    "Venezuela": "VEN",
    "Vanuatu": "VUT",
    "Viet Nam": "VNM",
    "Saint Kitts and Nevis": "KNA",
    "Saint Lucia": "LCA",
    "Saint Vincent and the Grenadines": "VCT",
    "Trinidad and Tobago": "TTO",
    "Yemen": "YEM",
    "Brunei Darussalam": "BRN",
    "Dominican Rep.": "DOM",
    "Palestine": "PSE",
}


def to_iso3(name: str) -> str | None:
    if name in ISO3_OVERRIDES:
        return ISO3_OVERRIDES[name]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None


def parse() -> pd.DataFrame:
    if not TXT.exists():
        raise FileNotFoundError(
            f"{TXT} not found. Run `pdftotext -layout data/raw/itu_idi_2024_report.pdf "
            f"data/raw/itu_idi_2024_report.txt` first."
        )
    text = TXT.read_text(encoding="utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        d = m.groupdict()
        economy = d["economy"].strip()
        # Reject false positives — economy must contain at least one alpha char and not be a header.
        # Range À-ſ covers Latin-1 Supplement + Latin Extended-A (accented characters
        # in country names like "Türkiye", "Côte d'Ivoire").
        if not re.search(r"[A-Za-zÀ-ſ]", economy):
            continue
        if economy.lower().startswith(("table ", "annex ", "figure ")):
            continue
        iso3 = to_iso3(economy)
        rows.append(
            {
                "economy_name": economy,
                "iso3": iso3,
                "idi_score": float(d["idi_2024"]),
                "idi_2023": None if d["idi_2023"] == "n.a." else float(d["idi_2023"]),
                "year": 2024,
                "region": d["region"],
                "income_group": d["income"],
            }
        )
    return pd.DataFrame(rows).drop_duplicates(subset=["economy_name"])


def main() -> None:
    # Force stdout to UTF-8 to allow non-ASCII economy names on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    df = parse()
    print(f"Parsed {len(df)} economies from IDI 2024 Table 1")
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Wrote {OUT}")
    unmapped = df[df["iso3"].isna()]
    if len(unmapped):
        names = unmapped["economy_name"].tolist()
        print(f"Unmapped to ISO3 ({len(unmapped)}): {names}")
    # Sanity check on the 14 middle powers
    target = [
        "GBR",
        "CAN",
        "FRA",
        "DEU",
        "JPN",
        "IND",
        "ISR",
        "SGP",
        "KOR",
        "SWE",
        "SAU",
        "ARE",
        "TWN",
    ]
    sub = df[df["iso3"].isin(target)][["iso3", "economy_name", "idi_score"]]
    print(
        f"\nMiddle-power IDI 2024 coverage ({len(sub)}/13 reported by ITU; EU not in dataset):"
    )
    print(sub.to_string(index=False))
    missing = set(target) - set(sub["iso3"])
    if missing:
        print(f"\nNot in ITU IDI 2024: {sorted(missing)}")
        print(
            "(Notebook will compute EU as member-state aggregate; Taiwan and India remain missing.)"
        )


if __name__ == "__main__":
    main()
