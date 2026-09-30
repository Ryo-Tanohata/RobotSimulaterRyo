#!/usr/bin/env bash
# 実験 2: 体に合わせたお手本 + 足首のばね + 脚の長さに合わせた速さ (フルード数 0.1)。
# 3 つの体 × 4 足・2 足 × 乱数の種 3 = 18 回の学習 → 評価 → 表・グラフ・動画。シャットダウンはしない。
#   bash sim/bipedal/run_exp2.sh
cd "$(dirname "$0")"
PREFIX=e2_ TAG=2 EXTRA="--exp2 --froude 0.1" CONDS="s0:quad s0.5:quad s1:quad s0:biped s0.5:biped s1:biped" \
  bash run_study.sh 60000000 3 > runs/study2.log 2>&1
