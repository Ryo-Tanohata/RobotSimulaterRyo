# 川辺の五人を 3D の人にする (クラウドでの作り方)

本人のパソコンの VRoid Studio を使わずに、クラウドの CPU だけで川辺の五人を作るための
スクリプトです。画像と模型 (.glb) は公開リポジトリに入れません。

| ファイル | 役目 |
|---|---|
| `build_sena.py` | 人を組み立てて、描画し、.glb に書き出す本体 |
| `people.py` | 人ごとの設定 (`PEOPLE`) と、作風ごとの設定 (`STYLES`) |
| `run.py` | bpy を動かす小さな入口 (終わったら確実に止める) |
| `build_person_vroid.py` | VRoid の CC0 サンプルから五人のだれでも作る道 (作風 4)。`--person <名前>` |
| `make_lineup.py` | 五人を横に並べた絵 (`kawabe_five_vroid.png`) を作る (PIL だけ) |

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
- `--head-asset <file>` : 頭と顔を外の素材に差しかえる (下の「頭の差しかえ口」)
- `--keep-hair` : 差しかえても、作った髪を残す
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
   材質 `mat_hair()`: 縦にのばしたノイズで毛すじの色むら・凹凸・つやのむら、異方性 0.5 (毛の向きにのびるつや)、つやの強さ 0.2、粗さ 0.42〜0.6 (つやを強くしすぎると灰色に見えるため控えめ)。
5. **服**: `build_underwear()`。胴と脚の表面を輪切りに拾った筒 (`loft_rings()`) で、ふちがまっすぐな
   胸の帯 (胸の高さ −10.5〜−0.5 cm) と短パン、股の当て布。色 #141414。骨の重みは近い肌の頂点から写す (`copy_weights()`)。
6. **材質**: 肌 #8a5636 (濃い日焼け)、表面下散乱 (SSS) 0.22、粗さ 0.48。唇 #7a4232 を 55% だけ混ぜる。傷 #b98c78。
7. **光**: 主光 420 W / 補助光 160 W / 縁取り光 260 W (エリアライト)、背景 #aeb3bb 強さ 0.55、露出 −0.9。
8. **描画**: Cycles CPU、128 サンプル + ノイズ除去 (OpenImageDenoise)、色変換 Standard、輪郭線なし。
   3 面図は 560×1100 を 3 枚、顔は 900×900。
   かかった時間 (この機械、CPU 4 コア): 試し描き (24 サンプル) で 1 枚 9〜13 秒・顔 23 秒、
   本番 (128 サンプル): 3 面図の 1 枚が 23〜36 秒、顔 80 秒、組み立て 5 秒、全部で約 3 分 (村の計算と同時に動かして 29〜46 秒・90 秒のこともあった)。
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

## 作風 4: VRoid の素体から作る道 `build_person_vroid.py` (五人)

MakeHuman の顔がこわく見える問題 (docs/society_phase/face_model_search.md) への答え。
VRoid の CC0 サンプルを土台にして、プロフィールに合わせて変える。人ごとの数値は `people.py` の `VROID[<名前>]`
(`sena` `ruo` `tahi` `wiro` `isa`)。最初はセナだけの `build_sena_vroid.py` だったものを、だれでも作れるように広げた。

```bash
BLENDER_USER_RESOURCES=/dev/shm/sena/userres PYTHONPATH=/dev/shm/bpy \
  python3.11 -u <repo>/sim/society/tools/human/run.py <repo>/sim/society/tools/human/build_person_vroid.py \
  -- --person ruo [--quick] [--samples 96] [--only sheet,face,expr,lineup] [--no-tie] > /dev/shm/sena/vroid/logs/ruo.txt 2>&1
# 五人ぶんの lineup を描いたあとで
python3 <repo>/sim/society/tools/human/make_lineup.py
```

