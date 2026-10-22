"""Aggregate per-sequence metrics, bootstrap CIs, verdicts per PREREGISTRATION.md, figures."""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams.update({"font.size": 13})
R = Path(__file__).resolve().parents[1]; RUN = R / "run" / "full"; OUT = R / "results"; FIG = R / "figures"
OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
CASES = ["T_samba", "T_swing", "D_bouncing", "D_handstand", "I_jumping"]  # PREREGISTRATION Amendment 1 (5-sequence cut)
rows, dropped = {}, []
for c in CASES:
    f = RUN / c / "metrics.json"
    if f.exists(): rows[c] = json.load(open(f))
    else: dropped.append(c)
cs = list(rows)
arms = ["PM", "LBS", "NN", "STATIC"]
M = {k: np.array([rows[c]["metrics"][a][k] for c in cs for a in [arm]]) for k in ["rmse"] for arm in [None]} if False else None
get = lambda a, k="rmse": np.array([rows[c]["metrics"][a][k] for c in cs])
rng = np.random.default_rng(0)
def boot(fn, n=10000):
    idx = rng.integers(0, len(cs), (n, len(cs))); v = np.array([fn(i) for i in idx]); return np.percentile(v, [2.5, 97.5])
def rel(a, b, k="rmse"):  # mean_s (a-b)/a  -> reduction of b vs a
    A, Bv = get(a, k), get(b, k); r = (A - Bv) / A
    return float(r.mean()), boot(lambda i: r[i].mean()).tolist(), r.tolist()
out = {"n": len(cs), "dropped": dropped, "sequences": cs}
r1, ci1, per1 = rel("LBS", "PM"); r2, ci2, per2 = rel("NN", "PM")
v1 = "INCONCLUSIVE" if len(dropped) > 3 else ("PROVEN" if ci1[0] >= 0.10 else "DISPROVEN" if ci1[1] < 0.10 else "INCONCLUSIVE")
v2 = "INCONCLUSIVE" if len(dropped) > 3 else ("PROVEN" if ci2[0] > 0 else "DISPROVEN" if ci2[1] <= 0 else "INCONCLUSIVE")
san = {a: int(sum(get(a) < get("STATIC"))) for a in ["PM", "LBS"]}
out["H1"] = {"r1_mean": r1, "ci95": ci1, "per_seq": dict(zip(cs, per1)), "verdict": v1}
out["H2"] = {"r2_mean": r2, "ci95": ci2, "per_seq": dict(zip(cs, per2)), "verdict": v2}
out["sanity_beats_static"] = san; out["sanity_pass"] = all(v >= 4 for v in san.values())
out["secondary"] = {k: {"PM_vs_LBS": rel("LBS", "PM", k)[:2], "PM_vs_NN": rel("NN", "PM", k)[:2]} for k in ["p95", "dyn_rmse"]}
out["table"] = {c: {a: rows[c]["metrics"][a]["rmse"] for a in arms} | {"joints": rows[c]["joints"], "frames": rows[c]["frames"],
                "test": rows[c]["test"], "time_min": rows[c]["times_s"]["total"] / 60, "rss_gb": rows[c]["max_rss_gb"],
                **{f"fit_{k}": v for k, v in rows[c]["fit_check"].items()}} for c in cs}
out["pm_wins_vs_lbs"] = int(sum(get("PM") < get("LBS"))); out["pm_wins_vs_nn"] = int(sum(get("PM") < get("NN")))
json.dump(out, open(OUT / "summary.json", "w"), indent=1)
# figure 1: per-sequence RMSE bars
x = np.arange(len(cs)); w = 0.2; cols = {"PM": "#2b6cb0", "LBS": "#dd6b20", "NN": "#38a169", "STATIC": "#a0aec0"}
fig, ax = plt.subplots(figsize=(14, 5))
LBL = {"PM": "PartMM", "LBS": "Fitted skinning (LBS)", "NN": "Nearest training pose"}; w = 0.26
for k, a in enumerate(["PM", "LBS", "NN"]): ax.bar(x + (k - 1) * w, get(a) * 100, w, label=LBL[a], color=cols[a])
ax.set_xticks(x); ax.set_xticklabels(cs); ax.set_ylim(0, 13); ax.set_ylabel("held-out vertex RMSE (% of body diagonal)")
ax.set_title(f"Unseen-pose error on {len(cs)} AMA sequences, last 20% of frames held out (lower is better)"); ax.legend(ncol=3, frameon=False, loc="upper left"); ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(FIG / "rmse_by_sequence.png", dpi=200)
plt.close(fig)
# figure 2: relative reductions with CI
fig, ax = plt.subplots(figsize=(14, 4))
for y, (lab, m, ci) in enumerate([("PM vs LBS (H1)", r1, ci1), ("PM vs NN (H2)", r2, ci2)]):
    ax.errorbar(m * 100, y, xerr=[[100 * (m - ci[0])], [100 * (ci[1] - m)]], fmt="o", capsize=5, color="#2b6cb0")
ax.axvline(10, ls="--", color="#dd6b20", lw=1); ax.axvline(0, color="k", lw=0.8)
ax.set_yticks([0, 1]); ax.set_yticklabels(["PM vs LBS (H1)", "PM vs NN (H2)"]); ax.set_ylim(-0.6, 1.6)
ax.set_xlabel("mean relative RMSE reduction by PartMM (%), 95% bootstrap CI"); ax.text(10.5, 1.4, "H1 bar: 10%", color="#dd6b20", fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "relative_reduction_ci.png", dpi=200)
print(json.dumps({k: out[k] for k in ["n", "dropped", "H1", "H2", "sanity_beats_static", "pm_wins_vs_lbs", "pm_wins_vs_nn"]}, indent=1, default=str)[:3000])
