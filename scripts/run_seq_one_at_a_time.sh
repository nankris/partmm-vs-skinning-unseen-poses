#!/bin/bash
# Sequential runner (parent request 12:51 IST): one sequence at a time, OMP_NUM_THREADS=4. Resumable.
HERE=$(cd "$(dirname "$0")/.." && pwd)            # this repo
GA_DIR=${GA_DIR:-$HERE/../GaussiAnimate}          # clone of Net-Maker/GaussiAnimate @2012a6e
VENV=${VENV:-$HERE/.venv}
cd "$GA_DIR"
source "$VENV/bin/activate"
export OMP_NUM_THREADS=4 PYTHONPATH="$GA_DIR"
export GA_TRACK_PROCS=4
R=$HERE/run/full; S=$HERE/run/smoke_T_samba
for c in D_bouncing T_samba D_handstand T_swing I_jumping; do  # Amendment 1 (13:59 IST): 5-sequence cut
  [ -f $R/$c/metrics.json ] && continue
  while pgrep -f "eval_sequence.py" >/dev/null; do sleep 30; done
  [ -f $R/$c/metrics.json ] && continue
  if [ $c = T_samba ] && [ -f $S/full_extraction/skelebones.npz ] && [ ! -d $R/T_samba ]; then
    mkdir -p $R/T_samba && cp -r $S/full_extraction $R/T_samba/ && cp $S/metrics_extraction_time.json $R/T_samba/ 2>/dev/null; fi
  echo "$(date +%T) start $c"
  python $HERE/scripts/eval_sequence.py $c $R/$c > $R/$c.log 2>&1; echo "$(date +%T) end $c exit $?"
done; echo ALL_DONE
