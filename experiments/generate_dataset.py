"""Deterministic genuine-population generator from seed tables.

Reproducibility contract (matches the TestCaseGen / Defect-Analysis idiom):
re-running with the same master seed regenerates an identical dataset, verified
by a SHA-256 content hash written to a provenance/audit record.
"""
from __future__ import annotations
import hashlib
import json
import os
import random
from typing import Dict, List

from .schema import summed_years

SEEDS_PATH = os.path.join(os.path.dirname(__file__), "seeds", "seed_tables.json")


def _load_seeds(path: str = SEEDS_PATH) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def generate(n: int = 3000, master_seed: int = 20260612, seeds_path: str = SEEDS_PATH) -> List[Dict]:
    """Generate n internally-consistent (clean) trajectories deterministically."""
    s = _load_seeds(seeds_path)
    rng = random.Random(master_seed)
    out: List[Dict] = []
    for i in range(n):
        grad_age = rng.choice(s["grad_age_distribution"])
        birth = rng.randint(*s["birth_year_range"])
        grad_year = birth + grad_age
        age = 2026 - birth
        cursor = grad_year
        jobs = []
        for _ in range(rng.choice(s["jobs_per_career_distribution"])):
            if cursor >= 2026:
                break
            dur = rng.choice(s["job_duration_years_distribution"])
            end = min(cursor + dur, 2026)
            jobs.append({
                "title": rng.choice(s["titles"]),
                "company": rng.choice(s["employers"]),
                "start": f"{cursor}-01",
                "end": "present" if end >= 2026 else f"{end}-01",
                "employment_type": "full_time",
            })
            if end >= 2026:
                break
            cursor = end + rng.choice(s["gap_years_distribution"])
        if not jobs:
            continue
        rec = {"candidate_id": f"gen-{i:05d}", "age": age,
               "graduation_year": grad_year, "jobs": jobs}
        rec["total_claimed_years"] = summed_years(rec)
        out.append(rec)
    return out


def content_hash(records: List[Dict]) -> str:
    blob = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def write_dataset(records: List[Dict], out_dir: str, master_seed: int) -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    data_path = os.path.join(out_dir, "genuine.jsonl")
    with open(data_path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    audit = {
        "generator": "experiments/generate_dataset.py",
        "master_seed": master_seed,
        "record_count": len(records),
        "content_sha256": content_hash(records),
        "seed_tables": os.path.relpath(SEEDS_PATH, out_dir),
        "schema": "experiments/schema.py",
    }
    with open(os.path.join(out_dir, "build_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(audit, fh, indent=2)
    return audit
