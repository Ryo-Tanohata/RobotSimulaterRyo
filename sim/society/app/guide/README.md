# 案内役の小さな絵 (年報・統計のページ用)

年報 (`sim/society/reports/yearN.html`) と統計のページで、吹き出しの横に出す案内役の顔です。
案内役は村の人 **ソナ85** (女・74 歳・251年30日目)。選んだわけとプロフィールは
`docs/society_phase/guide_character.md`。

- 名前: ソナ85
- 絵: sona85

(この 2 行を `tools/explain_data.py` の `guide_info()` が読む。年報と統計のページの吹き出しは案内役の顔だけ)

| ファイル | 表情 |
|---|---|
| `sona85_neutral.webp` / `.png` | ふつう |
| `sona85_smile.webp` / `.png` | 笑顔 (よい知らせ) |
| `sona85_concern.webp` / `.png` | 心配 (蓄えが減った・子が亡くなった など) |
| `sona85_surprise.webp` / `.png` | おどろき (大きく動いた数) |

- 大きさは 128×128。webp (約 2 KB) を使い、読めない場所では png (128 色、約 7 KB) を使う。
  HTML に埋めこむときは base64 にしてもよい。
- 元の 512×512 の絵は `sim/society/out/human/guide_sona85_*.png` (git に入れない)。作り方は
  `sim/society/tools/human/build_person_vroid.py -- --person sona85 --only guide` (README は同じ場所)。

## 解説の係 (年報の動画で分野ごとに話す村の人)

年報の動画 (`sim/society/video/yearly/`) では、案内役のほかに 4 つの分野の係も、顔を出して自分の声で話す。
選んだわけは `docs/society_phase/guide_character.md` の「解説の係」、声は `sim/society/video/yearly/voices.json`。

| 係 | 人 | ファイル |
|---|---|---|
| 人口の係 | キオ85 (女・50 歳) | `kio85_{neutral,smile,concern,surprise}.{webp,png}` |
| くらし・食べ物の係 | ネイ75 (男・61 歳) | `nei75_*` |
| 知恵・技術の係 | ケセ98 (男・39 歳) | `kese98_*` |
| よその村・町の係 | ナセ110 (女・30 歳) | `nase110_*` |

作り方はソナ85 と同じ (`build_person_vroid.py -- --person <名前> --only guide`、設定は `people.py` の `VROID`)。服はみなヤギのなめし革の貫頭衣 (色と丈を変えた)。

## ライセンス

- 人の模型は、VRoid のサンプル「HairSample_Female」(体・骨組み) と「Victoria Rubin」(顔・髪) から作った。
  係の 4 人は、ほかに「HairSample_Male」「千駄ヶ谷 篠」「桜田 フミリヤ」も使った。
  どれも CC0 (ファイル内の VRM meta が `licenseName: CC0`。https://github.com/madjin/vrm-samples の `vroid/beta/`、
  commit e16eb187100149a315ad92c3c9968f1d5baa6c7d)。作者 pixiv Inc. (VRoid) に感謝をこめて記す。
- 服 (革の貫頭衣と帯)・髪の色と結び方・しわ・表情の組み合わせは、スクリプトが作ったもの。
- 描画は Blender (bpy 4.5) の Cycles。描いた絵は、元の素材と同じく CC0 として扱う (このリポジトリのほかのファイルのライセンスとは別)。
