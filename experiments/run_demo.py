"""Demonstration run on synthetic genuine data + injected fraud.

Swap load_synthetic() for load_karrierewege(path) once the real corpus is local.
"""
import json
from experiments.loaders import load_synthetic
from experiments.fraud_injection import build_benchmark
from experiments.evaluate import evaluate

if __name__ == "__main__":
    genuine = load_synthetic(n=3000)
    bench = build_benchmark(genuine, fraud_rate=0.5)
    metrics = evaluate(bench)
    print(json.dumps(metrics, indent=2))
