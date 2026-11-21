#!/usr/bin/env bash
# 「Society 3.0 これまで」(200年120日目〜232年の終わり。後押しなしの確かめ・フェーズ 1〜4) の約 32 年をまとめた動画を作る
# (232年の終わり、フェーズ 4「頼み書きと町」の 1 年目が終わったあと)。作り方は part7/ と同じ。はじめに G15 (193〜200年) を 1 枚だけふりかえる。
# ナレーション: VOICEVOX:ずんだもん (tools/voicevox/setup.sh で用意。声・絵・動画はリポジトリに入れない)。
#   使い方: bash sim/society/video/s3/make.sh <作業フォルダ (例: /tmp/s3v)> [VOICEVOX の保存先 (既定 /tmp/vv)]
#   出力: <作業フォルダ>/s3.mp4 (1920x1080、音は -16 LUFS)
# 文は lines.json (text = 字幕、say = 読み上げ)。文に書いた数は data.py が記録 (sim/society/data。読むだけ) と合うか確かめ、合わないと止まる。
# 中身のもと: 年報 (sim/society/reports/year200〜232.html)・記録・HANDOFF.md・docs/society_phase/ (G15_push・S3_check・S4_check・I4_design・I4_check・P4_design)。
# 図は charts.py (matplotlib・IPA ゴシック)、絵は shots.cjs (Playwright。232年の年報のフェーズ 3 の表も撮る)。
# 呼び名: コードと state の文には前の呼び名 (Society 4.0 …) が残るが、動画には今の呼び名「Society 3.0 フェーズ N」だけを出す (data.py が確かめる)。
# 重い所は nice -n 19、ffmpeg のスレッドは FFMPEG_THREADS (既定 2)。村のワークフローと同じ checkout で動かしてよい (data は読むだけ、書くのは作業フォルダだけ)。
# python は python3.13 (PY で変えられる)。playwright が見つからないときは npm の大域のフォルダを NODE_PATH に足す。
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
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -i raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -ar 48000 -b:a 160k s3.mp4
echo "できた: $OUT/s3.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 s3.mp4) 秒)"
