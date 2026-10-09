#!/bin/bash
# Society 2.0: 1 季節を進めて (step.py season)、データをコミットする。ワークフロー (society2_seasons_workflow.js) から呼ぶ
# 作者は Ryo-Tanohata、Claude は共同作者 (本人の決まり)
cd "$(dirname "$0")/../../.."
# PY: 使う Python (クラウドは python3。本人の PC は PY="py -3" = Python 3.13。2026-10-09: 3.11 で進めると食べ物の数の最後の桁がずれる (3.12 から sum() の足し方が変わった))
PY=${PY:-python3}
export PYTHONIOENCODING=utf-8
D=$($PY -c "import json;print(json.load(open('sim/society/data/state.json'))['day'])")
$PY sim/society/step.py season; rc=$?; echo "season exit=$rc"
git add sim/society/data && git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -q -m "社会シミュレーション: ${D} 日目から (季節)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>${CLAUDE_SESSION_URL:+
Claude-Session: $CLAUDE_SESSION_URL}" && echo committed
