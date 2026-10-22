# Issues found
| # | Issue | Status |
|---|---|---|
| 01 | Surface-constrained IK dominates runtime (16–26 s/frame, single-threaded) | fixed with a bit-identical 4-process wrapper |
| 02 | Scope cut from 10 to 5 sequences (user time decision) | disclosed; Amendment 1 |
| 03 | Small setup snags: `/usr/bin/time` missing, an interrupted foreground build, and a dropped sequence (D_march) that the old runner had started, killed after 30 s with no output | handled |
