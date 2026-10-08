#!/bin/bash
# Society 2.0 の動画 (G1〜G4 と F、13 本) を話の順に 2 本ずつ撮り、音を合わせて app/ に入れ、最後に第 2 部の通し (G3 + G4) をつなぐ。
# 本人の PC (Windows・Git Bash・GPU) 用:  bash sim/society/video/render_all.sh   (PY は既定で py)
# 続きから撮れる: できた動画は out/society_<名前>.final があれば飛ばす。撮り終えた 60 秒の区間も render_parts.sh が飛ばす
set -u
cd "$(dirname "$0")"
mkdir -p out
LOG=out/ordered.log
log() { echo "$(date '+%m-%d %H:%M:%S') $*" | tee -a "$LOG"; }
export GPU=1 PY=${PY:-py}
ITEMS=(G1:510,600,629,659,990,1019,1229 G1F1:509,510,600 G1F2:629,630,631 G1F3:659,660,779
       G2:1230,1259,1320,1415,1469,1529 G2F1:1259,1260,1290 G2F2:1409,1415,1435 G2F3:1499,1529
       G3:1530,1559,1562,1573,1580,1589 G3F3:1559,1562,1589
       G4:1591,1625,1675,1679,1680,1709 G4F1:1680,1695,1709 G4F2:1636,1679,1680)

render_one() {
  local name=$1 days=$2 out="out/society_$1"
  [ -f "$out.final" ] && { log "$name: already done, skip"; return 0; }
  log "$name: render start (days $days)"
  local t0=$(date +%s)
  DAYS=$days bash render_parts.sh "narration_$name.json" "voice/$name" "$out" >> "out/render_$name.log" 2>&1 || { log "$name: RENDER FAILED"; return 1; }
  $PY ../../../tools/audio/mix.py "$out.timeline.json" "voice/$name" "$out.wav" >> "out/render_$name.log" 2>&1 || { log "$name: MIX FAILED"; return 1; }
  ffmpeg -loglevel error -y -i "${out}_silent.mp4" -i "$out.wav" -c:v libx264 -crf 28 -preset medium -pix_fmt yuv420p \
    -c:a aac -b:a 128k -af loudnorm=I=-16:TP=-1.5:LRA=11 -movflags +faststart -shortest "../app/society_$name.mp4" >> "out/render_$name.log" 2>&1 \
    || { log "$name: ENCODE FAILED"; return 1; }
  touch "$out.final"
  log "$name: done -> app/society_$name.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "../app/society_$name.mp4") s, $(( ($(date +%s) - t0) / 60 )) min)"
}

log "ordered render start (${#ITEMS[@]} videos, 2 at a time)"
for item in "${ITEMS[@]}"; do
  while [ "$(jobs -rp | wc -l)" -ge 2 ]; do wait -n; done
  render_one "${item%%:*}" "${item#*:}" &
  sleep 2
done
wait
if [ -f out/society_G3.final ] && [ -f out/society_G4.final ]; then
  printf "file '%s'\n" ../../app/society_G3.mp4 ../../app/society_G4.mp4 > out/part2.txt
  ffmpeg -loglevel error -y -f concat -safe 0 -i out/part2.txt -c copy -movflags +faststart ../app/society_part2.mp4 >> "$LOG" 2>&1 \
    && log "part2: done -> app/society_part2.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 ../app/society_part2.mp4) s)" \
    || log "part2: CONCAT FAILED"
fi
log "ordered render finished"
