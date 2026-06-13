"""End-to-end experiment: generate (or load real) -> inject -> evaluate -> audit.

Usage:
  python -m experiments.run_experiment                 # seeded synthetic (reproducible)
  python -m experiments.run_experiment --karrierewege PATH   # real data (FP measurement)
"""
from __future__ import annotations
import argparse
import json
import os

from experiments.generate_dataset import generate, write_dataset, content_hash
from experiments.loaders import load_karrierewege
from experiments.fraud_injection import build_benchmark
from experiments.evaluate import evaluate

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "datasets", "truthhire")
RESULTS = os.path.join(HERE, "..", "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=20260612)
    ap.add_argument("--fraud-rate", type=float, default=0.5)
    ap.add_argument("--karrierewege", type=str, default=None,
                    help="Path to a local KARRIEREWEGE export; if set, real "
                         "genuine records are used and left unperturbed for the "
                         "false-positive measurement (no fraud injected).")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True)

    if args.karrierewege:
        genuine = load_karrierewege(args.karrierewege, limit=args.limit)
        bench = [(r, 0, "genuine") for r in genuine]   # FP-only run on real data
        source = {"source": "karrierewege", "path": args.karrierewege,
                  "records": len(genuine), "content_sha256": content_hash(genuine)}
    else:
        genuine = generate(n=args.n, master_seed=args.seed)
        audit = write_dataset(genuine, DATA_DIR, args.seed)
        bench = build_benchmark(genuine, fraud_rate=args.fraud_rate, seed=args.seed + 1)
        source = {"source": "seeded_synthetic", **audit}

    metrics = evaluate(bench)
    report = {"experiment": "truthhire_timeline_layer", "source": source,
              "benchmark_size": len(bench), "metrics": metrics}
    out_path = os.path.join(RESULTS, "truthhire_timeline_results.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    print(f"\nwrote {os.path.relpath(out_path)}")


if __name__ == "__main__":
    main()
