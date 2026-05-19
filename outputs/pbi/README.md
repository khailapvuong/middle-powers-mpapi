# outputs/pbi/ — Power BI consumption layer

This folder is a **star-schema slice** of the M-PAPI notebook outputs, designed for direct ingestion by Power BI Desktop. All files here are emitted by §20 of `M-PAPI.ipynb`; do not edit by hand. Re-run the notebook to refresh.

## Files

| File | Grain | Primary key | Source frame |
|---|---|---|---|
| `dim_country.csv` | per country | `iso3` | `master` + `typology` + `EXTRACTIONS["C5_aisi_presence"]` |
| `dim_indicator.csv` | per indicator | `indicator_id` | `indicators` (§3.2 INDICATORS) |
| `dim_action.csv` | per policy action | `action_key` | `ACTIONS` (§13.4) |
| `fact_index_long.csv` | iso3 × scheme × axis_or_composite | composite | melt of `scoreboard` (§11) |
| `fact_vulnerability_long.csv` | iso3 × vector | composite | melt of `exposure` (§13) |
| `fact_shap_long.csv` | iso3 × indicator | composite | melt of `shap_df` (Appendix B.1) |
| `fact_counterfactual.csv` | iso3 × action | composite | passthrough of `counterfactual_scenarios.csv` (§13.4) |
| `fact_sensitivity.csv` | iso3 | `iso3` | passthrough of `rank_summary` (§12.1) |

## Relationships (single-direction many-to-one)

```
dim_country[iso3] ──┬── fact_index_long[iso3]
                    ├── fact_vulnerability_long[iso3]
                    ├── fact_shap_long[iso3]
                    ├── fact_counterfactual[iso3]
                    └── fact_sensitivity[iso3]

dim_indicator[indicator_id] ── fact_shap_long[indicator_id]
dim_action[action_key]      ── fact_counterfactual[action_key]
```

## Load order in Power BI Desktop

1. Get Data → Folder → point at this directory → Combine & Load.
2. Verify each file imports as its own table (do not auto-merge).
3. In Model view, draw the 7 relationships above. Set every relationship to single-direction (filter: `dim → fact`).
4. Hide `iso3` and `action_key` foreign-key columns in fact tables from the report view (right-click → "Hide in report view"). The dimension-side columns are the user-facing slicer values.

## Column conventions

- All ISO codes are ISO 3166-1 alpha-3 (e.g., `GBR`, `KOR`); `EUU` for the European Union row.
- `scheme_code` ∈ {`equal`, `pca`, `literature`}; `scheme_label` is the human-readable form.
- `vector_code` ∈ {`cyber`, `cbrn`, `influence_ops`}; `vector_label` is the human-readable form.
- `axis_code` ∈ {`capacity_depth`, `governance_orientation`, `infrastructure_posture`, `composite`}.
- `score`, `shapley_value`, `delta_composite` are float; `rank`, `is_composite` are int.

## Versioning

The data layer regenerates byte-identically on every notebook re-execute (see README byte-identity claim). For a snapshot citation, pin to a commit SHA on `github.com/khailapvuong/middle-powers-mpapi`.
