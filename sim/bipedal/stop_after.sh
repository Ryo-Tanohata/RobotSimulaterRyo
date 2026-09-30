#!/usr/bin/env bash
# 学習 (名前) の保存が指定ステップ数に届いたら、学習を止める (それまでの保存は残る)。
#   bash sim/bipedal/stop_after.sh 名前 40000000
cd "$(dirname "$0")/runs"
name=$1 limit=$2
until ls "$name/checkpoints" | awk -v l="$limit" '$1 + 0 >= l { found = 1 } END { exit !found }'; do sleep 20; done
sleep 30
pkill -INT -f "train.py $name "
sleep 15
tail -n 2 "$name/log.csv"
