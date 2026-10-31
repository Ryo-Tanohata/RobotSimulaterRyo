#!/bin/bash
# 論文 2・実験 4: 写しの村を 1 つ作る (トークン 0。docs/research/humanity/paper2_exp4_prereg.md の 9.)。本物の村 (sim/society/data) にはさわらない
#
#   bash sim/society/tools/exp4_setup.sh B0 1            → sim/society/data_E4_B0_1 (組 B0・写しの 1 つ目)
#   bash sim/society/tools/exp4_setup.sh B1 1 726c5340   (はじめのコミット。書かなければ 726c5340 = 本物の村を G9 に入れた 12599 日目。実験 3 と同じ)
#
# - はじめのコミットの sim/society/data の state.json・archive/・records/・app_data.json を写す (お題と答えは写さない。実験 3 の exp3_setup.sh と同じ)。
# - SOC_DATA で写しを指して step.py exp4 <組> を動かす: 組を state の g7.exp4 に残し、12599 日目のお題 (季節・気持ち・まわりの集落) を書く。
# - 書いたお題から、足した節と欄 (exp4.strip) を除くと、本物のコミットのお題と 1 バイトも同じかをくらべる (この台本の終わり)。
# - コミットはしない (終わりに、コミットの仕方を出す)。
set -euo pipefail
ARM=${1:?組 (B0 / B1) を書く}
REP=${2:?写しの番号 (1, 2, …) を書く}
START=${3:-726c5340}
PY=${PY:-python3.13}
cd "$(dirname "$0")/../../.."
DST="sim/society/data_E4_${ARM}_${REP}"
case "$ARM" in B0|B1) ;; *) echo "組は B0 / B1"; exit 2;; esac
if [ -e "$DST" ]; then echo "$DST はもうある (消してから作り直すか、ほかの番号にする)"; exit 2; fi
TMP=$(mktemp -d)
git archive --format=tar "$START" sim/society/data/state.json sim/society/data/archive sim/society/data/records sim/society/data/app_data.json | tar -x -C "$TMP"
mv "$TMP/sim/society/data" "$DST"
rm -rf "$TMP"
DAY=$($PY -c "import json;print(json.load(open('$DST/state.json', encoding='utf-8'))['day'])")
export SOC_DATA="$PWD/$DST" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
$PY sim/society/step.py exp4 "$ARM" --note "論文 2・実験 4 の写しの村 (組 $ARM・写し $REP・はじめ $START の $DAY 日目)"
$PY sim/society/step.py status | tail -5
# お題は、足した節と欄を除けば、本物のコミットのお題と同じか
$PY - "$START" "$DST" "$DAY" <<'PYEOF'
import subprocess, sys, io, tarfile
sys.path.insert(0, "sim/society")
import exp4
start, dst, day = sys.argv[1], sys.argv[2], int(sys.argv[3])
p = f"sim/society/data/prompts/day{day:03d}"
r = subprocess.run(["git", "archive", "--format=tar", start, p], capture_output=True)
if r.returncode:
    print("はじめのコミットにお題がない (くらべない)"); sys.exit(0)
bad = n = added = 0
with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
    for m in t.getmembers():
        if not m.isfile():
            continue
        rel = m.name[len(p) + 1:]
        ref = t.extractfile(m).read().decode("utf-8")
        mine = open(f"{dst}/prompts/day{day:03d}/{rel}", encoding="utf-8").read()
        added += mine != ref
        n += 1
        bad += exp4.strip(mine) != ref
print(f"お題 {n} 通 (節を足した {added} 通): " + ("足した節と欄を除いて、本物のコミットと同じ" if not bad else f"{bad} 通ちがう (まちがい)"))
sys.exit(1 if bad else 0)
PYEOF
echo "できた: $DST ($DAY 日目・組 $ARM)"
echo "コミット: git add $DST && git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -m \"社会シミュレーション: 実験 4 の写しの村 ${DST##*/} を作った (組 $ARM。$DAY 日目)\""
echo "回し方 (ワークフロー): tools/society2_seasons_workflow.js に {\"mode\": \"year\", \"years\": 1, \"py\": \"$PY\", \"data\": \"$DST\", \"session\": \"<セッションの URL>\"}"
