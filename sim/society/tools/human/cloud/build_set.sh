#!/bin/bash
# (クラウドで使っていた写し。2026-11-26 にリポジトリへ。ローカルで使うときは docs/society_phase/local_gpu_prompt.md のとおり、/dev/shm と /root とリポジトリの場所を自分の PC のフォルダに読みかえる)
# 動画の組ごとの人のモデル。使い方: bash /root/build_set.sh <時代 hide|leather> <自動の人の json> <組の名前 例 g2>
# 手で決めた七人は、同じ時代の組 /dev/shm/sena_<時代> にあれば写す (なければ作る)
ERA=$1 AUTO=$2 TAG=$3
bash /root/env_setup.sh || exit 1
R=/home/user/RobotSimulaterRyo/sim/society/tools/human
W=/dev/shm/sena_$TAG OUT=/dev/shm/people_glb_$TAG
mkdir -p $W/vroid/logs
cd /tmp
run() { PEOPLE_ERA=$ERA HUMAN_GLB_DIR=$W VROID_WORK=$W/vroid BLENDER_USER_RESOURCES=/dev/shm/sena/userres PYTHONPATH=/dev/shm/bpy python3.11 -u $R/run.py $R/build_person_vroid.py -- "$@"; }
for p in sena ruo tahi wiro isa nagi sol; do
  if [ -f /dev/shm/sena_$ERA/${p}_vroid.glb ]; then cp /dev/shm/sena_$ERA/${p}_vroid.glb $W/; echo "$p copied"; else run --person $p --samples 48 --only none > $W/vroid/logs/$p.txt 2>&1; echo "$p rc=$? $(ls $W/${p}_vroid.glb 2>/dev/null)"; fi
done
for p in $(python3.13 -c "import json;print(' '.join(json.load(open('$AUTO'))['configs']))"); do run --config $AUTO --person $p --samples 48 --only sheet > $W/vroid/logs/$p.txt 2>&1; echo "$p rc=$? $(ls $W/${p}_vroid.glb 2>/dev/null)"; done
PEOPLE_ERA=$ERA python3 $R/retarget_cmu.py --bvh /dev/shm/cmu/una/data --src $W --out $OUT --config $AUTO > $W/retarget.log 2>&1; echo "retarget rc=$?"
mkdir -p /root/people_glb_$TAG && cp $OUT/* /root/people_glb_$TAG/ && du -sh /root/people_glb_$TAG
echo SETDONE
