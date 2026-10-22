#!/bin/bash
# Runs all AMA sequences, up to MAXJ concurrent, memory-gated (MemAvailable >= 1500 MB to start). Resumable.
cd /workspace/new-exp/GaussiAnimate
source /workspace/new-exp/gaussianimate/.venv/bin/activate
export OMP_NUM_THREADS=2 PYTHONPATH=/workspace/new-exp/GaussiAnimate
R=/workspace/new-exp/gaussianimate/run/full; mkdir -p $R
MAXJ=${MAXJ:-3}
for c in ${CASES:-D_bouncing D_handstand D_march D_squat I_crane I_jumping I_march I_squat T_swing T_samba}; do
  [ -f $R/$c/metrics.json ] && continue
  while [ $(pgrep -fc "eval_sequence.py") -ge $MAXJ ] || [ $(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo) -lt 1500 ]; do sleep 30; done
  echo "$(date +%T) start $c"
  ( python /workspace/new-exp/gaussianimate/scripts/eval_sequence.py $c $R/$c > $R/$c.log 2>&1; echo "$(date +%T) end $c exit $?" ) &
  sleep 60
done
wait; echo ALL_DONE