- 準備: サンプルを `git clone --filter=blob:none https://github.com/madjin/vrm-samples` で取り、
  `git checkout HEAD -- vroid/beta/<名前>.vrm` で使うものだけを出す。置き場所は `/dev/shm/heads/src/vrmsamples/vroid/beta/`
  (環境変数 `VROID_DIR` で変えられる)。使うのは `Sendagaya_Shino.vrm` `HairSample_Female.vrm` `HairSample_Male.vrm`
  `Sakurada_Fumiriya.vrm` `Victoria_Rubin.vrm` の 5 つ (合わせて約 88 MB)。作業ファイルは `/dev/shm/sena/vroid/`。
- 出力: `sim/society/out/human/<名前>_vroid_3view.png` (正面・横・後ろ)、`<名前>_vroid_face.png` (顔)、
  `<名前>_vroid_expr.png` (ふつう / ふだんの顔)、`kawabe_five_vroid.png` (五人を並べた絵、本人の絵と同じ順:
  ルオ・セナ・タヒ・ウィロ・イサ)、`/dev/shm/sena/<名前>_vroid.glb` (骨組み・重み・表情キーつき)。
  並べる絵の部品は `/dev/shm/sena/vroid/lineup/` (同じ縮尺の正面、背景は透明)。画像と模型は git に入れない。

### 案内役 ソナ85 (`--person sona85`)

年報と統計のページを説明する村の人 (選んだわけは `docs/society_phase/guide_character.md`)。
体 HairSample_Female、顔 Victoria Rubin、髪 Victoria Rubin の髪を灰色にして結ぶ。設定は `people.py` の `VROID["sona85"]`。
五人のために足したものではなく、次の 3 つをこの人のために足した (五人の絵は変わらない):

- `outfit.dress`: ヤギのなめし革の長い貫頭衣 (技の木で「布を織る」は届かなかったので革)。胴とすそは体の輪切りの外側を
  なぞる筒 (`skirt_loft()`。胸から下はまっすぐ落ち、すそは少し広がる)、肩と短い袖は `make_band(..., xcut=0.26)`、腰に革紐の帯。
