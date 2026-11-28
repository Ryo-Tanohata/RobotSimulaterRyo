#!/bin/bash
# 素材を取りに行く (2026-11-28)。札 sim/society/assets.json に書いた組の、その版 (コミット番号) の、その組のファイルだけを取ってくる。
#   bash sim/society/tools/fetch_assets.sh g4        → 取ってきた場所 (フォルダ) を 1 行だけ出す
# 置き場: KAWABE_ASSETS (なければ リポジトリの .kawabe_work/assets)。<置き場>/<組>-<版>/ に入れる。一度取ったら取り直さない。
# クラウドでも本人の PC (Git Bash) でも同じ。素材のリポジトリは非公開なので、読む許可が要る (クラウドはセッションにつなぐ・PC は本人の GitHub のログイン)。
set -euo pipefail
SET=${1:?組の名前 (例 g4)}
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../../.." && pwd)"
PY=${PY:-python3}; command -v "$PY" >/dev/null 2>&1 || PY=py
# tr -d '\r': Windows の Python は行の終わりに \r をつけるので、最後の値 (SUB) に \r が残らないように落とす (2026-11-28、本人の PC)
read -r REPO VER COMMIT SUB < <("$PY" -c "import json,sys;a=json.load(open(sys.argv[1],encoding='utf-8'));s=a['sets'][sys.argv[2]];print(a['repo'],s['version'],s['commit'],s['path'])" "$ROOT/sim/society/assets.json" "$SET" | tr -d '\r')
CACHE=${KAWABE_ASSETS:-$ROOT/.kawabe_work/assets}
DEST="$CACHE/$SET-$VER"
if [ -f "$DEST/.done" ]; then echo "$DEST"; exit 0; fi
TMP="$CACHE/.git-$SET-$VER"; rm -rf "$TMP" "$DEST"; mkdir -p "$TMP"
(
  cd "$TMP"
  git init -q
  git remote add origin "https://github.com/$REPO"
  git config core.sparseCheckout true
  echo "$SUB/" > .git/info/sparse-checkout
  git fetch -q --depth 1 --filter=blob:none origin "$COMMIT" 2>/dev/null || git fetch -q --depth 1 origin "$COMMIT"
  git checkout -q FETCH_HEAD
) >&2
mkdir -p "$DEST" && cp -r "$TMP/$SUB/." "$DEST/" && rm -rf "$TMP"
n=$(ls "$DEST" | wc -l); [ "$n" -gt 0 ] || { echo "取ってこられなかった: $REPO $COMMIT $SUB" >&2; exit 1; }
touch "$DEST/.done"
echo "取ってきた: $SET $VER ($n ファイル) → $DEST" >&2
echo "$DEST"
