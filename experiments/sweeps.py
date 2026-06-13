"""Parameter sweeps and multi-seed studies feeding the paper's tables/figures."""
from __future__ import annotations
from typing import Dict, List

import app.timeline as TL
from app.timeline import timeline_score
from .generate_dataset import generate
from .fraud_injection import build_benchmark, inject, FRAUD_TYPES
from .evaluate import evaluate
from .sim_incentive import _simulate
from .sim_privacy import _identifier_universe, _sha, _hmac
from .agent_generator import generate_fabricated
from .sim_agent import regularity_score, regularity_features, roc_auc
from .sim_network import flywheel, fraud_ring
from .stats import mean_ci
import random


def incentive_ci(strategic=(0.0, 0.1, 0.25, 0.4, 0.5), regimes=("naive", "proposed"),
                 seeds=range(30)):
    out = []
    for sf in strategic:
        for rg in regimes:
            fp = [_simulate(sf, rg, seed=s)["network_fp_rate"] for s in seeds]
            pr = [_simulate(sf, rg, seed=s)["network_precision"] for s in seeds]
            rc = [_simulate(sf, rg, seed=s)["network_recall"] for s in seeds]
            out.append({"strategic": sf, "regime": rg,
                        "fp": mean_ci(fp), "precision": mean_ci(pr), "recall": mean_ci(rc)})
    return out


def incentive_threshold(thresholds=(1, 2, 3, 4), strategic=0.5, seeds=range(30)):
    out = []
    for th in thresholds:
        fp = [_simulate(strategic, "proposed", seed=s, threshold=th)["network_fp_rate"] for s in seeds]
        rc = [_simulate(strategic, "proposed", seed=s, threshold=th)["network_recall"] for s in seeds]
        out.append({"threshold": th, "fp": mean_ci(fp), "recall": mean_ci(rc)})
    return out


def privacy_coverage(coverages=(0.1, 0.25, 0.5, 0.75, 1.0), seeds=range(10)):
    out = []
    for c in coverages:
        naive, pepper = [], []
        for s in seeds:
            rng = random.Random(1000 + s)
            uni = _identifier_universe(8000, rng); shared = set(rng.sample(uni, 2000))
            guess = set(rng.sample(uni, int(len(uni) * c)))
            pub = {_sha(x) for x in shared}
            recov = sum(1 for x in (shared & guess) if _sha(x) in pub)
            naive.append(recov / len(shared))
            key = b"pepper"; pubk = {_hmac(key, x) for x in shared}
            recovk = sum(1 for x in (shared & guess) if _sha(x) in pubk)  # outsider, wrong fn
            pepper.append(recovk / len(shared))
        out.append({"coverage": c, "naive": mean_ci(naive), "peppered_outsider": mean_ci(pepper)})
    return out


def det_attribution(seed=20260612, n=2000):
    genuine = generate(n=n, master_seed=seed)
    rng = random.Random(seed + 5)
    rows = {ft: {} for ft in FRAUD_TYPES}
    for ft in FRAUD_TYPES:
        counts = {}
        total = 0
        for rec in genuine:
            r = inject(rec, ft, rng); total += 1
            _, flags, _ = timeline_score(r)
            for f in flags:
                counts[f.code] = counts.get(f.code, 0) + 1
        rows[ft] = {k: round(v / total, 3) for k, v in counts.items()}
    return rows


def det_tolerance(seed=20260612, n=2000):
    genuine = generate(n=n, master_seed=seed)
    rng = random.Random(seed + 7)
    overlap_fraud = [inject(r, "employment_overlap", rng) for r in genuine]
    inflation_fraud = [inject(r, "experience_inflation", rng) for r in genuine]
    res = {"overlap_months": [], "inflation_years": []}
    orig_o, orig_i = TL.OVERLAP_TOLERANCE_MONTHS, TL.INFLATION_TOLERANCE_YEARS
    for m in (0, 1, 3, 6, 12):
        TL.OVERLAP_TOLERANCE_MONTHS = m
        fp = sum(1 for r in genuine if any(f.code == "EMPLOYMENT_OVERLAP" for f in timeline_score(r)[1])) / len(genuine)
        rc = sum(1 for r in overlap_fraud if any(f.code == "EMPLOYMENT_OVERLAP" for f in timeline_score(r)[1])) / len(overlap_fraud)
        res["overlap_months"].append({"tol": m, "fp": round(fp, 4), "recall": round(rc, 4)})
    TL.OVERLAP_TOLERANCE_MONTHS = orig_o
    for y in (0, 1, 2, 3):
        TL.INFLATION_TOLERANCE_YEARS = y
        fp = sum(1 for r in genuine if any(f.code == "EXPERIENCE_INFLATION" for f in timeline_score(r)[1])) / len(genuine)
        rc = sum(1 for r in inflation_fraud if any(f.code == "EXPERIENCE_INFLATION" for f in timeline_score(r)[1])) / len(inflation_fraud)
        res["inflation_years"].append({"tol": y, "fp": round(fp, 4), "recall": round(rc, 4)})
    TL.INFLATION_TOLERANCE_YEARS = orig_i
    return res


def agent_sophistication(levels=(0.0, 0.25, 0.5, 0.75, 1.0), seeds=range(10), n=1000):
    out = []
    for nz in levels:
        aucs = []
        for s in seeds:
            g = generate(n=n, master_seed=20260612 + s)
            f = generate_fabricated(n=n, master_seed=4242 + s, noise=nz)
            sc = [regularity_score(r) for r in g] + [regularity_score(r) for r in f]
            lab = [0] * len(g) + [1] * len(f)
            aucs.append(roc_auc(sc, lab))
        out.append({"noise": nz, "auc": mean_ci(aucs)})
    return out


def agent_feature_ablation(seed=20260612, n=1500):
    g = generate(n=n, master_seed=seed); f = generate_fabricated(n=n, noise=0.0)
    feats = ["january", "uniformity", "no_gap", "roundness"]
    lab = [0] * len(g) + [1] * len(f)
    out = {}
    for feat in feats:
        sc = [regularity_features(r)[feat] for r in g] + [regularity_features(r)[feat] for r in f]
        out[feat] = round(roc_auc(sc, lab), 4)
    sc = [regularity_score(r) for r in g] + [regularity_score(r) for r in f]
    out["combined"] = round(roc_auc(sc, lab), 4)
    return out


def network_flywheel(part=(0.1, 0.25, 0.5, 0.75, 1.0), seeds=range(20)):
    return [{"participation": p, "catch_rate": mean_ci([flywheel(p, seed=s) for s in seeds])}
            for p in part]


def fraud_ring_sweep(identities=(1, 2, 3, 4, 5, 6), seeds=range(20)):
    return [{"identities": k, "detection": mean_ci([fraud_ring(k, seed=s) for s in seeds])}
            for k in identities]


def economics(contrib_ratios=(0.0, 0.25, 0.5, 0.75, 1.0), base_cost=0.35, price=0.75):
    """Effective cost per check vs contribution ratio (credits offset checks)."""
    out = []
    for c in contrib_ratios:
        credit_offset = c * 0.5 * price          # 0.5 blended credits per contributed profile
        eff = max(base_cost, price - credit_offset)
        out.append({"contribution_ratio": c, "effective_price": round(eff, 3),
                    "savings_pct": round(100 * (price - eff) / price, 1)})
    return out
