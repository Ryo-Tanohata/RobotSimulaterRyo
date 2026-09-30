#!/usr/bin/env bash
# 学習結果をまとめて動画にし、移動のコストなどを表示する。
#   bash sim/bipedal/render_all.sh s0_quad s0.5_biped ...
cd "$(dirname "$0")"
for n in "$@"; do
  echo "== $n"
  MUJOCO_GL=egl ~/mjx/venv/bin/python render.py "$n" "../../docs/media/bipedal_$n.mp4" --seconds 15 2>&1 \
    | grep -E "脳|秒|仕事率|Error" | grep -v NoneType
done
