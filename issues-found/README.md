# Issues found
| # | Issue | Status |
|---|---|---|
| [01](01-surface-ik-runtime.md) | Surface-constrained IK dominates runtime (16–26 s/frame, single-threaded) | fixed with a bit-identical 4-process wrapper |
| [02](02-scope-cut-5-sequences.md) | Scope cut from 10 to 5 sequences (user time decision) | disclosed; Amendment 1 |
| [03](03-setup-snags.md) | Setup snags: Python 3.13 vs the repo's ≤3.11 pin, `/usr/bin/time` missing, an interrupted foreground build, and a dropped sequence (D_march) that the old runner had started (killed after 30 s, no output) | handled |
| [04](04-method-limits.md) | Method limits: pose-tracker test leak, paper not reproducible (gated data, no checkpoints), CPU only, frame-level CIs too narrow, baseline changed before pre-registration | disclosed |

The step-by-step setup with timings is in [../SETUP_LOG.md](../SETUP_LOG.md).
