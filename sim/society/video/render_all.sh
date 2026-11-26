#!/bin/bash
# Society 2.0 の動画 (G1〜G4 と F、13 本) を話の順に 2 本ずつ撮り、音を合わせて app/ に入れ、最後に第 2 部の通し (G3 + G4) をつなぐ。
# Society 1.0 の短いまとめ (S1) も一覧にある (2026-10-15)。第 4 部の G6 と G6 の F1・F2・F4 も一覧にある (2026-10-21。撮る日は days_G6*.txt と同じ)。
# 第 5 部の G7 も一覧にある (2026-10-23。G7 の F はどれも起きなかったので 1 本だけ。撮る日は days_G7.txt と同じ)。
# 第 5 部の G8 と、G8 の F2・F3 も一覧にある (2026-10-27。撮る日は days_G8*.txt と同じ)。
# G8 の最後の 1 年 G8b (「G8 の続き 国の外へ」) も一覧にある (2026-10-28。撮る日は days_G8b.txt と同じ)。
# Society 3.0 フェーズ 3・4 (読み書きと知らせ板・頼み書きと町) の S3P34 も一覧にある (2026-11-22。撮る日は days_S3P34.txt と同じ)。
# 1 日目 (村のいちばん最初の日) を今の 3D で撮り直す D1 も一覧にある (2026-11-22。撮る日は days_D1.txt と同じ)。D1 は SLIM_ITEMS にあるので、撮る日に要る分だけの小さなデータで撮る (make_video.mjs の SLIM)
# D1P (2026-11-23) は、D1 と同じナレーションと声で、棒の人の代わりに人のモデル (VRoid の五人と記録した動き) を動かす。モデルは PEOPLE_DIR (既定は human-model/people_glb。GitHub には入れない)
# D1V (2026-11-23) は、D1P と同じしかけを、クラウドの CPU で撮る版。モデルは tools/human/retarget_cmu.py で作った VRoid の CC0 サンプルの五人 (PEOPLE_DIR_D1V、既定 /dev/shm/people_glb)。
#   12 コマ/秒で撮って、コマを重ねて 24 コマ/秒にする。カメラは五人にもっと寄る。クラウドでは:  GPU= PY=python3 CHROME=<chromium> LIBS=/tmp/libs3 bash render_all.sh D1V
# S1V (2026-11-25 本人「society1.0 からの棒人間を、写実の様式化をしたキャラクターに置き換えたい」「まずは 1 つ」): S1 と同じナレーションと声と撮る日で、
#   D1V と同じしかけ (VRoid の CC0 サンプルの五人をクラウドの CPU で) で撮る。Society 1.0 (8〜489 日目) にいたのは五人だけ
# G1F1V・G1F2V・G1F3V (2026-11-25 本人「あと 3 本」): G1 の F の 3 本を同じしかけで。よそから来たナギ・ソル (629 日目) は people.py の VROID で作る
# 絵コンテ (2026-11-23 本人の決め「まず動画を作る時に絵コンテを作る」): 動画は 1. 絵コンテ → 本人が見る → 2. 本番。
#   bash render_all.sh --storyboard D1V  → out/storyboard_D1V.html (絵つき。git に入れない) と storyboards/storyboard_D1V.json (git に入れる)
# 本人の PC (Windows・Git Bash・GPU) 用:  bash sim/society/video/render_all.sh   (PY は既定で py)
# 名前を渡すと、その動画だけ撮る:  bash sim/society/video/render_all.sh S1   (いくつでも並べられる。名前がなければ一覧の全部)
# 続きから撮れる: できた動画は out/society_<名前>.final があれば飛ばす。撮り終えた 60 秒の区間も render_parts.sh が飛ばす
set -u
cd "$(dirname "$0")"
mkdir -p out
LOG=out/ordered.log
log() { echo "$(date '+%m-%d %H:%M:%S') $*" | tee -a "$LOG"; }
export GPU=${GPU-1} PY=${PY:-py}  # GPU= (空) にすると CPU (swiftshader) で描く (クラウド)
# 日付の書き方が変わったら、前に撮った区間と動画は使えない (時計の日付が全部のコマに入っている)。書き方の印を見て、古いものを消してから撮る
# (2026-10-09: 「11 年目 31 日目」→「10年31日目」。本人の希望)
DATE_FMT="10年31日目 (年は過ぎた年の数、2026-10-09)"
if [ "$(cat out/date_format.txt 2>/dev/null)" != "$DATE_FMT" ]; then
  log "date format changed -> remove parts and finals rendered with the old format"
  rm -f out/society_*_p[0-9][0-9].mp4 out/society_*_silent.mp4 out/society_*.final
  echo "$DATE_FMT" > out/date_format.txt
