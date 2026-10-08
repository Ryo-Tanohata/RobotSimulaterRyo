# ローカルへの引き継ぎ (2026-10-08)

クラウドのセッションから、自分の PC の Claude Code (Desktop アプリ、または `claude remote-control`) に引き継ぐためのメモ。
進め方の決まりは `daily_run.md` (Society 2.0 の手順・全員が亡くなったら戻してやり直す決まり・作者の決まり など) を見る。

## 1. 今の状態

- ブランチ: `claude/physics-engine-robot-simulator-xmyxdn`
- Society 2.0: **1709 日目、G5 (リーダーと決まり) に進んで一時停止**。第 2 部 (G3・G4) を終えた。まとめは `docs/society_phase/part2.md`。本人と相談して (4 つともおすすめ)、第 3 部 (G5) をそのまま始めた (2026-10-08 夜、クラウド)。人 22 人 (大人 15・子 7)、家族 8 つ、家族の住まい 5 軒、ヤギ 10 頭、土器 340 個。季節の集まりでは家族の代表 8 人が答える
- 終わったフェーズ: G1 (489〜1229 日目)・G2 (1229〜1529 日目)・G3 (1529〜1589 日目)・G4 (1589〜1709 日目)。評価の下書きは `docs/society_phase/G1.md`〜`G4.md`
- 家族の住まい (G3 から働く。計画 5 の「家族の住まい」) と、3D の家族の見た目 (色・家・家族ごとに集まる) を足した (2026-10-08、本人の希望)
- G5 (リーダーと決まり) は作った (2026-10-08、クラウドで。G5 に入ってから働く。計画 5 の G5、設計は `docs/society_phase/G5_design.md`)。**まだ作っていない**: G6 (交易・町・記録)

## 1.2 止めたところ (2026-10-09、本人「これで一旦作業を止めてください」)

- シミュレーション: 1709 日目 (G5 の最初の季節)。まだだれも答えていない (`data/answers/day1709/season/` はない)。続けるときは季節を進めるワークフローを `{"steps": 5}` で動かす
- 動画: **撮り直しの途中で止めた** (2026-10-09 7:14、本人の依頼でパソコンの電源を切るため)。日付の表し方を変えたので、G1 も含めて 13 本を話の順に撮り直している。**できたのは G1 の F1 だけ** (`app/society_G1F1.mp4`)。残りは G1・G1 の F2・F3・G2・G2 の F1〜F3・G3・G3 の F3・G4・G4 の F1・F2 と、第 2 部の通し (`app/society_part2.mp4`、G3 と G4 をつなぐ)。続きは本人の PC で `bash sim/society/video/render_all.sh` (話の順に 2 本ずつ撮る。できた動画は飛ばし、撮り終えた 60 秒の区間も残っているので続きから撮れる。この PC の `video/out/` に G1 の途中まである)。撮り終えたら、アプリの「動画」のボタンを話の順 (G → その F) に並べ、年で表す (例「G2: 畑と家畜 11〜13 年目」)。`<video id="mv">` の src も合わせる。撮る日: G1 510,600,629,659,990,1019,1229 / G1F1 509,510,600 / G1F2 629,630,631 / G1F3 659,660,779 / G2 1230,1259,1320,1415,1469,1529 / G2F1 1259,1260,1290 / G2F2 1409,1415,1435 / G2F3 1499,1529 / G3 1530,1559,1562,1573,1580,1589 / G3F3 1559,1562,1589 / G4 1591,1625,1675,1679,1680,1709 / G4F1 1680,1695,1709 / G4F2 1636,1679,1680
- **日付の表し方を変えた** (2026-10-09、本人の希望): アプリ・動画・ナレーションで「11 年目 31 日目」(この世界の 1 年 = 120 日、0 日目が 1 年目の 1 日目)。現実の 1 年とは違うので注釈を入れた (アプリの日付の横、動画の最初の 10 秒とクレジット)。ナレーションは日付の入った 70 文を書き直し、声を作り直した。決まりは `daily_run.md` の冒頭。Society 1.0 の動画 (1〜5 日目・F1〜F5) は撮り直していない (中の表示は「N 日目」のまま)

## 1.5 本人と決めたこと (2026-10-08)

- **Society 2.0 は大きすぎるので、いくつかの部に分ける**。分け方は学説と史実をもとに決める (本人の希望)。調べは済んだ: `docs/research/society2_periodization.md`。部の終わりには止まって、まとめ・通しの動画・次の部の相談をする
  - **決まった (2026-10-08、PC のセッションで本人が 4 つともおすすめを選んだ)**。中身は `docs/society2_phase_plan.md` の 2.1
    1. 分け方: **4 部** (第 1 部 村と畑 G1・G2 済み / 第 2 部 土器と家の倉 G3・G4 / 第 3 部 まとめ役と神殿 G5 / 第 4 部 町と文字 G6)
    2. G4 の「ジニ係数 0.3 以上」は条件から外し、大きな差は後の部の目安にする。**`era2.py` の CRITERIA["G4"] は直した** (家ごとの持ち物がある、受けつぎが 1 回以上)。ジニ係数は計算と記録を続ける
    3. G6 の町と記録は**別々の条件**にする (どちらが先でもよい。G6 を作るときに入れる)
    4. G5 は**2 段階** (話し合い・長老・祭り → 決まったまとめ役・罰・裁き。村が分かれるのも起きてよい結果。G5 を作るときに入れる)
