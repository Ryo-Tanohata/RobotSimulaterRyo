# 社会シミュレーション: 1 回の実行の手順 (スケジュール実行・手動実行の Claude 用)

1 回の実行で、**フェーズが進むまで、最大 20 日分**進める。計画は `docs/society_phase_plan.md`。
**パソコンのシャットダウンや、この手順にないスケジュールの変更はしない。**
**日付の書き方** (2026-10-09、本人の希望): アプリ・動画・ナレーションなど本人に見せるものでは「10年31日目」と書く (2026-10-09 に「11 年目 31 日目」から変えた。本人「動画での表記は◯年◯日目が良かった」。年は過ぎた年の数で、最初の年は 0年 = era2.py の day // YEAR。この世界の 1 年は 120 日 = 季節 30 日 × 4。`app/replay3d.js` の `dayLabel`)。現実の 1 年より短いので、日付を最初に出すところに注釈をつける。評価の下書きなどの文書では「10年31日目 (1230 日目)」と通しの日もそえる。お題・コミット・run_log は通しの「N 日目」のまま (記録の番号として使う)

## 0. 準備

```bash
git pull
python3 sim/society/step.py status
```

- 「一時停止中」と出たら、何も進めずに 6 (記録) だけ行って終わる (本人の評価待ち)
- 段階が `evening` や `night` のときは、その段階から続ける (前回途中で止まった日)

## 1 日分の進め方 (これを最大 20 回くり返す)

### 1. 1 日を進める

```bash
python3 sim/society/step.py day
```

終了コードが 3 なら一時停止中、4 なら生きている人がいないので、くり返しをやめて 5 へ (どちらも再開は本人の判断)。

### 2. 夕方 (話す・分ける・蓄える)

`sim/society/data/prompts/dayNNN/evening/` の `名前.md` ごとに、**1 人ずつ別のサブエージェント** (Agent ツール、`model: haiku`) を起動する。
1 つのサブエージェントには 1 人分のお題だけを渡す。5 人分は同時に起動してよい。指示は次の文のとおり (パスは置き換える):

> Read `sim/society/data/prompts/dayNNN/evening/名前.md` and follow its instructions exactly: role-play that character and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to `sim/society/data/answers/dayNNN/evening/名前.json` with the Write tool. Do not read any other files. Reply "done".

そろったら `python3 sim/society/step.py evening`

### 3. 夜 (振り返り・知識と掟・明日の予定)

2 と同じやり方で `prompts/dayNNN/night/` のお題を渡し、答えを `answers/dayNNN/night/名前.json` に書かせる。そろったら:

```bash
python3 sim/society/step.py night
```

「フェーズが … に進んだ → 一時停止」と出たら、くり返しをやめて 4 へ。

### その日の保存 (コミットだけ。push はしない)

```bash
git add sim/society/data
git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com \
  commit -q -m "社会シミュレーション: N 日目" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

GitHub への push は、実行の最後 (6) に 1 回だけ行う (本人の希望)。

## 4. フェーズが進んだとき: 評価の下書き

終わったフェーズ (例: F2 に進んだなら F1) の評価の下書きを `docs/society_phase/F1.md` に書く。
材料は `state.json` の `era_log` (進んだ日と指標)、`events`、`knowledge_log`、`laws`、`stats`。書くこと:

1. 期間 (何日目から何日目まで) と、フェーズが進んだ決め手 (指標の数字)
2. このフェーズで起きた主な出来事 (日付つき、記録にあることだけ)
3. 通説との比較 (`docs/society_phase_plan.md` 2 章の表): 通説どおりだった点 / 違った点
4. 模倣と創発: そのフェーズで生まれた知識と掟のラベルの内訳と、目立った例
5. 気になった点 (世界の仕組みの不足、不自然な行動など)

**シミュレーションは止めたまま**にする (再開は本人の評価のあと)。

## 5. アプリを更新する (実行の最後に 1 回)

Artifact ツールで、アプリを同じ URL のまま更新する:

- `url`: https://claude.ai/artifact/QuYyaTsj7d7JyNnnL64GfV
- `file_path`: `sim/society/app/index.html`
- `files`: `{"app_data.json": "sim/society/data/app_data.json", "replay3d.js": "sim/society/app/replay3d.js"}` に加えて、この実行で書いたり直したりした評価の文書を、同じ道筋で入れる (例: `"docs/society_phase/F3.md": "docs/society_phase/F3.md"`)。アプリの「記録と評価」タブで読める

公開が「新しい版がある」と断られたら、公開中のページと app_data.json を読んでから、もう一度公開する。

Artifact ツールがないセッション (クラウドなど) では、この手順は飛ばしてよい。6 の `git push` で、
Cloudflare Pages の本人だけが見られるページ (README「結果を見るページ」) も新しくなる (2026-10-05 更新。GitHub Pages での公開はやめた)。

## 6. 記録

`sim/society/data/run_log.md` の末尾に 1 行追記してコミットし、ここで初めて `git push` する (この実行のすべての日のコミットがまとめて上がる):
日時・何日目から何日目まで進んだか・止まった理由 (フェーズが進んだ / 20 日に達した / 失敗)・今のフェーズ・目立った出来事。

## 失敗したとき

- 途中で止まっても、`state.json` の段階から続きをやり直せる。無理に続けず、そこまでをコミットし、記録に残して **push してから** 終わる (push しないと、その分は失われる)
- 答えの JSON が壊れていても `step.py` は読める部分だけ使う。同じ人のサブエージェントを 1 回だけやり直してよい
- 世界の状態やシミュレーションのコードを手で書き換えない

## Society 2.0 (2026-10-07 から): 1 回 = 1 季節

計画は `docs/society2_phase_plan.md`。`python3 sim/society/step.py start2` で始めた (489 日目)。

1. `sim/society/data/prompts/dayNNN/season/` のお題を、大人 1 人に 1 体のサブエージェント (haiku) に渡し、答えを `answers/dayNNN/season/名前.json` に書かせる (子は答えない)
2. そろったら `python3 sim/society/step.py season` (30 日進む。蓄えが尽きると途中で区切る)
3. その回をコミット (push はしない): `社会シミュレーション: N 日目 (季節)`
4. 20 回ごとに記録 (run_log・G?_notes) を書いて push。フェーズが進んだら (一時停止)、報告・評価の下書き・動画のあと `resume` して続ける
   - 動画の撮影は数時間かかるので、`app_data.json` の写しを固定して (`DATA_DIR=写しのフォルダ`) 撮り始めたら、撮り終わるのを待たずに `resume` してよい (写しから撮るので、動画の中身は変わらない。2026-10-08)

## 全員が亡くなった・立ち行かなくなったとき (2026-10-07、本人の決まり)

本人: 「A でお願いします。今までもそのようなことがあったら同じように戻していたと思います。今後もそのようにして下さい」

- 相談せずに、そのフェーズの始まり (または原因の前の日) のコミットに `state.json` を戻し、世界のつくり・お題を見直してやり直す
- 戻す前の日の `answers/`・`prompts/` と最後の `state.json` は `data_archive/<フェーズ>_try<回>_d<始め>-<終わり>/` に移して残す
- 何を変えたか・なぜか・出典 (仮定なら【仮定】) を、フェーズのメモ (`*_notes.md`) と `run_log.md` に書く。通説と比べるときの注意も書く
- 本番の前に、写し (`SOC_DATA=/tmp/...`) で、決まった答え方を何通りか回して、すぐに全員が亡くならないかを確かめる
- やり直したことは、次の報告でまとめて伝える
- G5 で家が村を出ていく (村が分かれる) のは起きてよい結果。戻してやり直さない (全員が亡くなったときだけ戻す)。G5 で 8 季節たってももめごとが 0、第 2 段に入って 8 季節たってもまとめ役がいない・罰のある掟が 0 のときは、5 季節ごとの報告で本人に相談する (相談なしに世界やお題を変えない)

## 2026-10-08 本人と決めたこと (Society 2.0 の進め方)

- Society 2.0 は大きすぎるので、学説と史実をもとに、いくつかの部に分ける (分け方は `docs/research/society2_periodization.md` を見て本人と決める)
  - 決まった (2026-10-08): 4 部 (村と畑 G1・G2 / 土器と家の倉 G3・G4 / まとめ役と神殿 G5 / 町と文字 G6)。G4 からジニ係数の条件を外す (直した)。G5 は 2 段階。G6 の町と記録は別々の条件。中身は `docs/society2_phase_plan.md` の 2.1。部の終わりには止まって、まとめ・通しの動画・次の部の相談をする
- 5 季節ごとに、短い文の報告とグラフ 1 枚を本人に見せる
- フェーズごとの動画は 8〜9 分 (今まで通り)
- 作業は本人の PC (内蔵 GPU で撮影) で続ける。引き継ぎは `HANDOFF.md`
- フェーズ (G1〜G6) が進むたびに、すぐ push する (2026-10-08 本人の希望。G は Society 2.0 のフェーズの番号で、F の次の字。generation の意味ではない)
- G の中の小さな区切り F (計画 2.2): F に入ったら (出来事「区切り」)、その F の動画 (3〜4 分) を作って送る。G が進んだら、G の動画 (8〜9 分) を作って送る。どちらも止まらずに撮る (写しのデータで)
