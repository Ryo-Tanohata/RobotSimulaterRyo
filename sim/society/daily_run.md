# 社会シミュレーション: 1 回の実行の手順 (スケジュール実行・手動実行の Claude 用)

1 回の実行で、**フェーズが進むまで、最大 20 日分**進める。計画は `docs/society_phase_plan.md`。
**パソコンのシャットダウンや、この手順にないスケジュールの変更はしない。**

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

Artifact ツールがないセッション (クラウドなど) では、この手順は飛ばしてよい。GitHub Pages を有効にしてあれば、
6 の `git push` で https://ryo-tanohata.github.io/RobotSimulaterRyo/sim/society/app/ も新しくなる (2026-10-02 追加)。

## 6. 記録

`sim/society/data/run_log.md` の末尾に 1 行追記してコミットし、ここで初めて `git push` する (この実行のすべての日のコミットがまとめて上がる):
日時・何日目から何日目まで進んだか・止まった理由 (フェーズが進んだ / 20 日に達した / 失敗)・今のフェーズ・目立った出来事。

## 失敗したとき

- 途中で止まっても、`state.json` の段階から続きをやり直せる。無理に続けず、そこまでをコミットし、記録に残して **push してから** 終わる (push しないと、その分は失われる)
- 答えの JSON が壊れていても `step.py` は読める部分だけ使う。同じ人のサブエージェントを 1 回だけやり直してよい
- 世界の状態やシミュレーションのコードを手で書き換えない
