# M-PAPI Power BI dashboard — design specification

Companion to `docs/PBI_BUILD_TUTORIAL.md` (the step-by-step build) and to the data layer at `outputs/pbi/` (the input). This document specifies *what to build*; the tutorial covers *how to build it in Power BI Desktop*.

## Audience and purpose

Policy / government analysts in middle-power foreign-affairs ministries and AISI-equivalent bodies who consume empirical work through Power BI. The dashboard exposes the M-PAPI composite ranking and per-country drill-through, with a live counterfactual what-if so a reviewer can ask *"what would happen to my country's rank if it joined the AISI Network?"* without reopening the notebook.

The dashboard is a **consumption surface**, not a re-implementation. Every number it shows is sourced from `outputs/pbi/` files emitted by §20 of `M-PAPI.ipynb`. No new computation is introduced at the DAX layer.

## Scope — 2-page MVP

| Page | Audience question it answers |
|---|---|
| **1. Overview** | Where do the 14 middle powers sit overall? Is the ranking robust? |
| **2. Country drill-through** | For a specific country, what drives the rank, what's the threat profile, and what would each §13.4 policy action do? |

A Phase-2 expansion (vector drill-through, sensitivity deep-dive, methodology walkthrough) is listed under [Future expansion](#future-expansion). Phase-2 pages duplicate work the paper and PNGs already do better, so they are deliberately out-of-scope for v1.

## Data model

Three dimension tables + five fact tables emitted by `M-PAPI.ipynb` §20 to `outputs/pbi/`. Schema documented in `outputs/pbi/README.md`.

```
            dim_country ──┬── fact_index_long          (iso3 × scheme × axis|composite → score, rank)
                          ├── fact_vulnerability_long  (iso3 × vector → score, rank)
                          ├── fact_shap_long           (iso3 × indicator → shapley_value)
                          ├── fact_counterfactual      (iso3 × action → delta_axis, delta_composite, delta_rank)
                          └── fact_sensitivity         (iso3 → rank_median, p10, p90, iqr)

            dim_indicator ── fact_shap_long
            dim_action    ── fact_counterfactual
```

Seven many-to-one relationships, all single-direction. No bi-directional filters, no role-playing dimensions, no calculated tables. Beginner-PBI-friendly.

## Page 1 — Overview

### Layout (left → right, top → bottom)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  M-PAPI: Middle-Power AI Proliferation Preparedness Index               │
│  Companion to Teague, Ali, Sfeir, Fort (2026)                           │
├─────────────────────────────┬───────────────────────────────────────────┤
│  KPI: Rank-1 country        │  Slicer: Weighting scheme                 │
│  KPI: Rank-14 country       │  ○ Equal  ● Literature  ○ PCA-derived     │
│  KPI: Top-5 set             │                                           │
├─────────────────────────────┼───────────────────────────────────────────┤
│  Sortable ranking table     │  Interactive typology scatter             │
│  (14 rows × 5 cols)         │  (Capacity Depth × Infrastructure Posture)│
│  iso3, name, axis scores,   │  Colour: §14 archetype                    │
│  composite, rank            │  Shape:  AISI Network membership          │
├─────────────────────────────┴───────────────────────────────────────────┤
│  Robustness CI bar chart                                                │
│  4 perturbations × Spearman ρ + Fisher-z 95% CI lower bound             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Visuals

**V1.1 — KPI cards (3 cards, stacked top-left)**

| Visual | Data | DAX |
|---|---|---|
| `[Top Country]` | `dim_country` × `fact_index_long` filtered by `scheme = "literature"` and `axis_code = "composite"`, ordered by `rank` ASC, top 1 | `[Top Country] = LOOKUPVALUE(dim_country[name], dim_country[iso3], CALCULATE(SELECTEDVALUE(fact_index_long[iso3]), fact_index_long[rank] = 1, fact_index_long[is_composite] = 1))` |
| `[Bottom Country]` | same, `rank` DESC | `[Bottom Country] = LOOKUPVALUE(dim_country[name], dim_country[iso3], CALCULATE(SELECTEDVALUE(fact_index_long[iso3]), fact_index_long[rank] = 14, fact_index_long[is_composite] = 1))` |
| `[Top-5 Set]` | top-5 names concatenated | `[Top-5 Set] = CONCATENATEX(TOPN(5, FILTER(fact_index_long, fact_index_long[is_composite] = 1), fact_index_long[rank], ASC), RELATED(dim_country[name]), ", ")` |

All three respond to the weighting-scheme slicer (V1.2) — switching to PCA shifts the order.

**V1.2 — Weighting-scheme slicer (top-right)**

- Slicer field: `fact_index_long[scheme_label]`
- Single-select, default `Literature-elicited`
- Slicer style: horizontal pill list

**V1.3 — Sortable ranking table (middle-left, 14 rows)**

Columns:

| Column | Source | Format |
|---|---|---|
| Rank | `[Rank]` measure | int, sortable |
| iso3 | `dim_country[iso3]` | text |
| Country | `dim_country[name]` | text |
| Capacity | `[Capacity Z]` | decimal, 2dp, diverging conditional formatting |
| Governance | `[Governance Z]` | decimal, 2dp, diverging conditional formatting |
| Infrastructure | `[Infrastructure Z]` | decimal, 2dp, diverging conditional formatting |
| Composite | `[Composite Score]` | decimal, 3dp |

Measures:

```dax
[Composite Score] =
    CALCULATE(
        SUM(fact_index_long[score]),
        fact_index_long[axis_code] = "composite"
    )

[Capacity Z] =
    CALCULATE(
        SUM(fact_index_long[score]),
        fact_index_long[axis_code] = "capacity_depth"
    )

[Governance Z] =
    CALCULATE(
        SUM(fact_index_long[score]),
        fact_index_long[axis_code] = "governance_orientation"
    )

[Infrastructure Z] =
    CALCULATE(
        SUM(fact_index_long[score]),
        fact_index_long[axis_code] = "infrastructure_posture"
    )

[Rank] =
    CALCULATE(
        MIN(fact_index_long[rank]),
        fact_index_long[is_composite] = 1
    )
```

All five measures filter by the currently-selected `scheme_code` via the slicer.

**V1.4 — Interactive typology scatter (middle-right)**

- X-axis: `[Capacity Z]`
- Y-axis: `[Infrastructure Z]`
- Bubble size: constant (large enough to read)
- Marker colour: `dim_country[archetype]` (5 categorical values from §14)
- Marker shape: conditional on `dim_country[is_aisi_network]` (1 = circle, 0 = diamond)
- Data labels: `dim_country[name]`, position = top-right of marker
- Cross-filters: clicking a country bubble filters V1.3 to that row

Note: PBI's native scatter plot supports marker colour by category and marker size/colour by measure, but **does not natively support shape variation by category**. Workaround: use two scatter visuals layered with a transparent background — one for AISI members (circles), one for non-members (diamonds), both filtered by `is_aisi_network`. Document in tutorial.

**V1.5 — Robustness CI bar chart (bottom)**

- Source: `outputs/robustness_summary_with_ci.csv` loaded directly (not via fact tables — only 4 rows, no need for star integration).
- Visual: horizontal error-bar chart (PBI native: clustered bar with error-bar markers, or use the Power BI Visuals Marketplace "Forecast Funnel" / "Strip Plot")
- X-axis: Spearman ρ (range 0.85 – 1.00)
- Y-axis: perturbation name
- Error bars: ci_lower_95 to ci_upper_95
- Reference lines: vertical dashed at `threshold` per perturbation (0.70 for the 3 weighting/normalisation rows; 0.85 for classifier)
- Subtitle (text box below): "All four CI lower bounds clear their thresholds — see §17.10 / Appendix A.2"

Fallback if a forest plot visual is unavailable: use clustered bar with two adjacent bars per perturbation (`ci_lower_95`, `rho`, `ci_upper_95`) and a reference line at `threshold`.

## Page 2 — Country drill-through

### Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Slicer: Country selector  [South Korea ▾]                              │
├─────────────────────────────┬───────────────────────────────────────────┤
│  Per-axis bar (3 axes)      │  Per-vector bar (cyber/CBRN/influence)    │
│  Selected scheme z-scores   │  Vector score + rank                      │
├─────────────────────────────┼───────────────────────────────────────────┤
│  Shapley waterfall          │  Counterfactual what-if table             │
│  15 indicators              │  5 actions × delta_composite              │
│  Sorted by abs(value) DESC  │  Toggle switches (binary parameters)      │
├─────────────────────────────┴───────────────────────────────────────────┤
│  MC rank IQR card                                                       │
│  median · p10 · p90 · iqr · interpretation text                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Visuals

**V2.1 — Country selector (top, single-select slicer)**

- Field: `dim_country[name]`
- Style: dropdown, single-select, default `South Korea`
- All other visuals on the page filter to the selected country.

**V2.2 — Per-axis horizontal bar (middle-left)**

- Y-axis: `axis_label` (3 rows: Capacity Depth, Governance Orientation, Infrastructure Posture)
- X-axis: `[Axis Score]` measure
- Bars coloured diverging (red below 0, blue above 0; PBI conditional formatting on measure value)
- Title: dynamic — `"Axis profile for {SelectedCountry}"`

```dax
[Axis Score] =
    CALCULATE(
        SUM(fact_index_long[score]),
        fact_index_long[is_composite] = 0,
        FILTER(VALUES(fact_index_long[axis_code]), fact_index_long[axis_code] <> "composite")
    )
```

Filters by the slicer-selected country (via the `dim_country → fact_index_long` relationship).

**V2.3 — Per-vector vertical bar (middle-right)**

- X-axis: `vector_label`
- Y-axis: `[Vector Score]`
- Title: `"Vulnerability profile for {SelectedCountry}"`
- Data labels: show `rank` as overlay text

```dax
[Vector Score] = SUM(fact_vulnerability_long[score])

[Vector Rank] = SUM(fact_vulnerability_long[rank])
```

**V2.4 — Shapley waterfall (bottom-left)**

- Visual type: PBI's native "Waterfall chart" (or clustered horizontal bar if waterfall is unavailable)
- Category: `dim_indicator[indicator_id]`
- Y-axis: `[Shapley Value]`
- Sort: descending by absolute value
- Colour: positive green, negative red

```dax
[Shapley Value] = SUM(fact_shap_long[shapley_value])
```

**V2.5 — Counterfactual what-if table (bottom-right) — KILLER DEMO**

This is the headline elevated view. PBI's **What-If Parameter** feature drives five toggles, one per action. The output composite updates live as the analyst toggles actions on/off.

**Step 1: Create 5 what-if parameters** (Modelling → New Parameter → Numeric range)

| Parameter name | Min | Max | Increment | Default |
|---|---|---|---|---|
| `WhatIf_JoinAISI` | 0 | 1 | 1 | 0 |
| `WhatIf_PublishStrategy` | 0 | 1 | 1 | 0 |
| `WhatIf_JoinAustraliaGroup` | 0 | 1 | 1 | 0 |
| `WhatIf_SignLabMoU` | 0 | 1 | 1 | 0 |
| `WhatIf_FosterIGSCFirm` | 0 | 1 | 1 | 0 |

Each parameter creates a 1-column 2-row hidden table + a slicer (style: toggle switch, format: integer).

**Step 2: Create the delta measure**

```dax
[Selected Action Delta] =
    VAR _delta_aisi      = CALCULATE(SUM(fact_counterfactual[delta_composite]), fact_counterfactual[action_key] = "JOIN_AISI") * [WhatIf_JoinAISI Value]
    VAR _delta_strategy  = CALCULATE(SUM(fact_counterfactual[delta_composite]), fact_counterfactual[action_key] = "PUBLISH_AI_STRATEGY") * [WhatIf_PublishStrategy Value]
    VAR _delta_aus_grp   = CALCULATE(SUM(fact_counterfactual[delta_composite]), fact_counterfactual[action_key] = "JOIN_AUSTRALIA_GROUP") * [WhatIf_JoinAustraliaGroup Value]
    VAR _delta_mou       = CALCULATE(SUM(fact_counterfactual[delta_composite]), fact_counterfactual[action_key] = "SIGN_LAB_MOU") * [WhatIf_SignLabMoU Value]
    VAR _delta_igsc      = CALCULATE(SUM(fact_counterfactual[delta_composite]), fact_counterfactual[action_key] = "FOSTER_IGSC_FIRM") * [WhatIf_FosterIGSCFirm Value]
    RETURN COALESCE(_delta_aisi, 0) + COALESCE(_delta_strategy, 0) + COALESCE(_delta_aus_grp, 0) + COALESCE(_delta_mou, 0) + COALESCE(_delta_igsc, 0)

[New Composite If Acted] =
    [Composite Score] + [Selected Action Delta]
```

**Step 3: Display**

Two KPI cards side-by-side:

- "Composite (baseline)" → `[Composite Score]` filtered by `scheme_code = "literature"`
- "Composite (post-action)" → `[New Composite If Acted]` — colour-coded green if higher than baseline, otherwise unchanged

Below the cards: a 5-row table listing each action with its `delta_composite` value and the toggle slicer inline. Each action's row title cites the paper section (e.g., "JOIN_AISI → paper §1 institutional commitment").

**Methodological caveat** (display in a text box adjacent to the visual):

> The what-if combines single-action deltas linearly. Each `delta_composite` in `fact_counterfactual` is a marginal-effect estimate (single action holding all other indicators constant). True multi-action composition is non-linear under geometric across-axis aggregation; for combined-action scenarios consult §13.4's per-action `delta_axis_score` (free of the §11 geometric-shift artifact) and re-run the notebook with simultaneous indicator updates.

**V2.6 — MC rank IQR card (bottom-full-width)**

A 3-card row + interpretation text:

| Card | Measure |
|---|---|
| "Monte Carlo median rank" | `[Rank Median] = SUM(fact_sensitivity[rank_median])` |
| "10th percentile rank" | `[Rank p10] = SUM(fact_sensitivity[rank_p10])` |
| "90th percentile rank" | `[Rank p90] = SUM(fact_sensitivity[rank_p90])` |

Text box below: dynamic interpretation —

```dax
[Rank Interpretation] =
    VAR _iqr = SUM(fact_sensitivity[rank_iqr])
    RETURN
        SWITCH(
            TRUE(),
            _iqr <= 1, "Rank is highly stable across 10,000 weight draws (IQR ≤ 1).",
            _iqr <= 2, "Rank is moderately stable; small re-ordering under perturbation.",
            _iqr <= 3, "Rank is weight-sensitive; cite as a range, not a point.",
            "Rank cycles substantially under perturbation; treat with caution."
        )
```

## DAX measure reference — full list

For an at-a-glance cheat-sheet during the build:

```dax
-- Page 1
[Composite Score]
[Capacity Z]
[Governance Z]
[Infrastructure Z]
[Rank]
[Top Country]
[Bottom Country]
[Top-5 Set]

-- Page 2
[Axis Score]
[Vector Score]
[Vector Rank]
[Shapley Value]
[Selected Action Delta]
[New Composite If Acted]
[Rank Median]
[Rank p10]
[Rank p90]
[Rank Interpretation]
```

Plus five what-if parameter `[…WhatIf… Value]` measures auto-generated by PBI when each parameter is created.

## Future expansion (Phase 2, out of scope for v1)

If supervisor or stakeholder feedback warrants, add:

| Page | Audience question | Rough effort |
|---|---|---|
| **3. Vector drill-through** | For a specific attack vector (cyber / CBRN / influence), who ranks best/worst and what axis decomposition drives it? Includes V-Dem polarity-flipped influence-ops view. | ~2 hours |
| **4. Methodology walkthrough** | How does the index work? Step-by-step OECD/JRC mapping. | **Not recommended** — the paper does this better. |
| **5. Sensitivity deep-dive** | Visual MC rank densities; LOO matrix; cross-axis correlation heatmap. | ~3 hours; mostly replicates `figures/figA1`, `fig15_4`, `fig8_within` interactively. |
| **Cross-page bookmarks** | Guided supervisor tour (click a sequence of pre-set views). | ~1 hour. |
| **Publish to PBI Service** | Cloud share via PBI Pro. | User-side decision (Pro licence ≈ $14/mo/user as of 2026). |

## Refresh cadence

Re-run `M-PAPI.ipynb` end-to-end to regenerate `outputs/pbi/`. In Power BI Desktop, Home → Refresh re-imports the CSV folder. No PBI Service-side scheduled refresh is configured because the input source is a local file folder; if you publish to Service and want refresh, configure an on-premises data gateway pointing at the repo checkout.

## Build order — keep next to `PBI_BUILD_TUTORIAL.md`

1. Open Power BI Desktop (Free or Pro).
2. Get Data → Folder → `outputs/pbi/` → Combine & Load.
3. In Model view, draw the 7 relationships from the data-model diagram above.
4. Page 1: place visuals in the order V1.1 → V1.5; create measures `[Composite Score]` through `[Top-5 Set]` as you go.
5. Page 2: add the country slicer first, then V2.1 → V2.6; defer the what-if parameters to last (Modelling → New Parameter).
6. Theme: apply the JSON theme in `docs/pbi_theme.json` (optional; matches the notebook's matplotlib palette).
7. Save as `.pbix` (not committed to repo — see `.gitignore`).
8. Optional: File → Publish → My workspace (requires PBI Pro).
