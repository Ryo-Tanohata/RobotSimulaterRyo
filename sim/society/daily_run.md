# 社会シミュレーション: 1 日分を進める手順 (スケジュール実行の Claude 用)

この手順で、世界を 1 日分進めてアプリを更新する。計画は `docs/society_plan.md`。
**パソコンのシャットダウンや、この手順にないスケジュールの変更はしない。**

## 0. 準備

```bash
git pull
python3 sim/society/step.py status
```

`status` の「段階」で始める場所が決まる (途中で止まった日は、続きから):
- `day` → 1 から
- `evening` → 2 から
- `night` → 3 から

## 1. 1 日を進める

```bash
python3 sim/society/step.py day
```

## 2. 夕方 (各キャラクターが話すこと・分けること)

`sim/society/data/prompts/dayNNN/evening/` にある `名前.md` ごとに、**1 人ずつ別のサブエージェント** (Agent ツール、`model: haiku`) を起動する。
互いの心の中が混ざらないように、1 つのサブエージェントには 1 人分のお題だけを渡す。5 人分は同時に起動してよい。サブエージェントへの指示は次の文のとおり (パスは置き換える):

> Read `sim/society/data/prompts/dayNNN/evening/名前.md` and follow its instructions exactly: role-play that character and produce ONLY the JSON object it asks for. Write that JSON (nothing else) to `sim/society/data/answers/dayNNN/evening/名前.json` with the Write tool. Do not read any other files. Reply "done".

全員分の答えのファイルがそろったら (欠けた人は何もしなかった扱いになる):

```bash
python3 sim/society/step.py evening
```

## 3. 夜 (振り返り・知識と掟・明日の予定)

2 と同じやり方で、`prompts/dayNNN/night/` のお題を 1 人ずつサブエージェントに渡し、答えを `answers/dayNNN/night/名前.json` に書かせる。そろったら:

```bash
python3 sim/society/step.py night
```

これでアプリ用のデータ `sim/society/data/app_data.json` が更新される。

## 4. アプリを更新する

Artifact ツールで、アプリ (下の URL) を同じ URL のまま更新する。ページ本体は変えず、データのファイルだけを差し替える:

- `url`: https://claude.ai/artifact/QuYyaTsj7d7JyNnnL64GfV
- `file_path`: `sim/society/app/index.html`
- `files`: `{"app_data.json": "sim/society/data/app_data.json"}` (歩く動画 walk.mp4 は公開済みなので送らない)

## 5. 保存する

```bash
git add sim/society/data
git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com \
  commit -m "社会シミュレーション: N 日目" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

## 6. 記録

`sim/society/data/run_log.md` の末尾に 1 行追記してコミットする:
日付・何日目まで進んだか・起動したサブエージェントの数・目立った出来事 (死・掟の採用・種から育つ など)・失敗したこと。

## 失敗したとき

- 途中で止まっても、`state.json` の段階から続きをやり直せる。無理に最後まで進めず、そこまでをコミットして記録に残す
- 答えの JSON が壊れていても `step.py` は読める部分だけ使う。同じ人のサブエージェントを 1 回だけやり直してよい
- 世界の状態を手で書き換えない
