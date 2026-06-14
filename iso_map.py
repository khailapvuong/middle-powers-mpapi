"""Shared country-name -> ISO 3166-1 alpha-3 resolver for the extract_*.py helpers.

Centralises the resolution logic so the data-extraction scripts do not each copy-paste
it (the duplication that previously let a source-specific country label slip through).
Source-specific name overrides stay in each script, since every upstream source spells
economies differently; this module owns only the lookup logic, not the per-source data.
"""

from __future__ import annotations

import pycountry


def to_iso3(name: str, overrides: dict[str, str] | None = None) -> str | None:
    """Resolve a country/economy name to its ISO 3166-1 alpha-3 code.

    Checks ``overrides`` (source-specific spellings that ``pycountry`` cannot resolve)
    first, then ``pycountry.countries.lookup``. Returns ``None`` for empty input or for
    a name that neither path resolves.
    """
    if not isinstance(name, str) or not name.strip():
        return None
    name = name.strip()
    if overrides and name in overrides:
        return overrides[name]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None
