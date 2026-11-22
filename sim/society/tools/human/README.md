# 川辺の五人を 3D の人にする (クラウドでの作り方)

本人のパソコンの VRoid Studio を使わずに、クラウドの CPU だけで 1 人 (セナ) を作るための
スクリプトです。画像と模型 (.glb) は公開リポジトリに入れません。

| ファイル | 役目 |
|---|---|
| `build_sena.py` | 人を組み立てて、描画し、.glb に書き出す本体 |
| `people.py` | 人ごとの設定 (`PEOPLE`) と、作風ごとの設定 (`STYLES`) |
| `run.py` | bpy を動かす小さな入口 (終わったら確実に止める) |

## 準備 (一度だけ。すべてメモリ上の /dev/shm に置く)

ディスクの空きが少ないため、Blender も素材も `/dev/shm` (メモリ) に置きます。
`/dev/shm` は機械を立ち上げなおすと消えるので、そのときはもう一度準備します。

```bash
# 1) Blender の Python 版 (bpy 4.5 LTS、python3.11 用) 約 0.9 GB
TMPDIR=/dev/shm/tmp python3.11 -m pip install --no-cache-dir --target /dev/shm/bpy "bpy==4.5.*"

# 2) MPFB2 (MakeHuman の Blender 用部品)。基本メッシュと形の素材 (targets) が入っている
mkdir -p /dev/shm/sena/assets /dev/shm/sena/assets/ext
git clone --depth 1 https://github.com/makehumancommunity/mpfb2.git /dev/shm/sena/assets/mpfb2
ln -sfn /dev/shm/sena/assets/mpfb2/src/mpfb /dev/shm/sena/assets/ext/mpfb

# 3) MakeHuman の目の素材 (high-poly eyes と茶色の瞳)
git clone --depth 1 --filter=blob:none --sparse https://github.com/makehumancommunity/makehuman.git /dev/shm/dl/mh
git -C /dev/shm/dl/mh sparse-checkout set makehuman/data/eyes
cp -r /dev/shm/dl/mh/makehuman/data/eyes /dev/shm/sena/assets/mh_eyes
```

MPFB は Blender の「拡張機能」として読みこみます (`build_sena.py` の `setup_mpfb()`)。
設定ファイルなどは `BLENDER_USER_RESOURCES=/dev/shm/sena/userres` に書かれます。

## 動かしかた

```bash
cd /tmp   # どこでもよい
BLENDER_USER_RESOURCES=/dev/shm/sena/userres PYTHONPATH=/dev/shm/bpy \
  python3.11 -u <repo>/sim/society/tools/human/run.py <repo>/sim/society/tools/human/build_sena.py \
  --style mid --only face,sheet > /dev/shm/sena/log.txt 2>&1
```

- `--style mid` / `--style real` : 作風 (下の節)
- `--only face,sheet,poses` : 描く画像を選ぶ。`--only none` なら組み立てと .glb だけ
- `--quick` : 試し描き (24 サンプル)
- ログは必ずファイルへ。パイプ (`| grep`) につなぐと終了時に止まることがある
- 出力: `sim/society/out/human/<name>_<style>_3view.png`, `..._face.png` (git には入らない)、
  `/dev/shm/sena/<name>_<style>.glb` (骨組みつき。公開しない)

## 共通の流れ (どの作風も同じ順番)

