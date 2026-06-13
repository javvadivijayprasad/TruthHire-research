# TruthHire (research)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20681819.svg)](https://doi.org/10.5281/zenodo.20681819)

Paper, experiments, and reproducible evaluation harness for
**"A Shared Intelligence Network for Employment-Experience Fraud:
Privacy-Preserving Signal Sharing and Incentive Design."**

The deployable system lives in a separate repository (TruthHire). This repository
vendors only the minimal detection engine (`app/timeline.py`) that the experiments
need, so it reproduces end-to-end on its own.

## Layout

```
app/timeline.py     # vendored deterministic engine (for experiments)
experiments/        # seeded datasets, simulations, sweeps, figure scripts
paper/              # LaTeX source, references.bib, figures, datasets, results, PDF
```

## Reproduce everything (seeded; master seed 20260612)

```bash
pip install -r requirements.txt
PYTHONPATH=. python -m experiments.study              # all numbers -> paper/results/study.json
PYTHONPATH=. python -m experiments.make_study_figures  # all 13 figures -> paper/figures/
# real-data false-positive experiment (after downloading the corpus):
bash paper/scripts/download_datasets.sh
PYTHONPATH=. python -m experiments.run_experiment --karrierewege <path>
```

Build the paper: `cd paper && ./compile.sh` (needs pdflatex + bibtex).

## Key results

- Deterministic engine: precision/recall 1.00 on injected fraud (by construction on consistent data).
- Naive `SHA-256(email+phone)` re-identification = adversary coverage, up to 100%; threshold-PSI bounds it.
- Fraud-weighted rewards drive network false positives 0% -> 19%; outcome-symmetric design holds precision at 1.00.
- Regularity detection of AI fakes: AUC 0.90 on naive fakes, collapsing to chance under adaptive noise.
- Network flywheel: repeat-fraud catch rate 6% -> 67% as participation rises; fraud-ring detection 0 -> 0.99.

## Status & ethics
Framework paper with reproducible simulations and a public-corpus protocol; no deployed
multi-organization study yet. Outputs are advisory and disputable by design.

## Cite
See `CITATION.cff` / the Zenodo DOI once archived. License: MIT.
