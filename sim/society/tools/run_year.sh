#!/usr/bin/env bash
# 本物の村を 1 年回し、年の終わりの手順 (年報 → 解説の係 → 年報を作り直す → 統計のページ → 年報の動画の絵コンテ) まで進めて、コミットする (push はしない)。
# 2026-11-28: 前は /tmp/yearend.sh・/tmp/yrcheck.sh (入れ物が替わると消える) だったので、HANDOFF.md の手順から作り直してリポジトリに置いた。
# 作者は Ryo-Tanohata、Claude は共同作者 (本人の決まり)。
#
#   bash sim/society/tools/run_year.sh                 1 年回して (季節のワークフロー)、年の終わりなら年の終わりの手順まで
#   bash sim/society/tools/run_year.sh --yearend Y [T] 年の終わりの手順だけ (Y年。T はその年のトークン。なければ年報に出さない)
#
# 環境の変数: PY (既定 python3.13。3.11 だと食べ物の数の最後の桁がずれる)・CLAUDE_SESSION_URL (コミットの Claude-Session の行)・
#   RUN_WF_CONC (同時に動かす係。既定 8)・FABLE (Fable で答える人。既定 オセ78 = G15 で作る側が入れた人。HANDOFF.md の G15)
# ログ: /tmp/run_year_<はじめの日>.log (季節のワークフロー。合わせのトークンは最後の行)・.json (ワークフローの返した値)・
#   /tmp/explain_wf_<年>.log (解説の係)・/tmp/yv<年>/ (年報の動画の作業フォルダ。本人の go のあと GO=1 で本番に使う)
# 記憶: 季節の歩 (記録づくり) は 約 10〜12 GB。年報の動画の絵コンテ (声 約 1.7 GB) は季節の歩と重ならないよう、年の終わりのあとに動かす。
# 止まったとき (HOLD consult など) も、年の終わりの日なら年の終わりの手順まで進めてから止まる (相談は本人への報告で)。
set -uo pipefail
cd "$(dirname "$0")/../../.."
PY=${PY:-python3.13}
FABLE=${FABLE:-オセ78}
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

commit() {  # commit "<見出し>" ファイル...
  local msg=$1; shift
  git add "$@" && git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -q -m "$msg" \
    -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>${CLAUDE_SESSION_URL:+
Claude-Session: $CLAUDE_SESSION_URL}" && echo "コミットした: $msg"
}

yearend() {  # yearend Y [T]
  local Y=$1 T=${2:-}
  local TOK=(); [ -n "$T" ] && TOK=(--tokens "$T")
  local BR=(); [ -f "docs/society_phase/g15_branches/$Y.txt" ] && BR=(--branches "docs/society_phase/g15_branches/$Y.txt")
  local R="sim/society/reports/year$Y.html" EX="sim/society/reports/explain/year$Y.json" SB="sim/society/video/storyboards/storyboard_yearly_$Y.json"
  echo "== ${Y}年の年報"
  "$PY" sim/society/tools/year_report.py --data sim/society/data --year "$Y" "${TOK[@]}" "${BR[@]}" --out "$R" | tail -1 || { echo "年報: 作れなかった"; return 1; }
  echo "== 解説の係 (約 10 分・係 6 人)"
  if "$PY" sim/society/tools/explain_data.py --year "$Y" >/dev/null \
     && node sim/society/tools/run_workflow.mjs sim/society/tools/explainer_workflow.js "{\"year\":$Y,\"data_ready\":true}" --log "/tmp/explain_wf_$Y.log" >/dev/null \
     && [ -f "$EX" ]; then
    "$PY" sim/society/tools/year_report.py --data sim/society/data --year "$Y" "${TOK[@]}" "${BR[@]}" --out "$R" | tail -1
  else
    echo "解説の係: 出せなかった (年報は解説なしのまま。ログ /tmp/explain_wf_$Y.log)"
  fi
  echo "== 統計のページ"
  "$PY" sim/society/tools/build_stats.py | tail -1 || echo "統計のページ: 作れなかった"
  echo "== 年報の動画の絵コンテ (約 1 分)"
  bash sim/society/video/yearly/make.sh "$Y" "/tmp/yv$Y" "${VV:-/tmp/vv}" 2>&1 | tail -1 || echo "絵コンテ: 作れなかった"
  local F=("$R" sim/society/app/stats.html)
  [ -f "$EX" ] && F+=("$EX")
  [ -f "$SB" ] && F+=("$SB")
  commit "社会シミュレーション: ${Y}年の年報 (トークン ${T:-?})" "${F[@]}"
}

day() { "$PY" -c "import json;print(json.load(open('sim/society/data/state.json', encoding='utf-8'))['day'])"; }

if [ "${1:-}" = --yearend ]; then yearend "${2:?年}" "${3:-}"; exit $?; fi

D0=$(day)
LOG=/tmp/run_year_$D0.log
echo "== 季節のワークフロー: ${D0} 日目から 1 年 (ログ $LOG)"
RUN_WF_TOKENS=/tmp/run_year_${D0}.tokens RUN_WF_CONC=${RUN_WF_CONC:-8} node sim/society/tools/run_workflow.mjs sim/society/tools/society2_seasons_workflow.js \
  "{\"mode\":\"year\",\"years\":1,\"py\":\"$PY\",\"session\":\"${CLAUDE_SESSION_URL:-}\",\"fable\":[\"$FABLE\"]}" --log "$LOG" > "/tmp/run_year_$D0.json"
WHY=$("$PY" -c "import json;r=json.load(open('/tmp/run_year_$D0.json'));print(r.get('why'), r.get('stopped'))" 2>/dev/null || echo "? ?")
D1=$(day); T=$(cat "/tmp/run_year_${D0}.tokens" 2>/dev/null || echo)
echo "ワークフローの終わり: $WHY / いま ${D1} 日目 / トークン ${T:-?}"
if [ $(( (D1 + 1) % 120 )) = 0 ] && [ "$D1" != "$D0" ]; then
  yearend $(( (D1 + 1) / 120 - 1 )) "$T"
else
  echo "年の終わりではないので、年の終わりの手順はしない"
fi
echo "RUN_YEAR_DONE $WHY"
