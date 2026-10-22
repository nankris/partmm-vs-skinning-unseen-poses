"""Evaluate PM / LBS / NN / STATIC on held-out frames of one AMA sequence.

Usage: python scripts/eval_sequence.py CASE OUTDIR
Pre-registered in PREREGISTRATION.md. Uses GaussiAnimate @2012a6e.
"""
import json, resource, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import nnls

from skelebone.examples.ama import load_ama_sequence
from skelebone.types import DynamicPointSequence, PoseSequence
from skelebone.pipeline import ExtractionConfig, SkelebonePipeline
from skelebone.extraction import decompose_ssdr
from skelebone.kinematics import forward_kinematics, quaternion_to_matrix
from partmm import PartMMConfig, PartMMInput, PartMMQuery, animate
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fast_tracking; fast_tracking.install()  # exact parallel per-frame surface IK (see fast_tracking.py)

AMA = Path(__file__).resolve().parents[1] / "data" / "AMA"
CFG = ExtractionConfig(num_bones=50, ssdr_max_iterations=50)


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def skin(rest, weights, transforms):
    """LBS of rest points [N,3] with weights [N,B] and transforms [T,B,4,4]."""
    h = np.concatenate([rest, np.ones((len(rest), 1))], 1)
    return np.einsum("nb,tbij,nj->tni", weights, transforms, h, optimize=True)[..., :3]


def rmse_frames(pred, gt):
    return np.sqrt(((pred - gt) ** 2).sum(-1).mean(-1))  # [T]


def so3_angle(qa, qb):
    """Angle between unit quaternions, [...]."""
    d = np.abs((qa * qb).sum(-1)).clip(0, 1)
    return 2 * np.arccos(d)


