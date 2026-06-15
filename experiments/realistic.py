"""Realistic genuine-population false-positive experiment.

The clean generator in ``generate_dataset.py`` builds internally-consistent
trajectories, so the deterministic engine scores 0 false positives *by
construction*. That proves the logic is sound but says nothing about how the
engine behaves on the messy-but-honest resumes seen in the real world.

This module builds a deliberately *messy* genuine population and measures the
deterministic layer's false-positive (FP) rate on it. None of these people are
fraudulent; the messiness is the kind real applicants exhibit:

  * month-level start/end dates (not tidy January boundaries);
  * career gaps and sabbaticals;
  * short legitimate transition overlaps (notice period / garden leave);
  * rounding of ``total_claimed_years`` (people round up to a whole year);
  * year-granularity dates ("2019" with no month), which a naive parser reads as
    January and which can manufacture phantom overlaps between adjacent jobs;
  * a documented minority with *legitimately concurrent* full-time-coded roles
    (portfolio careers: founder + advisor, dual appointments, overlapping
    consulting). The timeline heuristic cannot distinguish these from fraud
    without external evidence.

The experiment reports FP under two engine settings: naive parsing and the
granularity-aware tolerance (``YEAR_GRANULARITY_SLACK_MONTHS``), plus the
overlap-fraud recall under each, to show the mitigation removes phantom FPs
without sacrificing detection power.
"""
from __future__ import annotations

import random
from typing import Dict, List

import app.timeline as TL
from app.timeline import timeline_score
from .fraud_injection import inject, FRAUD_TYPES
from .stats import mean_ci

TITLES = [
    "Software Engineer", "Senior Engineer", "Product Manager", "Data Analyst",
    "Consultant", "Designer", "Operations Lead", "Account Manager",
    "Research Scientist", "Marketing Manager",
]
EMPLOYERS = [
    "Northwind", "Acme Corp", "Globex", "Initech", "Umbrella", "Hooli",
    "Stark Industries", "Wayne Enterprises", "Soylent", "Vandelay",
]


def _month_str(abs_month: int, *, year_only: bool) -> str:
    y, m = abs_month // 12, abs_month % 12 + 1
    return f"{y}" if year_only else f"{y}-{m:02d}"


