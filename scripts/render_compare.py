"""Side-by-side GIF + contact sheet: GT | PartMM | LBS | NN on held-out frames, colored by per-vertex error.
usage: render_compare.py CASE  (reads run/full/CASE/preds.npz)"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib; matplotlib.use("Agg"); from matplotlib import cm
R = Path(__file__).resolve().parents[1]; case = sys.argv[1]
d = np.load(R / "run/full" / case / "preds.npz"); faces = d["faces"]; gt = d["gt"]
arms = ["GT", "PM", "LBS", "NN"]; label = {"GT": "Ground truth", "PM": "PartMM", "LBS": "LBS (fitted)", "NN": "Nearest frame"}
P = {"GT": gt, **{a: d[a] for a in arms[1:]}}
allp = np.concatenate([gt.reshape(-1, 3)]); lo, hi = allp.min(0), allp.max(0)
emax = 0.05  # 5% of body diagonal saturates the colormap
S = 480; font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
yaw = np.radians(30); Rz = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
c = (lo + hi) / 2; scale = 0.9 * S / (hi - lo)[[0, 1]].max()
def render(v, err):
    q = (v - c) @ Rz.T; x = q[:, 0] * scale + S / 2; y = S / 2 - q[:, 1] * scale; z = q[:, 2]
    tri = faces; zc = z[tri].mean(1); order = np.argsort(zc)
    n = np.cross(q[tri[:, 1]] - q[tri[:, 0]], q[tri[:, 2]] - q[tri[:, 0]]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    shade = 0.35 + 0.65 * np.abs(n[:, 2])
    col = (np.array([0.8, 0.8, 0.82])[None] if err is None else cm.magma(np.clip(err[tri].mean(1) / emax, 0, 1))[:, :3] * 0.9 + 0.1)
    rgb = (col * shade[:, None] * 255).astype(np.uint8) if err is not None else (np.full((len(tri), 3), 200) * shade[:, None]).astype(np.uint8)
    im = Image.new("RGB", (S, S), (255, 255, 255)); dr = ImageDraw.Draw(im)
    for t in order:
        i, j, k = tri[t]; dr.polygon([(x[i], y[i]), (x[j], y[j]), (x[k], y[k])], fill=tuple(rgb[t]))
    return im
frames = []; idx = np.linspace(0, len(gt) - 1, min(len(gt), 24)).astype(int)
for f in idx:
    row = Image.new("RGB", (S * 4, S + 30), (255, 255, 255)); dr = ImageDraw.Draw(row)
    for k, a in enumerate(arms):
        err = None if a == "GT" else np.linalg.norm(P[a][f] - gt[f], axis=1)
        row.paste(render(P[a][f], err), (k * S, 30))
        txt = label[a] if a == "GT" else f"{label[a]}  RMSE {100*np.sqrt((err**2).mean()):.2f}%"
        dr.text((k * S + 10, 5), txt, fill=(0, 0, 0), font=font)
    frames.append(row)
out = R / "figures"; out.mkdir(exist_ok=True)
frames[0].save(out / f"compare_{case}.gif", save_all=True, append_images=frames[1:], duration=120, loop=0)
sheet = Image.new("RGB", (S * 4, (S + 30) * 3), (255, 255, 255))
for r, f in enumerate([0, len(frames) // 2, len(frames) - 1]): sheet.paste(frames[f], (0, r * (S + 30)))
sheet.save(out / f"compare_{case}_sheet.png")
# colorbar strip
cb = Image.new("RGB", (S * 4, 50), (255, 255, 255)); dr = ImageDraw.Draw(cb)
for xpx in range(200, S * 4 - 200):
    cc = (np.array(cm.magma((xpx - 200) / (S * 4 - 400))[:3]) * 255).astype(int); dr.line([(xpx, 5), (xpx, 25)], fill=tuple(cc))
dr.text((200, 28), "0", fill=(0, 0, 0), font=font); dr.text((S * 4 - 330, 28), "≥5% of body diagonal (vertex error)", fill=(0, 0, 0), font=font)
cb.save(out / "error_colorbar.png"); print("ok", out / f"compare_{case}.gif")
