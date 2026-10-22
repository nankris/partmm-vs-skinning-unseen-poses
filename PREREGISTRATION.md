# Pre-registration: PartMM vs skinning on unseen poses (AMA clothed humans)

Written **2026-10-22 12:02 IST**. This is before any extraction, run or scoring. It supersedes the protocol section in DESIGN.md (v1) where they differ. The main change: outer bones are now fitted on train frames only.

## Code and data
- GaussiAnimate (MIT), github.com/Net-Maker/GaussiAnimate @ 2012a6e (2026-10-18), with default configs: `ExtractionConfig(num_bones=50, ssdr_max_iterations=50)` and `PartMMConfig()` defaults (balanced_tree, 5 parts, patch 7, 7 neighbours).
- AMA (Vlasic et al. 2008), all 10 public registered mesh sequences: D_bouncing 175, D_handstand 175, D_march 250, D_squat 250, I_crane 175, I_jumping 150, I_march 250, I_squat 250, T_samba 175, T_swing 150 frames.
- Every sequence is uniformly scaled so the frame-0 bounding-box diagonal = 1. Units in all results are "fraction of body diagonal".

## Split (temporal, unshuffled)
Train = the first floor(0.8·T) frames, test = the rest (30–50 frames per sequence).

## What each arm sees
1. **Inner skeleton + per-frame inner pose:** the GaussiAnimate pipeline is run on the full sequence. It's used only as the pose tracker. The test-frame *inner pose* (joint local rotations + root translation) is the query given to every arm.
   - Disclosed leak: skeleton topology and joint tracking used test surfaces. This is the same for all arms.
2. **Outer bones (SSDR, 50 bones):** re-fitted with the same SSDR config on **train frames only** (rest frame 0). No arm sees any test-frame surface.
3. Arms, all predicting the test-frame vertex positions:
   - **PM:** PartMM (`partmm.animate`) with database = train inner poses + train-only SSDR transforms/weights/rest points.
   - **LBS:** linear blend skinning over the inner joints (`partmm.fallback.SkinningBaseline`, reference = frame 0). Per-vertex joint weights are fitted on the train frames by non-negative least squares (sum-to-one via a penalty row of weight 10), using the joint global transforms. This is the best LBS the train data allows, and it's stronger than heuristic weight transfer.
   - **NN:** for each test frame, take the nearest train frame by mean squared SO(3) angle over all joints, and apply its train-only SSDR transforms with the train-only weights. This is whole-body retrieval with no partwise matching.
   - **STATIC:** the frame-0 surface, as a sanity floor.
4. Descriptive only: train-frame reconstruction RMSE of SSDR and of LBS (fit quality), runtime and RAM per stage.

## Metric
Per test frame, vertex RMSE = sqrt(mean_n ||pred_n − gt_n||²). Per sequence, take the mean over its test frames (primary). Secondary: per-sequence p95 per-vertex error, and the "dynamic-region" RMSE over the 20% of vertices with the largest train-set LBS residual.

## Hypotheses (n = 10 sequences, paired; bootstrap over sequences, 10,000 resamples, seed 0, percentile 95% CI)
- **H1 (PartMM beats skinning by a meaningful margin):** r1 = mean_s (LBS_s − PM_s)/LBS_s.
  - **PROVEN** if LB(r1) ≥ 0.10.
  - **DISPROVEN** if UB(r1) < 0.10.
  - Otherwise **INCONCLUSIVE**.
  - (The paper reports 48.4% on VTO garments against a robust-transfer LBS. That's context, not the bar.)
- **H2 (partwise beats whole-body retrieval):** r2 = mean_s (NN_s − PM_s)/NN_s. **PROVEN** if LB(r2) > 0. **DISPROVEN** if UB(r2) ≤ 0. Otherwise **INCONCLUSIVE**.
- Sanity (not a hypothesis): PM and LBS must both beat STATIC on at least 8/10 sequences. If not, the pipeline is suspect, and that's reported before any verdict.

## Exclusions and robustness, fixed now
- A sequence is dropped only if extraction crashes, or yields < 3 joints, after 1 retry with the same defaults. Every drop is reported. If more than 3 are dropped, H1 and H2 are **INCONCLUSIVE**.
- No parameter tuning per sequence. If a default fails on every sequence, the one change and its reason are logged in issues-found, and the run is labelled "deviation".
- The smoke run on T_samba checks only that the code works and how long it takes. Its numbers are recomputed in the full run and aren't looked at for design decisions. The split, arms and metric above are fixed now.

## Clarification 1 (2026-10-22 12:03 IST, before any scoring, while the smoke extraction runs)
- **NN** is root-aligned. The retrieved frame's predicted surface is mapped by G_root(test) · G_root(nn)⁻¹, the root joint's global transform from FK. So whole-body retrieval isn't penalised for where the dancer is standing. That's the fair version of "global retrieval".
- **STATIC** stays unaligned (raw frame 0), as a floor only.
- NN pose distance uses the joint *local* rotations, excluding the root joint's rotation.

## AMENDMENT 1 (2026-10-22 13:59 IST): scope cut to 5 sequences, BEFORE any scoring of the new sequences
- **Reason:** the user cut the scope to save time, so the post is ready tonight. Surface-constrained IK takes 17–70 min per sequence on this shared, CPU-saturated box.
- **Sequences (n = 5):** T_samba (done), D_bouncing (done), D_handstand (already running when the cut arrived), T_swing and I_jumping.
  - T_swing and I_jumping were picked for variety and cloth motion. The set covers all three AMA performers (D, I, T), an inverted pose (handstand), and two sequences from the T performer, whose loose dress moves the most (samba, swing). Both are also the shortest remaining sequences (150 frames).
  - I chose them before seeing any score of them. The only results already seen are T_samba and D_bouncing, which are disclosed in the run notes.
- **Dropped, not run:** D_march, D_squat, I_crane, I_march, I_squat. They are not counted as drops under the crash rule.
- **Decision rules are unchanged.** The bootstrap is over n = 5 sequences, and the sanity rule becomes "PM and LBS beat STATIC on ≥ 4/5". The rule "more than 3 drops → INCONCLUSIVE" now counts only crashes among the 5.
- With n = 5 the CIs are wide. The post reports this as a 5-sequence study, with the cut disclosed.
