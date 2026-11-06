# 大きくなる 2 つのファイルをどうするか (計画。2026-11-05)

本物の村 (sim/society/data) のファイルのうち、2 つが GitHub の 100 MB の上限に近づいている。

- `sim/society/data/app_data.json` (アプリ用のデータ)
- `sim/society/data/records/season_person.jsonl` (1 行 = 1 季節 × 1 人の記録)

この文書は計画だけ。コードも data も変えていない (data には書いていない。git にもさわっていない。LLM も使っていない)。
**2026-11-05 に案 A と案 C を入れた (下の 7. 入れたこと)。**
調べは、コードと git の履歴を読むだけで行った。

年の数え方: 年の集まりの日は 120 × 年 − 1 (例: 141年の年の集まり = 16919 日目、142年 = 17039 日目)。
1 年は 4 季節で、本物の村は 1 季節ごとにコミットする。いまの速さは **1 年で 約 34 分** (137〜141年の 4 年が 134 分)。

## 0. みじかい答え

- いまの大きさ (HEAD 7bba5e34、16949 日目): **app_data.json 64.2 MB・season_person.jsonl 61.8 MB**。思っていたより大きい (どちらも 50 MB をこえて、GitHub はもう注意を出している)。
  ついでに state.json も 49.7 MB で、50 MB の手前。
- **app_data.json の 3 分の 2 は、ほぼ 0 だけの「信頼」(trust) の表**。1 人ごとに、これまで村にいた 1198 人ぶんの名前と数が入っていて、
  それが `people` と `resumes` に 2 回入っている (21 MB × 2 = 42 MB)。1434006 組のうち 0 でないのは 17 組だけ。
  人の数 N の 2 乗で増えるので、増え方はだんだん速くなる。
- **90 MB に届く見込み: app_data.json は 156年ごろ (あと 約 15 年 = 村を回して 約 9 時間)**。100 MB は 160年ごろ。
  season_person.jsonl は 164年ごろ (あと 約 23 年 = 約 13 時間)。state.json は 180年より後。
- **おすすめ: (A) app_data.json の信頼の表から 0 を外す (日で切りかえる) と、(C) season_person.jsonl を年ごとのファイルに分ける の 2 つを、1 回の年の集まりの止まりで入れる。**
  app_data.json は 64 MB → 約 22 MB になり、そのあとは 1 年 約 0.2〜0.3 MB しか増えない。season_person は 1 ファイル 約 1 MB になる。
  どちらも世界 (state.json・お題) は 1 バイトも変わらない。前の歩のやり直しも 1 バイトも同じのまま。

## 1. 大きさの移り変わり (git の履歴から)

`git cat-file -s <コミット>:<道>` で、年の集まりのコミットごとに見た (単位 MB = 1,000,000 バイト)。

| 日 (コミット) | 年 | app_data.json | season_person.jsonl | state.json |
|---|---|---|---|---|
| 11969 (5955be77) | 99 | 29.3 | 33.4 | 29.5 |
| 13079 (3dde5ba2) | 109 | 32.0 | 38.5 | 30.2 |
| 14609 (f4e6f2b1) | 122 | 44.2 | 46.8 | 39.0 |
| 15449 (5a57fbe3) | 129 | 48.1 | 51.8 | 41.1 |
| 15929 (7f4d8ea1) | 133 | 52.1 | 54.6 | 43.4 |
| 16439 (ba962178) | 137 | 58.6 | 58.1 | 48.0 |
| 16919 (43cb746b) | 141 | 62.6 | 61.8 | 49.7 |
| 16949 (7bba5e34、HEAD) | 141 | 64.2 | 62.0 (いまの data) | 49.7 |

1 年あたりの増え方:

