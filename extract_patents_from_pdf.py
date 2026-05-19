"""
Parse Stanford AI Index 2025 Chapter 1 Figure 1.2.3 country-level AI patent rates.

The chart "Granted AI patents per 100,000 inhabitants by country, 2023" lists the
top-15 countries by per-capita rate. The 15 (country_name, rate) pairs are extracted
from the cached `data/raw/stanford_aiindex_2025_ch1.txt` (pdftotext output of the
public report PDF at https://hai.stanford.edu/assets/files/hai_ai-index-report-2025_chapter1_final.pdf).

The extraction is bounded between the figure caption "Granted AI patents per
100,000 inhabitants by country, 2023" and the next "Figure 1.2.4" marker, so it
will not pick up neighbouring chart data.

Prerequisite: pdftotext extracted text at `data/raw/stanford_aiindex_2025_ch1.txt`.

Run:  python extract_patents_from_pdf.py
Produces: data/raw/stanford_ai_patents_2025.csv
   columns: country_name, iso3, ai_patents_per_100k, year
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pycountry

ROOT = Path(__file__).parent
TXT = ROOT / "data" / "raw" / "stanford_aiindex_2025_ch1.txt"
OUT = ROOT / "data" / "raw" / "stanford_ai_patents_2025.csv"

CAPTION = "Granted AI patents per 100,000 inhabitants by country, 2023"
END_MARKER = "Figure 1.2.4"

# Country names Stanford writes in non-pycountry-friendly form
ISO3_OVERRIDES: dict[str, str] = {
    "South Korea": "KOR",
    "United States": "USA",
    "United Kingdom": "GBR",
}

# A row in the chart-data block looks like:
#   <country name>  <whitespace>  <rate>
# where the rate is a positive decimal. The country name is one to three
# capitalised words (e.g. "Japan", "South Korea", "United Arab Emirates"). The
# whitespace separator varies from a single space for short-rate rows (e.g.
# "Denmark 0.47") to a large block of spaces for the chart's top entries
# (e.g. "South Korea ............... 17.27"), so the regex requires only
# `\s+` and relies on the bounded chunk between the Fig 1.2.3 caption and
# the Figure 1.2.4 marker to avoid false positives. The 1-3 word ceiling
# accommodates "United Arab Emirates" should it ever appear in Stanford's
# top-15; rates trailing a numeric ratio column (e.g. "+12.5%") are stripped
# by anchoring on `\d+\.\d+$` so the rate is the last token on the line.
ROW_RE = re.compile(r"^([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\s+(\d+\.\d+)$")


def to_iso3(name: str) -> str | None:
    """Resolve a country name to ISO 3166-1 alpha-3 via overrides + pycountry."""
    if name in ISO3_OVERRIDES:
        return ISO3_OVERRIDES[name]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None


def parse() -> pd.DataFrame:
    """Extract Stanford Fig 1.2.3 country-rate pairs from the cached PDF text."""
    if not TXT.exists():
        raise FileNotFoundError(
            f"{TXT} not found. Run `pdftotext -layout "
            f"data/raw/stanford_aiindex_2025_ch1.pdf "
            f"data/raw/stanford_aiindex_2025_ch1.txt` first."
        )
    text = TXT.read_text(encoding="utf-8", errors="replace")
    start = text.find(CAPTION)
    if start < 0:
        raise RuntimeError(
            f"Caption '{CAPTION}' not found in {TXT}. The Stanford PDF layout "
            "may have changed; re-verify against the source PDF before re-running."
        )
    end = text.find(END_MARKER, start)
    if end < 0:
        raise RuntimeError(
            f"End marker '{END_MARKER}' not found after caption. Cannot bound "
            "the chart-data block."
        )
    chunk = text[start:end]
    rows: list[dict[str, str | int | float | None]] = []
    for line in chunk.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        name, rate = m.group(1), float(m.group(2))
        iso3 = to_iso3(name)
        if iso3 is None:
            print(f"[WARN] No ISO3 mapping for '{name}'", file=sys.stderr)
        rows.append(
            {
                "country_name": name,
                "iso3": iso3,
                "ai_patents_per_100k": rate,
                "year": 2023,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Extract the Stanford Fig 1.2.3 country rates and write to CSV."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    df = parse()
    expected = 15
    if len(df) != expected:
        raise RuntimeError(
            f"Stanford Fig 1.2.3 extractor expected {expected} country-rate pairs "
            f"(top-15) but got {len(df)}. The PDF layout may have changed; "
            "re-verify the chunk boundaries (CAPTION / END_MARKER) and the ROW_RE "
            "country-name token count before re-running. Refusing to overwrite "
            f"{OUT} with a partial extract."
        )
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Parsed {len(df)} country-rate pairs from Stanford Fig 1.2.3.")
    print(f"Wrote {OUT}")
    print()
    print("Top-15 AI-patent rates (per 100,000 inhabitants, 2023):")
    print(df.to_string(index=False))

    # Sanity check on the 14 middle powers — note 7 are below Stanford's cutoff
    middle_powers = [
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
        "EUU",
        "TWN",
    ]
    in_top15 = df[df["iso3"].isin(middle_powers)][
        ["iso3", "country_name", "ai_patents_per_100k"]
    ]
    print()
    print(f"Middle-power coverage in Stanford's top-15 ({len(in_top15)}/14):")
    print(in_top15.to_string(index=False))
    missing = [m for m in middle_powers if m not in set(df["iso3"])]
    if missing:
        print(f"\nMiddle powers below Stanford's top-15 cutoff: {sorted(missing)}")
        print(
            "(These countries enter the C4 indicator as NaN and are imputed by "
            "the §7 axis-mean fallback in the notebook.)"
        )


if __name__ == "__main__":
    main()
