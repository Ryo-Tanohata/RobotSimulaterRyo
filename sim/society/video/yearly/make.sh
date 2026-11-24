#!/usr/bin/env bash
# 年報の動画 (1 年 1 本、2〜3 分)。案内役ソナ85 と 4 つの分野の係 (みな村の人) が、それぞれの声 (VOICEVOX) で、年報と統計のページの図を見せながら話す。
# 決まり (HANDOFF §3): 先に絵コンテを作って本人に見てもらい、本人の「go」のあとで本番の動画を作る。
#   絵コンテまで: bash sim/society/video/yearly/make.sh <年> <作業フォルダ (例 /tmp/yv250)> [VOICEVOX の保存先 (既定 /tmp/vv)]
#     → sim/society/video/out/storyboard_yearly_<年>.html と .jpg (絵つき。git に入れない)・video/storyboards/storyboard_yearly_<年>.json (git に入れてよい)
#   本番 (本人の go のあと): GO=1 bash sim/society/video/yearly/make.sh <年> <作業フォルダ> [VOICEVOX]
#     → <作業フォルダ>/year<年>.mp4 (1280x720・30 コマ/秒・音は -16 LUFS)。絵コンテと同じ絵と声を使う (作業フォルダを消さないこと)
# 先に要るもの: reports/explain/year<年>.json (解説の係のワークフロー)。/tmp/explain_data_<年>.json がなければ explain_data.py で作る (data は読むだけ)。
# 中身: script.py (台本) → tools/voicevox/synth.py (声。話す人ごとに voices.json の声) → charts.py (図と 1 文の絵) → storyboard.py (絵コンテ)。
# 声・絵・動画はリポジトリに入れない。声の音声モデルは voices.json の vvm (tools/voicevox/setup.sh のあと、voicevox_vvm の vvms/ から足す。README)。
# 重い所は nice -n 19、ffmpeg のスレッドは FFMPEG_THREADS (既定 2)。記憶: 声 約 1.7 GB (音声モデル 4 つ)・絵 約 0.3 GB・ffmpeg 約 0.2 GB。村の重い歩 (記録づくり 約 10 GB) と重ねない。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
Y="${1:?年}"; OUT="$(mkdir -p "${2:?作業フォルダ}" && cd "$2" && pwd)"; VV="${3:-/tmp/vv}"
TH="${FFMPEG_THREADS:-2}"; PY="${PY:-python3.13}"
DATA="/tmp/explain_data_$Y.json"; EX="$ROOT/sim/society/reports/explain/year$Y.json"
SB="$ROOT/sim/society/video/out/storyboard_yearly_$Y"
[ -f "$EX" ] || { echo "解説の JSON がない: $EX (先に解説のワークフロー)"; exit 1; }
[ -f "$DATA" ] || nice -n 19 "$PY" "$ROOT/sim/society/tools/explain_data.py" --year "$Y" --out "$DATA"
cd "$OUT"
if [ "${GO:-0}" != 1 ]; then
  nice -n 19 "$PY" "$HERE/script.py" "$DATA" "$EX" "$HERE/voices.json" .
  [ -x "$VV/venv/bin/python" ] || bash "$ROOT/tools/voicevox/setup.sh" "$VV"
  for v in $("$PY" -c "import json;print(' '.join(sorted({l['vvm'] for l in json.load(open('lines.json'))})))"); do
    [ -f "$VV/vvms/$v" ] || { echo "音声モデルがない: $VV/vvms/$v (README の「声」)"; exit 1; }
  done
  nice -n 19 "$VV/venv/bin/python" "$ROOT/tools/voicevox/synth.py" lines.json voice "$VV" > voice.log
  nice -n 19 "$PY" "$HERE/charts.py" "$DATA" . "$HERE/voices.json"
  nice -n 19 "$PY" "$HERE/storyboard.py" . "$SB"
  echo "絵コンテまで作った。本人に見てもらい、go のあとで: GO=1 bash $0 $Y $OUT $VV"
  exit 0
fi
[ -f "$SB.html" ] && [ -f voice/durations.json ] || { echo "先に絵コンテ (GO なしで make.sh)"; exit 1; }
rm -f seg_*.mp4 list.txt
for id in $("$PY" -c "import json;print(' '.join(l['id'] for l in json.load(open('lines.json'))))"); do
  nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i "$id.png" -i "voice/$id.wav" -af "adelay=300|300,apad=pad_dur=0.8" \
    -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -c:a aac -ar 48000 -ac 2 -b:a 160k -shortest "seg_$id.mp4"
  echo "file 'seg_$id.mp4'" >> list.txt
done
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -loop 1 -i s99.png -f lavfi -i anullsrc=r=48000:cl=stereo -t 5 \
  -c:v libx264 -threads "$TH" -tune stillimage -pix_fmt yuv420p -r 30 -c:a aac -ar 48000 -ac 2 -b:a 160k seg_99.mp4
echo "file 'seg_99.mp4'" >> list.txt
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -f concat -safe 0 -i list.txt -c copy raw.mp4
nice -n 19 ffmpeg -loglevel error -y -threads "$TH" -i raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -ar 48000 -b:a 160k "year$Y.mp4"
echo "できた: $OUT/year$Y.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "year$Y.mp4") 秒)"
