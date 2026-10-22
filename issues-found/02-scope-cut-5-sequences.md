# 02: Scope cut from 10 to 5 AMA sequences (user decision, 13:58 IST)
- **What:** only 5 of the 10 AMA sequences were evaluated: T_samba, D_bouncing, D_handstand, T_swing and I_jumping.
- **Why:** the user cut the scope to save time, so the post would be ready the same evening. The upstream tracking stage (surface-constrained IK, one SLSQP solve per frame) took 70 min for T_samba single-threaded, and still 17+ min per sequence after parallelising it (issue 01), on a shared CPU box at load 15–38.
- **How the 5 were picked:** before scoring them, for variety (all three performers, an inverted pose) and for cloth (T_samba and T_swing, the loose-dress sequences). Recorded as PREREGISTRATION Amendment 1.
- **Effect:** n = 5 gives wide bootstrap CIs. Not run: D_march, D_squat, I_crane, I_march, I_squat. Running them is a single command (`scripts/run_seq_one_at_a_time.sh` with the full list).