| 順 | 工程 | 関数 | 中身 |
|---|---|---|---|
| 1 | 基本メッシュ | `setup_mpfb()`, `make_body()` | MakeHuman の基本メッシュ hm08 (CC0) を MPFB2 の `HumanService.create_human()` で読む |
| 2 | 体の数値 | `make_body()` | `people.py` の `macro` (性・年齢・体重・筋肉・背) と `targets` (肩幅・腰など) を形として足す。`bake_shape()` で焼きこむ |
| 3 | 骨組み | `HS.add_builtin_rig(body, "default")` | MakeHuman の default リグ (重みつき)。しゃがむ姿勢などはこの骨を回す (`set_pose()`) |
| 4 | 顔 | `make_body()` の顔 targets、`HS.add_mhclo_asset()` (目)、`build_brows()`、まつ毛 (基本メッシュの補助形状) | 丸い顔・上がった口角・大きめの目 |
| 5 | 髪 | `build_hair()` | 頭の表面に光線を当てて形を拾い、(a) 頭をおおう帽子状のメッシュ、(b) 前髪・横の髪・後ろの髪の束 (曲線)、(c) うなじで低く結んだ束と結び紐、を作る |
| 6 | 服 | `build_tunic()`+`build_belt()` または `build_underwear()` | 貫頭衣と紐の帯 (real)、または無地の胸の帯と短パン (mid) |
| 7 | 材質 | `mat_basic()`, `mat_hair()`, `mat_leather()`, `mat_eye()` | 肌・唇 (頂点グループ `lips` を色の混ぜ具合に使う)・傷・髪・目 |
| 8 | 光 | `setup_render()` | 3 点照明: 主光 (右前上)・補助光 (左前)・縁取り光 (後ろ上)。背景は VRoid の画面に近い灰色 |
| 9 | 描画 | `render()`, `compose()` | Cycles の CPU。正面・横・後ろ (正射影) をつないで 3 面図、顔の寄り |
| 10 | 書き出し | `bpy.ops.export_scene.gltf` | .glb (骨組みと重みつき、形は焼きこみ済み) |

傷は `build_scar()` で左の前腕の外側に細い盛り上がりとして置き、前腕の骨につないでいる。

## 作風 1: 中間 (様式化した写実) `--style mid`

実在の人の体の比率と、物理に沿った材質 (PBR) はそのまま。顔だけを少し整えた作風。
特定のゲームなどのキャラクターをまねたものではなく、一般的な作り方。

1. **基本メッシュ**: MakeHuman hm08 (CC0)。
2. **体の数値** (`people.py` → `PEOPLE["sena"]["macro"]`):
   gender 0.0 (女)、age `mh_age(29)` = 0.531、muscle 0.62、weight 0.60 (がっしり、54.5 kg に合わせ少し重め)、
   height 0.42 (約 1.50 m)、race asian 0.6 / african 0.25 / caucasian 0.15。
   体の targets: `measure-shoulder-dist-incr` 0.45、`hip-scale-horiz-incr` 0.3、`measure-hips-circ-incr` 0.2、
   `torso-scale-horiz-incr` 0.2、上腕の筋肉 0.3。
3. **顔** (人の targets に `STYLES["mid"]["targets"]` を上書き):
   `head-round` 0.7 (丸い顔)、`mouth-angles-up` 0.9 (口角を上げた笑顔)、ほお 0.35、
   目 `eye-scale-incr` 0.45 (約 1 割大きく)、鼻を小さく (`nose-scale-horiz-decr` 0.35、`nose-scale-vert-decr` 0.2、
   `nose-volume-decr` 0.3 ほか)、あごをすっきり (`chin-jaw-drop-decr` 0.3、`chin-width-decr` 0.15)、唇を少し薄く。
   目は MakeHuman の high-poly eyes と茶色の瞳の画像。上まつ毛だけを使う。
4. **髪** (`build_hair()`、値は `people.py` の `hair` と `STYLES["mid"]["hair"]`):
   色 #0e0b0a。細い束 (太さ 6.8 mm) を多く: 前髪 4.5° おき、横の髪 6 本ずつ、後ろ 5.5° おき、結んだ束 5 本 (幅 4 cm、長さ 36 cm)。
   結ぶ位置はうなじ (頭の中心から下 52°)。
   材質 `mat_hair()`: 縦にのばしたノイズで毛すじの色むら・凹凸・つやのむら、異方性 0.75 (毛の向きにのびるつや)。
5. **服**: `build_underwear()`。胴と脚の表面を輪切りに拾った筒 (`loft_rings()`) で、ふちがまっすぐな
   胸の帯 (胸の高さ −10.5〜−0.5 cm) と短パン、股の当て布。色 #141414。骨の重みは近い肌の頂点から写す (`copy_weights()`)。
