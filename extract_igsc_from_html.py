"""
Parse the IGSC member roster directly from the IGSC homepage HTML.

The official IGSC member list lives on https://genesynthesisconsortium.org/ in the
#members-section (no separate /members/ URL exists; that path returns 404). This script
extracts every member firm via a regex over the page HTML and joins each to a curated
HQ-country lookup. The lookup is provenance-tracked: each firm cites the page on the
firm's own website (or Bloomberg/LinkedIn HQ field) used to determine HQ.

Run:  python extract_igsc_from_html.py
Produces: data/raw/igsc_members.csv  (cols: firm_name, firm_url, hq_iso3, hq_source_note)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
HTML = ROOT / "data" / "raw" / "igsc_homepage.html"
OUT = ROOT / "data" / "raw" / "igsc_members.csv"

# Curated HQ mapping. Each entry: firm_name -> (iso3 or None, source_note).
# iso3 is None for international/non-country member entries (e.g., IBBIS, Geneva-based).
# Source notes cite the firm's own corporate page or a known directory.
HQ_LOOKUP: dict[str, tuple[str | None, str]] = {
    "Aclid": ("USA", "aclid.bio About: San Francisco, CA"),
    "Aldevron": ("USA", "aldevron.com: Fargo, ND HQ; subsidiary of Danaher (USA)"),
    "Ansa Biotechnologies": ("USA", "ansabio.com: Emeryville, CA"),
    "Atum": ("USA", "atum.bio: Newark, CA (formerly DNA2.0)"),
    "Azenta Life Sciences": ("USA", "azenta.com: Burlington, MA"),
    "Battelle": ("USA", "battelle.org: Columbus, OH"),
    "Biolytic Lab Performance, Inc.": ("USA", "biolytic.com: Fremont, CA"),
    "Blue Heron": (
        "USA",
        "blueheronbio.com: Bothell, WA; Eurofins Genomics subsidiary",
    ),
    "BUILT": ("USA", "builtdna.com: Boston, MA"),
    "Camena Bioscience": ("GBR", "camenabio.com: Cambridge, UK"),
    "Constructive Bio": ("GBR", "constructive.bio: Cambridge, UK"),
    "Cyber@Ben-Gurion University of the Negev": (
        "ISR",
        "cyber.bgu.ac.il: Beer-Sheva, Israel",
    ),
    "The DAMP Lab": ("USA", "damplab.org: Boston University, MA"),
    "DNA Script": ("FRA", "dnascript.com: Le Kremlin-Bicetre, France"),
    "Elegen Bio": ("USA", "elegenbio.com: South San Francisco, CA"),
    "Emerald Cloud Lab": ("USA", "emeraldcloudlab.com: Austin, TX"),
    "GenScript": (
        "USA",
        "genscript.com: Piscataway, NJ HQ (parent GenScript Biotech HQ in Nanjing, China)",
    ),
    "GP-Write": ("USA", "engineeringbiologycenter.org: Boston University-affiliated"),
    "IBBIS": (None, "ibbis.bio: International, Geneva-based; not a country firm"),
    "iBioFAB": ("USA", "igb.illinois.edu/iBIOFAB: University of Illinois"),
    "IDT": ("USA", "idtdna.com: Coralville, IA; subsidiary of Danaher"),
    "Molecular Assemblies": ("USA", "molecularassemblies.com: San Diego, CA"),
    "Nuclera": ("GBR", "nuclera.com: Cambridge, UK"),
    "Raytheon BBN": ("USA", "rtx.com: Cambridge, MA"),
    "Ribbon Bio": ("USA", "ribbonbio.com: South San Francisco, CA"),
    "Switchback Systems": ("USA", "switchbacksys.com: Boston, MA"),
    "Synbio Technologies": (
        "USA",
        "synbio-tech.com: Monmouth Junction, NJ HQ (parent in Suzhou, China)",
    ),
    "Synplogen": ("JPN", "synplogen.com: Kobe, Japan"),
    "Telesis Bio": ("USA", "telesisbio.com: San Diego, CA"),
    "Thermo Fisher Scientific": ("USA", "thermofisher.com: Waltham, MA"),
    "Touchlight": ("GBR", "touchlight.com: London, UK"),
    "Tsingke Biotechnology Co., Ltd.": ("CHN", "tsingke.com.cn: Beijing, China"),
    "BGI": ("CHN", "bgi.com: Shenzhen, China"),
    "Bioneer Corp.": ("KOR", "bioneer.com: Daejeon, South Korea"),
    "Edinburgh Genome Foundry": ("GBR", "genomefoundry.org: Edinburgh, UK"),
    "Ginkgo Bioworks": ("USA", "ginkgobioworks.com: Boston, MA"),
    "Twist Bioscience": ("USA", "twistbioscience.com: South San Francisco, CA"),
}


def parse() -> pd.DataFrame:
    if not HTML.exists():
        raise FileNotFoundError(
            f"{HTML} not found. Fetch the IGSC homepage to that path first "
            f"(the notebook does this automatically in §4.5)."
        )
    html = HTML.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<h4>\s*<a\s+href="([^"]+)"[^>]*>([^<]+)</a>\s*</h4>',
        re.DOTALL,
    )
    rows = []
    for m in pattern.finditer(html):
        url, name = m.group(1), m.group(2).strip()
        hq = HQ_LOOKUP.get(name)
        if hq is None:
            print(f"[WARN] No HQ mapping for: {name}", file=sys.stderr)
            iso3, note = None, "MAPPING MISSING"
        else:
            iso3, note = hq
        rows.append(
            {
                "firm_name": name,
                "firm_url": url,
                "hq_iso3": iso3,
                "hq_source_note": note,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    df = parse()
    print(f"Extracted {len(df)} IGSC member firms")
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Wrote {OUT}")
    # Country counts of relevance
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
        "USA",
        "CHN",
    ]
    counts = df["hq_iso3"].value_counts()
    print("\nIGSC member-firm count by HQ country:")
    for iso3 in target:
        print(f"  {iso3}: {int(counts.get(iso3, 0))}")
    no_hq = df[df["hq_iso3"].isna()]
    if len(no_hq):
        print(f"\nFirms with no country (international/unmapped): {len(no_hq)}")
        for _, r in no_hq.iterrows():
            print(f"  {r['firm_name']}")


if __name__ == "__main__":
    main()
