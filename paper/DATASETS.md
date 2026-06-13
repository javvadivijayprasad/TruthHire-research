# Datasets

## Included (generated, reproducible, safe to commit)

| File | Rows | What |
|------|------|------|
| `datasets/genuine_synthetic.jsonl` | 3,000 | Seeded genuine career trajectories (deterministic from `seeds/seed_tables.json`) |
| `datasets/benchmark_labeled.jsonl` | 3,000 | Genuine + injected labeled fraud (4 types) for the deterministic experiment |
| `datasets/build_summary.json` | – | Provenance: master seed, count, SHA-256 content hash |

Regenerate identically: `PYTHONPATH=. python -m experiments.run_experiment` (same seed → same SHA-256).

## External (download locally, then cite — not redistributed here)

| Dataset | Role | How to get it |
|---------|------|---------------|
| **KARRIEREWEGE** (arXiv:2412.14612) | real genuine population for the false-positive measurement | `scripts/download_datasets.sh` → `github.com/elenasenger/karrierewege` (verify licence) |
| **Kaggle 54k structured resumes** | supplementary genuine | `kaggle datasets download -d suriyaganesh/resume-dataset-structured` |
| **ResumeAtlas** (arXiv:2406.18125) | supplementary | arXiv release |

After download: `PYTHONPATH=. python -m experiments.run_experiment --karrierewege <path>` runs the
false-positive measurement on real, unperturbed trajectories.

## Results (machine-readable)

`results/{deterministic,incentive,privacy,agent}.json` — the exact numbers behind Tables 2–5 and Figures 1–4.
