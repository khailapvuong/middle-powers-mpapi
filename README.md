# Middle-Power AI Proliferation Preparedness Index (M-PAPI)

Companion notebook to *AI-Proliferation and Middle Powers: Preparation and Response Mechanisms* (Teague, Ali, Sfeir, Fort — working paper). The notebook empirically operationalises the working paper's three-axes framework — **Capacity Depth**, **Governance Orientation**, **Infrastructure Posture** — across the 14 middle powers named in the paper, and reports per-country preparedness rankings against the three attack vectors discussed in §2 (cyber, CBRN, influence operations).

The methodology follows the OECD/JRC *Handbook on Constructing Composite Indicators* (2008). Every indicator value cites a named source with retrieval date and URL. **13 of the 15 indicators are fully sourced from Tier-1 institutional providers with no analyst-coding step**: Epoch AI (C1, C2), OpenAlex (C3), Stanford AI Index 2025 (C4, via `extract_patents_from_pdf.py`), ITU GCI via World Bank Data360 (G2), V-Dem (G3), IGSC (G5, via `extract_igsc_from_html.py`), ITU IDI (I1, via `extract_idi_from_pdf.py`), World Bank WDI (I2, I3), and ND-GAIN (I5). The Australia Group public roster feeds G6 (binary 0/1 membership) and is inlined in the `EXTRACTIONS` registry against the cited URL because the upstream page (`australiagroup.net/en/participants.html`) redirects to a DFAT-hosted page that is unreliable for programmatic fetch from many environments; membership rarely changes (India was the most recent addition, January 2018). The remaining **3 indicators (G1, G4, C5) carry an analyst-coding step**: G1 (national AI strategy comprehensiveness) translates the OECD.AI Policy Observatory dashboards into a 0–3 rubric; G4 (bilateral lab MoU count) enumerates UK gov.uk publications and Anthropic / OpenAI / Google DeepMind partnership press releases — no consolidated public registry exists; C5 (AISI presence) is binary-authoritative from the NIST AISI Network fact sheet, with a 0/1/2 ordinal extension applied to non-Network states by the authors. G1 and G4 are flagged `requires_verification: True` in §4.9; C5's coding note is in the same registry. Their literature-scheme weights (G1 20%, G4 10%, C5 25% within their respective axes) are documented in §3.2, and §12.2 leave-one-indicator-out sensitivity shows the top-5 set is unchanged when any of the three is dropped (under G1 drop, Germany rises from rank 8 to rank 6, displacing Canada 6→7 and Singapore 7→8; see §17.5 for the full reshuffle). Full bibliography in §19 of the notebook.

