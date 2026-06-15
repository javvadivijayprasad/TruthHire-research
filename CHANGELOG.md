# Changelog

All notable changes to the TruthHire research artifact are documented here.
This project follows semantic versioning.

## [1.1.0] — 2026-06-14

### Added
- **Realistic false-positive experiment** (`experiments/realistic.py`): a
  "messy-but-honest" genuine population (career gaps, month- and year-granularity
  dates, short transition overlaps, claimed-year rounding, and a minority with
  legitimately concurrent roles). Deterministic false-positive rate is 24.1%
  under naive date parsing and 5.5% with the granularity-aware rule, with
  overlap-fraud recall held at 1.00. Added figure `paper/figures/realistic_fp.png`.
- **Data-availability assessment** (`paper/results/realdata_corpus_assessment.json`,
  `experiments/diagnose_corpus.py`): empirical finding that KARRIEREWEGE has no
  employment dates and that a dated public resume corpus is dominated by synthetic
  records with incoherent timelines — documenting why the headline FP figure comes
  from a controlled realistic population.
- **Dated-corpus harness:** `load_resume_corpus` (auto-detects date-field
  spellings and combined ranges) and `run_experiment.py --resume-corpus`, with a
  date-coverage report so low coverage is never mistaken for a low FP rate.

### Changed
- **Engine:** granularity-aware overlap tolerance (year-only dates widen the
  overlap tolerance by 12 months), mirrored from the system repo.
- **Paper:** new "Realistic false positives" results subsection; corrected the
  datasets section/table (KARRIEREWEGE and the dated corpus marked unusable, with
  reasons); softened the former "near-zero false-positive" claim; reframed the
  validity and research-agenda sections. Rebuilt PDF (31 pp).
- Study harness now emits `realistic_fp` and the concurrent-role sweep into
  `paper/results/study.json`.
