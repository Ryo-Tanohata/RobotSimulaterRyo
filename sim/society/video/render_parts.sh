#!/bin/bash
# 動画を 60 秒ずつ撮り、撮り終えた区間は飛ばす (コンテナが止まっても続きから撮れる)。最後に 1 本につなぐ
# 使い方: CHROME=... LIBS=... DAYS=... bash render_parts.sh <ナレーション.json> <音声フォルダ> <出力の名前 (拡張子なし)>
set -u
cd "$(dirname "$0")"
NARR=$1; VOICE=$2; OUT=$3
TOTAL=$(${PY:-python3} -c "import json;print(json.load(open('$OUT.timeline.json'))['duration'])" 2>/dev/null)
if [ -z "$TOTAL" ]; then PLAN_ONLY=1 node make_video.mjs "$NARR" "$VOICE" "$OUT" >/dev/null; TOTAL=$(${PY:-python3} -c "import json;print(json.load(open('$OUT.timeline.json'))['duration'])"); fi
N=$(${PY:-python3} -c "import math;print(math.ceil($TOTAL/60))")
for ((k=0; k<N; k++)); do
  P=$(printf "%s_p%02d.mp4" "$OUT" $k)
  [ -s "$P" ] && continue
  FROM_SEC=$((k*60)) TO_SEC=$(((k+1)*60)) PART="$P.tmp.mp4" node make_video.mjs "$NARR" "$VOICE" "$OUT" && mv "$P.tmp.mp4" "$P" || exit 1
  echo "part $k / $N"
done
# ffmpeg は一覧の中の道筋を、一覧のファイルがあるフォルダから読むので、名前だけを書く (OUT に out/ などのフォルダがつくとき)
for f in "$OUT"_p*.mp4; do echo "file '$(basename "$f")'"; done > "$OUT.parts.txt"
ffmpeg -loglevel error -y -f concat -safe 0 -i "$OUT.parts.txt" -c copy "${OUT}_silent.mp4" && echo "→ ${OUT}_silent.mp4"
