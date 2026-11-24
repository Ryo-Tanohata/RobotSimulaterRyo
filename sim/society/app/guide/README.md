# 案内役の小さな絵 (年報・統計のページ用)

年報 (`sim/society/reports/yearN.html`) と統計のページで、吹き出しの横に出す案内役の顔です。
案内役は村の人 **ソナ85** (女・74 歳・251年30日目)。選んだわけとプロフィールは
`docs/society_phase/guide_character.md`。

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

## ライセンス

- 人の模型は、VRoid のサンプル「HairSample_Female」(体・骨組み) と「Victoria Rubin」(顔・髪) から作った。
  どちらも CC0 (ファイル内の VRM meta が `licenseName: CC0`。https://github.com/madjin/vrm-samples の `vroid/beta/`、
  commit e16eb187100149a315ad92c3c9968f1d5baa6c7d)。作者 pixiv Inc. (VRoid) に感謝をこめて記す。
- 服 (革の貫頭衣と帯)・髪の色と結び方・しわ・表情の組み合わせは、スクリプトが作ったもの。
- 描画は Blender (bpy 4.5) の Cycles。描いた絵は、元の素材と同じく CC0 として扱う (このリポジトリのほかのファイルのライセンスとは別)。
