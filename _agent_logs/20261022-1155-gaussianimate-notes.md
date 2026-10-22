# GaussiAnimate run notes (IST)
- 11:56 apt: build-essential cmake libcgal-dev 6.0.1 libeigen3-dev (+GL libs). AMA 10 sequences downloaded (frames: 175/175/250/250/175/150/250/250/175/150).
- 11:57 uv venv py3.10.22 at .venv; `uv pip install -e '.[geometry,visualization,ssdr,dev]' pybind11` → numpy 1.25.2, open3d 0.19.0.
- 12:01 first native build attempt interrupted (user-side interrupt of my foreground call); re-run in background.
- 12:02 PREREGISTRATION.md written (before any run). 12:03 native build OK with CGAL 6.0.1: pyssdr + .native/bin/curve_skeleton (54 s).
- 12:03 first smoke attempt failed to start (/usr/bin/time missing) – nothing ran. 12:0x smoke = scripts/eval_sequence.py T_samba (prints only timings).
- ~12:10 Clarification 1 appended to PREREGISTRATION.md (NN root alignment) – before any scoring.
- Smoke timing: SSDR full seq ≈70 s; curve skeleton+skinning ≈8 s; tracking surface-refine (SLSQP per frame, single-thread) ≈16 s/frame → ~50+ min for 175 frames. Default config kept (no tuning).
- 12:30 eval script made resumable (reuses full_extraction/skelebones.npz). run_all.sh launched: 3 concurrent (memory gate ≥1.5 GB free), OMP_NUM_THREADS=2.
- 12:51 parent: one sequence at a time. Killed run_all.sh queue; started scripts/run_seq_one_at_a_time.sh (OMP_NUM_THREADS=4).
- 12:54 measured surface-IK rate under box load ~30: ~26 s/frame → 1,650 remaining frames ≈ 12 h sequential. Not feasible today.
- 12:57 scripts/fast_tracking.py: runs the *same* per-frame constrain_surface_frame calls over a 4-process fork pool (records the calls from the unmodified original function, then solves them in parallel). Equivalence test (scripts/test_fast_tracking.py, T_samba first 8 frames): max |Δquat| = 0.0, max |Δroot| = 0.0 (bit-identical); 113 s → 75 s on 8 frames (gain is bigger on long sequences). Installed in eval_sequence.py.
- 13:00 killed the old sequential D_bouncing (it was at surface-IK frame ~65/175); the runner restarts it with the parallel patch. Smoke T_samba (old code path) left to finish; its extraction is reused for the full T_samba eval.

## 13:15 IST: smoke T_samba finished (original sequential tracking)
- `time python scripts/eval_sequence.py T_samba run/smoke_T_samba`: real 71m09s, user 37m12s (box load 15–38 from other tenants).
- Stage times: full_extraction 4207 s (almost all surface-constrained IK), SSDR on train 11 s, PartMM 4.3 s, LBS fit 18.6 s.
- 23 joints, 50 SSDR bones, 9,971 points, train 140 / test 35 frames.
- Test RMSE (units of bbox diagonal): PM 0.0117, NN 0.0143, LBS 0.0290, STATIC 0.575. p95: PM 0.0223, NN 0.0312, LBS 0.0509.
  - These are smoke numbers on the pre-registered code path. They count as the T_samba result (run_seq copies the extraction, then re-evaluates deterministically).
- 13:15:30 run_seq_one_at_a_time.sh started D_bouncing with fast_tracking (4 procs, OMP_NUM_THREADS=4).
- Concurrency note: from 13:25 the WorldGacha GT capture (SwiftShader, about 3 cores) runs at the same time; RAM about 2 GB free, within the 5 GB per-job cap.

## 13:47 IST
- D_bouncing done with fast_tracking: full_extraction 1015 s (17 min, vs 70 min sequential T_samba), total 18.8 min, peak RSS 2.50 GB. PM 0.0214 / LBS 0.0276 / NN 0.0698 / STATIC 0.143.
- T_samba re-evaluated from the smoke extraction in 1m46s (deterministic downstream).
- render_compare.py checked on D_bouncing (12 s); S raised 360→480 px per panel so sheets are 1920 px wide for Substack.

## 13:58–14:00 IST: scope cut to 5 sequences (user, via parent)
- D_handstand finished 13:58:51. The old runner started D_march at the same moment, and I killed it at 13:59:24 with no metrics produced (moved to run/dropped/).
- New queue: T_swing (started 13:59:35), then I_jumping. PREREGISTRATION Amendment 1 written before either was scored. issues-found/02.

## 14:54 IST: GaussiAnimate done
- analyze.py: H1 r1 = 21.8% [−1.9, 45.5] INCONCLUSIVE (4/5 wins); H2 r2 = 61.3% [38.9, 75.5] PROVEN (5/5); sanity 5/5.
- Renders for all 5; tables as PNG (2800 px); setup diagram; post + Substack html/meta.
- Secret scan CLEAN (52 files). Pushed github.com/nankris/partmm-vs-skinning-unseen-poses (public).
