#!/bin/bash
# 自分の PC (Windows・Git Bash) で、動画の組ごとの人のモデルを作る。cloud/build_set.sh と cloud/env_setup.sh のローカル版。
# 使い方 (リポジトリの一番上で):
#   bash sim/society/tools/human/local/build_set_local.sh hide sim/society/tools/human/sets/auto_g1_hide.json hide
#   bash sim/society/tools/human/local/build_set_local.sh hide sim/society/tools/human/sets/auto_g2_hide.json g2
# 置き場: W (既定 リポジトリの .kawabe_work。.git/info/exclude に入れてコミットしない)。できた人のモデルは W/people_glb_<組>。何度動かしても、できているものは飛ばす。
ERA=$1 AUTO=$2 TAG=$3
[ -n "$TAG" ] || { echo "使い方: build_set_local.sh <時代 hide|leather> <自動の人の json> <組の名前>"; exit 1; }
PY311=${PY311:-"py -3.11"} PY=${PY:-py}
REPO="$(cd "$(dirname "$0")/../../../../.." && (pwd -W 2>/dev/null || pwd))"
W=${W:-$REPO/.kawabe_work}
R=$REPO/sim/society/tools/human
AUTO="$(cd "$(dirname "$AUTO")" && (pwd -W 2>/dev/null || pwd))/$(basename "$AUTO")"
set -e
$PY311 --version >/dev/null 2>&1 || { echo "Python 3.11 がありません (py -3.11)。入れてからもう一度"; exit 1; }
$PY -c "import numpy" 2>/dev/null || $PY -m pip install -q numpy
mkdir -p "$W/tmp" "$W/cmu" "$W/vrmsamples"

# 1. CMU の動き (14 個の .bvh)
if [ ! -f "$W/cmu/una/data/026/26_10.bvh" ]; then
  rm -rf "$W/cmu/una"; ( cd "$W/cmu" && git clone -q --filter=blob:none --no-checkout https://github.com/una-dinosauria/cmu-mocap una && cd una && git checkout -q 09a07f54f3bbb58797325f009282d0b2048a2871 -- data/008/08_01.bvh data/013/13_10.bvh data/015/15_07.bvh data/018/18_08.bvh data/022/22_13.bvh data/069/69_73.bvh data/077/77_06.bvh data/077/77_08.bvh data/077/77_16.bvh data/077/77_25.bvh data/079/79_12.bvh data/062/62_07.bvh data/062/62_21.bvh data/026/26_10.bvh )
fi
# 2. VRoid のサンプル (5 つの .vrm)
VROID_DIR="$W/vrmsamples/vroid/beta"
if [ ! -f "$VROID_DIR/Victoria_Rubin.vrm" ]; then
  rm -rf "$W/vrmsamples"; mkdir -p "$W"; ( cd "$W" && git clone -q --filter=blob:none --no-checkout https://github.com/madjin/vrm-samples vrmsamples && cd vrmsamples && git checkout -q HEAD -- vroid/beta/Sendagaya_Shino.vrm vroid/beta/HairSample_Female.vrm vroid/beta/HairSample_Male.vrm vroid/beta/Sakurada_Fumiriya.vrm vroid/beta/Victoria_Rubin.vrm )
fi
# 3. bpy (Blender を Python から)
FL=""; ls "$W"/wheels/bpy-4.5.*-cp311-*win_amd64.whl >/dev/null 2>&1 && FL="--no-index --find-links $W/wheels"  # 先に取っておいた PyPI の wheel
[ -d "$W/bpy/bpy" ] || TMPDIR="$W/tmp" $PY311 -m pip install -q --no-cache-dir $FL --target "$W/bpy" "bpy==4.5.*"
[ -d "$W/bpy/bpy" ] && echo "env ok"
set +e

WK="$W/sena_$TAG" OUT="$W/people_glb_$TAG"
mkdir -p "$WK/vroid/logs"
run() { PEOPLE_ERA=$ERA HUMAN_GLB_DIR="$WK" VROID_WORK="$WK/vroid" VROID_DIR="$VROID_DIR" BLENDER_USER_RESOURCES="$W/userres" PYTHONPATH="$W/bpy" $PY311 -u "$R/run.py" "$R/build_person_vroid.py" -- "$@"; }
# 手で決めた七人 (同じ時代の組にあれば写す)
for p in sena ruo tahi wiro isa nagi sol; do
  if [ -f "$WK/${p}_vroid.glb" ]; then echo "$p ok (前に作った)"
  elif [ -f "$W/sena_$ERA/${p}_vroid.glb" ]; then cp "$W/sena_$ERA/${p}_vroid.glb" "$WK/"; echo "$p copied"
  else run --person $p --samples 48 --only none > "$WK/vroid/logs/$p.txt" 2>&1; echo "$p rc=$? $(ls "$WK/${p}_vroid.glb" 2>/dev/null)"; fi
done
# 記録から自動で決めた人
for p in $($PY -c "import json,sys;print(' '.join(json.load(open(sys.argv[1],encoding='utf-8'))['configs']))" "$AUTO"); do
  if [ -f "$WK/${p}_vroid.glb" ]; then echo "$p ok (前に作った)"; continue; fi
  run --config "$AUTO" --person $p --samples 48 --only sheet > "$WK/vroid/logs/$p.txt" 2>&1; echo "$p rc=$? $(ls "$WK/${p}_vroid.glb" 2>/dev/null)"
done
# 動きをつける
PEOPLE_ERA=$ERA $PY "$R/retarget_cmu.py" --bvh "$W/cmu/una/data" --src "$WK" --out "$OUT" --config "$AUTO" > "$WK/retarget.log" 2>&1; echo "retarget rc=$?"
ls "$OUT" | wc -l; du -sh "$OUT"
echo SETDONE