- app_data.json: 99〜122年は 約 0.6 MB/年、122〜141年は 約 1.0 MB/年、133〜141年は 約 1.3 MB/年 (速くなっている)。季節によって ±1 MB ほどゆれる (しまっていない年の出来事の数がちがうので)。
- season_person.jsonl: 1 年分の行が 130年 0.70 MB → 140年 0.93 MB。1 年に 約 25 KB ずつ増える (村の人が増えているので)。
- state.json: 122〜141年で 約 0.55 MB/年。

### 1.1 app_data.json の中身 (HEAD、64.2 MB)

| 鍵 | 大きさ | 中身 |
|---|---|---|
| people | 23.1 MB | 1198 人 (いま生きているのは 約 250 人)。そのうち **trust が 21.0 MB** |
| resumes | 22.8 MB | 履歴書 1198 人。そのうち **trust が 21.0 MB** (people と同じもの) |
| events | 8.3 MB | しまっていない年 (今の年と前の 2 年) の出来事。archive.py があるので、これ以上は増えない |
| stats | 4.7 MB | 日ごとの数 16979 日分。1 年 約 34 KB 増える |
| days | 2.1 MB | 3D の再生の行 (しまっていない日) |
| plants・archive・ほか | 3.2 MB | |

trust は `world.py` 145 行・`era2.py` 162/169 行で、村に入った人ごとに「これまでのみんなの名前: 0.0」で作られ、亡くなった人・出た人の名前も消えない。
だから 1 人ぶんの表は N 個、全部で N × N 個 (1 組 約 14.7 バイト)。2 か所に入るので **約 29.3 × N² バイト**。
N は 130年 1007 人 → 135年 1090 人 → 140年 1177 人 (1 年 約 17〜19 人ずつ増え、少しずつ速くなる)。
N が 19 人増えると、trust だけで 約 1.3 MB 増える。これが app_data.json の増え方のほとんどを説明する。

### 1.2 見込み (90 MB に届く年)

- app_data.json ≒ 29.3 × N² + (ほか 22 MB、1 年 約 0.2 MB 増える)。N が 1 年 19 人増えるとして:
  - 150年 (N ≒ 1370) で 約 79 MB、**156年ごろ (N ≒ 1480) で 90 MB**、160年ごろで 100 MB。
  - N が 1 年 22 人ずつ増えれば、90 MB は 155年ごろ (1 年早い)。
  - 村を回す速さ (1 年 約 34 分) なら、**ふつうに回すと 約 8〜9 時間で 90 MB に届く**。いまの 1 日の回し方なら、あと 1〜2 日。
- season_person.jsonl: 1 年 0.93 MB から 1 年 25 KB ずつ増えるとして、90 MB まで あと 約 23 年 (**164年ごろ**、約 13 時間)。
- state.json: trust (21 MB、1 回だけ) + ほか 29 MB。90 MB は N ≒ 2000 人のころで、あと 40 年ほど (180年より後)。いまはしない (下の 6.)。

## 2. だれが書いて、だれが読むか

### app_data.json

- 書く: `step.py export()` (395〜432 行)。季節を進めるたびに state から全部を作り直す。`archive.full()` でしまった年も戻して、
  `resume.build()` (resume.py 138 行で trust を写す) と `people[].trust` (step.py 408 行) を入れる。
  `standalone.py` も同じ export で 1 つの HTML (`_site/society_view.html`) を作る。
- 読む:
  - `app/index.html` (540 行で読む)。trust を使うのは **442 行の「信頼している人」だけで、読むのは `resumes[].trust`**。
    0 も「ナギ 0.00 ・ …」と 1197 人ぶん並べて見せている。`people[].trust` はどこも読まない (index.html・replay3d.js・video/make_video.mjs を調べた)。
  - `video/make_video.mjs` (動画)、`daily_run.md` の公開 (app_data.json を出す)、`tools/test_g7.py` 426 行 (era を見るだけ)。
  - `tools/cloudflare/build.sh` は 25 MiB をこえるファイルを入れない。**いまの app_data.json (61 MiB) はもう Cloudflare に出ていない。**
