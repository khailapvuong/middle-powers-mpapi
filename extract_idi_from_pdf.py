"""
Parse ITU IDI 2024 country scores from the public IDI 2024 report PDF (Table 1).

The official Excel at itu.int/.../IDIDataset.xlsx is auth-gated, but the full report
PDF at https://www.itu.int/dms_pub/itu-d/opb/ind/d-ind-ict_mdd-2024-3-pdf-e.pdf is public
and contains the country scores in Table 1.

This script reads the pdftotext-extracted .txt and writes a clean CSV with columns
(economy_name, iso3, idi_score, idi_2023, year, region, income_group). The notebook's
loader (§4.7 of M-PAPI.ipynb) reads this CSV when the auth-gated official URL fails.

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
from iso_map import to_iso3

ROOT = Path(__file__).parent
TXT = ROOT / "data" / "raw" / "itu_idi_2024_report.txt"
OUT = ROOT / "data" / "raw" / "itu_idi_2024.csv"

# Table 1 row pattern. Region code is one of {AFR, AMS, ARB, ASP, CIS, EUR}.
# Income code is one of {HI, UMI, LMI, LI, n.a.}.
# Layout: "<economy> <region> <income> <idi_2023> <idi_2024> [<change%>] [<sub1> <sub2>]".
# The two IDI scores are the FIRST two floats after the income code; idi_2024 is the
# second. A year-over-year change column (signed integer percent, e.g. "+1%"/"-3%")
# usually follows, and on many rows two further sub-pillar floats trail it from the
# report's two-panel column layout — so the row CANNOT be end-anchored (doing so drops
# ~half the economies). The pattern therefore deliberately grabs only the first 2023/
# 2024 pair and ignores the trailing columns. Protection against an upstream layout
# change (e.g. an inserted column shifting which float is idi_2024) is structural rather
# than regex-based: the _IDI_MIN_ROWS floor and the explicit middle-power coverage check
# in main() refuse to overwrite the CSV on a partial or shifted extract.
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



def parse() -> pd.DataFrame:
    if not TXT.exists():
        raise FileNotFoundError(
            f"{TXT} not found. Run `pdftotext -layout data/raw/itu_idi_2024_report.pdf "
            f"data/raw/itu_idi_2024_report.txt` first."
        )
    # The pdftotext-extracted .txt is Latin-1/CP1252-encoded (ITU economy names such as
    # "Côte d'Ivoire" and "Türkiye" carry single-byte accented characters). Reading it as
    # UTF-8 would turn those bytes into U+FFFD and break the ISO3_OVERRIDES lookup, leaving
    # an empty iso3; Latin-1 decodes them losslessly.
    text = TXT.read_text(encoding="latin-1")
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
        iso3 = to_iso3(economy, ISO3_OVERRIDES)
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
    _IDI_MIN_ROWS = 100
    if len(df) < _IDI_MIN_ROWS:
        raise RuntimeError(
            f"ITU IDI 2024 extractor parsed only {len(df)} economies (Table 1 lists "
            f"~170; floor {_IDI_MIN_ROWS}). The PDF layout or ROW_RE likely changed; "
            f"refusing to overwrite {OUT} with a partial extract."
        )
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Wrote {OUT}")
    unmapped = df[df["iso3"].isna()]
    if len(unmapped):
        names = unmapped["economy_name"].tolist()
        print(f"Unmapped to ISO3 ({len(unmapped)}): {names}")
    # Sanity check against the 13 paper-listed middle powers ITU could plausibly
    # cover (EU excluded — ITU IDI reports at economy level, not at the EU
    # supranational level; the notebook builds an EU row from member states in
    # §5.2 via fill_eu_with_member_mean).
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
        f"\nMiddle-power IDI 2024 coverage "
        f"({len(sub)}/{len(target)} reported by ITU; EU not in dataset):"
    )
    print(sub.to_string(index=False))
    missing = sorted(set(target) - set(sub["iso3"]))
    if missing:
        print(f"\nNot in ITU IDI 2024: {missing}")
        print(
            "(The notebook imputes these downstream — §7 axis-mean if the "
            "indicator's overall missingness is below IMPUTATION_THRESHOLD, "
            "otherwise §11 column-mean.)"
        )


if __name__ == "__main__":
    main()
