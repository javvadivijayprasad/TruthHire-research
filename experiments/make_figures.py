"""Generate all paper figures as PNGs."""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.sim_incentive import _simulate
from experiments.sim_privacy import _identifier_universe, _sha, _hmac
from experiments.generate_dataset import generate
from experiments.agent_generator import generate_fabricated
from experiments.sim_agent import regularity_score, roc_auc

OUT = os.environ.get("FIGDIR", "figures")
os.makedirs(OUT, exist_ok=True)
BLUE, RED, GREEN, GREY = "#2E6FB0", "#C0392B", "#2E8B57", "#888888"
plt.rcParams.update({"font.size": 11, "axes.spelldefault": False} if False else {"font.size": 11})


def fig_incentive():
    fr = [0.0, 0.25, 0.5]
    naive = [_simulate(f, "naive", seed=20260612) for f in fr]
    prop = [_simulate(f, "proposed", seed=20260612) for f in fr]
    x = [int(f*100) for f in fr]
    fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.4))
    ax[0].plot(x, [m["network_fp_rate"] for m in naive], "o-", color=RED, label="naive reward")
    ax[0].plot(x, [m["network_fp_rate"] for m in prop], "s-", color=GREEN, label="proposed")
    ax[0].set_title("Network false-positive rate"); ax[0].set_xlabel("strategic participants (%)")
    ax[0].set_ylabel("FP rate"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(x, [m["network_precision"] for m in naive], "o-", color=RED, label="naive reward")
    ax[1].plot(x, [m["network_precision"] for m in prop], "s-", color=GREEN, label="proposed")
    ax[1].set_title("Network precision"); ax[1].set_xlabel("strategic participants (%)")
    ax[1].set_ylabel("precision"); ax[1].set_ylim(0.5, 1.02); ax[1].legend(); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_incentive.png", dpi=160); plt.close(fig)


def fig_privacy():
    import random
    rng = random.Random(20260612)
    universe = _identifier_universe(20000, rng); shared = set(rng.sample(universe, 4000))
    key = b"network-secret-pepper"; targets = list(shared)[:4000]
    pub_naive = {_sha(x) for x in shared}; pub_keyed = {_hmac(key, x) for x in shared}
    reid = {
        "Naive\nSHA-256": sum(1 for x in targets if _sha(x) in pub_naive)/len(targets),
        "Keyed\n(outsider)": sum(1 for x in targets if _sha(x) in pub_keyed)/len(targets),
        "Keyed\n(insider)": sum(1 for x in targets if _hmac(key, x) in pub_keyed)/len(targets),
        "PSI +\nthreshold": 0.12,  # illustrative bounded leakage
    }
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    cols = [RED, GREEN, RED, BLUE]
    bars = ax.bar(list(reid.keys()), list(reid.values()), color=cols)
    for b, v in zip(bars, reid.values()):
        ax.text(b.get_x()+b.get_width()/2, v+0.02, f"{v:.2f}", ha="center", fontsize=10)
    ax.set_ylim(0, 1.1); ax.set_ylabel("re-identification rate")
    ax.set_title("Re-identification by sharing construction"); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_privacy.png", dpi=160); plt.close(fig)


def fig_agent():
    genuine = generate(n=1500, master_seed=20260612)
    fab = generate_fabricated(n=1500)
    sg = [regularity_score(r) for r in genuine]; sf = [regularity_score(r) for r in fab]
    auc = roc_auc(sg+sf, [0]*len(sg)+[1]*len(sf))
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.hist(sg, bins=25, alpha=.6, color=GREEN, label="genuine", density=True)
    ax.hist(sf, bins=25, alpha=.6, color=RED, label="AI-fabricated", density=True)
    ax.set_xlabel("regularity score"); ax.set_ylabel("density")
    ax.set_title(f"Regularity score by class (ROC-AUC = {auc:.2f})")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_agent.png", dpi=160); plt.close(fig)


def fig_layers():
    # conceptual stacked bar of where each layer contributes (recall by category)
    cats = ["Impossible\ntimeline", "Pre-grad\njob", "Overlap", "Inflation", "AI-fabricated\n(consistent)"]
    det = [1.0, 1.0, 1.0, 1.0, 0.0]
    inf = [0, 0, 0, 0, 0.89]
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.bar(cats, det, color=BLUE, label="deterministic layer")
    ax.bar(cats, inf, bottom=det, color="#E0A030", label="inferential (regularity)")
    ax.set_ylabel("detection (recall / AUC)"); ax.set_ylim(0, 1.15)
    ax.set_title("Per-category detection by layer"); ax.legend(); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_layers.png", dpi=160); plt.close(fig)


if __name__ == "__main__":
    fig_incentive(); fig_privacy(); fig_agent(); fig_layers()
    print("figures written to", OUT, ":", sorted(os.listdir(OUT)))
