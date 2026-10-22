#!/bin/bash
# Sequential runner (parent request 12:51 IST): one sequence at a time, OMP_NUM_THREADS=4. Resumable.
cd /workspace/new-exp/GaussiAnimate
source /workspace/new-exp/gaussianimate/.venv/bin/activate
export OMP_NUM_THREADS=4 PYTHONPATH=/workspace/new-exp/GaussiAnimate
export GA_TRACK_PROCS=4
R=/workspace/new-exp/gaussianimate/run/full; S=/workspace/new-exp/gaussianimate/run/smoke_T_samba
for c in D_bouncing T_samba D_handstand T_swing I_jumping; do  # Amendment 1 (13:59 IST): 5-sequence cut
  [ -f $R/$c/metrics.json ] && continue
  while pgrep -f "eval_sequence.py" >/dev/null; do sleep 30; done
  [ -f $R/$c/metrics.json ] && continue
  if [ $c = T_samba ] && [ -f $S/full_extraction/skelebones.npz ] && [ ! -d $R/T_samba ]; then
    mkdir -p $R/T_samba && cp -r $S/full_extraction $R/T_samba/ && cp $S/metrics_extraction_time.json $R/T_samba/ 2>/dev/null; fi
  echo "$(date +%T) start $c"
  python /workspace/new-exp/gaussianimate/scripts/eval_sequence.py $c $R/$c > $R/$c.log 2>&1; echo "$(date +%T) end $c exit $?"
done; echo ALL_DONE
