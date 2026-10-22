# 03: Small setup and run snags
- `/usr/bin/time` isn't installed on the box, so the first smoke launch failed before running anything. I used bash `time` instead.
- The first native build ran in the foreground, was interrupted, and was re-run in the background. It succeeded in 54 s with CGAL 6.0.1, no patches needed.
- When the 5-sequence cut arrived (13:58 IST), the old runner had just started D_march (dropped). I killed it after 30 s, before any metric existed, and moved its partial output to `run/dropped/` (not in the repo).
- The box was shared with other heavy jobs (load average 15–55), so every timing is pessimistic.
