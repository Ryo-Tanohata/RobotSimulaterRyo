#!/usr/bin/env bash
# Cloudflare Pages のビルド: リポジトリの追跡ファイルを _site/ にコピーする。
# Cloudflare Pages は 1 ファイル 25 MiB までなので、それを超えるファイル (docs/media の大きい動画) は入れない。
# アプリが再生する動画は sim/society/app/ の小さい版 (各 12 MB) なので、ページの表示には影響しない。
#   Cloudflare の設定: ビルドコマンド `bash tools/cloudflare/build.sh`、出力ディレクトリ `_site`
set -euo pipefail
cd "$(dirname "$0")/../.."
out=_site
limit=$((25 * 1024 * 1024))
rm -rf "$out"
mkdir -p "$out"
n=0
while IFS= read -r -d '' f; do
  [ -f "$f" ] || continue
  if [ "$(stat -c %s "$f")" -gt "$limit" ]; then
    echo "入れない (25 MiB 超): $f"
    continue
  fi
  mkdir -p "$out/$(dirname "$f")"
  cp "$f" "$out/$f"
  n=$((n + 1))
done < <(git ls-files -z)
echo "コピーしたファイル: $n 個 → $out/"
