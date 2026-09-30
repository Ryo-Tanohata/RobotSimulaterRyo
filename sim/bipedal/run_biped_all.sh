#!/usr/bin/env bash
# 2 足のお手本で、体の形 s を変えて順に学習する。
#   bash sim/bipedal/run_biped_all.sh 0.5 0
cd "$(dirname "$0")"
for s in "$@"; do
  ~/mjx/venv/bin/python train.py "s${s}_biped" --s "$s" --imitate --speed 0.8 --alive 0.5 --fall-penalty 5 \
    --steps 120000000 --evals 24 > "runs/s${s}_biped.train.log" 2>&1
  echo "s=$s done"
  tail -1 "runs/s${s}_biped/log.csv"
done
