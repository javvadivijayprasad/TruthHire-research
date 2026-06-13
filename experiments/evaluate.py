"""Run the deterministic timeline engine over a benchmark and report metrics."""
from __future__ import annotations
import collections
from typing import List, Tuple

from app.timeline import timeline_score


def evaluate(benchmark: List[Tuple[dict, int, str]], decision_threshold: int = 1):
    tp = fp = tn = fn = 0
    per_type = collections.Counter()
    per_type_total = collections.Counter()
    for rec, label, ftype in benchmark:
        score, flags, _ = timeline_score(rec)
        pred = 1 if score >= decision_threshold else 0
        if label == 1:
            per_type_total[ftype] += 1
            if pred == 1:
                per_type[ftype] += 1
        if pred == 1 and label == 1: tp += 1
        elif pred == 1 and label == 0: fp += 1
        elif pred == 0 and label == 0: tn += 1
        else: fn += 1
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec_ = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec_ / (prec + rec_) if (prec + rec_) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "n": len(benchmark), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(prec, 4), "recall": round(rec_, 4),
        "f1": round(f1, 4), "false_positive_rate": round(fpr, 4),
        "recall_by_fraud_type": {k: round(per_type[k]/per_type_total[k], 4)
                                  for k in per_type_total},
    }
