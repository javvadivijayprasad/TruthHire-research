# Experiments — reproducible datasets & evaluation

Evaluates the deterministic **Timeline Intelligence Engine** (`app/timeline.py`)
on a labeled benchmark. Two data tracks:

1. **Seeded synthetic** (reproducible) — a genuine population generated
   deterministically from seed tables, with labeled fraud injected. Mirrors the
   seed-table / deterministic-regeneration methodology used in the author's
   TestCaseGen and Defect-Analysis studies.
2. **Real data** — the public **KARRIEREWEGE** career-trajectory corpus, used
   *unperturbed* to measure the false-positive rate on real, atypical careers.

## Layout

```
experiments/
  seeds/seed_tables.json     # name/employer/title pools + distributions
  generate_dataset.py        # deterministic genuine generator + provenance hash
  loaders.py                 # load_generated / load_karrierewege / kaggle
  fraud_injection.py         # labeled fraud injection (4 types)
  evaluate.py                # precision / recall / F1 / FP-rate / per-type recall
  run_experiment.py          # orchestrator -> results/ + datasets/ + audit
  run_demo.py                # minimal synthetic demo
```

## Run (reproducible synthetic)

```bash
cd truthhire_api
PYTHONPATH=. python -m experiments.run_experiment            # writes results + audit
```

Outputs `datasets/truthhire/genuine.jsonl`, a `build_summary.json` provenance
record (master seed, record count, SHA-256 content hash), and
`results/truthhire_timeline_results.json`. Re-running with the same seed
reproduces the dataset byte-for-byte (verified by hash).

## Run on real data (KARRIEREWEGE)

Download locally (the sandbox blocks the hosts):

```bash
# github.com/elenasenger/karrierewege  (arXiv:2412.14612) — verify licence
PYTHONPATH=. python -m experiments.run_experiment --karrierewege path/to/karrierewege.jsonl
```

The loader accepts `.jsonl` / `.json` (person objects with an experiences list)
and `.csv` (one experience per row, grouped by person id), and tolerates several
common column spellings — adjust `KW_CONFIG` in `loaders.py` after inspecting a
few rows of your download. Age/graduation are usually absent, so those checks
skip; the **overlap** and **inflation** checks still run, which is precisely the
false-positive behaviour to measure on real careers. No fraud is injected on this
path — it is a pure FP measurement.

## Result so far (seeded synthetic, n=3,000, 50% fraud)

| Metric | Value |
|--------|-------|
| Precision | 1.00 |
| Recall (all 4 fraud types) | 1.00 |
| False-positive rate | 0.00 |

Perfect separation is expected by construction on internally-consistent data.
The headline empirical number for the paper is the **FP rate on unperturbed
KARRIEREWEGE**, plus recall against agent-generated synthetic identities.

## Datasets used (download locally)

| Dataset | Role | Source |
|---------|------|--------|
| KARRIEREWEGE (arXiv:2412.14612) | real genuine population (FP test) | github.com/elenasenger/karrierewege |
| ResumeAtlas (arXiv:2406.18125) | supplementary résumés | arXiv |
| 54k Structured Resumes | supplementary | Kaggle: suriyaganesh/resume-dataset-structured |

## Simulations (demonstrate the paper's two novel claims)

```bash
PYTHONPATH=. python -m experiments.sim_incentive   # adverse-selection failure & fix
PYTHONPATH=. python -m experiments.sim_privacy      # re-identification demonstration
```

- **sim_incentive** — naive "fraud pays more" reward vs. outcome-symmetric +
  threshold + reputation. Headline: as strategic participants rise 0→50%, the
  naive network FP rate climbs 0%→17% (precision 1.00→0.60), while the proposed
  regime holds FP at 0% / precision 1.00 (Table 3 in the paper).
- **sim_privacy** — naive `SHA-256(email‖phone)` gives 100% re-identification of
  any enumerable candidate; keyed HMAC stops outsiders (0%) but not insiders
  (100%); PSI + threshold bounds insider leakage (Table 4 in the paper).
