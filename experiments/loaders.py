"""Dataset loaders -> canonical records (schema.py).

- load_generated(): read the deterministically generated genuine population.
- load_karrierewege(): map the real KARRIEREWEGE corpus (download locally).
- load_kaggle_structured(): map Kaggle structured-resume corpora.
"""
from __future__ import annotations
import json
import os
import re
from typing import Dict, List, Optional

from .schema import summed_years

# ------------------------------------------------------------------ generated
def load_generated(path: str) -> List[Dict]:
    """Load JSONL produced by generate_dataset.write_dataset()."""
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# --------------------------------------------------------------- KARRIEREWEGE
# KARRIEREWEGE (arXiv:2412.14612) stores ordered work experiences per person.
# Field names vary by release/export, so the mapping is configurable: inspect a
# few rows of your download and adjust CONFIG, then run. The loader is tolerant
# of JSON, JSONL, and CSV and of several common column spellings.
KW_CONFIG = {
    # the field holding the ordered list of experiences (for nested formats)
    "experiences_field": ["experiences", "career", "path", "work_experience", "jobs"],
    # within one experience: title / start / end keys (first match wins)
    "title_keys": ["title", "job_title", "esco_label", "occupation", "position"],
    "start_keys": ["start", "start_date", "from", "begin", "startdate"],
    "end_keys": ["end", "end_date", "to", "until", "enddate"],
}


def _first(d: dict, keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _norm_year_month(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("present", "current", "now", "ongoing"):
        return "present"
    m = re.search(r"(\d{4})(?:[-/](\d{1,2}))?", s)
    if not m:
        return None
    return f"{m.group(1)}-{int(m.group(2)):02d}" if m.group(2) else m.group(1)


def _record_from_experiences(cid, experiences) -> Optional[Dict]:
    jobs = []
    for e in experiences:
        if not isinstance(e, dict):
            continue
        start = _norm_year_month(_first(e, KW_CONFIG["start_keys"]))
        end = _norm_year_month(_first(e, KW_CONFIG["end_keys"]))
        if not start or not end:
            continue
        jobs.append({"title": _first(e, KW_CONFIG["title_keys"]),
                     "company": None, "start": start, "end": end,
                     "employment_type": "full_time"})
    if not jobs:
        return None
    rec = {"candidate_id": str(cid), "age": None, "graduation_year": None, "jobs": jobs}
    rec["total_claimed_years"] = summed_years(rec)
    return rec


def load_karrierewege(path: str, limit: Optional[int] = None) -> List[Dict]:
    """Map a local KARRIEREWEGE export to canonical records.

    Supports: .jsonl / .json (list of person objects, each with an experiences
    list) and .csv (one experience per row with a person id to group on).
    Download: github.com/elenasenger/karrierewege (verify licence/terms).
    Age and graduation year are typically absent -> left None, so the age and
    graduation checks skip cleanly; the OVERLAP and INFLATION checks still apply,
    which is exactly the false-positive behaviour we want to measure on real,
    messy careers.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Download KARRIEREWEGE locally first (see README).")
    out: List[Dict] = []
    ext = os.path.splitext(path)[1].lower()

    if ext in (".jsonl", ".ndjson"):
        with open(path, encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if not line.strip():
                    continue
                obj = json.loads(line)
                exps = _first(obj, KW_CONFIG["experiences_field"]) or obj.get("items")
                rec = _record_from_experiences(obj.get("id", i), exps or [])
                if rec:
                    out.append(rec)
                if limit and len(out) >= limit:
                    break
    elif ext == ".json":
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        for i, obj in enumerate(data):
            exps = _first(obj, KW_CONFIG["experiences_field"]) or []
            rec = _record_from_experiences(obj.get("id", i), exps)
            if rec:
                out.append(rec)
            if limit and len(out) >= limit:
                break
    elif ext == ".csv":
        import csv, collections
        groups = collections.OrderedDict()
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                pid = row.get("person_id") or row.get("id") or row.get("cv_id") or "0"
                groups.setdefault(pid, []).append(row)
        for pid, rows in groups.items():
            rec = _record_from_experiences(pid, rows)
            if rec:
                out.append(rec)
            if limit and len(out) >= limit:
                break
    else:
        raise ValueError(f"Unsupported extension {ext}; use .jsonl/.json/.csv")
    return out


def load_kaggle_structured(path: str) -> List[Dict]:
    """Map Kaggle '54k structured resume' fields to schema (adjust to columns)."""
    raise NotImplementedError("Map Kaggle structured resume fields here.")
