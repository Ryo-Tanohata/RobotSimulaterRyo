#!/usr/bin/env bash
# 2 足・4 足の比較をまとめて行う: 条件 × 乱数の種 の学習 → 評価 → 表とグラフ → 種 1 の動画。
#   bash sim/bipedal/run_study.sh [ステップ数 (既定 60000000)] [種の数 (既定 3)]
# 学習は 1 つずつ順に行う。途中で止まっても、終わった学習は runs/ に残る (同じ名前はやり直さない)。
cd "$(dirname "$0")"
STEPS=${1:-60000000}
SEEDS=${2:-3}
PY=~/mjx/venv/bin/python
CONDS=${CONDS:-"s0:quad s0:biped s0.5:biped s1:biped"}  # 体の形:歩き方
PREFIX=${PREFIX:-}  # 学習の名前の先頭 (実験 2 は e2_)
EXTRA=${EXTRA:-}    # train.py に足す設定 (実験 2 は "--exp2 --froude 0.1")
TAG=${TAG:-}        # 表・グラフ・動画のファイル名に付ける (実験 2 は 2)
names=()
for c in $CONDS; do
  s=${c%%:*} gait=${c##*:}
  for seed in $(seq 1 "$SEEDS"); do
    n="${PREFIX}${s}_${gait}_seed${seed}"
    names+=("$n")
    if [ -f "runs/$n/done" ]; then echo "skip $n"; continue; fi
    echo "$(date +%H:%M) train $n"
    $PY train.py "$n" --s "${s#s}" --gait "$gait" --imitate --speed 0.8 --alive 0.5 --fall-penalty 5 \
      --torque-weight 0.00001 --seed "$seed" --steps "$STEPS" $EXTRA --evals 12 > "runs/$n.train.log" 2>&1 && touch "runs/$n/done"
    tail -n 1 "runs/$n/log.csv"
  done
done
echo "$(date +%H:%M) evaluate"
$PY eval.py "${names[@]}" 2>&1 | grep '^{'
$PY eval.py --summary --tag "$TAG" "${names[@]}" 2>&1 | grep -v -E 'Warning|warn'
echo "$(date +%H:%M) videos"
for c in $CONDS; do
  s=${c%%:*} gait=${c##*:}
  MUJOCO_GL=egl $PY render.py "${PREFIX}${s}_${gait}_seed1" "../../docs/media/bipedal_study${TAG}_${s}_${gait}.mp4" --seconds 15 2>&1 | grep -E '秒|仕事率'
done
echo "$(date +%H:%M) study done"
