#!/usr/bin/env bash
# VOICEVOX (ずんだもん) の音声合成をこの PC / 環境に用意する。
# VOICEVOX 本体・音声モデル・ONNX Runtime は再配布が制限されているため、リポジトリには含めず公式の配布元から取得する。
#   使い方: bash tools/voicevox/setup.sh [保存先 (既定: ~/.cache/robotsim-voicevox)]
# 利用規約: https://voicevox.hiroshiba.jp/term/ , https://zunko.jp/con_ongen_kiyaku.html
# 生成した音声には「VOICEVOX:ずんだもん」のクレジット表記が必要。
set -euo pipefail
DIR="${1:-$HOME/.cache/robotsim-voicevox}"
CORE=0.17.0
ORT=1.23.2
mkdir -p "$DIR" && cd "$DIR"
[ -f "voicevox_core-$CORE.whl" ] || curl -fsSL -o "voicevox_core-$CORE.whl" \
  "https://github.com/VOICEVOX/voicevox_core/releases/download/$CORE/voicevox_core-$CORE-cp310-abi3-manylinux_2_34_x86_64.whl"
[ -d "voicevox_onnxruntime-linux-x64-$ORT" ] || curl -fsSL \
  "https://github.com/VOICEVOX/onnxruntime-builder/releases/download/voicevox_onnxruntime-$ORT/voicevox_onnxruntime-linux-x64-$ORT.tgz" | tar xz
[ -d open_jtalk_dic_utf_8-1.11 ] || curl -fsSL \
  "https://github.com/r9y9/open_jtalk/releases/download/v1.11.1/open_jtalk_dic_utf_8-1.11.tar.gz" | tar xz
if [ ! -f vvms/0.vvm ]; then  # 0.vvm = ずんだもん など
  git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/VOICEVOX/voicevox_vvm vvm-repo
  (cd vvm-repo && git checkout -q HEAD -- vvms/0.vvm TERMS.txt README.md)
  mkdir -p vvms && mv vvm-repo/vvms/0.vvm vvms/ && mv vvm-repo/TERMS.txt ./VVM_TERMS.txt && rm -rf vvm-repo
fi
[ -d venv ] || python3 -m venv venv
cp "voicevox_core-$CORE.whl" "voicevox_core-$CORE-cp310-abi3-manylinux_2_34_x86_64.whl" 2>/dev/null || true
./venv/bin/pip install -q "./voicevox_core-$CORE-cp310-abi3-manylinux_2_34_x86_64.whl"
echo "準備完了: $DIR"
