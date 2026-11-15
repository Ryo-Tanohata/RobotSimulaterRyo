#!/usr/bin/env bash
# 第 7 部「帝国のあとと町」(G13 172年120日目〜178年60日目・G14 178年60日目〜193年60日目) の約 20 年半をまとめた動画を作る
# (193年60日目に G14 を本人の決め (Claude のおすすめ) で閉じ、第 7 部が終わったあと)。作り方は g12/ と同じ。
# ナレーション: VOICEVOX:ずんだもん (tools/voicevox/setup.sh で用意。声・絵・動画はリポジトリに入れない)。
#   使い方: bash sim/society/video/part7/make.sh <作業フォルダ (例: /tmp/p7v)> [VOICEVOX の保存先 (既定 /tmp/vv)]
#   出力: <作業フォルダ>/part7.mp4 (1920x1080、音は -16 LUFS)
# 文は lines.json (text = 字幕、say = 読み上げ)。文に書いた数は data.py が記録 (sim/society/data。読むだけ) と合うか確かめ、合わないと止まる。
# 中身のもと: 年報 (sim/society/reports/year173〜193.html)・記録・G13.md・G14_design.md・HANDOFF.md。図は charts.py (matplotlib・IPA ゴシック)、
# 絵は shots.cjs (Playwright。テクノロジーツリーの「商業」も開いて撮る)。
# 重い所は nice -n 19、ffmpeg のスレッドは FFMPEG_THREADS (既定 2)。data は読むだけ、書くのは作業フォルダだけ。
# g12 とのちがい: python は python3.13 (PY で変えられる)。playwright が見つからないときは npm の大域のフォルダを NODE_PATH に足す。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
OUT="$(mkdir -p "${1:?作業フォルダ}" && cd "$1" && pwd)"; VV="${2:-/tmp/vv}"
TH="${FFMPEG_THREADS:-2}"; PY="${PY:-python3.13}"
node -e "require('playwright')" 2>/dev/null || export NODE_PATH="${NODE_PATH:+$NODE_PATH:}$(npm root -g)"
cd "$OUT"
nice -n 19 "$PY" "$HERE/data.py" facts.json
nice -n 19 "$PY" "$HERE/charts.py" facts.json charts
[ -x "$VV/venv/bin/python" ] || bash "$ROOT/tools/voicevox/setup.sh" "$VV"
nice -n 19 "$VV/venv/bin/python" "$ROOT/tools/voicevox/synth.py" "$HERE/lines.json" voice "$VV"
nice -n 19 node "$HERE/shots.cjs" "$OUT"
rm -f seg_*.mp4 list.txt
for id in $("$PY" -c "import json,sys;print(' '.join(l['id'] for l in json.load(open(sys.argv[1]))))" "$HERE/lines.json"); do
  nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i "$id.png" -i "voice/$id.wav" -af "adelay=300|300,apad=pad_dur=0.8" \
    -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k -shortest "seg_$id.mp4"
  echo "file 'seg_$id.mp4'" >> list.txt
done
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i s99.png -f lavfi -i anullsrc=r=48000:cl=stereo -t 5 \
  -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k seg_99.mp4
echo "file 'seg_99.mp4'" >> list.txt
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -f concat -safe 0 -i list.txt -c copy raw.mp4
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -i raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -ar 48000 -b:a 160k part7.mp4
echo "できた: $OUT/part7.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 part7.mp4) 秒)"
