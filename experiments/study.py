"""Run the full expanded study and dump machine-readable results."""
import json, os
from experiments import sweeps as S

PAPER = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "paper"))


def run():
    os.makedirs(f"{PAPER}/results", exist_ok=True)
    study = {
        "incentive_ci": S.incentive_ci(),
        "incentive_threshold": S.incentive_threshold(),
        "privacy_coverage": S.privacy_coverage(),
        "det_attribution": S.det_attribution(),
        "det_tolerance": S.det_tolerance(),
        "agent_sophistication": S.agent_sophistication(),
        "agent_feature_ablation": S.agent_feature_ablation(),
        "network_flywheel": S.network_flywheel(),
        "fraud_ring": S.fraud_ring_sweep(),
        "economics": S.economics(),
    }
    json.dump(study, open(f"{PAPER}/results/study.json", "w"), indent=2)
    print(f"wrote {PAPER}/results/study.json")
    return study


if __name__ == "__main__":
    run()
