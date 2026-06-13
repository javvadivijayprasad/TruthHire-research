# TruthHire — research paper package

Framework paper: *A Shared Intelligence Network for Employment-Experience Fraud —
Privacy-Preserving Signal Sharing and Incentive Design.* Self-contained and
git-ready, structured like the author's prior paper repos.

```
paper/
  truthhire_paper.tex      # arXiv-ready source (single column, booktabs)
  references.bib           # BibTeX
  truthhire_paper.pdf      # compiled (10 pp.)
  compile.sh               # pdflatex + bibtex build
  figures/                 # fig_layers, fig_incentive, fig_privacy, fig_agent (PNG, 160 dpi)
  datasets/                # generated genuine + labeled benchmark + provenance
  results/                 # machine-readable numbers behind every table
  scripts/download_datasets.sh   # clone the real corpora locally
  DATASETS.md              # dataset inventory + access
```

## Build

```bash
./compile.sh           # or: pdflatex -> bibtex -> pdflatex x2
```

## Reproduce the numbers

All experiments live in `../truthhire_api/experiments/` and are seeded:

```bash
cd ../truthhire_api
PYTHONPATH=. python -m experiments.run_experiment   # deterministic + provenance
PYTHONPATH=. python -m experiments.sim_incentive    # Table 5 / Fig 2
PYTHONPATH=. python -m experiments.sim_privacy       # Table 6 / Fig 3
PYTHONPATH=. python -m experiments.sim_agent         # Table 7 / Fig 4
PYTHONPATH=. python -m experiments.make_figures      # regenerate all PNGs
```

## Tables & figures

8 tables (notation, design failure-modes, datasets, deterministic, incentive,
re-identification, agent-detection) and 4 figures (per-layer detection, incentive
curves, re-identification bars, regularity distributions).

## Status

Framework paper with reproducible simulation results. The one external experiment
— false-positive rate on real KARRIEREWEGE — runs locally after
`scripts/download_datasets.sh` (the sandbox that generated this could not reach
those hosts). Commercial operation is deferred; released open source for scrutiny.


## v2 (expanded, 30 pages)

The paper now compiles to **30 pages** with **13 figures** and ~20 tables,
including multi-seed studies (95% CIs), parameter sweeps, two added experiments
(network flywheel; fraud-ring detection), an attribution map, a formal
mechanism-design analysis, a threshold-PSI protocol, worked scenarios, a
systems-positioning comparison, deployment/governance sections, and a full-results
appendix generated directly from `results/study.json`.

Reproduce everything (seeded): from `../truthhire_api/`,
`PYTHONPATH=. python -m experiments.study` then
`PYTHONPATH=. python -m experiments.make_study_figures`.