- **途中経過: 5 季節ごとに、短い文の報告とグラフ 1 枚**を本人に見せる (人数・蓄え・食べ物の中身・家ごとの持ち物などの移り変わり)。ワークフローは `{"steps": 5}` で動かす
- **フェーズごとの動画は、今まで通り 8〜9 分**
- フェーズの終わりの報告・評価の下書き・動画、20 季節ごとの記録 (run_log・G?_notes) は今まで通り

## 2. 必要なもの (自分の PC)

- Git、Python 3 (+ numpy: `pip install numpy`。音を合わせる `tools/audio/mix.py` が使う)
- Node.js 18 以上、Google Chrome、ffmpeg (PATH に入れる)
- Windows なら Git Bash (`render_parts.sh` が bash の台本のため)。Python が `python3` という名前で動かないときは、`PY=python` を前につける (`render_parts.sh`)。`step.py` やワークフローの中の `python3` も、`python` に読みかえる
- 取得: `git fetch origin && git checkout claude/physics-engine-robot-simulator-xmyxdn && git pull`

## 3. G1・G2 の動画を作る (GPU で)

**撮影の速さ (2026-10-09、本人の PC の GPU RTX 5070)**: 1 本ずつなら 10 秒ぶんに約 25 秒。1 コマずつ順に撮るので CPU に余裕があり、2 本同時に撮ると全体でほぼ 2 倍の速さになる (13 本で約 1 時間 45 分の見込み)。`render_all.sh` がこれをする。前の G1 (2026-10-08 に別の PC の内蔵 GPU Intel Iris Xe で撮影) は日付が「N 日目」のままなので撮り直す。

PC での注意 (2026-10-09 に分かったこと)
- Windows の Python は `PY=py` でよい。`render_parts.sh` が `timeline.json` (日本語が入る) を文字コードの指定なしで読んでいて、Windows の Python 3.13 では CP932 で読もうとして撮影が始まらなかったので、UTF-8 で読むように直した
- 撮り直すと、時計の日付が全部のコマに入っているので、全部撮り直しになる。字幕の誤字のように長さが変わらない直しなら、`out/<名前>_pNN.mp4` を消してもう一度動かすと、その 60 秒だけ撮り直してつなぎ直す

PC での注意 (2026-10-08 に G1 を撮って分かったこと)
- ffmpeg は `winget install Gyan.FFmpeg` で入る。入れたあと、シェルを開き直すまで PATH に入らない (Git Bash なら `export PATH="$PATH:$LOCALAPPDATA/Microsoft/WinGet/Links"` か、`.../WinGet/Packages/Gyan.FFmpeg_.../bin` を足す)
- `render_parts.sh` の最後の「区間をつなぐ」が、`out/` の下に撮ると `out/out/...` を探して失敗していたのを直した (撮った区間は残るので、同じコマンドをもう一度動かせば、つなぐところから続く)
- Windows では `PY=python` をつける。撮影中に季節を進めるなら `DATA_DIR=写しのフォルダ` をつける

クラウドでは GPU がなく、CPU で 3D を描いていたので、9 分の動画に 3 時間以上かかった。自分の PC の GPU (内蔵 GPU でもよい) を使うと速い。
ナレーションの文 (`video/narration_G1.json`・`narration_G2.json`) と声 (`video/voice/G1`・`voice/G2`、VOICEVOX:ずんだもん) はリポジトリにある。

```bash
cd sim/society/video
npm install                      # 初めてのときだけ (puppeteer-core)
mkdir -p out
# Chrome の場所が違うときは CHROME="C:/.../chrome.exe" を前につける (既定は C:/Program Files/Google/Chrome/Application/chrome.exe)
GPU=1 DAYS=510,600,629,659,990,1019,1229 bash render_parts.sh narration_G1.json voice/G1 out/society_G1
GPU=1 DAYS=1230,1259,1320,1415,1469,1529 bash render_parts.sh narration_G2.json voice/G2 out/society_G2
# 注意: app_data.json は撮る日より後のデータでもよい (その日に村にいた人だけを映す)。ただし撮っているあいだに季節を進めると
#   app_data.json が書きかわるので、写しを作って DATA_DIR=写しのフォルダ をつけるとよい
# 音 (ナレーション + 効果音 + BGM) を合わせて、アプリに入れる
for G in G1 G2; do
  python ../../../tools/audio/mix.py out/society_$G.timeline.json voice/$G out/society_$G.wav
  ffmpeg -y -i out/society_${G}_silent.mp4 -i out/society_$G.wav -c:v libx264 -crf 28 -preset medium -pix_fmt yuv420p \
    -c:a aac -b:a 128k -af loudnorm=I=-16:TP=-1.5:LRA=11 -movflags +faststart -shortest ../app/society_$G.mp4
done
```

