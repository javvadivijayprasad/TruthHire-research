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


# ----------------------------------------------------- dated resume corpora
# Generic loader for nested-JSON resume corpora that DO carry employment dates
# (e.g. HF `datasetmaster/resumes`, MIT-licensed). Field spellings vary across
# corpora, so every key is matched first-wins and we also parse a single
# combined "start - end" range field. Records with no dated experience are
# reported (not silently dropped) so a zero result is never mistaken for "0% FP".
import re as _re

RC_CONFIG = {
    "experiences_field": [
        "experience", "experiences", "work_experience", "workExperience",
        "employment", "work_history", "professional_experience", "jobs",
        "positions", "career",
    ],
    "title_keys": ["job_title", "jobTitle", "title", "position", "role", "designation"],
    "company_keys": ["company", "company_name", "companyName", "employer",
                     "organization", "organisation"],
    "start_keys": ["start_date", "startDate", "start", "from", "begin",
                   "date_from", "dateFrom", "start_year", "startYear"],
    "end_keys": ["end_date", "endDate", "end", "to", "until", "date_to",
                 "dateTo", "end_year", "endYear"],
    # single field holding a combined range, e.g. "Jan 2019 - Present"
    "range_keys": ["dates", "employment_dates", "duration", "period",
                   "date_range", "dateRange", "employment_period", "tenure",
                   "years"],
    # sub-objects that may themselves hold start/end (one level of nesting)
    "nested_date_objs": ["dates", "duration", "period", "date_range", "dateRange"],
}

_RANGE_SEP = _re.compile(r"\s*[–—]\s*|\s+to\s+|\s+-\s+|\s+until\s+", _re.I)


def _split_range(val):
    """Split a combined range string into (start, end); None if not splittable."""
    if val is None:
        return None, None
    s = str(val).strip()
    parts = _RANGE_SEP.split(s, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, None


def _exp_dates(e: dict):
    """Best-effort (start, end) extraction from one experience dict."""
    start = _norm_year_month(_first(e, RC_CONFIG["start_keys"]))
    end = _norm_year_month(_first(e, RC_CONFIG["end_keys"]))
    if start and end:
        return start, end
    # combined range field
    for k in RC_CONFIG["range_keys"]:
        if k in e and e[k]:
            a, b = _split_range(e[k])
            if a and b:
                return _norm_year_month(a), _norm_year_month(b)
    # nested date object
    for k in RC_CONFIG["nested_date_objs"]:
        sub = e.get(k)
        if isinstance(sub, dict):
            s2 = _norm_year_month(_first(sub, RC_CONFIG["start_keys"]))
            e2 = _norm_year_month(_first(sub, RC_CONFIG["end_keys"]))
            if s2 and e2:
                return s2, e2
    return start, end  # may be partial/None


def _company_of(e: dict):
    c = _first(e, RC_CONFIG["company_keys"])
    if isinstance(c, dict):
        c = _first(c, ["name", "company_name", "companyName"]) or None
    return c


def load_resume_corpus(path: str, limit: Optional[int] = None) -> Dict:
    """Load a dated resume corpus -> canonical records + a coverage report.

    Returns {"records": [...], "report": {...}}. Only experiences with BOTH a
    start and end date contribute to the timeline checks; the report says how
    many resumes and jobs carried usable dates so a low FP is never confused
    with low date coverage.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Download the corpus first (see README).")
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jsonl", ".ndjson"):
        rows = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    elif ext == ".json":
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
        if isinstance(rows, dict):
            rows = rows.get("data") or rows.get("resumes") or list(rows.values())
    else:
        raise ValueError(f"Unsupported extension {ext}; use .jsonl/.json")

    out: List[Dict] = []
    n_people = n_with_dates = n_jobs = n_dated_jobs = 0
    for i, obj in enumerate(rows):
        if not isinstance(obj, dict):
            continue
        n_people += 1
        exps = _first(obj, RC_CONFIG["experiences_field"]) or []
        if isinstance(exps, dict):
            exps = list(exps.values())
        jobs = []
        for e in exps:
            if not isinstance(e, dict):
                continue
            n_jobs += 1
            start, end = _exp_dates(e)
            if not (start and end):
                continue
            n_dated_jobs += 1
            jobs.append({"title": _first(e, RC_CONFIG["title_keys"]),
                         "company": _company_of(e), "start": start, "end": end,
                         "employment_type": "full_time"})
        if not jobs:
            continue
        n_with_dates += 1
        rec = {"candidate_id": str(obj.get("id", obj.get("_id", i))),
               "age": None, "graduation_year": None, "jobs": jobs}
        rec["total_claimed_years"] = summed_years(rec)
        out.append(rec)
        if limit and len(out) >= limit:
            break

    report = {"people_seen": n_people, "people_with_dated_jobs": n_with_dates,
              "jobs_seen": n_jobs, "jobs_with_dates": n_dated_jobs,
              "usable_records": len(out)}
    return {"records": out, "report": report}
