#!/usr/bin/env bash
# WSL2 (Ubuntu) に JAX (GPU 版) と MuJoCo Playground を入れる。
#   bash tools/mjx/setup.sh [入れる場所 (既定: ~/mjx)]
# - GPU のドライバーは Windows 側のものを使う。WSL の中に NVIDIA のドライバーは入れないこと
# - uv (https://docs.astral.sh/uv/) で Python 3.12 の仮想環境を作る
set -euo pipefail
DIR="${1:-$HOME/mjx}"
mkdir -p "$DIR"
cd "$DIR"
command -v uv >/dev/null || { echo "uv が必要です: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
uv venv --python 3.12 venv
# shellcheck disable=SC1091
source venv/bin/activate
uv pip install "jax[cuda13]" mujoco mujoco-mjx brax playground mediapy
python - <<'EOF'
import jax, mujoco
print("jax", jax.__version__, "devices:", jax.devices())
print("mujoco", mujoco.__version__)
EOF
