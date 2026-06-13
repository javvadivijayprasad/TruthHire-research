"""Simulation of the incentive adverse-selection failure mode (Section 4.4).

A consortium of participants screens candidates and contributes reports. Under a
reward schedule that pays MORE for a 'fraud' report than a 'legitimate' one,
self-interested participants over-label genuine borderline candidates as fraud
to farm credits. We measure the resulting network false-positive rate and
precision, and compare against the proposed regime (outcome-symmetric reward +
report-corroboration threshold t + reputation weighting).
"""
from __future__ import annotations
import collections
import random
from typing import Dict


def _simulate(strategic_frac: float, regime: str, seed: int = 0,
              n_part: int = 12, n_cand: int = 4000,
              fraud_prior: float = 0.2, borderline_frac: float = 0.3,
              threshold: int = None, reward_gap: float = None,
              use_reputation: bool = None) -> Dict:
    rng = random.Random(seed)
    # reward gap drives farming; proposed regime makes it zero (outcome-symmetric)
    if reward_gap is None: reward_gap = 1.0 if regime == "naive" else 0.0
    if threshold is None: threshold = 1 if regime == "naive" else 2
    if use_reputation is None: use_reputation = (regime == "proposed")

    strategic = [rng.random() < strategic_frac for _ in range(n_part)]

    # ground-truth candidates
    cands = []
    for _ in range(n_cand):
        is_fraud = rng.random() < fraud_prior
        borderline = rng.random() < borderline_frac
        cands.append((is_fraud, borderline))

    # warmup reputation: agreement of each participant with ground truth on a
    # held-out sample (a real system learns this from adjudication outcomes).
    rep = [1.0] * n_part
    if use_reputation:
        agree = [0] * n_part; total = [0] * n_part
        for is_fraud, borderline in cands[:1000]:
            p = rng.randrange(n_part)
            total[p] += 1
            farms = strategic[p] and borderline and (not is_fraud)
            reported_fraud = is_fraud or farms
            if reported_fraud == is_fraud:
                agree[p] += 1
        rep = [(agree[p] / total[p]) if total[p] else 1.0 for p in range(n_part)]

    reports = collections.defaultdict(list)
    for ci, (is_fraud, borderline) in enumerate(cands):
        for p in rng.sample(range(n_part), rng.randint(1, 3)):
            if not borderline:
                label = "fraud" if is_fraud else "legit"
            elif is_fraud:
                label = "fraud"
            else:  # genuine borderline -> farming target
                farm = strategic[p] and (rng.random() < reward_gap * 0.8)
                label = "fraud" if farm else "legit"
            reports[ci].append((p, label))

    flagged = set()
    for ci, reps in reports.items():
        if use_reputation:
            w = sum(rep[p] for p, l in reps if l == "fraud")
            if w >= threshold:
                flagged.add(ci)
        else:
            if sum(1 for _, l in reps if l == "fraud") >= threshold:
                flagged.add(ci)

    genuine = [i for i, c in enumerate(cands) if not c[0]]
    fraud = [i for i, c in enumerate(cands) if c[0]]
    fp = sum(1 for i in genuine if i in flagged)
    tp = sum(1 for i in fraud if i in flagged)
    return {
        "network_fp_rate": round(fp / len(genuine), 4) if genuine else 0.0,
        "network_precision": round(tp / len(flagged), 4) if flagged else 1.0,
        "network_recall": round(tp / len(fraud), 4) if fraud else 0.0,
    }


def run():
    print(f"{'strategic%':>10} | {'regime':>8} | {'FP rate':>8} | {'precision':>9} | {'recall':>7}")
    print("-" * 56)
    rows = []
    for sf in (0.0, 0.25, 0.5):
        for regime in ("naive", "proposed"):
            m = _simulate(sf, regime, seed=20260612)
            rows.append({"strategic_frac": sf, "regime": regime, **m})
            print(f"{int(sf*100):>9}% | {regime:>8} | {m['network_fp_rate']:>8} | "
                  f"{m['network_precision']:>9} | {m['network_recall']:>7}")
    return rows


if __name__ == "__main__":
    run()
