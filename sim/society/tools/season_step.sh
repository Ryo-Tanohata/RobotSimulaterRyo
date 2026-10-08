#!/bin/bash
# Society 2.0: 1 季節を進めて (step.py season)、データをコミットする。ワークフロー (society2_seasons_workflow.js) から呼ぶ
# 作者は Ryo-Tanohata、Claude は共同作者 (本人の決まり)
cd "$(dirname "$0")/../../.."
D=$(python3 -c "import json;print(json.load(open('sim/society/data/state.json'))['day'])")
python3 sim/society/step.py season; rc=$?; echo "season exit=$rc"
git add sim/society/data && git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -q -m "社会シミュレーション: ${D} 日目から (季節)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>${CLAUDE_SESSION_URL:+
Claude-Session: $CLAUDE_SESSION_URL}" && echo committed
