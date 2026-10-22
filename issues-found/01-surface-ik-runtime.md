# 01: Surface-constrained IK dominates runtime (~16–26 s per frame, single-threaded)
- **Symptom:** the T_samba smoke run spent about 70 s in SSDR, about 8 s on the curve skeleton, then about 50+ min in `refine_motion_with_surface` (SLSQP per frame with signed-distance constraints). At that rate the 10 sequences (2,050 frames) would take about 12 h on the shared, loaded box.
- **Evidence:** py-spy stacks (`constrain_surface_frame` → `compute_closest_points`); frame counter 69 → 81 in 3.3 min, then 115 → 138 in 10 min under load about 30.
- **Fix:** `scripts/fast_tracking.py` runs the identical per-frame calls on a 4-process pool. The equivalence test is bit-identical (max |Δ| = 0.0 for quaternions and root translation on 8 frames). No numerical change, no config change.
- **Status:** fixed; used for every sequence except the T_samba extraction, which came from the original sequential path (smoke) and is reused.
