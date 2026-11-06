#!/usr/bin/env bash
# G10「鉄と広い国」(118年120日目〜150年120日目) の 32 年をまとめた動画を作る (2026-11-06、本人の希望「G10の動画を作って下さい」)。作り方は g9/ と同じ。
# ナレーション: VOICEVOX:ずんだもん (tools/voicevox/setup.sh で用意。声・絵・動画はリポジトリに入れない)。
#   使い方: bash sim/society/video/g10/make.sh <作業フォルダ (例: /tmp/g10v)> [VOICEVOX の保存先 (既定 /tmp/vv)]
#   出力: <作業フォルダ>/g10.mp4 (1920x1080、音は -16 LUFS)
# 文は lines.json (text = 字幕、say = 読み上げ)。文に書いた数は data.py が記録 (sim/society/data。読むだけ) と合うか確かめ、合わないと止まる。
# 中身のもと: docs/society_phase/G10.md。図は charts.py (matplotlib・IPA ゴシック)、絵は shots.cjs (Playwright。テクノロジーツリーも開いて撮る)。
# 重い所は nice -n 19、ffmpeg のスレッドは FFMPEG_THREADS (既定 2)。村のワークフローと同じ checkout で動かしてよい (data は読むだけ、書くのは作業フォルダだけ)。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
OUT="$(mkdir -p "${1:?作業フォルダ}" && cd "$1" && pwd)"; VV="${2:-/tmp/vv}"
TH="${FFMPEG_THREADS:-2}"
cd "$OUT"
nice -n 19 python3 "$HERE/data.py" facts.json
nice -n 19 python3 "$HERE/charts.py" facts.json charts
[ -x "$VV/venv/bin/python" ] || bash "$ROOT/tools/voicevox/setup.sh" "$VV"
nice -n 19 "$VV/venv/bin/python" "$ROOT/tools/voicevox/synth.py" "$HERE/lines.json" voice "$VV"
nice -n 19 node "$HERE/shots.cjs" "$OUT"
rm -f seg_*.mp4 list.txt
for id in $(python3 -c "import json,sys;print(' '.join(l['id'] for l in json.load(open(sys.argv[1]))))" "$HERE/lines.json"); do
  nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i "$id.png" -i "voice/$id.wav" -af "adelay=300|300,apad=pad_dur=0.8" \
    -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k -shortest "seg_$id.mp4"
  echo "file 'seg_$id.mp4'" >> list.txt
done
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i s99.png -f lavfi -i anullsrc=r=48000:cl=stereo -t 5 \
  -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k seg_99.mp4
echo "file 'seg_99.mp4'" >> list.txt
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -f concat -safe 0 -i list.txt -c copy raw.mp4
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -i raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -ar 48000 -b:a 160k g10.mp4
echo "できた: $OUT/g10.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 g10.mp4) 秒)"