- 試し撮り: `LIMIT=10` をつけると最初の 10 秒だけ撮る (`node make_video.mjs narration_G1.json voice/G1 out/t 510 510` のように 1 日だけでも撮れる)
- 撮った区間 (`out/society_G1_p00.mp4` …) は残るので、途中で止まっても同じコマンドで続きから撮れる
- アプリの「動画」の一覧 (`app/index.html` の `data-src="society_F5.mp4"` の行の下) に、G1・G2 のボタンを足す (長さは `ffprobe` で見る)。G1 は約 9 分 12 秒
- `out/` はコミットしない。`app/society_G1.mp4`・`society_G2.mp4` はコミットする (前の動画と同じ)
- 動画の最後にクレジット (VOICEVOX:ずんだもん、three.js) が入る (`make_video.mjs` が入れる)

## 4. シミュレーションを続ける

- 自分の PC の Claude Code で、このリポジトリを開いて、たとえば「`sim/society/daily_run.md` と `sim/society/HANDOFF.md` に従って、Society 2.0 を続けて」と頼む
- 季節を進めるワークフロー: `tools/society2_seasons_workflow.js`。**先頭の `ROOT` を自分の PC のリポジトリの場所に書きかえる**。Workflow で `{"steps": 20}` を渡して動かす (家族の代表ごとに haiku が役を演じて答え、`tools/season_step.sh` で 1 季節進めてコミットする)
- 手で 1 季節進めるとき: 答えを `data/answers/dayNNNN/season/<名前>.json` に置いて、`python3 sim/society/step.py season`。今の状態は `python3 sim/society/step.py status`
- フェーズが進んだら止まる (一時停止)。報告・評価の下書き・動画のあと `python3 sim/society/step.py resume`

### G5 (リーダーと決まり) の仕組み (2026-10-08 に作った。G5 に入ってから働く)

中身は `docs/society2_phase_plan.md` の 5. G5。もめごとの中身は世界で実際に起きたこと (ヤギ・倉・蓄え・刈る) から作る。設計書の 15. の 7 つは、本人がおすすめの通りに決めた (2026-10-08)

(以下は、作る前に書いた設計のメモ)

**設計書ができた (2026-10-08): `docs/society_phase/G5_design.md`**。2 段階 (計画 2.1) の決まりを入れた、そのままコードにできる設計 (はじめに日本語の要約)。次のセッションは、これを読んで、コードを書き (`era2.py`・`step.py`・`resume.py`)、13. の試し方で確かめ (G3・G4 の結果が前と同じか、G5 の試し回し)、15. の「本人に確かめること」を本人に聞く。下の箇条書きは、もとの計画 (設計書はこれを細かくしたもの)

`docs/society2_research.md` の 6. G5 による。G4 が終わる前に作り、G5 に入ってから働くようにする (`era2.py` の `era_at_least(state, "G5")`)。
- もめごと: 家の数が多いほど起きやすい (【文献】スカラー・ストレス、Johnson 1982: 決める単位が 6 をこえると難しくなる)。中身は世界で実際に起きたことから作る (よその家の畑を刈った、世話のないヤギが畑を荒らした、など)
- 裁かれないまま 2 季節たつと、もめごとの家が村を出ていくことがある (村の分裂)
- 人が決めること: まとめ役を選ぶ (大人の半分をこえる賛成)、まとめ役がもめごとを裁く、掟を提案するときに罰を書く
- 条件 (計画): 家族が 6 つ以上で、まとめ役がいる。罰のある決まりが 3 つ以上。もめごとの裁きが 2 回以上

## 5. クラウドでしか動かなかったもの

- VOICEVOX の声づくり (`tools/voicevox/setup.sh` は Linux 用)。**本人の PC の WSL (Ubuntu) で動いた (2026-10-09)**: git の改行の設定で台本が CRLF になっているので `sed 's/\r$//' tools/voicevox/setup.sh > /tmp/vv_setup.sh && bash /tmp/vv_setup.sh`。Windows から WSL の台本を動かすときは `wsl -d Ubuntu --exec bash <台本>` (`wsl -- bash -lc '…'` だと変数が先に展開されて動かない)。声は `~/.cache/robotsim-voicevox/venv/bin/python tools/voicevox/synth.py <セリフ.json> <出力>`。読みを変えたいときはセリフに `say` を足す (例: 104日目 → ひゃくよっかめ)
- 撮影はクラウドでは止めた (G1 は半分まで撮っていたが、ローカルで撮り直す)
