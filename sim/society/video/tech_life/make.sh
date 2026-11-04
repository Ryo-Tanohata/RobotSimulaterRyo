#!/usr/bin/env bash
# テクノロジーツリーに届いたテクノロジーが、村の暮らしにどう出たかの動画を作る (2026-11-04、本人の希望
# 「テクノロジーツリーでテクノロジーが可視化されましたが、それで実際生活にどのように反映されているかも動画化したいです」)。
# ナレーション: VOICEVOX:ずんだもん (tools/voicevox/setup.sh で用意。声・絵・動画はリポジトリに入れない)。
#   使い方: bash sim/society/video/tech_life/make.sh <作業フォルダ> [記録の日 (既定 13799 = 114年120日目)] [VOICEVOX の保存先 (既定 /tmp/vv)]
#   出力: <作業フォルダ>/tech_life.mp4 (1920x1080、音は -16 LUFS)
# 文は lines.json。文に書いた数は data.py が記録 (sim/society/data。読むだけ) と合うか確かめ、合わないと止まる。
# 図は charts.py (matplotlib・IPA ゴシック)、絵は shots.cjs (Playwright。ツリーの箱はページから切り出す)。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
OUT="$(mkdir -p "${1:?作業フォルダ}" && cd "$1" && pwd)"; ASOF_DAY="${2:-13799}"; VV="${3:-/tmp/vv}"
ASOF="$((ASOF_DAY / 120))年$((ASOF_DAY % 120 + 1))日目まで"
cd "$OUT"
python3 "$HERE/data.py" facts.json "$ASOF_DAY"
python3 "$HERE/charts.py" facts.json charts
cp "$ROOT/sim/society/app/tech_tree.html" tt.html
python3.13 "$ROOT/sim/society/tools/build_tech_tree.py" --out tt.json --embed tt.html --quiet
[ -x "$VV/venv/bin/python" ] || bash "$ROOT/tools/voicevox/setup.sh" "$VV"
"$VV/venv/bin/python" "$ROOT/tools/voicevox/synth.py" "$HERE/lines.json" voice "$VV"
node "$HERE/shots.cjs" "$OUT" "$ASOF"
rm -f seg_*.mp4 list.txt
for id in $(python3 -c "import json,sys;print(' '.join(l['id'] for l in json.load(open(sys.argv[1]))))" "$HERE/lines.json"); do
  ffmpeg -loglevel error -y -loop 1 -i "$id.png" -i "voice/$id.wav" -af "adelay=300|300,apad=pad_dur=0.5" \
    -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k -shortest "seg_$id.mp4"
  echo "file 'seg_$id.mp4'" >> list.txt
done
ffmpeg -loglevel error -y -loop 1 -i s99.png -f lavfi -i anullsrc=r=48000:cl=stereo -t 5 \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k seg_99.mp4
echo "file 'seg_99.mp4'" >> list.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i list.txt -c copy raw.mp4
ffmpeg -loglevel error -y -i raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -ar 48000 -b:a 160k tech_life.mp4
echo "できた: $OUT/tech_life.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 tech_life.mp4) 秒)"