## How to run

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace M-PAPI.ipynb
```

Random seeds are fixed (`SEED = 20260506` in §3.1, passed explicitly to the §12.1 Monte Carlo, the §14 k-means typology, the §14.3 MDS embedding, and the §16.10 sparse-PCA decomposition); reruns produce byte-identical outputs and figures. The first run fetches sources from the public web and caches them under `data/raw/`; subsequent runs read from cache. **The current snapshot in `data/raw/` is bundled with the notebook**, so the analysis is fully reproducible offline. Per-file retrieval dates are recorded in the `*.meta.json` sidecars in `data/raw/` and are updated on each successful live re-fetch; the manually-extracted indicator values in §4.9's `EXTRACTIONS` registry carry their own `retrieved_date` field for the date of the analyst-coding pass.

## Headline result

Literature-weighted composite ranking (full table and per-scheme variants in §11 of the notebook):

| Rank | Country     | Composite | Rank | Country      | Composite |
| ---- | ----------- | --------- | ---- | ------------ | --------- |
|    1 | UK          |     2.314 |    8 | Germany      |     1.434 |
|    2 | South Korea |     2.185 |    9 | Sweden       |     1.157 |
|    3 | France      |     1.980 |   10 | UAE          |     1.020 |
|    4 | EU          |     1.824 |   11 | Saudi Arabia |     0.922 |
|    5 | Japan       |     1.823 |   12 | Israel       |     0.144 |
|    6 | Singapore   |     1.809 |   13 | India        |     0.106 |
|    7 | Canada      |     1.472 |   14 | Taiwan       |     0.057 |

The top-5 set {UK, South Korea, France, EU, Japan} is identical across all three weighting schemes; the bottom-3 set {Israel, India, Taiwan} is identical under the equal and literature schemes, with Saudi Arabia sitting one rank above Israel at 11th. Under the PCA scheme Israel rises from rank 12 to rank 10 (displacing UAE 10→11 and Saudi Arabia 11→12), so PCA's bottom-3 is {Saudi Arabia, India, Taiwan}. Every perturbation in `outputs/robustness_summary_with_ci.csv` reports Spearman ρ ≥ 0.96, with Fisher-z 95% CI lower bounds spanning [+0.876, +0.986]; the lowest lower bound (the classifier-sensitivity check at +0.876) clears its 0.85 threshold, and the three weighting/normalisation perturbations all clear the 0.70 threshold with lower bound ≥ 0.90. **Tier stability is partial.** Of the baseline top-5 {UK, South Korea, France, EU, Japan} and bottom-3 {Israel, India, Taiwan}, seven of the eight baseline-tier countries appear in their baseline tier in ≥ 80% of the 10,000 Monte Carlo draws; Israel is the single exception at 62% (it swaps with Saudi Arabia in 38% of draws). Within-1-swap tolerance — at most one country differs from the baseline tier — is preserved in 94% of top-5 draws and 83% of bot-3 draws (per `outputs/h6_set_membership.json`, computed in §16.11). The *exact* tier set is recovered in only ~46% of top-5 draws and ~43% of bot-3 draws because the 5th and 12th slots cycle. Within-tier ordering fluctuates. The EU has the widest in-tier IQR (≈ 3, p10–p90 = 1–7) because the EU row is partly synthetic (see §16.9); Korea's Monte Carlo median rank is 2 (IQR ≈ 2) and Korea also ranks 2 under both the equal and literature weighting schemes (rank 4 under PCA). The literature-scheme ordering inside the {France, EU, Japan} block (positions 3–5) is weight-sensitive: France at 1.980, EU at 1.824, Japan at 1.823 — the EU/Japan gap is 0.001 and Monte Carlo gives all three a median rank of 4. Middle ranks (positions 7–10) are also weight-sensitive — refer to Monte Carlo rank distributions in §15.4 and the per-country IQR in `outputs/sensitivity_ranks.csv`.

## Notebook structure

The notebook follows the OECD/JRC 10-step composite-indicator process:

- §1 introduction, paper-mapping, and six pre-registered hypotheses (H1–H6 in §1.4; resolved in §16.11 as three fully supported and three partially supported).
- §2 conceptual framework (axes, attack vectors, composite logic).
- §3–§5 setup, configuration, data acquisition, cleaning and harmonisation.
- §6–§7 indicator construction and two-stage imputation.
- §8 multivariate diagnostics (per-axis PCA + Horn's parallel analysis in §8.1).
- §9–§11 normalisation, weighting (equal / PCA-derived / literature-elicited), composite computation.
- §12 sensitivity and robustness (Monte Carlo, leave-one-out, alternative normalisation, classifier sensitivity).
- §13 vulnerability overlay (per-vector cyber / CBRN / influence-ops preparedness rankings; per-country counterfactual policy scenarios in §13.4).
- §14 typology — k-means (§14), hierarchical clustering (§14.2), MDS embedding (§14.3).
- §15 visualisation — country × axis heatmap (§15.1), two-axis typology plot (§15.2), vulnerability per-vector ranks (§15.3), Monte Carlo rank boxplots (§15.4), EU vs member-state cross-validation (§15.5), pairwise axis scatter matrix (§15.6).
- §16 discussion mapping findings back to working-paper sections, including sparse-PCA governance sub-axes (§16.10) and hypothesis-testing results (§16.11).
- §17 limitations (§17.1–§17.10), threats-to-validity audit (§17.11), methodological reflections from the build process (§17.12), and future-work priorities.
- §18 verification (four end-to-end checks + source-URL liveness probe).
- §19 bibliography.
- Appendix A — methodology hygiene diagnostics (cross-axis Pearson correlations, Fisher-z 95% CIs on robustness Spearman ρ values, Cronbach-style within-axis α) — recomputed live each rebuild.
- Appendix B — interpretability (exact Shapley composite decomposition over 2¹⁵ subsets in B.1; permutation feature importance in B.2).
- Concluding Remarks — workflow recap, headline findings, reproducibility note.

## File layout

```text
M-PAPI.ipynb              — the notebook (configuration, data, analysis, bibliography)
README.md                 — this file
LICENSE                   — MIT for the notebook and Python code; upstream sources retain their own licences (see §19 bibliography)
requirements.txt
extract_idi_from_pdf.py      — parses ITU IDI 2024 report PDF Table 1; called by §4.7
extract_igsc_from_html.py    — parses IGSC member roster from homepage HTML; called by §4.5
extract_patents_from_pdf.py  — parses Stanford AI Index 2025 Figure 1.2.3 (top-15 per-100k AI patent rates); called by §4.8
data/raw/                 — cached source files (bundled snapshot; live re-fetch on rerun if reachable, cache fallback otherwise)
figures/                  — sixteen PNG figures exported by the notebook
outputs/                  — index CSVs and sensitivity tables exported by the notebook
```

## Citing the working paper

> Teague, J., Ali, A., Sfeir, S., & Fort, K. (2026). *AI-Proliferation and Middle Powers: Preparation and Response Mechanisms*.
