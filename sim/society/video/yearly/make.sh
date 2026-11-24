#!/usr/bin/env bash
# 大きな年 (はじめて届いた技術・ききん・フェーズが変わった・人が 1 年で 10% 以上動いた・蓄えが 30 日分を切った) だけの、
# ずんだもんの声で図を見せる 1〜2 分の動画 (解説の係の (c))。作り方は video/s3/make.sh と同じ (図 → 声 → ffmpeg でつなぐ)。
#   使い方: bash sim/society/video/yearly/make.sh <年> <作業フォルダ (例: /tmp/yv250)> [VOICEVOX の保存先 (既定 /tmp/vv)]
#   先に: tools/explain_data.py --year <年> (→ /tmp/explain_data_<年>.json) と、解説のワークフロー (→ reports/explain/year<年>.json の video.lines)。
#   大きな年でなければ、何もせずに終わる (FORCE=1 で、文があれば作る)。DRY=1 なら絵と lines.json だけ (声と動画は作らない)。
#   出力: <作業フォルダ>/year<年>.mp4 (1920x1080、音は -16 LUFS)。声・絵・動画はリポジトリに入れない。
#   VOICEVOX がなければ tools/voicevox/setup.sh で入れ直す (HANDOFF の動画の節)。重い所は nice -n 19、ffmpeg のスレッドは FFMPEG_THREADS (既定 2)。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
Y="${1:?年}"; OUT="$(mkdir -p "${2:?作業フォルダ}" && cd "$2" && pwd)"; VV="${3:-/tmp/vv}"
TH="${FFMPEG_THREADS:-2}"; PY="${PY:-python3.13}"
DATA="/tmp/explain_data_$Y.json"; EX="$ROOT/sim/society/reports/explain/year$Y.json"
[ -f "$DATA" ] || "$PY" "$ROOT/sim/society/tools/explain_data.py" --year "$Y" --out "$DATA"
[ -f "$EX" ] || { echo "解説の JSON がない: $EX (先に解説のワークフロー)"; exit 1; }
Q=$("$PY" -c "import json,sys;x=json.load(open(sys.argv[1]));v=x.get('video') or {};print('yes' if v.get('qualifies') and v.get('lines') else 'no')" "$EX")
if [ "$Q" != yes ] && [ "${FORCE:-0}" != 1 ]; then echo "${Y}年は大きな年ではない (動画は作らない)"; exit 0; fi
cd "$OUT"
nice -n 19 "$PY" "$HERE/charts.py" "$DATA" "$EX" .
[ "${DRY:-0}" = 1 ] && { echo "DRY: 絵と lines.json だけ作った ($OUT)"; exit 0; }
[ -x "$VV/venv/bin/python" ] || bash "$ROOT/tools/voicevox/setup.sh" "$VV"
nice -n 19 "$VV/venv/bin/python" "$ROOT/tools/voicevox/synth.py" lines.json voice "$VV"
rm -f seg_*.mp4 list.txt
for id in $("$PY" -c "import json;print(' '.join(l['id'] for l in json.load(open('lines.json'))))"); do
  nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i "$id.png" -i "voice/$id.wav" -af "adelay=300|300,apad=pad_dur=0.8" \
    -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k -shortest "seg_$id.mp4"
  echo "file 'seg_$id.mp4'" >> list.txt
done
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i s99.png -f lavfi -i anullsrc=r=48000:cl=stereo -t 4 \
  -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -vf scale=1920:1080 -c:a aac -ar 48000 -ac 2 -b:a 160k seg_99.mp4
echo "file 'seg_99.mp4'" >> list.txt
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -f concat -safe 0 -i list.txt -c copy raw.mp4
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -i raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -ar 48000 -b:a 160k "year$Y.mp4"
echo "できた: $OUT/year$Y.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "year$Y.mp4") 秒)"
