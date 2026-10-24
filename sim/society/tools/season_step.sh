#!/bin/bash
# Society 2.0: 1 季節を進めて (step.py season)、データをコミットする。ワークフロー (society2_seasons_workflow.js) から呼ぶ
# 作者は Ryo-Tanohata、Claude は共同作者 (本人の決まり)
cd "$(dirname "$0")/../../.."
# PY: 使う Python (クラウドは PY=python3.13 を渡す (python3 は 3.11)。本人の PC は PY="py -3" = Python 3.13。2026-10-09: 3.11 で進めると食べ物の数の最後の桁がずれる (3.12 から sum() の足し方が変わった))
PY=${PY:-python3}
# データの置き場所 (2026-10-24): SOC_DATA_REL (リポジトリからの道) を渡すと、そこを進める (実験 C の試しの村 sim/society/data_C)。渡さなければ本物の村
DATA=${SOC_DATA_REL:-sim/society/data}
export SOC_DATA="$PWD/$DATA"
TAG=""; [ "$DATA" != "sim/society/data" ] && TAG="試しの村 ${DATA##*/}: "
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1  # Windows でも記録を UTF-8 で読む
D=$($PY -c "import json;print(json.load(open('$DATA/state.json', encoding='utf-8'))['day'])")
# G7 から: コミットの文に、この歩が年の集まり・寄る季節・集まり直し・秋の集まりかをそえる (集まりのない季節と G6 までは「季節」のまま)
K=$($PY -c "import json;g=(json.load(open('$DATA/state.json', encoding='utf-8')).get('era2') or {}).get('g7');print({'年': '年の集まり', '寄る': '寄る季節', '集まり直し': '集まり直し', '秋': '秋の集まり'}.get((g or {}).get('ask'), '季節'))")
$PY sim/society/step.py season; rc=$?; echo "season exit=$rc"
git add "$DATA" && git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -q -m "社会シミュレーション: ${TAG}${D} 日目から (${K:-季節})" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>${CLAUDE_SESSION_URL:+
Claude-Session: $CLAUDE_SESSION_URL}" && echo committed
