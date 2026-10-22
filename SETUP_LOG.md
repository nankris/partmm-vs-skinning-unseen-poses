# Setup log: GaussiAnimate on a CPU-only Linux box

These are the steps in the order I ran them on 22 Oct 2026, with the times in IST. Nothing here needs a GPU, an account or a licence form.

**Machine:** Debian, 8 cores, 15 GB RAM, no GPU. The box was shared with other heavy jobs the whole time (load average 15–55). Every timing below is pessimistic.

| # | Step | Command | Result / time |
|---|---|---|---|
| 1 | System packages | `sudo apt install build-essential cmake libcgal-dev libeigen3-dev python3-dev libx11-6 libgl1 libegl1 libegl-mesa0 fonts-dejavu-core` | Installed **CGAL 6.0.1**, Eigen 3.4.0, Boost 1.83, cmake 3.31.6 and g++ 14.2. The repo doesn't pin a CGAL version. |
| 2 | Code | `git clone https://github.com/Net-Maker/GaussiAnimate && git checkout 2012a6e` | MIT licence, commit of 18 Oct 2026 |
| 3 | Python | `uv venv --python 3.10 .venv` | The system Python is 3.13, but the repo requires `>=3.8,<3.12` and `numpy<1.26`. uv 0.13 fetched Python 3.10.22 on its own, so there was no need to touch the system Python. |
| 4 | Python deps | `uv pip install -e '.[geometry,visualization,ssdr,dev]' pybind11` | numpy 1.25.2, scipy 1.15.3, open3d 0.19.0; a minute or two (not timed precisely) |
| 5 | Native builds | `bash scripts/install_geometry.sh` | Builds `pyssdr` (Dem Bones via pybind11) and the CGAL `curve_skeleton` binary: **54 s** wall. With CGAL 6.0.1 it needed no patches. The only output was two harmless CMake warnings (pybind11's old `cmake_minimum_required` and CGAL's FindBoost policy CMP0167). |
| 6 | Data | AMA mesh archives from https://people.csail.mit.edu/drdaniel/mesh_animation/ unpacked to `data/AMA/<case>/meshes/` | 10 sequences, 1.7 GB unpacked; public, no forms |
| 7 | Smoke run | `time python scripts/eval_sequence.py T_samba run/smoke_T_samba` | **71 min 09 s** wall (user 37 min), peak RAM 2.48 GB. Extraction took 4,207 s, almost all of it surface-constrained IK. The rest: SSDR on train frames 11 s, PartMM 4 s, LBS fit 19 s. |
| 8 | Patch | `scripts/fast_tracking.py` (+ `scripts/test_fast_tracking.py`) | The per-frame IK solves run on a 4-process pool. The output is bit-identical (max difference 0.0 on 8 frames) and 8 frames took 75 s instead of 113 s. |
| 9 | Full runs | `scripts/run_seq_one_at_a_time.sh` (one sequence at a time, `OMP_NUM_THREADS=4`, `GA_TRACK_PROCS=4`) | 13–27 min per sequence end to end, about 2.5 GB peak RAM each |
| 10 | Analysis | `python scripts/analyze.py && python scripts/frame_analysis.py` | A few seconds |
| 11 | Renders | `python scripts/render_compare.py <case>` | About 12 s per sequence (24 frames × 4 panels, 480 px each, pure PIL) |

## What broke, and the fix

1. **The Python version.** The box has Python 3.13, and the repo refuses anything newer than 3.11. Its NumPy pin (`<1.26`) has no 3.13 wheels anyway. **Fix:** a uv-managed Python 3.10 virtualenv (step 3). No system changes.
2. **CGAL 6.0.1.** I expected trouble because CGAL 6 changed several headers and the repo gives no version. **No fix needed:** the curve-skeleton tool compiled and ran as is.
3. **A foreground build was interrupted.** The first `install_geometry.sh` call ran in the foreground and was interrupted before it finished. **Fix:** re-ran it in the background with `nohup`, and it succeeded in 54 s.
4. **`/usr/bin/time` was missing.** The first smoke launch failed before running anything. **Fix:** used bash's `time` builtin.
5. **Surface-IK runtime (the real problem).** `refine_motion_with_surface` solves one SLSQP problem per frame, single-threaded, at 16–26 s per frame under load. All 10 sequences would have taken about 12 hours. **Fix:** the per-frame solves don't depend on each other, so `fast_tracking.py` records the exact arguments from the unmodified function and solves them in parallel. The result is bit-identical. T_samba's extraction was made before the patch and is reused as is. See `issues-found/01-surface-ik-runtime.md`.
6. **Scope.** Even with the patch, 10 sequences didn't fit the day, so I cut to 5 sequences before scoring the new ones (PREREGISTRATION Amendment 1, `issues-found/02-scope-cut-5-sequences.md`).