- `skin.face_lines`: 顔のしわ (頭の骨からの x・z の線を、前から光線を当てて顔のテクスチャに描く)。
- `--only guide`: 吹き出し用の胸から上の絵 `guide_<名前>_<表情>.png` (512×512、背景 #e6e1d8、腕を下ろす)。
  表情は `VROID[<名前>]["guide"]["expr"]`。128×128 に縮めたものを `sim/society/app/guide/` に置く (git に入れる)。

```bash
... build_person_vroid.py -- --person sona85 --only sheet,face,guide
```

### 五人の土台 (どのサンプルの、どの部分を使うか)

| 人 | 体・骨組み | 顔 | 髪 |
|---|---|---|---|
| セナ | HairSample_Female | 千駄ヶ谷 篠 | 篠の髪 (髪どめを消す) を黒に、うなじで低く結ぶ |
| ルオ | HairSample_Male | HairSample_Male (切れ長の目) | HairSample_Male の髪を頭へ寄せて短く刈る (`crop`) + 桜田 フミリヤの地肌に近い後ろ髪 (HairBack)。こげ茶 |
| タヒ | HairSample_Male | 桜田 フミリヤ (若い顔) | HairSample_Male の乱れた短い髪 (はねた毛つき) をそのまま。赤茶 |
| ウィロ | HairSample_Female | HairSample_Female (やわらかい目) | Victoria Rubin の長めの髪 (リボンと横の房を消す) を赤茶に、うなじで結んで三つ編み (`braid`) |
| イサ | HairSample_Male | 桜田 フミリヤ | フミリヤの短い髪 (後ろの刈り上げも) を、ひとつの栗色に |

男の体は、本物の男のサンプル (HairSample_Male、CC0) を使う。女の体から作りかえてはいない。
HairSample_Male の体は服の下まで肌があるが、肌のテクスチャに下着と靴下が描いてあるので、
肌の中央値より暗いところを肌の色でうめる (`skin.fill_dark`)。足は靴下の形のまま (指がない)。

### 工程 (どの人も同じ順番)

| 順 | 工程 | 関数 | 中身 |
|---|---|---|---|
| 1 | 組み合わせ | `assemble()` | 体と骨組み (`body_src`)、顔 (`face_src`)、髪の部品 (`hair.parts`) を、それぞれのサンプルから読む。骨の名前はどれも同じ (J_Bip_*)。頭の骨の差だけ顔と髪をずらし、骨組みにない髪の骨の重みは頭の骨にまとめる (髪はゆれない)。服・靴・髪どめは消す。いらない房は `drop_parts` (束の重心の位置) で消す |
| 2 | 目じるし | `Frame` | 腰・首・頭の骨の高さと肩の幅。`people.py` の高さ (結ぶ高さ・服の上下など) は女の素体の高さで書き、`Frame.z()` で男の体などへ写す (セナはそのまま) |
| 3 | 体つき | `sturdy()` | 肩幅 (m)・腰・胴まわり・胸板 (割合)、腕と脚を骨の軸から外へ (負なら細く)。骨もいっしょに動かす |
| 4 | 背・手足 | `proportions()` | 背の高さ `scale`、脚の長さ `legs`、腕の長さ `arms` を、すべてのメッシュ (表情キーも) と骨に同じ写像で |
| 5 | 顔 | `round_face()`, `thick_brows()` | ほおからあごを横に (負ならこけた頬)。眉を縦に太く |
| 6 | 髪 | `crop_hair()`, `tie_hair()`, `braid()` | 短く刈る: 頭の表面 (顔の肌 + 後頭部) からのはなれを縮め、たれる毛先を上げる。結ぶ: 後ろの髪をうなじに寄せ、結び紐の輪。三つ編み: 3 本の管を 8 の字にからめ、先を細く、毛先の房と結び紐 |
| 7 | 肌の色 | `skin_textures()` | 顔と体のテクスチャを、それぞれ肌の中央値が `skin.tan` になるよう掛け算。ほおの赤み、古い傷 (`scars`: 骨の上の線)、煤 (`patches`: 骨のまわりのしみ) を、3D の点から UV を求めて描く |
| 8 | 材質 | `materials()` | 肌・髪・白目・虹彩・口の中を Principled BSDF に (肌は SSS)。髪は明るさだけを使って `dark`〜`light` の 2 色の間に。虹彩は色をうすめて `tint` を掛ける (灰色の目など)。目の線・まつ毛・眉・ハイライトは光の影響なしのまま (線はアニメ、面は写実) |
| 9 | 服 | `outfit()` | 体の表面を高さで切りとった筒を少し外へ: 女は無地の胸の帯と短パン、男は短パンだけ (#161514) |
| 10 | 表情 | `set_expr()`, `set_gaze()` | ふだんの顔 (`expr`、VRM の表情キーを少しずつ)。伏し目は目の骨を下へ (描くときだけ) |
| 11 | 光と描画 | `setup_scene()` | 色の管理は Standard・露出 0。主光・補助光・後ろの縁取り光 2 つ。背景はカメラにだけ明るい灰色。Cycles CPU 96 サンプル + ノイズ除去 |

### 人ごとの設定 (プロフィール → 数値)

| 人 | 肌 | 髪 | 目 | 体 | 表情 | ほか |
|---|---|---|---|---|---|---|
| セナ (女 29) | #9a6448 濃い日焼け | 黒、長く、低く結ぶ | 茶 | がっしり: 肩 +1.8 cm、腰 +7%、胴 +13%、腕脚を太く | `MTH_Fun` 0.55 + `EYE_Joy` 0.22 + `BRW_Fun` 0.45 | 左の前腕に古い傷 |
| ルオ (男 39) | #7a4a32 いちばん濃い | こげ茶、短く刈る | 茶、ハイライト弱め | 肩 +2 cm、胸板 +8%、腰 −4%、胴 −8%、上腕 +13%・前腕 +10%、背 0.97 倍 | `EYE_Close` 0.22 + `BRW_Angry` 0.35 + `MTH_Close` 0.3 (目を細めた鋭いまなざし) | 頬をこけさせる (−6%)、眉を 1.45 倍の太さ、右の前腕に小さな古傷 |
| タヒ (男 18) | #a06a4a 日焼け | 赤茶、短く乱れる | 灰色 | 細身: 胴 −5%、腕脚 −3〜−5%、脚 1.05 倍・腕 1.04 倍 (手足が長い)、背 0.96 倍 | `MTH_Fun` 0.65 + `MTH_Joy` 0.12 + `EYE_Joy` 0.28 + `BRW_Surprised` 0.55 (よく笑う、上がった眉) | ザガのけが 4 回: 左の前腕・右の上腕・左の太もも・右のすねに古い傷 |
| ウィロ (女 21) | #b58466 浅め | 赤茶、長く三つ編み (結び目から 34 cm) | 茶 (うすめ) | ふつう、やわらかい: 腰 +4%、胴 +5%、腕脚を少し太く | `MTH_Fun` 0.35 + `EYE_Sorrow` 0.28 + `EYE_Joy` 0.12 + `BRW_Sorrow` 0.3 (おだやかな垂れ目、ゆるい眉) | 両手に煤、ほおを少し丸く |
| イサ (男 20) | #9a6648 日焼け | 栗色、短く無造作 | 茶 | いちばん細い: 胴 −12%、胸 −5%、上腕 −16%・前腕 −12%・脚 −8〜−10%、背 0.96 倍 | `EYE_Close` 0.28 + `BRW_Sorrow` 0.25 + `MTH_Close` 0.5、目を 8° 下へ (伏し目、口を結ぶ) | 頬をこけさせる (−8%) |

かかった時間 (CPU 4 コア、村の計算と同時、96 サンプル): 1 人あたり組み立て 4 秒、3 面図 1 枚 13〜25 秒、
顔 70〜93 秒、表情 2 枚 各 33〜36 秒、並べる絵の部品 2 枚 約 60 秒、全部で 4.5〜5 分。メモリは約 1 GB。

残っている課題:
- 男の足は靴下の形のまま (指がない)。すねの上のほうに靴下のふちの線がうすく残る。
- 髪は頭の骨に固定 (ゆれない)。三つ編みは胸の骨に固定。
- タヒとイサは同じ顔 (桜田 フミリヤ) で、表情・目の色・髪・体つきで分けている。ルオは HairSample_Male の顔。
- ウィロの前髪は Victoria Rubin のまっすぐな切りそろえのまま (本人の絵の流した前髪とはちがう)。
- セナの結んだ髪の先が胸の帯の後ろにかくれて短く見える。胸の帯にふくらみの形が少し出る。

## 作風 3: アニメ調 (トゥーン) — まだ作っていない

本人の指示 (「まずは中間だけで」) で後回し。準備だけ済み:
EEVEE はクラウドに GPU がないため、そのままでは動かない (libEGL がない)。
Ubuntu の mesa (llvmpipe、ソフトウェアの OpenGL) を `apt-get download` して `/dev/shm/mesa` に展開し、
`LD_LIBRARY_PATH` などを設定すると EEVEE も動くことを確かめた (256×256 の試験で 39 秒)。
作るときは Shader to RGB + 色の段 (Color Ramp) と、裏返しの外殻による輪郭線を `mat_*` に足す。

## 頭の差しかえ口 (`replace_head()`)

いまの顔は MakeHuman の顔を数値で整えたもので、まだ「こわい」(不自然) という感想がある。
よい頭・顔の 3D 素材が見つかったら、顔は作りなおさずに差しかえる。

```bash
... build_sena.py --style mid --head-asset /path/to/head.glb [--keep-hair]
```

- 対応する形式: .glb / .gltf / .obj / .fbx。向きは「前が -Y、上が +Z」(glTF ならそのまま)。
- 体の首より上 (首の関節 + 2.5 cm より上) をマスク (`MASK` 変形) で隠す。
- 素材のメッシュを 1 つにまとめ、隠した頭と同じ高さに拡大縮小し、真ん中と下端をそろえる。
- head の骨につなぐので、姿勢を変えても付いてくる。
- 元の目・まつ毛・眉は隠す。`--keep-hair` がなければ、作った髪も隠す。
- 球を使った試験で、位置合わせと隠す処理が動くことを確かめた。首の切り口はぎざぎざなので、
  素材は首を少し含むもの (首の付け根で体と重なるもの) がよい。肌の色は素材側で合わせる。
- 素材を使うときは、ライセンス (CC0 / CC-BY など) と出典を下の表に足すこと。

## ほかの四人を同じように作るには

VRoid の道 (作風 4) で五人とも作った (上の節)。MakeHuman の道 (`build_sena.py`) で作るときは、
`people.py` の `PEOPLE` にセナと同じ形で 1 人を足し、`--person` で描く。

## 時間の記録

`build_sena.py` は描いた 1 枚ごとに `render <file>: <秒>` を、最後に `TIMES {...}` を出す。

## 素材のライセンスと出典

| 素材 | ライセンス | 出典 |
|---|---|---|
| MakeHuman 基本メッシュ hm08 (`data/3dobjs/base.obj`)、形の素材 (`data/targets/`)、リグと重み (`data/rigs/`) | CC0 1.0 | https://github.com/makehumancommunity/mpfb2 (commit 650c5c53bd6989a8ac264f31fa1d11d4a0c7bd8a) |
| MPFB2 のプログラム (読みこみに使うだけ。リポジトリには入れない) | GPL-3.0-or-later | https://github.com/makehumancommunity/mpfb2 |
| MakeHuman の目 (high-poly eyes、brown 瞳) | CC0 1.0 | https://github.com/makehumancommunity/makehuman (commit a8bc2d54ff0ac92e78ff71431b1023eda42bf482、`makehuman/data/eyes`) |
| Blender (bpy 4.5.16、Python モジュール版) | GPL-2.0-or-later | https://pypi.org/project/bpy/ |
| VRoid サンプル「千駄ヶ谷 篠 (Sendagaya Shino)」(セナの顔・髪)、「HairSample_Female」(女の体・骨組み、ウィロの顔)、「HairSample_Male」(男の体・骨組み、ルオの顔、ルオとタヒの髪)、「桜田 フミリヤ (Sakurada Fumiriya)」(タヒとイサの顔、イサの髪、ルオの後ろ髪)、「Victoria Rubin」(ウィロの髪、ソナ85の顔と髪) | CC0 (5 つともファイル内の VRM meta が `licenseName: CC0`、`commercialUssageName: Allow`、`allowedUserName: Everyone` であることを確かめた。pixiv の説明「CC0 license models … Copyright is waived」) | https://github.com/madjin/vrm-samples (commit e16eb187100149a315ad92c3c9968f1d5baa6c7d、`vroid/beta/`)。条件の説明: https://vroid.pixiv.help/hc/en-us/articles/4402614652569 。作者 pixiv Inc. (VRoid) に感謝をこめて記す。同じリポジトリの `vroid/stable/AvatarSample_*` と `vroid/masc_vroid.vrm` は `licenseName: Other` なので使っていない |
| mesa (llvmpipe、EEVEE の試験だけ) | MIT ほか | Ubuntu 24.04 の `libegl-mesa0`, `mesa-libgallium` ほか |

髪 (MakeHuman の道)・服・眉・傷・煤・帯・三つ編み・結び紐は、スクリプトが手続き的に作るもので、外の素材は使っていない。
MakeHuman の CC0 素材は、出典を書く義務はないが、感謝をこめて記す (MakeHuman Community, Data Collection AB)。
