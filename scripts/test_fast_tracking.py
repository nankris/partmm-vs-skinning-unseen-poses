"""Equivalence test: original vs parallel surface refinement on the first 8 frames of T_samba."""
import sys, time, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skelebone.examples.ama import load_ama_sequence
from skelebone.types import DynamicPointSequence
from skelebone.pipeline import ExtractionConfig, SkelebonePipeline
import skelebone.extraction.tracking as T
seq = load_ama_sequence(Path(__file__).resolve().parents[1] / "data/AMA", "T_samba")
p = seq.points[:8]; c0 = p[0].min(0); d = np.linalg.norm(p[0].max(0) - c0)
seq = DynamicPointSequence((p - c0) / d, faces=seq.faces, fps=30.0)
cfg = ExtractionConfig(num_bones=50, ssdr_max_iterations=50)
out = Path("/tmp/ga_eqtest"); t = time.time()
a = SkelebonePipeline(cfg).run(seq, out / "orig").bundle.motion; t1 = time.time()
import fast_tracking; fast_tracking.install()
b = SkelebonePipeline(cfg).run(seq, out / "fast").bundle.motion; t2 = time.time()
print("orig_s", round(t1 - t, 1), "fast_s", round(t2 - t1, 1))
print("max|dq|", np.abs(a.local_rotations - b.local_rotations).max(), "max|dt|", np.abs(a.root_translation - b.root_translation).max())
