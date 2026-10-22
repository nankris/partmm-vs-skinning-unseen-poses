"""Descriptive, frame-level analysis on top of analyze.py (does NOT change the pre-registered verdicts).
1) error-over-time chart: per-frame held-out RMSE for PartMM / LBS / nearest pose, all 5 sequences.
2) two-level bootstrap (resample sequences, then test frames within each sequence), 10,000 resamples, seed 0.
3) per-sequence frame-bootstrap CI of PartMM's reduction vs LBS and vs nearest pose.
Reads run/full/<case>/metrics.json (rmse_per_frame); writes results/frame_bootstrap.json, tables/per_sequence_ci.md,
figures/error_over_time.png."""
import json
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 13})
R = Path(__file__).resolve().parents[1]
CASES = ["T_samba", "T_swing", "D_bouncing", "D_handstand", "I_jumping"]
pf = {c: {a: np.array(json.load(open(R / "run/full" / c / "metrics.json"))["metrics"][a]["rmse_per_frame"])
          for a in ["PM", "LBS", "NN"]} for c in CASES}
# sanity: per-frame means reproduce the per-sequence primary metric
for c in CASES:
    m = json.load(open(R / "run/full" / c / "metrics.json"))["metrics"]
    for a in ["PM", "LBS", "NN"]: assert abs(pf[c][a].mean() - m[a]["rmse"]) < 1e-9, (c, a)
rng = np.random.default_rng(0); B = 10000
def two_level(base):
    out = np.empty(B)
    for b in range(B):
        ss = rng.integers(0, len(CASES), len(CASES)); r = []
        for s in ss:
            c = CASES[s]; n = len(pf[c]["PM"]); fi = rng.integers(0, n, n)
            r.append((pf[c][base][fi].mean() - pf[c]["PM"][fi].mean()) / pf[c][base][fi].mean())
        out[b] = np.mean(r)
    return np.percentile(out, [2.5, 97.5]).tolist()
def per_seq(c, base):
    n = len(pf[c]["PM"]); fi = rng.integers(0, n, (B, n))
    A, P = pf[c][base][fi].mean(1), pf[c]["PM"][fi].mean(1)
    pt = (pf[c][base].mean() - pf[c]["PM"].mean()) / pf[c][base].mean()
    return pt, np.percentile((A - P) / A, [2.5, 97.5]).tolist(), int((pf[c]["PM"] < pf[c][base]).sum()), n
res = {"note": "descriptive only; verdicts use the pre-registered sequence-level bootstrap (results/summary.json)",
       "two_level_ci95": {"PM_vs_LBS": two_level("LBS"), "PM_vs_NN": two_level("NN")}, "per_sequence": {}}
rows = []
for c in CASES:
    l = per_seq(c, "LBS"); n_ = per_seq(c, "NN")
    res["per_sequence"][c] = {"vs_LBS": l, "vs_NN": n_}
    f = lambda x: f"{100*x:.0f}%".replace("-", "−")
    rows.append(f"| {c} | {l[3]} | {f(l[0])} | {f(l[1][0])} to {f(l[1][1])} | {l[2]}/{l[3]} | {f(n_[0])} | {f(n_[1][0])} to {f(n_[1][1])} | {n_[2]}/{n_[3]} |")
json.dump(res, open(R / "results/frame_bootstrap.json", "w"), indent=1)
tl = res["two_level_ci95"]
md = ["| Sequence | Test frames | vs LBS: reduction | 95% CI | Frames won | vs nearest pose: reduction | 95% CI | Frames won |",
      "|---|---:|---:|---:|---:|---:|---:|---:|"] + rows + [
      f"| **All 5 (two-level bootstrap)** | 165 | 21.8% | {100*tl['PM_vs_LBS'][0]:.1f}% to {100*tl['PM_vs_LBS'][1]:.1f}% | | 61.3% | {100*tl['PM_vs_NN'][0]:.1f}% to {100*tl['PM_vs_NN'][1]:.1f}% | |".replace("% to -", "% to −").replace("| -", "| −")]
open(R / "tables/per_sequence_ci.md", "w").write("\n".join(md) + "\n")
# error over time
cols = {"PM": "#2b6cb0", "LBS": "#dd6b20", "NN": "#38a169"}; LBL = {"PM": "PartMM", "LBS": "Fitted skinning (LBS)", "NN": "Nearest training pose"}
fig, axs = plt.subplots(1, 5, figsize=(20, 4.6), sharey=False)
for ax, c in zip(axs, CASES):
    for a in ["NN", "LBS", "PM"]: ax.plot(np.arange(1, len(pf[c][a]) + 1), 100 * pf[c][a], color=cols[a], lw=2.2 if a == "PM" else 1.6, label=LBL[a])
    ax.set_title(c); ax.set_xlabel("held-out frame (1 = first after training)"); ax.set_ylim(bottom=0); ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("vertex RMSE (% of body diagonal)")
h, l = axs[0].get_legend_handles_labels(); fig.legend(h[::-1], l[::-1], ncol=3, frameon=False, loc="upper center")
fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(R / "figures/error_over_time.png", dpi=150)
print(json.dumps(res, indent=1))
# p95 per-vertex error table (pre-registered secondary metric)
p95 = {c: {a: json.load(open(R / "run/full" / c / "metrics.json"))["metrics"][a]["p95"] for a in ["PM", "LBS", "NN", "STATIC"]} for c in CASES}
def cell(c, a):
    best = min(p95[c][x] for x in ["PM", "LBS", "NN"]); v = f"{100*p95[c][a]:.2f}"
    return f"**{v}**" if p95[c][a] == best else v
md = ["| Sequence | PartMM | Fitted skinning (LBS) | Nearest training pose | Static frame 0 | PartMM vs LBS |", "|---|---:|---:|---:|---:|---:|"]
for c in CASES:
    r = (p95[c]["PM"] - p95[c]["LBS"]) / p95[c]["LBS"]
    md.append(f"| {c} | {cell(c,'PM')} | {cell(c,'LBS')} | {cell(c,'NN')} | {100*p95[c]['STATIC']:.1f} | {'+' if r > 0 else '−'}{abs(100*r):.0f}% |")
mean = {a: np.mean([p95[c][a] for c in CASES]) for a in ["PM", "LBS", "NN", "STATIC"]}
md.append(f"| **Mean** | **{100*mean['PM']:.2f}** | {100*mean['LBS']:.2f} | {100*mean['NN']:.2f} | {100*mean['STATIC']:.1f} | |")
open(R / "tables/results_p95.md", "w").write("\n".join(md) + "\n")