fi
ITEMS=(G1:510,600,629,659,990,1019,1229 G1F1:509,510,600 G1F2:629,630,631 G1F3:659,660,779
       G2:1230,1259,1320,1415,1469,1529 G2F1:1259,1260,1290 G2F2:1409,1415,1435 G2F3:1499,1529
       G3:1530,1559,1562,1573,1580,1589 G3F3:1559,1562,1589
       G4:1591,1625,1675,1679,1680,1709 G4F1:1680,1695,1709 G4F2:1636,1679,1680
       S1:8,32,84,153,285,489
       G6:3569,4259,4439,4922,5309,5849 G6F1:3539,3569,3599 G6F2:3539,3989,4049 G6F4:5249,5309,5339
       G7:5849,6449,7559,7829,8159,8519
       G8:8519,8639,10919,11159,12461,12479 G8F2:8639,8759,8789 G8F3:8999,9509,9629
       G8b:12479,12509,12599
       S3P34:27000,27059,27360,27839,27870,28079
       D1:1 D1P:1 D1V:1
       S1V:8,32,84,153,285,489
       G1F1V:509,510,600 G1F2V:629,630,631 G1F3V:659,660,779
       G1V:510,600,629,659,990,1019,1229
       G2V:1230,1259,1320,1415,1469,1529 G2F1V:1259,1260,1290 G2F2V:1409,1415,1435 G2F3V:1499,1529
       G3V:1530,1559,1562,1573,1580,1589 G3F3V:1559,1562,1589)
# 小さなデータで撮る動画 (2026-11-22): ページには、撮る日に要る分だけの app_data.json を配る (make_video.mjs の SLIM=1。data/ には書かない)。
# 前からある動画は、前と同じく全部のデータで撮る
SLIM_ITEMS=" D1 D1P D1V S1V G1F1V G1F2V G1F3V G1V G2V G2F1V G2F2V G2F3V G3V G3F3V "
# 人のモデルで撮る動画と、ナレーションと声を借りる動画 (2026-11-23)
PEOPLE_ITEMS=" D1P D1V S1V G1F1V G1F2V G1F3V G1V G2V G2F1V G2F2V G2F3V G3V G3F3V "
src_of() { case "$1" in D1P|D1V) echo D1 ;; S1V) echo S1 ;; G1F1V|G1F2V|G1F3V|G1V|G2V|G2F1V|G2F2V|G2F3V|G3V|G3F3V) echo "${1%V}" ;; *) echo "$1" ;; esac; }
# 動画ごとの撮り方の違い (env で make_video.mjs に渡す)。D1V: クラウドの CPU 向け (12 コマ/秒・毎フレームの描画を止める・区間の前を進めておく・五人に寄る・モデルのクレジット)
opts_of() { case "$1" in
  D1V) echo "FPS=12 NO_RAF=1 PREROLL=3 PEOPLE=${PEOPLE_DIR_D1V:-/dev/shm/people_glb} PEOPLE_VIEW=$D1V_VIEW HIDE_TOASTS=1" ;;
  S1V|G1F1V|G1F2V|G1F3V|G1V) echo "FPS=12 NO_RAF=1 PREROLL=3 PEOPLE=$PEOPLE_DIR_HIDE PEOPLE_VIEW=$G1V_VIEW HIDE_TOASTS=1" ;;
  G2V|G2F1V|G2F2V|G2F3V|G3V|G3F3V) echo "FPS=12 NO_RAF=1 PREROLL=3 PEOPLE=$PEOPLE_DIR_G2 PEOPLE_VIEW=$G2V_VIEW HIDE_TOASTS=1" ;;
  *) echo "" ;; esac; }
