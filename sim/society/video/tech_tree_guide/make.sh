#!/usr/bin/env bash
# テクノロジーツリーのページ (sim/society/app/tech_tree.html) の見方の動画を作る (2026-11-04、本人の希望)。
# ナレーション: VOICEVOX:ずんだもん (tools/voicevox/setup.sh で用意。声も動画もリポジトリに入れない)。
#   使い方: bash sim/society/video/tech_tree_guide/make.sh <作業フォルダ> "<画面の記録の日 (例: 109年30日目の記録)>" [VOICEVOX の保存先 (既定 /tmp/vv)]
#   出力: <作業フォルダ>/tech_tree_guide.mp4 (1920x1080、音は -16 LUFS)
# 文は lines.json (act: top = いちばん上 / show = その部分を枠で囲む (outline false で囲まない) / click = 箱を押して説明を出す)。
# 数 (届いた数・年) は文に書いてあるので、ページの数が変わったら lines.json を直す。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
OUT="${1:?作業フォルダ}"; ASOF="${2:-}"; VV="${3:-/tmp/vv}"
mkdir -p "$OUT"; cd "$OUT"
[ -x "$VV/venv/bin/python" ] || bash "$ROOT/tools/voicevox/setup.sh" "$VV"
"$VV/venv/bin/python" "$ROOT/tools/voicevox/synth.py" "$HERE/lines.json" voice "$VV"
node "$HERE/shots.cjs" "$OUT"
node "$HERE/card.cjs" "$OUT" "$ASOF"
rm -f seg_*.mp4 list.txt
for id in $(python3 -c "import json,sys;print(' '.join(l['id'] for l in json.load(open(sys.argv[1]))))" "$HERE/lines.json"); do
  ffmpeg -loglevel error -y -loop 1 -i "$id.png" -i "voice/$id.wav" -af "adelay=300|300,apad=pad_dur=0.8" \
    -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k -shortest "seg_$id.mp4"
  echo "file 'seg_$id.mp4'" >> list.txt
done
ffmpeg -loglevel error -y -loop 1 -i s99.png -f lavfi -i anullsrc=r=48000:cl=stereo -t 5 \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k seg_99.mp4
echo "file 'seg_99.mp4'" >> list.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i list.txt -c copy raw.mp4
ffmpeg -loglevel error -y -i raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -ar 48000 -b:a 160k tech_tree_guide.mp4
echo "できた: $OUT/tech_tree_guide.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 tech_tree_guide.mp4) 秒)"
