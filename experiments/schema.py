"""Canonical career-trajectory record used across all dataset loaders.

Every loader (KARRIEREWEGE, Kaggle structured, synthetic) normalises to this
shape so the fraud-injection and evaluation code is dataset-agnostic.

record = {
  "candidate_id": str,
  "age": int | None,
  "graduation_year": int | None,
  "total_claimed_years": float | None,
  "jobs": [ {"title": str|None, "company": str|None,
             "start": "YYYY" | "YYYY-MM", "end": "YYYY"|"YYYY-MM"|"present",
             "employment_type": "full_time"|"part_time"|"contract"} ],
}
"""
from __future__ import annotations
from typing import Dict


def summed_years(rec: Dict) -> float:
    total = 0.0
    for j in rec.get("jobs", []):
        try:
            s = int(str(j["start"]).split("-")[0])
            e_raw = str(j["end"]).lower()
            e = 2026 if e_raw in ("present", "current", "now") else int(e_raw.split("-")[0])
            total += max(0, e - s)
        except (KeyError, ValueError):
            continue
    return float(total)
