#!/usr/bin/env bash
# Clone the real public corpora locally (run on your machine; not in the sandbox).
# After cloning, point the loader at the file and run the FP experiment.
set -e
ROOT="$(cd "$(dirname "$0")/.."; pwd)/datasets/external"
mkdir -p "$ROOT"; cd "$ROOT"

echo "[1/3] KARRIEREWEGE (career trajectories, arXiv:2412.14612)"
# Option A: git
git clone https://github.com/elenasenger/karrierewege.git || true
# Option B: Hugging Face (if mirrored): pip install datasets; python -c "from datasets import load_dataset; load_dataset('ElenaSenger/Karrierewege')"

echo "[2/3] Kaggle 54k structured resumes (needs Kaggle API token ~/.kaggle/kaggle.json)"
# pip install kaggle
kaggle datasets download -d suriyaganesh/resume-dataset-structured -p ./kaggle_structured --unzip || \
  echo "  (skip: configure Kaggle API token first)"

echo "[3/3] ResumeAtlas (arXiv:2406.18125) — see paper repo for the release link"

echo "Done. Then run, from truthhire_api/:"
echo "  PYTHONPATH=. python -m experiments.run_experiment --karrierewege $ROOT/karrierewege/<file>.jsonl"