6. **材質**: 肌 #8a5636 (濃い日焼け)、表面下散乱 (SSS) 0.22、粗さ 0.48。唇 #7a4232 を 55% だけ混ぜる。傷 #b98c78。
7. **光**: 主光 420 W / 補助光 160 W / 縁取り光 260 W (エリアライト)、背景 #aeb3bb 強さ 0.55、露出 −0.9。
8. **描画**: Cycles CPU、128 サンプル + ノイズ除去 (OpenImageDenoise)、色変換 Standard、輪郭線なし。
   3 面図は 560×1100 を 3 枚、顔は 900×900。
   かかった時間 (この機械、CPU 4 コア): 試し描き (24 サンプル) で 1 枚 9〜13 秒・顔 23 秒、
   本番 (128 サンプル): 3 面図の 1 枚が 29〜46 秒、顔 90 秒、組み立て 5 秒、全部で約 3.5 分。
   Blender のメモリは約 0.7 GB。
9. **書き出し**: `/dev/shm/sena/sena_mid.glb`。

## 作風 2: 写実寄り (最初の版) `--style real`

MakeHuman の顔をほぼそのまま使い、貫頭衣を着せた版。輪郭線 (Freestyle) つき。

- 顔: 中間と同じ人の targets (目 0.9 と大きめ、鼻は少し広め)。顔の整えはなし。
- 髪: 太い束 (10.5 mm)、毛すじの模様なし、粗さ 0.42。
- 服: `build_tunic()` — 基本メッシュの補助形状 `helper-tights` (胴) と `helper-skirt` (腰から下) を切りだし、
  1.2 cm 外へ押しだして、ひざ上までの革の貫頭衣にする (色 #5c3f2a、ノイズで色むら・凹凸・つやのむら)。
  `build_belt()` で腰に紐の帯と左前の結び目。素足。
- 描画: Cycles CPU、96 サンプル、Freestyle の線 (太さ 1.2)、露出 −0.5。

## 作風 3: アニメ調 (トゥーン) — まだ作っていない

本人の指示 (「まずは中間だけで」) で後回し。準備だけ済み:
EEVEE はクラウドに GPU がないため、そのままでは動かない (libEGL がない)。
Ubuntu の mesa (llvmpipe、ソフトウェアの OpenGL) を `apt-get download` して `/dev/shm/mesa` に展開し、
`LD_LIBRARY_PATH` などを設定すると EEVEE も動くことを確かめた (256×256 の試験で 39 秒)。
作るときは Shader to RGB + 色の段 (Color Ramp) と、裏返しの外殻による輪郭線を `mat_*` に足す。

## ほかの四人を同じように作るには

1. `people.py` の `PEOPLE` にセナと同じ形で 1 人を足す
   (例: ルオ = gender 1.0, age `mh_age(39)`, muscle 0.75, weight 0.4、髪は短く刈る → `hair` の
   `bang_end` を高く・`tail_clumps` 0・`line_nape` を上げる、肌はいちばん濃く)。
2. `python3.11 run.py build_sena.py --person ruo --style mid` で描く。
3. 髪型が大きくちがう人 (ウィロの編み髪など) は `build_hair()` に「編む」部品を足す。

## 時間の記録

`build_sena.py` は描いた 1 枚ごとに `render <file>: <秒>` を、最後に `TIMES {...}` を出す。

## 素材のライセンスと出典

| 素材 | ライセンス | 出典 |
|---|---|---|
| MakeHuman 基本メッシュ hm08 (`data/3dobjs/base.obj`)、形の素材 (`data/targets/`)、リグと重み (`data/rigs/`) | CC0 1.0 | https://github.com/makehumancommunity/mpfb2 (commit 650c5c53bd6989a8ac264f31fa1d11d4a0c7bd8a) |
| MPFB2 のプログラム (読みこみに使うだけ。リポジトリには入れない) | GPL-3.0-or-later | https://github.com/makehumancommunity/mpfb2 |
| MakeHuman の目 (high-poly eyes、brown 瞳) | CC0 1.0 | https://github.com/makehumancommunity/makehuman (commit a8bc2d54ff0ac92e78ff71431b1023eda42bf482、`makehuman/data/eyes`) |
| Blender (bpy 4.5.16、Python モジュール版) | GPL-2.0-or-later | https://pypi.org/project/bpy/ |
| mesa (llvmpipe、EEVEE の試験だけ) | MIT ほか | Ubuntu 24.04 の `libegl-mesa0`, `mesa-libgallium` ほか |

髪・服・眉・傷・帯は、このスクリプトが手続き的に作るもので、外の素材は使っていない。
MakeHuman の CC0 素材は、出典を書く義務はないが、感謝をこめて記す (MakeHuman Community, Data Collection AB)。