def generate_realistic(
    n: int = 3000,
    master_seed: int = 20260612,
    *,
    transition_overlap_rate: float = 0.35,
    concurrent_fulltime_rate: float = 0.07,
    year_only_rate: float = 0.30,
    round_claimed_rate: float = 0.60,
) -> List[Dict]:
    """Generate ``n`` genuine but realistically messy trajectories.

    Every record is non-fraudulent. Tunable knobs control how much each kind of
    real-world messiness appears so the experiment can report sensitivity.
    """
    rng = random.Random(master_seed)
    out: List[Dict] = []
    for i in range(n):
        grad_age = rng.choice([21, 22, 22, 23, 24, 26])
        birth = rng.randint(1968, 2001)
        grad_year = birth + grad_age
        age = 2026 - birth
        cursor = grad_year * 12 + rng.randint(0, 11)  # graduate mid-year
        jobs: List[Dict] = []
        n_jobs = rng.choice([1, 2, 2, 3, 3, 4, 5])
        prev_end = None
        for j in range(n_jobs):
            now = 2026 * 12
            if cursor >= now:
                break
            dur = rng.choice([12, 18, 24, 30, 36, 48, 60])  # months
            # legitimate short transition overlap with the previous job
            if prev_end is not None and j > 0 and rng.random() < transition_overlap_rate:
                cursor = prev_end - rng.randint(1, 3)  # 1-3 month overlap (within tolerance)
            start = cursor
            end = min(start + dur, now)
            year_only = rng.random() < year_only_rate
            jobs.append({
                "title": rng.choice(TITLES),
                "company": rng.choice(EMPLOYERS),
                "start": _month_str(start, year_only=year_only),
                "end": "present" if end >= now else _month_str(end, year_only=year_only),
                "employment_type": "full_time",
            })
            prev_end = end
            if end >= now:
                break
            # gap / sabbatical between jobs
            cursor = end + rng.choice([0, 0, 1, 2, 3, 6, 12, 18])

        if not jobs:
            continue

        # legitimately concurrent full-time-coded role (portfolio career)
        if len(jobs) >= 1 and rng.random() < concurrent_fulltime_rate:
            base = rng.choice(jobs)
            bs = _abs(base["start"])
            be = _abs(base["end"])
            ov_start = bs + rng.randint(1, max(1, (be - bs) // 3))
            ov_end = min(be, ov_start + rng.choice([6, 9, 12, 18]))
            jobs.append({
                "title": "Advisor / " + rng.choice(TITLES),
                "company": rng.choice(EMPLOYERS),
                "start": _month_str(ov_start, year_only=False),
                "end": _month_str(ov_end, year_only=False),
                "employment_type": "full_time",
            })

        rec: Dict = {
            "candidate_id": f"real-{i:05d}",
            "age": age,
            "graduation_year": grad_year,
            "jobs": jobs,
        }
        # honest summed tenure, then realistic rounding of the claimed figure
        summed = _summed_years(jobs)
        if rng.random() < round_claimed_rate:
            rec["total_claimed_years"] = float(round(summed))  # round to whole year
        else:
            rec["total_claimed_years"] = round(summed, 1)
        out.append(rec)
    return out


def _abs(value: str) -> int:
    v = str(value).strip().lower()
    if v in ("present", "current", "now"):
        return 2026 * 12
    parts = v.split("-")
    y = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 1
    return y * 12 + (m - 1)


def _summed_years(jobs: List[Dict]) -> float:
    total = 0
    for j in jobs:
        total += max(0, _abs(j["end"]) - _abs(j["start"]))
    return total / 12.0


def _fp_on(seeds, n) -> Dict:
    overall, by_flag = [], {}
    for s in seeds:
        pop = generate_realistic(n=n, master_seed=20260612 + s)
        flagged = 0
        counts: Dict[str, int] = {}
        for rec in pop:
            _, flags, _ = timeline_score(rec)
            if flags:
                flagged += 1
            for f in flags:
                counts[f.code] = counts.get(f.code, 0) + 1
        overall.append(flagged / len(pop))
        for code, c in counts.items():
            by_flag.setdefault(code, []).append(c / len(pop))
    return {"fp_overall": mean_ci(overall),
            "fp_by_flag": {k: mean_ci(v) for k, v in by_flag.items()}}


def _recall_on(seeds, n) -> float:
    """Overlap-fraud recall under the current engine settings (sanity check)."""
    hits = total = 0
    for s in seeds:
        rng = random.Random(99 + s)
        pop = generate_realistic(n=n, master_seed=20260612 + s)
        for rec in pop:
            fr = inject(rec, "employment_overlap", rng)
            total += 1
            if any(f.code == "EMPLOYMENT_OVERLAP" for f in timeline_score(fr)[1]):
                hits += 1
    return round(hits / total, 4) if total else 0.0


def realistic_fp(seeds=range(20), n: int = 3000) -> Dict:
    """Deterministic-engine FP on realistic genuine data: naive vs. granularity-aware.

    Toggles ``YEAR_GRANULARITY_SLACK_MONTHS`` to isolate the effect of treating
    year-granular dates as sub-year-ambiguous. Also reports overlap-fraud recall
    under both settings to confirm the mitigation does not cost detection power.
    """
    seeds = list(seeds)
    orig = TL.YEAR_GRANULARITY_SLACK_MONTHS
    TL.YEAR_GRANULARITY_SLACK_MONTHS = 0
    naive = _fp_on(seeds, n)
    naive_recall = _recall_on(seeds[:5], min(n, 2000))
    TL.YEAR_GRANULARITY_SLACK_MONTHS = orig
    aware = _fp_on(seeds, n)
    aware_recall = _recall_on(seeds[:5], min(n, 2000))
    return {
        "n_per_seed": n,
        "seeds": len(seeds),
        "naive_parsing": {**naive, "overlap_fraud_recall": naive_recall},
        "granularity_aware": {**aware, "overlap_fraud_recall": aware_recall},
    }


def realistic_fp_sweep(rates=(0.0, 0.03, 0.07, 0.12, 0.20), seeds=range(10), n: int = 2000) -> List[Dict]:
    """Sensitivity: FP vs. prevalence of legitimately concurrent full-time roles.

    Uses the granularity-aware engine so the residual FP is attributable to
    genuinely concurrent employment, not to date-rounding artefacts.
    """
    out = []
    for r in rates:
        vals = []
        for s in seeds:
            pop = generate_realistic(n=n, master_seed=20260612 + s, concurrent_fulltime_rate=r)
            fp = sum(1 for rec in pop if timeline_score(rec)[1]) / len(pop)
            vals.append(fp)
        out.append({"concurrent_rate": r, "fp": mean_ci(vals)})
    return out


if __name__ == "__main__":
    import json
    print(json.dumps({"realistic_fp": realistic_fp(),
                      "realistic_fp_concurrent_sweep": realistic_fp_sweep()}, indent=2))
