"""Detection experiment for AI-fabricated identities (Section 6.x).

Two findings:
  (1) The deterministic layer's recall on internally-consistent fabrications is
      ~0 -- well-formed fakes do not contradict themselves -- which motivates the
      inferential layer.
  (2) A lightweight *regularity* score separates fabricated from genuine-style
      trajectories; we report ROC-AUC. (Illustrative on synthetic populations;
      pending validation on real LLM-generated CVs.)
"""
from __future__ import annotations
from typing import Dict, List, Tuple

from app.timeline import timeline_score
from .generate_dataset import generate
from .agent_generator import generate_fabricated


def _months(j) -> Tuple[int, int]:
    s = int(str(j["start"]).split("-")[0]) * 12 + (int(str(j["start"]).split("-")[1]) - 1 if "-" in str(j["start"]) else 0)
    e_raw = str(j["end"]).lower()
    if e_raw in ("present", "current", "now"):
        e = 2026 * 12
    else:
        parts = str(j["end"]).split("-")
        e = int(parts[0]) * 12 + (int(parts[1]) - 1 if len(parts) > 1 else 0)
    return s, e


def regularity_score(rec: Dict) -> float:
    """Higher = more 'too regular' = more likely fabricated. Range ~0..1."""
    jobs = rec.get("jobs", [])
    if len(jobs) < 2:
        return 0.0
    spans = [_months(j) for j in jobs]
    durs = [max(0, e - s) for s, e in spans]
    # 1) all starts in January?
    jan = sum(1 for j in jobs if str(j["start"]).endswith("-01")) / len(jobs)
    # 2) duration uniformity (low variance -> high)
    mean = sum(durs) / len(durs)
    var = sum((d - mean) ** 2 for d in durs) / len(durs)
    uni = 1.0 / (1.0 + var / 9.0)
    # 3) no gaps between consecutive jobs?
    gaps = 0
    for k in range(1, len(spans)):
        if spans[k][0] - spans[k - 1][1] > 1:
            gaps += 1
    no_gap = 1.0 - gaps / (len(spans) - 1)
    # 4) round-year tenures (multiples of 12 months)?
    roundness = sum(1 for d in durs if d % 12 == 0) / len(durs)
    return 0.30 * jan + 0.30 * uni + 0.20 * no_gap + 0.20 * roundness


def regularity_features(rec):
    jobs = rec.get("jobs", [])
    if len(jobs) < 2:
        return {"january": 0.0, "uniformity": 0.0, "no_gap": 0.0, "roundness": 0.0}
    spans = [_months(j) for j in jobs]
    durs = [max(0, e - s) for s, e in spans]
    jan = sum(1 for j in jobs if str(j["start"]).endswith("-01")) / len(jobs)
    mean = sum(durs) / len(durs)
    var = sum((d - mean) ** 2 for d in durs) / len(durs)
    uni = 1.0 / (1.0 + var / 9.0)
    gaps = sum(1 for k in range(1, len(spans)) if spans[k][0] - spans[k-1][1] > 1)
    no_gap = 1.0 - gaps / (len(spans) - 1)
    roundness = sum(1 for d in durs if d % 12 == 0) / len(durs)
    return {"january": jan, "uniformity": uni, "no_gap": no_gap, "roundness": roundness}


def roc_auc(scores: List[float], labels: List[int]) -> float:
    pairs = sorted(zip(scores, labels))
    pos = sum(labels); neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return 0.5
    # rank-sum (Mann-Whitney) AUC
    ranks = {}
    i = 0
    srt = sorted(range(len(scores)), key=lambda k: scores[k])
    r = 1
    while i < len(srt):
        j = i
        while j + 1 < len(srt) and scores[srt[j + 1]] == scores[srt[i]]:
            j += 1
        avg = (r + (r + (j - i))) / 2.0
        for k in range(i, j + 1):
            ranks[srt[k]] = avg
        r += (j - i + 1); i = j + 1
    sum_pos = sum(ranks[k] for k in range(len(labels)) if labels[k] == 1)
    return (sum_pos - pos * (pos + 1) / 2.0) / (pos * neg)


def run():
    genuine = generate(n=1500, master_seed=20260612)
    fabricated = generate_fabricated(n=1500)

    # (1) deterministic recall on fabricated
    caught = sum(1 for r in fabricated if timeline_score(r)[0] >= 1)
    det_recall = caught / len(fabricated)
    # deterministic false positive on genuine
    fp = sum(1 for r in genuine if timeline_score(r)[0] >= 1) / len(genuine)

    # (2) regularity-score separation
    scores = [regularity_score(r) for r in genuine] + [regularity_score(r) for r in fabricated]
    labels = [0] * len(genuine) + [1] * len(fabricated)
    auc = roc_auc(scores, labels)
    mg = sum(regularity_score(r) for r in genuine) / len(genuine)
    mf = sum(regularity_score(r) for r in fabricated) / len(fabricated)

    res = {
        "deterministic_recall_on_fabricated": round(det_recall, 4),
        "deterministic_fp_on_genuine": round(fp, 4),
        "regularity_auc": round(auc, 4),
        "mean_regularity_genuine": round(mg, 3),
        "mean_regularity_fabricated": round(mf, 3),
        "n_genuine": len(genuine), "n_fabricated": len(fabricated),
    }
    import json; print(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    run()
