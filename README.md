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
PYTHONPATH=. python -m experiments.realistic           # realistic-FP table (naive vs granularity-aware)
# real-data false-positive number (corpus WITH employment dates):
bash paper/scripts/download_datasets.sh                # -> datasets/external/master_resumes.jsonl
PYTHONPATH=. python -m experiments.run_experiment \
  --resume-corpus datasets/external/master_resumes.jsonl   # -> results/truthhire_realdata_fp_results.json
# real-data false-positive experiment (after downloading the corpus):
bash paper/scripts/download_datasets.sh
PYTHONPATH=. python -m experiments.run_experiment --karrierewege <path>
```

Build the paper: `cd paper && ./compile.sh` (needs pdflatex + bibtex).

## Key results

- Deterministic engine: precision/recall 1.00 on injected fraud (by construction on consistent data).
- **False positives (headline):** on a messy-but-honest synthetic population (career
  gaps, month-level dates, year-granularity dates, short transition overlaps,
  claimed-year rounding, and a minority with legitimately concurrent roles), naive
  date parsing yields a **24.1%** false-positive rate (95% CI 23.7–24.4), almost
  all *phantom* overlaps from year-only dates. A granularity-aware overlap
  tolerance cuts this to **5.5%** (95% CI 5.3–5.8) with **overlap-fraud recall held
  at 1.00**; the residual FP is driven entirely by genuinely concurrent employment
  (≈0% when none is present). This is the primary FP figure — see the corpus note
  below for why a public real-data corpus could not improve on it. See
  `experiments/realistic.py` and `paper/figures/realistic_fp.png`.
- Naive `SHA-256(email+phone)` re-identification = adversary coverage, up to 100%; threshold-PSI bounds it.
- Fraud-weighted rewards drive network false positives 0% -> 19%; outcome-symmetric design holds precision at 1.00.
- Regularity detection of AI fakes: AUC 0.90 on naive fakes, collapsing to chance under adaptive noise.
- Network flywheel: repeat-fraud catch rate 6% -> 67% as participation rises; fraud-ring detection 0 -> 0.99.

## Real-data corpus note

The deterministic checks reason over **employment dates**, so a real-data
false-positive measurement needs a corpus with coherent dates. Two leading
public corpora were tested empirically and both proved unsuitable:

1. **KARRIEREWEGE (arXiv:2412.14612) — no dates.** It stores only ordered ESCO
   occupation sequences (`_id`, `experience_order`, synthesized
   titles/descriptions); no start/end dates, age, or claimed-years, so the
   engine's date checks cannot fire at all.
2. **`datasetmaster/resumes` (HF, MIT) — has dates but is dominated by synthetic
   data with incoherent timelines.** Running the harness on its 4,646
   dated résumés gave an implausible 65.9% overlap FP; diagnosis
   (`experiments/diagnose_corpus.py`) showed the cause is data quality, not the
   engine: byte-identical duplicate records, the *same* job title repeated 2–3
   times per person with independently-random overlapping date ranges, an
   implausibly uniform 1/2/3-jobs-per-person split (≈⅓ each — a generator
   signature), and placeholder fields (`"company": "Fresher"`). The engine
   correctly flags the artificial overlaps; the corpus is simply not real enough
   to measure a true FP rate.

Conclusion: clean, public résumé corpora with genuine, coherent employment dates
are scarce (a privacy reality). The harness (`run_experiment.py --resume-corpus`,
the auto-detecting `load_resume_corpus`, and the date-coverage report) is retained
so a suitable corpus can be plugged in later, but the **seeded `realistic_fp`
result (5.5%) is the primary, reproducible FP figure** for now.

## Status & ethics
Framework paper with reproducible simulations and a public-corpus protocol; no deployed
multi-organization study yet. Outputs are advisory and disputable by design.

## Cite
See `CITATION.cff` / the Zenodo DOI once archived. License: MIT.
