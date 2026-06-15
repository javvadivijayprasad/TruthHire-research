#!/usr/bin/env bash
# Download the real public corpora locally (run on your machine; not in the sandbox).
# After downloading, point the loader at the file and run the FP experiment.
set -e
ROOT="$(cd "$(dirname "$0")/.."; pwd)/datasets/external"
mkdir -p "$ROOT"; cd "$ROOT"

echo "[1/3] Dated resume corpus -> the false-positive HEADLINE number"
# datasetmaster/resumes (MIT). Each experience carries employment dates, so the
# deterministic timeline checks (overlap / inflation) actually apply. This is the
# corpus used for the real-data FP measurement.
#   pip install huggingface_hub
python - <<'PY' || echo "  (install huggingface_hub: pip install huggingface_hub)"
from huggingface_hub import hf_hub_download
p = hf_hub_download(repo_id="datasetmaster/resumes",
                    filename="master_resumes.jsonl",
                    repo_type="dataset", local_dir=".")
print("downloaded:", p)
PY

echo "[2/3] KARRIEREWEGE (arXiv:2412.14612) — NOT usable for the date FP number"
# NOTE: KARRIEREWEGE has NO employment dates (only ordered ESCO occupation
# sequences: _id, experience_order, titles/descriptions). The deterministic
# engine's date checks cannot fire, so it yields no false-positive rate. Kept
# here only for reference / sequence-level analysis.
# git clone https://github.com/elenasenger/karrierewege.git || true

echo "[3/3] Kaggle 54k structured resumes (optional, needs ~/.kaggle/kaggle.json)"
# kaggle datasets download -d suriyaganesh/resume-dataset-structured -p ./kaggle_structured --unzip || true

echo "Done. Then run, from the research repo root:"
echo "  PYTHONPATH=. python -m experiments.run_experiment --resume-corpus $ROOT/master_resumes.jsonl"
echo "  -> writes results/truthhire_realdata_fp_results.json (false_positive_rate + date coverage)"
