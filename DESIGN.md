# GaussiAnimate: does PartMM re-animate unseen poses better than plain skinning? (scout + design v1)

Status: SCOUTED + DESIGNED 2026-10-22 ~12:20 IST. **No installs, downloads or runs yet.**
Repo clone (read-only scouting): /workspace/new-exp/GaussiAnimate (github.com/Net-Maker/GaussiAnimate @ 2012a6e, 2026-10-18; MIT; SIGGRAPH Asia 2026, arXiv 2604.08547).

## Scouting findings
- Pipeline: registered point sequence `[T,N,3]` → SSDR outer bones (Dem Bones, `pyssdr`) → CGAL mean-curvature curve skeleton → inner kinematic tree → `skelebones.npz`. Then **PartMM** (pure NumPy, no learning) maps a novel inner pose to outer-bone motion → animated points.
- CPU-only path: core + `ssdr`/`geometry` extras + two small native builds (`scripts/install_geometry.sh`). Gaussian training/rendering (CUDA) is not needed for mesh inputs.
- Box fit:
  - Python must be 3.8–3.11 (box has 3.13), so use `uv` with cpython 3.10 (available). NumPy must be < 1.26; open3d 0.19 and libigl 2.5.1 are pinned.
  - `sudo` works, and apt has libcgal-dev 6.0.1 and libeigen3-dev 3.4.0. The repo just says "libcgal-dev", so the CGAL 6 build is **unverified**; that's the first risk.
  - 8 cores. RAM: 15 GB total, about 5 GB free right now (the llama-server is resident), so use a memory gate.
- Data that needs no licence form: **AMA** (Vlasic et al., MIT CSAIL), 10 registered clothed-human mesh sequences: D_bouncing, D_handstand, D_march, D_squat, I_crane, I_jumping, I_march, I_squat, T_samba, T_swing. They're public tgz files (T_samba is 39.5 MB, HTTP 200 confirmed). The repo's own example is T_samba: 175 frames, 9,971 verts, a skirt, so it has real non-rigid cloth.
- Not usable without signup/forms: VTO T-shirt (needs SMPL registration), DeformingThings4D (form), DNA-Rendering/ActorsHQ (request), and all Gaussian checkpoints (not released). So the paper's own tables (Table 2/3, VTO 48.4% RMSE) **cannot be reproduced as-is**. This is a fresh test of the core claim on public data.
- Built-in baselines: `partmm.fallback.SkinningBaseline` (LBS over inner joints, given `[N,J]` weights). Robust weight transfer is in `experiments/mesh/robust_weights.py` (biharmonic inpainting, Abdrashitov 2023).

## Question
On held-out frames of public clothed-human sequences, does PartMM (retrieve + blend outer-bone motion) reproduce the true surface better than driving the same inner skeleton with linear blend skinning? The paper claims large gains (48.4% RMSE vs robust LBS on VTO).

## Protocol (per AMA sequence, 10 sequences)
1. Load the meshes and normalise scale (bbox diagonal = 1) so the repo's absolute distance thresholds behave the same everywhere. Use the default config (50 bones, `ssdr_max_iterations` 50 as in the example). No per-sequence tuning.
2. Temporal split, unshuffled: first 80% of frames = train (database), last 20% = test.
3. Run extraction on the **full** sequence to get one consistent skeleton and per-frame inner poses. **Disclosed leak:** skeleton topology and the test inner poses come from an extraction that saw the test frames. Only the *inner pose* of test frames is used as the query; test-frame outer-bone transforms and surfaces are never given to any arm.
   - Strict variant: S2 extracts on train frames only. Test inner poses are then fitted with `fit_pose_to_joint_positions` to joint positions regressed from the GT test surface using train-fit barycentric joint anchors. It runs only if S1 works.
4. Arms on test frames (same inner query pose for all):
   - **PM:** PartMM, default `PartMMConfig` (balanced_tree, 5 parts), database = train-frame slice of the bundle.
   - **LBS-robust:** `SkinningBaseline` with `[N,J]` weights from robust transfer. Weights are first summed from SSDR bone weights to the nearest inner joint segment, then smoothed/inpainted with `transfer_skin_weights`. The reference pose is the first train frame.
   - **NN-global:** take the nearest train frame by whole-body pose distance (mean squared SO(3) radians) and copy its outer-bone transforms. This ablates "partwise".
   - **Static:** the rest/first-train-frame surface (sanity floor).
5. Metric: per-frame vertex RMSE vs GT (normalised units), averaged over test frames, then per sequence. Secondary: the p95 vertex error, plus a cloth-region RMSE on T_samba/T_swing/I_* skirts, picking vertices with the highest train-set residual of rigid LBS.

## Pre-registered hypotheses (n = 10 sequences, paired, sequence-level bootstrap 10k, 95% CI)
- **H1:** relative RMSE reduction PM vs LBS-robust, r = mean_s (LBS−PM)/LBS. PROVEN if LB(r) ≥ 0.10. DISPROVEN if UB(r) < 0.10. Otherwise INCONCLUSIVE. A reproduction of the paper's 48% would sit far above this.
- **H2:** partwise beats global retrieval, r2 = mean_s (NN−PM)/NN. PROVEN if LB > 0. DISPROVEN if UB ≤ 0.
- Exclusions, fixed now: a sequence is dropped only if extraction crashes or yields < 2 joints after 1 retry with the defaults. All drops are reported, and if > 3 are dropped the verdict is INCONCLUSIVE.

## Cost / runtime (estimate, unverified until the first sequence)
- 0 CU, CPU only. Download is about 10 × 40 MB.
- Setup: about 15–25 min (apt CGAL/Eigen, uv py3.10 venv, native builds).
- Per sequence: SSDR (50 bones × 50 iterations, about 10k verts × about 150–250 frames) plus the curve skeleton, guessed at 3–15 min. PartMM + baselines take seconds to minutes. **Total about 1–3 h**, run sequentially behind a memory gate (start only when ≥ 4 GB is free).
- First step on resume: smoke T_samba end-to-end (this is the repo's own example, so a mismatch points to the box environment, not the method). Time it and re-estimate before running all 10.

## Outputs (planned)
/workspace/new-exp/gaussianimate/{run/, results/RESULTS.md, figures/ (RMSE bars + per-frame error heatmap GIF via open3d offscreen), issues-found/}, plus a post draft.
