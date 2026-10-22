#!/bin/bash
# Runs all AMA sequences, up to MAXJ concurrent, memory-gated (MemAvailable >= 1500 MB to start). Resumable.
HERE=$(cd "$(dirname "$0")/.." && pwd)            # this repo
GA_DIR=${GA_DIR:-$HERE/../GaussiAnimate}          # clone of Net-Maker/GaussiAnimate @2012a6e
VENV=${VENV:-$HERE/.venv}
cd "$GA_DIR"
source "$VENV/bin/activate"
export OMP_NUM_THREADS=2 PYTHONPATH="$GA_DIR"
R=$HERE/run/full; mkdir -p $R
MAXJ=${MAXJ:-3}
for c in ${CASES:-D_bouncing D_handstand D_march D_squat I_crane I_jumping I_march I_squat T_swing T_samba}; do
  [ -f $R/$c/metrics.json ] && continue
  while [ $(pgrep -fc "eval_sequence.py") -ge $MAXJ ] || [ $(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo) -lt 1500 ]; do sleep 30; done
  echo "$(date +%T) start $c"
  ( python $HERE/scripts/eval_sequence.py $c $R/$c > $R/$c.log 2>&1; echo "$(date +%T) end $c exit $?" ) &
  sleep 60
done
wait; echo ALL_DONE
