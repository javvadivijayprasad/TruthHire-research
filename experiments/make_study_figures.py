"""Generate the expanded figure set from results/study.json."""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAPER = __import__("os").path.normpath(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "paper"))
OUT = f"{PAPER}/figures"; os.makedirs(OUT, exist_ok=True)
S = json.load(open(f"{PAPER}/results/study.json"))
plt.rcParams.update({"font.size": 11})
BLUE, RED, GREEN, ORANGE, GREY = "#2E6FB0", "#C0392B", "#2E8B57", "#E0A030", "#888888"

def band(ax, xs, mcs, color, label, marker="o"):
    m=[v[0] for v in mcs]; lo=[v[1] for v in mcs]; hi=[v[2] for v in mcs]
    ax.plot(xs, m, marker+"-", color=color, label=label)
    ax.fill_between(xs, lo, hi, color=color, alpha=.18)

# 5 incentive CI (FP)
d=S["incentive_ci"]; xs=sorted({r["strategic"] for r in d})
nv=[next(r for r in d if r["strategic"]==x and r["regime"]=="naive")["fp"] for x in xs]
pp=[next(r for r in d if r["strategic"]==x and r["regime"]=="proposed")["fp"] for x in xs]
fig,ax=plt.subplots(figsize=(6.2,3.6)); band(ax,[x*100 for x in xs],nv,RED,"naive"); band(ax,[x*100 for x in xs],pp,GREEN,"proposed","s")
ax.set_xlabel("strategic participants (%)"); ax.set_ylabel("network FP rate"); ax.set_title("Network FP vs. strategy (30 seeds, 95% CI)"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_incentive_ci.png",dpi=160); plt.close(fig)

# 6 threshold sweep
d=S["incentive_threshold"]; th=[r["threshold"] for r in d]
fig,ax=plt.subplots(figsize=(6.2,3.6))
band(ax,th,[r["recall"] for r in d],BLUE,"network recall")
ax.plot(th,[r["fp"][0] for r in d],"s--",color=RED,label="network FP")
ax.set_xlabel("corroboration threshold t"); ax.set_ylabel("rate"); ax.set_title("Threshold trades recall for safety (strat=50%)"); ax.set_xticks(th); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_threshold.png",dpi=160); plt.close(fig)

# 7 privacy coverage
d=S["privacy_coverage"]; cov=[r["coverage"]*100 for r in d]
fig,ax=plt.subplots(figsize=(6.2,3.6))
band(ax,cov,[r["naive"] for r in d],RED,"naive SHA-256")
band(ax,cov,[r["peppered_outsider"] for r in d],GREEN,"keyed (outsider)","s")
ax.plot([0,100],[0,1],":",color=GREY,label="re-id = coverage")
ax.set_xlabel("adversary coverage of universe (%)"); ax.set_ylabel("re-identification rate"); ax.set_title("Naive hashing leaks in proportion to coverage"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_privacy_coverage.png",dpi=160); plt.close(fig)

# 8 agent sophistication
d=S["agent_sophistication"]; nz=[r["noise"] for r in d]
fig,ax=plt.subplots(figsize=(6.2,3.6)); band(ax,nz,[r["auc"] for r in d],ORANGE,"regularity AUC")
ax.axhline(0.5,ls="--",color=GREY,label="chance"); ax.set_ylim(0,1)
ax.set_xlabel("fabrication sophistication (noise)"); ax.set_ylabel("ROC-AUC"); ax.set_title("Detector collapses to chance as fakes improve"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_sophistication.png",dpi=160); plt.close(fig)

# 9 feature ablation
d=S["agent_feature_ablation"]; keys=["january","uniformity","no_gap","roundness","combined"]
fig,ax=plt.subplots(figsize=(6.4,3.6))
bars=ax.bar(keys,[d[k] for k in keys],color=[BLUE,GREEN,BLUE,BLUE,ORANGE])
for b,k in zip(bars,keys): ax.text(b.get_x()+b.get_width()/2,d[k]+0.01,f"{d[k]:.2f}",ha="center",fontsize=9)
ax.axhline(0.5,ls="--",color=GREY); ax.set_ylim(0,1); ax.set_ylabel("ROC-AUC"); ax.set_title("Single-feature vs combined regularity (noise=0)")
fig.tight_layout(); fig.savefig(f"{OUT}/fig_ablation.png",dpi=160); plt.close(fig)

# 10 flywheel
d=S["network_flywheel"]; pt=[r["participation"]*100 for r in d]
fig,ax=plt.subplots(figsize=(6.2,3.6)); band(ax,pt,[r["catch_rate"] for r in d],BLUE,"network catch rate")
ax.set_xlabel("participation (% of orgs on network)"); ax.set_ylabel("repeat-fraud catch rate"); ax.set_title("Contributory-network flywheel"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_flywheel.png",dpi=160); plt.close(fig)

# 11 fraud ring
d=S["fraud_ring"]; k=[r["identities"] for r in d]
fig,ax=plt.subplots(figsize=(6.2,3.6)); band(ax,k,[r["detection"] for r in d],GREEN,"ring detection")
ax.set_xlabel("identities used by one actor (k)"); ax.set_ylabel("detection rate"); ax.set_title("Fraud-ring detection via shared-identifier linkage"); ax.set_xticks(k); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_fraud_ring.png",dpi=160); plt.close(fig)

# 12 economics
d=S["economics"]; cr=[r["contribution_ratio"]*100 for r in d]
fig,ax=plt.subplots(figsize=(6.2,3.6))
ax.plot(cr,[r["effective_price"] for r in d],"o-",color=BLUE,label="effective price ($/check)")
ax2=ax.twinx(); ax2.plot(cr,[r["savings_pct"] for r in d],"s--",color=GREEN,label="savings (%)")
ax.set_xlabel("contribution ratio (%)"); ax.set_ylabel("$/check",color=BLUE); ax2.set_ylabel("savings (%)",color=GREEN)
ax.set_title("Contribution-credit economics"); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_economics.png",dpi=160); plt.close(fig)

# 13 attribution heatmap
import numpy as np
d=S["det_attribution"]; ftypes=list(d.keys()); codes=sorted({c for v in d.values() for c in v})
M=np.array([[d[f].get(c,0.0) for c in codes] for f in ftypes])
fig,ax=plt.subplots(figsize=(7.6,3.4)); im=ax.imshow(M,cmap="Blues",vmin=0,vmax=1,aspect="auto")
ax.set_xticks(range(len(codes))); ax.set_xticklabels([c.replace("_","\n") for c in codes],fontsize=8)
ax.set_yticks(range(len(ftypes))); ax.set_yticklabels([f.replace("_"," ") for f in ftypes],fontsize=9)
for i in range(len(ftypes)):
    for j in range(len(codes)):
        if M[i,j]>0: ax.text(j,i,f"{M[i,j]:.2f}",ha="center",va="center",fontsize=8,color="white" if M[i,j]>0.5 else "black")
ax.set_title("Which check fires on which fraud type"); fig.colorbar(im,fraction=0.025)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_attribution.png",dpi=160); plt.close(fig)

print("figures:", sorted(f for f in os.listdir(OUT) if f.endswith(".png")))
