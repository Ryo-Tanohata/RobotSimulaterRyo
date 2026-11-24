# 年報の動画 (1 年 1 本、2〜3 分)

案内役のソナ85 と、4 つの分野の係 (みな川辺の村に生きている人) が、それぞれの声で、
年報 (`reports/yearN.html`) と統計のページの図を見せながら、その年のことを話す動画です。

- 本人の決め (2026-11-24): 声は VOICEVOX・係も村の人・1 年 1 本 2〜3 分・**先に絵コンテを作って本人に見てもらい、「go」のあとで本番**。
- 文は解説の係のワークフロー (`tools/explainer_workflow.js`) が書き、事実の確かめの係が数を確かめたもの (`reports/explain/yearN.json`) だけを使う。新しい数は作らない。

## 作り方

```bash
# 1) 絵コンテまで (声・図・1 文の絵・絵コンテ。約 2 分。記憶 2.2 GB ほど。村の重い歩と重ねない)
bash sim/society/video/yearly/make.sh 250 /tmp/yv250
#   → sim/society/video/out/storyboard_yearly_250.html と .jpg (git に入れない)
#     sim/society/video/storyboards/storyboard_yearly_250.json (絵のない小さな版。git に入れてよい)
# 2) 本人の「go」のあとで本番 (同じ作業フォルダ。約 1〜2 分。記憶 0.2 GB)
GO=1 bash sim/society/video/yearly/make.sh 250 /tmp/yv250
#   → /tmp/yv250/year250.mp4 (1280x720・30 コマ/秒・音 -16 LUFS。git に入れない)
```

| ファイル | 役目 |
|---|---|
| `script.py` | 台本: 案内役のはじめ (年・人の数・ひとことの気分) → 3 つの大事なこと → 分野の係 4 人 (1〜3 文。吹き出しが少ない係は図の見かたを 1 文) → 案内役の終わり。大きな年はまとめ役の動画の文 (video.lines) も案内役が読む |
| `charts.py` | 図 (年報のダッシュボードと統計のページの図を 1280×560 で描きなおす) と 1 文の絵 (下の帯に話す人の顔・名前の札・字幕)、クレジットの絵 |
| `storyboard.py` | 絵コンテ (1 行 1 文: 時刻・話す人・顔・字幕・読み・図・絵) と、絵を並べた 1 枚の jpg |
| `voices.json` | 顔ぶれと声 (下の表)。`teams` で分野と人を結ぶ |
| `make.sh` | ぜんぶをつなぐ。秒は声 (wav) の長さから: 1 文 = 0.3 秒 + 声 + 0.8 秒、最後にクレジット 5 秒 |

前の「大きな年だけのずんだもんの動画」はこれにまとめた (毎年作る。大きな年の文は案内役が読む)。

## 顔ぶれと声

| 人 | 役 | 声 (VOICEVOX) | スタイル ID | 音声モデル | クレジット |
|---|---|---|---|---|---|
| ソナ85 (女・74) | 案内役・まとめ役 | 東北イタコ ノーマル (少しゆっくり・少し低め) | 109 | 21.vvm | VOICEVOX:東北イタコ |
| キオ85 (女・50) | 人口の係 | 九州そら ノーマル | 16 | 2.vvm | VOICEVOX:九州そら |
| ネイ75 (男・61) | くらし・食べ物の係 | ちび式じい ノーマル | 42 | 10.vvm | VOICEVOX:ちび式じい |
| ケセ98 (男・39) | 知恵・技術の係 | 雀松朱司 ノーマル | 52 | 12.vvm | VOICEVOX:雀松朱司 |
| ナセ110 (女・30) | よその村・町の係 | 春日部つむぎ ノーマル | 8 | 0.vvm | VOICEVOX:春日部つむぎ |

動画の終わりのクレジットと、動画の説明文に、上の 5 つを書く。人の絵は「VRoid の CC0 サンプル (pixiv Inc.) をもとに作成」。

### 音声モデルの用意

`tools/voicevox/setup.sh` は 0.vvm (ずんだもん・春日部つむぎ など) だけを入れる。ほかは同じ配布元 (https://github.com/VOICEVOX/voicevox_vvm) から:

```bash
git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/VOICEVOX/voicevox_vvm /tmp/vvmrepo
(cd /tmp/vvmrepo && git checkout -q HEAD -- vvms/2.vvm vvms/10.vvm vvms/12.vvm vvms/21.vvm)
cp /tmp/vvmrepo/vvms/*.vvm /tmp/vv/vvms/    # 1 つ 約 60 MB
```

### 規約 (2026-11-24 に確かめた)

- VOICEVOX (ソフト): 商用・非商用とも使える。音声は各音声ライブラリの規約に従う。VOICEVOX を使ったことがわかるクレジットが要る (https://voicevox.hiroshiba.jp/term/)。
- 音声モデル (voicevox_vvm の TERMS と、VOICEVOX の各キャラクターの規約の文 voicevox_resource の policy.md): 5 人とも「『VOICEVOX:名前』とクレジットを記載すれば、商用・非商用で利用可能」。
  企業がかかわるときに事前の確認が要る声 (青山龍星・もち子さん・後鬼・Voidoll)、商用に問い合わせが要る声 (No.7・ぞん子・ユーレイちゃん) は使わない。
- 東北イタコ・九州そら (東北ずん子・ずんだもんプロジェクトの規約 https://zunko.jp/con_ongen_kiyaku.html、中身を読んだ): 商用・非商用とも可。
  クレジット「VOICEVOX:東北イタコ」のように。動画では説明文か動画の中の、見ればわかる場所に。
  してはいけないこと: 公序良俗に反する使い方・政治や宗教の活動・情報商材・わざと誤解させる内容・アダルト・反社会的勢力。この動画はどれにもあたらない。
- ちび式じい・雀松朱司・春日部つむぎ: VOICEVOX 公式の規約の文 (上) は確かめた。くわしい規約のページ
  (docs.google.com のちび式じいの規約・www.virvoxproject.com・tsumugi-official.studio.site) は、クラウドのネットワークで開けなかったため、中身は読めていない。
  公開の前に、本人の PC で一度読む (公式の文では、どれも商用・非商用で可・クレジットが要る)。
