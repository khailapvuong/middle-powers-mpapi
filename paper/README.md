# M-PAPI companion paper (LaTeX)

Self-contained arXiv-style source for **"Operationalising the Three-Axes Framework: A Composite-Indicator Companion to *AI-Proliferation and Middle Powers*."** This `paper/` folder consolidates the project's methodology, data-science application, results, and alignment with the working paper into a single PDF.

## Contents

| File | Purpose |
|---|---|
| `main.tex` | The paper (single-column preprint; standard CTAN packages only). |
| `references.bib` | Bibliography (data sources, methods, weighting frameworks, software stack, working paper). |
| `figures/` | The 16 figures, copied from `../figures/` so this folder is self-contained. |
| `main.pdf` | Pre-compiled output (≈22 pp). |

## Compile

**Overleaf:** create a new project, upload every file in this folder (keep `figures/` as a subfolder), set the compiler to **pdfLaTeX**, and Recompile. No package installation is needed — every package used ships with Overleaf's TeX Live.

**Locally** (TeX Live or MiKTeX, with `latexmk`):

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex   # runs pdflatex -> bibtex -> pdflatex x2
```

Or manually:

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

To clean auxiliary files afterwards: `latexmk -c`.

## Notes

- All numbers, tables, and figures are drawn verbatim from the validated notebook outputs (`../outputs/*.csv|json`) and figures (`../figures/*.png`); the paper does not recompute anything.
- The paper operationalises §1–§2 of the working paper (axes, country set, attack vectors) and explicitly does **not** operationalise §3–§4 (trigger ladder, preparedness checklist).
- On a fresh MiKTeX install, the on-the-fly package installer may need `initexmf --set-config-value "[MPM]AutoInstall=1"` and a one-time `miktex packages update-package-database`; `authblk` (from the `preprint` bundle) is the only non-default package required.
