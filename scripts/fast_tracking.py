"""Parallel (process-pool) version of GaussiAnimate's per-frame surface constraint loop.

refine_motion_with_surface() in skelebone/extraction/tracking.py ends with an independent
per-frame loop calling constrain_surface_frame(). We run exactly that function on exactly the
same inputs, but frames are distributed over a fork-based process pool. Results are identical
by construction (same deterministic per-frame call); only scheduling changes.
Everything before that loop is the original code, called unchanged.
"""
import multiprocessing as mp
import os
import numpy as np
import skelebone.extraction.tracking as T
from skelebone.types import PoseSequence

NPROC = int(os.environ.get("GA_TRACK_PROCS", "4"))
_G = {}


def _one(frame):
    from skelebone.extraction._surface_ik import constrain_surface_frame
    g = _G
    single = PoseSequence(g["rot"][frame:frame+1], g["tr"][frame:frame+1], fps=g["fps"])
    fitted = constrain_surface_frame(g["skeleton"], g["tracked"][frame], single, g["scenes"][frame],
                                     g["origins"][frame], margin=g["margin"], extent=g["extent"])
    return frame, fitted.local_rotations[0], fitted.root_translation[0]


_orig_constrain = None


def patched_refine(sequence, skeleton, tracked_positions, motion, **kw):
    """Run the original function with constrain_surface_frame swapped for a recorder,
    then solve the recorded per-frame problems in parallel."""
    import skelebone.extraction._surface_ik as SI
    calls = []
    real = SI.constrain_surface_frame

    def recorder(skel, target, initial, scene, origin, *, margin, extent):
        calls.append((skel, target, initial, scene, origin, margin, extent))
        return initial  # placeholder; replaced below
    SI.constrain_surface_frame = recorder
    try:
        result = T.__dict__["_orig_refine"](sequence, skeleton, tracked_positions, motion, **kw)
    finally:
        SI.constrain_surface_frame = real
    if not calls:
        return result
    _G.update(skeleton=calls[0][0], tracked=np.asarray(tracked_positions), scenes=[c[3] for c in calls],
              origins=[c[4] for c in calls], margin=calls[0][5], extent=calls[0][6],
              rot=result.local_rotations.copy(), tr=result.root_translation.copy(), fps=result.fps)
    with mp.get_context("fork").Pool(NPROC) as pool:
        for frame, r, t in pool.imap_unordered(_one, range(len(calls))):
            result.local_rotations[frame] = r
            result.root_translation[frame] = t
    return result


def install():
    if "_orig_refine" not in T.__dict__:
        T._orig_refine = T.refine_motion_with_surface
        T.refine_motion_with_surface = patched_refine
