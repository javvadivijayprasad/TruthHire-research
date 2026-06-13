"""Semi-synthetic fraud injection.

No public corpus carries ground-truth 'experience fraud' labels, so we follow
the standard practice for fraud research without labels: take a genuine
population and inject controlled, labeled fraud of each type. This yields a
benchmark with known positives while preserving realistic genuine trajectories.
"""
from __future__ import annotations
import copy
import random
from typing import Dict, Tuple

FRAUD_TYPES = ["impossible_experience", "job_before_graduation",
               "employment_overlap", "experience_inflation"]


def inject(rec: Dict, fraud_type: str, rng: random.Random) -> Dict:
    r = copy.deepcopy(rec)
    if fraud_type == "impossible_experience":
        # claim more years than working life allows (age-18)
        if r.get("age"):
            r["total_claimed_years"] = (r["age"] - 18) + rng.randint(3, 12)
        else:
            r["total_claimed_years"] = 40
    elif fraud_type == "job_before_graduation":
        if r.get("graduation_year") and r["jobs"]:
            gy = r["graduation_year"]
            r["jobs"][0] = {**r["jobs"][0], "start": f"{gy - rng.randint(2,6)}-01"}
    elif fraud_type == "employment_overlap":
        if r["jobs"]:
            base = r["jobs"][0]
            s = int(str(base["start"]).split("-")[0])
            r["jobs"].append({"title": "Concurrent Role", "company": "OrgX",
                              "start": f"{s+1}-01", "end": f"{s+4}-01",
                              "employment_type": "full_time"})
            # ensure first job is long enough to overlap
            r["jobs"][0] = {**base, "end": f"{s+5}-01"}
    elif fraud_type == "experience_inflation":
        from .schema import summed_years
        r["total_claimed_years"] = summed_years(r) + rng.randint(5, 15)
    return r


def build_benchmark(genuine, fraud_rate: float = 0.5, seed: int = 11):
    """Return list of (record, label, fraud_type). label: 1=fraud, 0=genuine."""
    rng = random.Random(seed)
    out = []
    for rec in genuine:
        if rng.random() < fraud_rate:
            ft = rng.choice(FRAUD_TYPES)
            out.append((inject(rec, ft, rng), 1, ft))
        else:
            out.append((rec, 0, "genuine"))
    return out
