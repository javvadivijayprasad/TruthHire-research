"""Generator of AI-fabricated (agent-style) career trajectories.

A wholly-synthetic identity built by an LLM tends to be *internally consistent*
(so the deterministic timeline layer cannot catch it) yet *too regular* — round
tenures, uniform durations, January-to-January spans, no employment gaps, and a
smooth title escalator. This generator emulates those statistical tells so the
inferential layer can be evaluated. It is a stand-in for true LLM generation
(e.g., agent frameworks [3]); swap in real generations when available.
"""
from __future__ import annotations
import random
from typing import Dict, List

from .schema import summed_years

_TITLE_LADDER = ["Associate", "Engineer", "Senior Engineer", "Lead Engineer",
                 "Principal Engineer", "Director of Engineering"]
_EMPLOYERS = ["TechCorp", "InnovateX", "NextGen Solutions", "CloudWorks",
              "DataSphere", "FutureSystems", "PeakSoft", "BrightLabs"]


def generate_fabricated(n: int = 1500, master_seed: int = 4242, noise: float = 0.0) -> List[Dict]:
    """Internally-consistent but distributionally over-regular trajectories."""
    rng = random.Random(master_seed)
    out: List[Dict] = []
    for i in range(n):
        grad_age = 22 if rng.random() > noise else rng.choice([21, 22, 23, 24])
        birth = rng.randint(1980, 1998)
        grad_year = birth + grad_age
        age = 2026 - birth
        base_tenure = rng.choice([3, 4, 5])
        cursor = grad_year
        jobs = []
        for lvl in range(rng.randint(2, 4)):
            if cursor >= 2026:
                break
            tenure = base_tenure + (rng.choice([-1, 0, 1, 2]) if rng.random() < noise else 0)
            tenure = max(1, tenure)
            end = min(cursor + tenure, 2026)
            jobs.append({
                "title": _TITLE_LADDER[min(lvl, len(_TITLE_LADDER) - 1)],
                "company": rng.choice(_EMPLOYERS),
                "start": f"{cursor}-{(rng.randint(1,9) if rng.random() < noise else 1):02d}",
                "end": "present" if end >= 2026 else f"{end}-01",
                "employment_type": "full_time",
            })
            if end >= 2026:
                break
            cursor = end + (1 if rng.random() < noise * 0.5 else 0)
        if not jobs:
            continue
        rec = {"candidate_id": f"fab-{i:05d}", "age": age,
               "graduation_year": grad_year, "jobs": jobs, "_label": "fabricated"}
        rec["total_claimed_years"] = summed_years(rec)
        out.append(rec)
    return out
