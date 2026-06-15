"""Diagnose what is driving false positives on a dated resume corpus.

Prints: top-level record fields (to spot a real/synthetic marker), a few flagged
examples with their job dates and overlap sizes, and summary stats that reveal
whether overlaps look like random synthetic dates vs. genuine messy careers.
"""
from __future__ import annotations
import json, sys, collections
from experiments.loaders import load_resume_corpus, RC_CONFIG, _first
from app.timeline import timeline_score, _spans, _overlap_months


def main(path, raw_path=None):
    loaded = load_resume_corpus(path)
    recs = loaded["records"]
    print("REPORT:", json.dumps(loaded["report"]))

    # 1) raw top-level fields (look for a real/synthetic source flag)
    with open(path, encoding="utf-8") as fh:
        first_raw = json.loads(next(l for l in fh if l.strip()))
    print("\nTOP-LEVEL FIELDS:", sorted(first_raw.keys()))
    exps = _first(first_raw, RC_CONFIG["experiences_field"]) or []
    if exps and isinstance(exps[0], dict):
        print("EXPERIENCE FIELDS:", sorted(exps[0].keys()))
        print("SAMPLE EXPERIENCE:", json.dumps(exps[0])[:400])

    # 2) flagged examples + overlap sizes
    jobs_per = collections.Counter()
    overlap_sizes = []
    exact_dupe_pairs = 0
    shown = 0
    flagged = 0
    for r in recs:
        jobs_per[len(r["jobs"])] += 1
        _, flags, _ = timeline_score(r)
        if not flags:
            continue
        flagged += 1
        full = [s for s in _spans(r["jobs"]) if s.employment_type == "full_time"]
        for i in range(len(full)):
            for k in range(i+1, len(full)):
                ov = _overlap_months(full[i], full[k])
                if ov > 3:
                    overlap_sizes.append(ov)
                    if full[i].start_month == full[k].start_month and full[i].end_month == full[k].end_month:
                        exact_dupe_pairs += 1
        if shown < 6 and any(f.code == "EMPLOYMENT_OVERLAP" for f in flags):
            shown += 1
            print(f"\n--- flagged {r['candidate_id']} ---")
            for j in r["jobs"]:
                print(f"    {j['start']} -> {j['end']}  {j.get('title')}")

    print("\nSTATS")
    print("  flagged records:", flagged, "/", len(recs))
    print("  jobs-per-person:", dict(sorted(jobs_per.items())))
    if overlap_sizes:
        overlap_sizes.sort()
        n = len(overlap_sizes)
        print("  overlap pairs >3mo:", n)
        print("  overlap months  min/median/max: %d / %d / %d" %
              (overlap_sizes[0], overlap_sizes[n//2], overlap_sizes[-1]))
        print("  exact-duplicate date pairs (synthetic signature):", exact_dupe_pairs)


if __name__ == "__main__":
    main(sys.argv[1])