def main(case, outdir):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    log = {"case": case, "times_s": {}}
    t0 = time.time()
    seq = load_ama_sequence(AMA, case=case)
    pts = seq.points
    c0 = pts[0].min(0); diag = np.linalg.norm(pts[0].max(0) - c0)
    pts = (pts - c0) / diag  # frame-0 bbox diagonal = 1
    seq = DynamicPointSequence(pts, faces=seq.faces, fps=30.0)
    T, N = pts.shape[:2]
    ntr = int(np.floor(0.8 * T)); te = np.arange(ntr, T)
    log.update(frames=T, points=N, train=ntr, test=len(te), scale_diag_original=float(diag))

    # 1) full-sequence pipeline = pose tracker (skeleton + per-frame inner pose)
    t = time.time()
    cached = out / "full_extraction" / "skelebones.npz"
    if cached.exists():  # resume: extraction is deterministic given inputs; reuse it
        from skelebone.io import load_bundle
        b = load_bundle(cached); log["extraction_reused"] = True
        prev = out / "metrics_extraction_time.json"
        log["times_s"]["full_extraction"] = json.load(open(prev))["s"] if prev.exists() else None
    else:
        res = SkelebonePipeline(CFG).run(seq, out / "full_extraction")
        b = res.bundle
        log["times_s"]["full_extraction"] = time.time() - t
        (out / "metrics_extraction_time.json").write_text(json.dumps({"s": time.time() - t}))
    sk, motion = b.skeleton, b.motion
    J = sk.num_joints
    log["joints"] = int(J)
    if J < 3:
        raise RuntimeError(f"only {J} joints")
    G, _ = forward_kinematics(sk, motion)  # [T,J,4,4]

    # 2) train-only SSDR
    t = time.time()
    tr_seq = DynamicPointSequence(pts[:ntr], faces=seq.faces, fps=30.0)
    from skelebone.pipeline import SkelebonePipeline as _P
    ssdr_cfg = _P(CFG)._component_configs()[0]
    ss = decompose_ssdr(tr_seq, ssdr_cfg)
    log["times_s"]["train_ssdr"] = time.time() - t
    W, Tb, rest = ss.weights, ss.transformations, ss.rest_pose  # [N,B],[ntr,B,4,4],[N,3]
    log["ssdr_bones"] = int(W.shape[1])
    ssdr_train_rmse = rmse_frames(skin(rest, W, Tb), pts[:ntr]).mean()

    gt = pts[te]
    preds = {}

    # PM
    t = time.time()
    db = PartMMInput(rest_joints=sk.rest_joints, parents=sk.parents,
                     source_local_rotations=motion.local_rotations[:ntr],
                     source_root_translation=motion.root_translation[:ntr],
                     bone_transforms=Tb, source_points=rest, skinning_weights=W, fps=30.0)
    q = PartMMQuery(local_rotations=motion.local_rotations[te],
                    root_translation=motion.root_translation[te], fps=30.0)
    pm = animate(db, q, PartMMConfig())
    preds["PM"] = pm.points
    log["times_s"]["partmm"] = time.time() - t
    # PM on train poses (fit check, descriptive)
    qtr = PartMMQuery(local_rotations=motion.local_rotations[:ntr],
                      root_translation=motion.root_translation[:ntr], fps=30.0)
    pm_train_rmse = rmse_frames(animate(db, qtr, PartMMConfig()).points, pts[:ntr]).mean()

    # LBS with NNLS weights fitted on train frames, relative to frame 0
    t = time.time()
    rel = G @ np.linalg.inv(G[0])[None]  # [T,J,4,4]
    p0 = np.concatenate([pts[0], np.ones((N, 1))], 1)
    Wl = np.zeros((N, J))
    lam = 10.0
    tr_idx = np.arange(ntr)
    for n in range(N):
        A = (rel[tr_idx] @ p0[n])[..., :3]  # [ntr,J,3]
        A = A.transpose(0, 2, 1).reshape(-1, J)
        y = pts[tr_idx, n].reshape(-1)
        A2 = np.vstack([A, lam * np.ones((1, J))]); y2 = np.append(y, lam)
        w, _ = nnls(A2, y2)
        s = w.sum(); Wl[n] = w / s if s > 1e-12 else np.full(J, 1.0 / J)
    lbs_all = np.einsum("nj,tjik,nk->tni", Wl, rel, p0, optimize=True)[..., :3]
    preds["LBS"] = lbs_all[te]
    lbs_train_res = np.linalg.norm(lbs_all[:ntr] - pts[:ntr], axis=-1)  # [ntr,N]
    log["times_s"]["lbs_fit"] = time.time() - t

    # NN (root-aligned whole-body retrieval)
    lr = motion.local_rotations
    nonroot = np.array([j for j in range(J) if sk.parents[j] >= 0])
    root = int(np.where(np.asarray(sk.parents) < 0)[0][0])
    d = (so3_angle(lr[te][:, None, nonroot], lr[:ntr][None, :, nonroot]) ** 2).mean(-1)  # [Q,ntr]
    nn = d.argmin(1)
    ssdr_train_pred = skin(rest, W, Tb)  # [ntr,N,3]
    nnp = []
    for qi, f in zip(te, nn):
        A = G[qi, root] @ np.linalg.inv(G[f, root])
        h = np.concatenate([ssdr_train_pred[f], np.ones((N, 1))], 1)
        nnp.append((h @ A.T)[:, :3])
    preds["NN"] = np.stack(nnp)
    preds["STATIC"] = np.repeat(pts[:1], len(te), 0)

    # metrics
    dyn = np.argsort(-lbs_train_res.mean(0))[: int(0.2 * N)]
    m = {}
    for k, p in preds.items():
        err = np.linalg.norm(p - gt, axis=-1)  # [Q,N]
        m[k] = {"rmse": float(rmse_frames(p, gt).mean()),
                "rmse_per_frame": rmse_frames(p, gt).tolist(),
                "p95": float(np.percentile(err, 95)),
                "dyn_rmse": float(np.sqrt((err[:, dyn] ** 2).mean(-1)).mean())}
    log["metrics"] = m
    log["fit_check"] = {"ssdr_train_rmse": float(ssdr_train_rmse),
                        "lbs_train_rmse": float(np.sqrt((lbs_train_res ** 2).mean(-1)).mean()),
                        "pm_train_rmse": float(pm_train_rmse)}
    log["times_s"]["total"] = time.time() - t0
    log["max_rss_gb"] = rss_gb()
    (out / "metrics.json").write_text(json.dumps(log, indent=1))
    np.savez_compressed(out / "preds.npz", te=te, gt=gt, faces=seq.faces,
                        **{k: v.astype(np.float32) for k, v in preds.items()})
    print("DONE", log["times_s"], f"rss {log['max_rss_gb']:.2f}GB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
