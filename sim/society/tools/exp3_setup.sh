#!/bin/bash
# 論文 2・実験 3: 写しの村を 1 つ作る (トークン 0。docs/research/humanity/paper2_exp3_prereg.md の 9.)。本物の村 (sim/society/data) にはさわらない
#
#   bash sim/society/tools/exp3_setup.sh A2 1            → sim/society/data_E3_A2_1 (組 A2・写しの 1 つ目)
#   bash sim/society/tools/exp3_setup.sh A0 1 726c5340   (はじめのコミット。書かなければ 726c5340 = 本物の村を G9 に入れた 12599 日目)
#
# - はじめのコミットの sim/society/data の state.json・archive/・records/・app_data.json を写す (お題と答えは写さない)。
# - SOC_DATA で写しを指して step.py exp3 <組> を動かす: 組を state の g7.exp3 に残し、12599 日目のお題 (季節・気持ち・まわりの集落) を書く。
#   A0 のお題は、本物のコミットのお題と 1 バイトも同じ (この台本の終わりでくらべる)。
# - コミットはしない (終わりに、コミットの仕方を出す)。
set -euo pipefail
ARM=${1:?組 (A0 / A1 / A2) を書く}
REP=${2:?写しの番号 (1, 2, …) を書く}
START=${3:-726c5340}
PY=${PY:-python3.13}
cd "$(dirname "$0")/../../.."
DST="sim/society/data_E3_${ARM}_${REP}"
case "$ARM" in A0|A1|A2|A3) ;; *) echo "組は A0 / A1 / A2 (/ A3)"; exit 2;; esac
if [ -e "$DST" ]; then echo "$DST はもうある (消してから作り直すか、ほかの番号にする)"; exit 2; fi
TMP=$(mktemp -d)
git archive --format=tar "$START" sim/society/data/state.json sim/society/data/archive sim/society/data/records sim/society/data/app_data.json | tar -x -C "$TMP"
mv "$TMP/sim/society/data" "$DST"
rm -rf "$TMP"
DAY=$($PY -c "import json;print(json.load(open('$DST/state.json', encoding='utf-8'))['day'])")
export SOC_DATA="$PWD/$DST" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
$PY sim/society/step.py exp3 "$ARM" --note "論文 2・実験 3 の写しの村 (組 $ARM・写し $REP・はじめ $START の $DAY 日目)"
$PY sim/society/step.py status | tail -4
# A0 のお題は本物のコミットのお題と同じか (A1・A2 は、足した節を除いて同じか)
$PY - "$START" "$DST" "$DAY" "$ARM" <<'EOF'
import subprocess, sys, io, tarfile
sys.path.insert(0, "sim/society")
import exp3
start, dst, day, arm = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
p = f"sim/society/data/prompts/day{day:03d}"
r = subprocess.run(["git", "archive", "--format=tar", start, p], capture_output=True)
if r.returncode:
    print("はじめのコミットにお題がない (くらべない)"); sys.exit(0)
bad = n = 0
with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
    for m in t.getmembers():
        if not m.isfile():
            continue
        rel = m.name[len(p) + 1:]
        ref = t.extractfile(m).read().decode("utf-8")
        mine = open(f"{dst}/prompts/day{day:03d}/{rel}", encoding="utf-8").read()
        if rel.startswith("season/") and arm != "A0":
            mine = exp3.strip(mine)
        n += 1
        bad += mine != ref
print(f"お題 {n} 通: " + ("本物のコミットと同じ" + (" (足した節を除いて)" if arm != "A0" else "") if not bad else f"{bad} 通ちがう (まちがい)"))
sys.exit(1 if bad else 0)
EOF
echo "できた: $DST ($DAY 日目・組 $ARM)"
echo "コミット: git add $DST && git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -m \"社会シミュレーション: 実験 3 の写しの村 ${DST##*/} を作った (組 $ARM。$DAY 日目)\""
echo "回し方 (ワークフロー): tools/society2_seasons_workflow.js に {\"mode\": \"year\", \"years\": 3, \"py\": \"$PY\", \"data\": \"$DST\", \"session\": \"<セッションの URL>\"}"