D1V_CAM='{"min":4.5,"add":2.5,"k":1.6,"max":40}'
# D1V の見せ方 (2026-11-23 本人の絵コンテの直し): 赤い玉 (木の実・芋) を隠す・昼は組ごとに画面を分ける・火のまわりは引いて上から。
# 出来事の帯は出さず、した人の頭の上に短い吹き出し (本人の選んだ案 C)
D1V_VIEW='{"split":true,"noPlants":true,"bubbles":true,"bubbleFont":22,"nightLight":true}'
# G1 の F と S1V (2026-11-25): D1V と同じ見せ方に、よそから来たナギ・ソルのモデル (opts.files)、本人の直し (v2: 住まいをよける・夜は住まいに入る・
#   採集の植物・住まいを建てる・動物・植物が育つ。fireNightly: 焚き火を毎晩灯す) を足す
G1V_VIEW='{"split":true,"noPlants":true,"bubbles":true,"bubbleFont":22,"nightLight":true,"fireMax":14,"v2":true,"fireNightly":true,"files":{"ナギ":"nagi","ソル":"sol","ミラ":"p008","ケト":"p009","ハユ":"p010","トワ":"p012","サエ":"p013","ユノ":"p014","カイ":"p015","フウ":"p018","モエ":"p019","シノ":"p020"}}'
# 2026-11-25: 服を着た人のモデル (時代 hide = Society 1.0〜G1 の生皮。docs/society_phase/fashion.md)。G1 の人は tools/human/auto_people.py で記録から自動で作った (files)
PEOPLE_DIR_HIDE=${PEOPLE_DIR_HIDE:-/dev/shm/people_glb_hide}
# G3 (2026-11-26) も G2 と同じ人の組と見せ方 (G3 に出る人は G2 と同じ。家族の家は 1590 日目からで、G3 の撮る日にはまだない)
# G2 (2026-11-26): 服は生皮のまま (ヤギを飼いはじめたばかり)。ヤギの囲いと頭数は記録から。人は G2 の撮る日々で作り直した組 (子の背が G1 とちがう)
G2V_VIEW='{"split":true,"noPlants":true,"bubbles":true,"bubbleFont":22,"nightLight":true,"fireMax":14,"v2":true,"fireNightly":true,"files":{"ナギ":"nagi","ソル":"sol","ミラ":"p008","ケト":"p009","ハユ":"p010","トワ":"p012","サエ":"p013","ユノ":"p014","カイ":"p015","ネム":"p016","ラタ":"p017","フウ":"p018","モエ":"p019","シノ":"p020","テオ":"p021","アル":"p022","ヨナ":"p023","クラ":"p024"}}'
PEOPLE_DIR_G2=${PEOPLE_DIR_G2:-/dev/shm/people_glb_g2}
D1V_CREDIT="VRoid の CC0 サンプル (pixiv) をもとに作成"
STORY=
[ "${1:-}" = "--storyboard" ] && { STORY=1; shift; }
# 名前が渡されたら、一覧からその動画だけを選ぶ (知らない名前なら何もせずに止まる)
PART2=1
if [ $# -gt 0 ]; then
  SEL=() PART2=
  for want in "$@"; do
    found=
    for item in "${ITEMS[@]}"; do [ "${item%%:*}" = "$want" ] && { SEL+=("$item"); found=1; }; done
    [ -n "$found" ] || { echo "unknown video name: $want (known: ${ITEMS[*]%%:*})" >&2; exit 1; }
    case "$want" in G3|G4) PART2=1 ;; esac  # 第 2 部の通しは、G3 か G4 を撮るときだけつなぎ直す
  done
  ITEMS=("${SEL[@]}")
fi

render_one() {
  local name=$1 days=$2 out="out/society_$1"
  [ -z "$STORY" ] && [ -f "$out.final" ] && { log "$name: already done, skip"; return 0; }
  log "$name: render start (days $days)"
  local t0=$(date +%s)
  local slim=; case "$SLIM_ITEMS" in *" $name "*) slim=1 ;; esac
  local src=$(src_of "$name") people=; case "$PEOPLE_ITEMS" in *" $name "*) people=${PEOPLE_DIR:-../../../../human-model/people_glb} ;; esac
  local cam= credit= vf=; case "$name" in D1V|S1V|G1F1V|G1F2V|G1F3V|G1V|G2V|G2F1V|G2F2V|G2F3V|G3V|G3F3V) ;; *) false ;; esac && { cam=$D1V_CAM credit=$D1V_CREDIT vf="-vf fps=24"; }
  case "$name" in S1V|G1F1V|G1F2V|G1F3V|G1V|G2V|G2F1V|G2F2V|G2F3V|G3V|G3F3V) credit="$D1V_CREDIT<br>毎晩の焚き火・家族の小屋・動物と植物の形と動きは、記録にない所を描きそえた (いつ・どこで・だれがは記録のとおり)" ;; esac
  if [ -n "$STORY" ]; then  # 絵コンテだけ
    env SLIM=$slim PEOPLE=$people DAYS=$days PEOPLE_CAM="$cam" PEOPLE_CREDIT="$credit" $(opts_of "$name") node storyboard.mjs "narration_$src.json" "voice/$src" "out/storyboard_$name" >> "out/storyboard_$name.log" 2>&1 \
      && log "$name: storyboard -> out/storyboard_$name.html" || log "$name: STORYBOARD FAILED"
    return 0
  fi
  env SLIM=$slim PEOPLE=$people DAYS=$days PEOPLE_CAM="$cam" PEOPLE_CREDIT="$credit" $(opts_of "$name") bash render_parts.sh "narration_$src.json" "voice/$src" "$out" >> "out/render_$name.log" 2>&1 || { log "$name: RENDER FAILED"; return 1; }
  $PY ../../../tools/audio/mix.py "$out.timeline.json" "voice/$src" "$out.wav" >> "out/render_$name.log" 2>&1 || { log "$name: MIX FAILED"; return 1; }
  ffmpeg -loglevel error -y -i "${out}_silent.mp4" -i "$out.wav" $vf -c:v libx264 -crf 28 -preset medium -pix_fmt yuv420p \
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
if [ -n "$PART2" ] && [ -f out/society_G3.final ] && [ -f out/society_G4.final ]; then
  printf "file '%s'\n" ../../app/society_G3.mp4 ../../app/society_G4.mp4 > out/part2.txt
  ffmpeg -loglevel error -y -f concat -safe 0 -i out/part2.txt -c copy -movflags +faststart ../app/society_part2.mp4 >> "$LOG" 2>&1 \
    && log "part2: done -> app/society_part2.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 ../app/society_part2.mp4) s)" \
    || log "part2: CONCAT FAILED"
fi
log "ordered render finished"