- くらべる: `tools/exp3_replay.py`・`tools/exp4_replay.py` は、歩のコミット C の 1 つ前 (C^) の state.json・archive/・app_data.json を写しに出し、
  いまのコードで `step.py season` を 1 回動かして、**state.json・app_data.json (sha256)・archive/・次のお題** が C と 1 バイトも同じかを見る (SOC_RECORDS=0)。
  だから **export の書き方を変えると、前の歩のやり直しで app_data.json が「ちがう」になる**。日で切りかえる必要がある (`era2.LEAVE_TALK_FROM`・`g10.G10_FIX_FROM` と同じやり方)。
  `tools/exp3_setup.sh`・`exp4_setup.sh` も app_data.json を写す。

### season_person.jsonl

- 書く: `tools/build_records.py` (1860 行)。step.py が季節ごとに `build_records.py --quiet` を呼び (step.py 109 行)、記録を **毎回はじめから全部作り直す**。
  `write()` (1798 行) は中身が同じなら書かない。控え (snapshots) はもう年ごとのファイル `records/snapshots/snapshots_NNNN.jsonl` に分けてある (`records.snap_path`・`snap_files`)。
- 読む: `tools/build_dashboard.py` 270 行 (家ごとの働いた日)、`tools/econ_report.py` 747 行、`tools/exp4_measure.py` 348 行、
  `tools/test_records.py` 100・665 行、`tools/test_g7.py` 1433 行。ブラウザ (app/*.html) は直接は読まない (dashboard.html は dashboard_data.json を読む)。
  `accounts.py` は行を受けとるだけ。`tools/year_report.py`・`tools/build_tech_tree.py` は読まない (season_village・state・archive を読む)。
- くらべる: やり直し (exp3/exp4_replay) は **SOC_RECORDS=0 で記録を作らない** ので、records/ はくらべていない。分け方を変えても、やり直しはそのまま。
- `tools/test_archive.py` は archive.py (state のしまう・戻す) の試しで、この 2 つのファイルの形にはよらない。

## 3. 案

### 案 A: app_data.json の信頼の表から 0 を外す (日で切りかえる) 【おすすめ】

- コードの変更 (step.py の export だけ。小さい):
  - `APP_SLIM_FROM = <止めた日 D>` を足す。`state["day"] > APP_SLIM_FROM` のときだけ:
    - `people[]` に `trust` を入れない (だれも読まない)。
    - `resumes[].trust` は 0 でないものだけにする (`{k: v for k, v in r["trust"].items() if v}`)。
  - D より前の日 (D をふくむ) の export は、いまと 1 バイトも同じ。
- 1 バイトも同じでなければならないもの: state.json・archive/・お題は変わらない (export は世界を変えない)。
  app_data.json は、D までの歩のやり直しでは同じ (切りかえ前)。D のあとの歩は、新しいコードで作ったものが本物なので、やり直しても同じ。
  **切りかえの日をつけずに入れると、前の歩のやり直しがみな「app_data ちがう」になる** ので、日の切りかえは必ず入れる。
- 大きさ: 64.2 MB → 約 22 MB (21.0 MB 消える + 21.0 MB がほぼ 0 になる)。増え方は 1 年 約 0.2〜0.3 MB になり、90 MB はずっと先 (200 年以上)。
  25 MiB より小さくなるので、Cloudflare にもまた出せる (25 MiB をこえるのは 15 年ほど先)。
- ダッシュボード (index.html): 「信頼している人」の行が、0 の人を並べなくなる。0 しかない人は「―」になる (442 行の `|| "―"` がもうある)。
  index.html の変更はいらない。見え方はむしろ読みやすくなる。動画・3D は変わらない。
- 危うさ: 小さい。気をつけるのは、data_E3_*・data_E4_* の写し (実験の村) を D より後の日まで回してやり直すとき。そのときも同じコードで作るので同じになる。
  `standalone.py` で古い state から作ると、その日によって切りかえ前・後のどちらかになる (見え方だけのちがい)。

### 案 B: app_data.json の古いもの (出来事・日ごとの数・亡くなった人の履歴書) をもっと archive/ に移す

- コードの変更: step.py export と index.html。たとえば stats を年ごとのファイルにし、亡くなった人・出た人の履歴書を `archive/resumes_YYYY.json` にして、見るときに読む。
- 大きさ: events は archive.py があるのでもう増えない (8 MB)。stats は 1 年 34 KB しか増えない。**増え方の本体 (trust) にはきかない**。
  亡くなった人の履歴書を出しても、生きている人の trust は N 個のまま (生きている人ぶんだけで 4.4 MB、N に比例して増える)。
- 1 バイトも同じ: app_data の形が変わるので、案 A と同じく日で切りかえる。index.html の読み方も変わる。
- ダッシュボード: 亡くなった人を見るたびに別のファイルを読む。動画 (make_video.mjs) も直す。
- 危うさ: 中くらい (アプリと動画の両方を直す)。得るものが小さい。**しない** (案 A のあと、もし要れば)。

### 案 C: season_person.jsonl を年ごとのファイルに分ける 【おすすめ】

- コードの変更:
  - `build_records.py`: `records/season_person/season_person_NNNN.jsonl` (NNNN = season_end_day // 120。控えと同じ数え方) に分けて書く。
    1 つのファイル `season_person.jsonl` は消す。もう作らない年のファイル (村を前のコミットに戻したとき) も消す。中身は同じ行を同じ順に。
  - `records.py`: `person_files(data_dir)` と `person_rows(data_dir)` を足す (`snap_files` と同じ: 前の 1 つのファイルがあればそれ → 年のファイルを年の順に)。
    前の形 (1 つのファイル) の data (data_E3_*・data_E4_*・古いコミットの写し) も読める。
  - 読む人を `records.person_rows()` に変える: build_dashboard.py・econ_report.py・exp4_measure.py・test_records.py・test_g7.py。
  - `columns.json` の説明・HANDOFF.md・docs/dashboard_records_spec.md に「年ごとのファイル」と書く。
- 1 バイトも同じ: やり直しは記録を作らない (SOC_RECORDS=0) ので、state.json・app_data.json・archive/・お題には関係しない。日の切りかえはいらない。
  全部の年のファイルを順につなげると、前の season_person.jsonl と 1 バイトも同じになることを確かめる。
- 大きさ: 1 ファイル 約 0.9〜1 MB (いちばん新しい年)。季節ごとにコミットで書きかわるのは今の年のファイルだけになる (いまは 62 MB のファイルが毎回書きかわる)。
- ダッシュボード: dashboard.html・research.html・tech_tree.html は変わらない (作るツールが同じ行を読むので)。
- 危うさ: 小さい。読む人を 1 人でも直しわすれると、そのツールが「ファイルがない」で止まる (気づきやすい)。
  `git archive ... sim/society/data/records` (exp3/exp4_setup.sh) はフォルダごとなので、そのまま動く。

### 案 D: 圧縮する (app_data.json.gz・season_person.jsonl.gz)

- コードの変更: export と build_records で gzip にして書く。index.html は `DecompressionStream` で読む。make_video.mjs・すべての読む人を直す。
- 1 バイトも同じ: gzip は書き方 (時刻・圧縮の強さ) で中身がかわるので、mtime=0 などで決めないとやり直しの sha が合わない。app_data の形が変わるので日で切りかえる。
- 大きさ: trust の 0 はよく縮むので 1/10 ほどになる。でも **git は圧縮したファイルどうしの差 (delta) がとれない** ので、コミットのたびにリポジトリが大きくなる
  (いまはテキストの差だけ増える。リポジトリはもう 1.5 GB)。中身を git の差で見ることもできなくなる。
- 危うさ: 中くらい〜大きい。**しない**。

### 案 E: Git LFS

- コードの変更: `.gitattributes` に 2 つのファイルを入れ、LFS に移す。
- 問題: LFS は版ごとにまるごと置く。60 MB のファイルを 2 つ、1 時間に 12 回ほどコミットするので、**GitHub の LFS の無料の量 (1 GiB) は 1 時間ほどでなくなる**。
  `git archive` (exp3/exp4_setup.sh・exp3_replay.py の git_extract) は LFS の「指し示しのファイル」しか出さないので、やり直しが動かなくなる。
  GitHub Pages や raw の URL でアプリが読むと、中身ではなく指し示しのファイルが返る。
- 危うさ: 大きい。**しない**。

### 案 F: season_person.jsonl をコミットしない (.gitignore して、要るときに作り直す)

- 記録は季節ごとに state・archive・控えから作り直しているので、ファイルを持たなくても作れる。
- 問題: 控えの一部 (meta の snapshots.git = 52) は git の履歴から読んでいる。手元のない人 (ほかの PC・Web から見る人) が記録を見られなくなる。
  記録は「村の跡」として残す決まり (HANDOFF の記録の節) なので、残すほうがよい。
- 危うさ: 中くらい。案 C で足りるので **しない**。

## 4. おすすめ: 案 A と案 C を、1 回の年の集まりの止まりで入れる

わけ:

- いちばん近い期限は app_data.json (156年ごろ) で、その原因は trust の 0。案 A は数行で 42 MB を消し、N の 2 乗の増え方そのものを止める。
- season_person.jsonl は期限がもう少し先 (164年ごろ) だが、控えと同じ分け方があり、やり直しにかからないので、同じ止まりで入れられる。
- どちらも世界は変わらない。トークンもいらない。

## 5. 入れる手順 (本物の村が年の集まりで止まっているとき)

止めるのは「年の集まりのお題が出て、まだだれも答えていない」ところ (例: 142年の年の集まり = 17039 日目)。この日を D とする。

1. 止まっていることを確かめる: `python3.13 sim/society/step.py who` → `DAY D season False`・`HOLD none`・`MEET 年`。(D + 1) が 120 で割り切れる。
   季節を進めているワークフローが動いていないこと。`git status` で data に書きかけがないこと (最後の歩のコミットが済んでいる)。
2. ブランチを作る。コードを直す:
   - 案 A: step.py に `APP_SLIM_FROM = D` と export の切りかえ (3. の案 A)。
   - 案 C: build_records.py・records.py・読む 5 つのツール (3. の案 C)。
3. 試し (どれも data の写しで。本物の data には書かない):
   - `tools/exp3_replay.py --commits <最後の 2〜3 の歩のコミット>` → state・app_data・archive・お題がみな「同じ」(切りかえ前の日なので)。
   - `tools/test_g7.py` に試しを 1 つ足す: 写しの state の日を D より後にして export → `people[].trust` がない・`resumes[].trust` に 0 がない・ほかの鍵は前と同じ。
     日が D 以下なら、前のコードの app_data.json と sha が同じ。
   - `tools/test_records.py` と `tools/test_archive.py` を回す。写しで `build_records.py` を動かし、年のファイルをつなげたものが前の season_person.jsonl と同じことを見る。
   - 写しで `build_dashboard.py`・`econ_report.py`・`year_report.py` (直前の年) を回し、前と同じ出力になることを見る (dashboard_data.json を前のものとくらべる)。
4. 本物の data で記録を作り直す: `python3.13 sim/society/tools/build_records.py` → `records/season_person/` ができて、`season_person.jsonl` が消える。
   app_data.json は D ではまだ前のまま (切りかえは D の「後」から) なので、ここでは作り直さない。
5. 本人が見てコミット (コード・試し・HANDOFF.md・この文書・`sim/society/data/records`)。コミットの文に「app_data の信頼の 0 を外す (D より後)・season_person を年ごとに分けた」と書く。
6. 年の集まりに答えて、村を続ける。最初の季節のコミットで見ること:
   - app_data.json が 約 22 MB になった。index.html で人の「信頼している人」が出る (0 の人は「―」)。3D と出来事のタブが前と同じに見える。
   - `records/season_person/` で、書きかわったのが今の年のファイルだけ。
   - その歩を `exp3_replay.py` でやり直して「同じ」。
7. もどすとき: コードを戻すのではなく、切りかえの日 (APP_SLIM_FROM) は残す (D より後の歩のやり直しが合わなくなるので)。
   記録は `build_records.py` を前のコードで回せば 1 つのファイルに戻る。

## 6. あとで考えること (いまはしない)

- state.json (49.7 MB) にも同じ trust の表がある (21 MB、1 回だけ)。trust は季節のお題 (characters.py 37 行: 生きている大人への信頼) に使われ、
  世界が読むので、形を変えると state.json もお題も変わる。180年より前に 90 MB には届かない見込みなので、いまはしない。
  するなら「亡くなった人・出た人の名前の 0 を消す」を日で切りかえる案 (お題は生きている大人しか出さないので、お題は同じのはず。試しで確かめる)。
  → 2026-11-06: state.json が 56.6 MB になったので、0 をみな外す案を作った (`docs/society_phase/state_size_plan.md`。印 `trust_sparse`・`step.py slim_trust`。147年の年の集まり = 17639 日目に入れる)。
- `ledger.jsonl` (13 MB、1 年 約 0.14 MB)・`season_household.jsonl` (10.6 MB) はまだ小さい。要れば案 C と同じ分け方ができる。
- 履歴に残った大きいファイル (前の 60 MB の版) は消さない。100 MB の上限は 1 つのファイルごと・プッシュのときなので、履歴にあるものは問題にならない。
  リポジトリ全体 (pack 1.5 GB) は、案 A・C で季節ごとに増える量が小さくなる。

## 7. 入れたこと (2026-11-05。142年の年の集まり = 17039 日目で止めて。コミットは本人)

### 案 A: app_data.json の信頼の表から 0 を外す

- `step.py`: `APP_SLIM_FROM = 17039` と `app_slim(state)`。軽い形にするのは **17039 日目より後の日はいつも、17039 日目は state に印 `app_slim` があるときだけ**。
  軽い形: `people[]` に `trust` を入れない・`resumes[].trust` は 0 でないものだけ。ほかの鍵は 1 バイトも同じ。
- 印にしたわけ: 17039 日目の app_data.json は、その日を作った歩 (17009 日目から。e3e9c684) が書いた。日だけで切りかえる (`day >= 17039`) と、その歩のやり直しで app_data が「ちがう」になる。
  `day > 17039` だけにすると、17039 日目の app_data.json は前の形 (66 MB) のままコミットすることになる。
  そこで G10 の直し (`g10.G10_FIX_FROM` と印 `g7.g10.fix`。`refresh_prompts` が書く) と同じに、その日は印があるときだけにした。
- 新しいコマンド `step.py slim_app --why "<わけ>"`: 17039 日目 (APP_SLIM_FROM) の歩で、止まっていなくて、その日の答え (season・feeling・council) がまだないときだけ、
  印 `state["app_slim"] = {"day", "why"}` を書き、app_data.json と記録を作り直す。お題・日・世界は変えない (印は export だけが読む)。答えがあれば・ほかの日なら断る (終わりのコード 3)。
- `app/index.html` 442 行: 「信頼している人」は `r.trust || {}` の 0 でないものだけ (なければ「―」)。前の形の app_data.json でも同じ見え方。
- 試し: `tools/test_g7.py T_AppSlim` (切りかえの日と印・slim_app の前後で people と resumes の trust のほかは同じ・答えがあれば断る)。

### 案 C: season_person.jsonl を年ごとのファイルに分ける

- `records.py`: `PERSON_FILE`・`PERSON_DIR`・`person_path`・`person_files`・`person_lines`・`person_rows` (前の 1 つのファイルがあればそれ → 年のファイルを年の順に。控えの `snap_files` と同じ)。
- `tools/build_records.py`: `write_person` が `records/season_person/season_person_NNNN.jsonl` (NNNN = season_end_day // 120) に書く。中身が同じ年のファイルは書かない。
  もう作らない年のファイルと、前の 1 つのファイル `season_person.jsonl` は消す。行が日の順に並んでいなければ止める。`columns.json` の説明に年ごとのファイルと書いた。
- 読む人を `records.person_rows` / `person_lines` に: `build_dashboard.py`・`econ_report.py`・`exp4_measure.py`・`test_records.py`・`test_g7.py` (G_Flow)。`year_report.py` は読まない (変えていない)。

### 本物の data に入れたこと

- `python3.13 sim/society/step.py slim_app --why "app_data.json と season_person.jsonl が大きくなった (docs/society_phase/data_size_plan.md の案 A・C)"` (state.json を手で直していない)。
- 確かめ: state.json は印 `app_slim` のほかは HEAD と同じ。prompts/day17039 の 62 通は sha256 が前と同じ。answers/day17039 は空のまま。
  年のファイル 138 (4〜141年) をつなげると前の season_person.jsonl (62,502,300 バイト) と 1 バイトも同じ。records/ のほかのファイルは columns.json (説明の 1 行) のほかは同じ。
  新しい app_data.json は、前のものから people の trust を消し、resumes の trust の 0 を外したものと同じ (0 でない組は 17)。
  `step.py who` → DAY 17039・MEET 年・HOLD none。
- やり直し (`tools/exp3_replay.py --work /tmp/rp`): 8dcf9d30 (14969)・e3e72933 (16979)・e3e9c684 (17009) はみな state・app_data・archive・次のお題が同じ。
- 試し: `test_g7.py T_G10FIX・T_AppSlim`・`test_archive.py`・`test_hints.py` はみな通る。`test_records.py` (M_Accounts.test_same_python を除く。メモリが足りないのでクラスの組ごとに別のプロセスで) は、落ちるのは HEAD と同じ 16 (B_KnownValues・B_Prompts・C_Ledger・H_Performance・E_Boundaries 2・J_Grounding 2・M_Accounts 4・I_Pasture 2・L_AskWhy・M_Accounts.test_same_as_before (polity・tribute のファイルが前のコードにないため。HEAD を写した git のない場所では飛ばされたが、わけは今度の直しと関係ない))。`D_Determinism` の比べ方は年ごとのフォルダも読むように直した。
- 写しで、前の形 (1 つのファイル) と新しい形の records から作った build_dashboard の中身は同じ。econ_report は HEAD でも動かない (`era2._season_end の書き方が変わった`。前からのこと)。

| ファイル | 前 (HEAD、17039 日目) | 後 |
|---|---|---|
| app_data.json | 66,360,138 | 23,792,951 |
| records/season_person.jsonl | 62,502,300 | (消した) |
| records/season_person/ (138 ファイル) | | 合わせて 62,502,300。いちばん大きいのは 141年の 946,195 |
| state.json | 52,639,022 | 52,639,167 (印の分だけ) |

- **次**: 本人が見てコミット (`sim/society/step.py`・`records.py`・`app/index.html`・`tools/` の 7 つ・`HANDOFF.md`・この文書・`sim/society/data` (state.json・app_data.json・records/)。
  `records/season_person.jsonl` は消したので `git add -A sim/society/data/records`)。そのあと 17039 日目の年の集まりに答えて村を続ける。最初の季節のコミットで 5. の 6. を見る。

