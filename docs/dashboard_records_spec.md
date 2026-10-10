<!-- 仕様書 (まだリポジトリのコードにはしていない)。2026-10-09、クラウドのセッションで書いた。
     材料: era2.py・world.py・step.py・docs/dashboard_data_model.md (1.・2. の表と 5. 本人と決めたこと)・docs/research/modern_records.md 7.6・docs/research/historical_records.md 5.
     数は、本物のデータ (state.json と、git に残る季節ごとの state.json) を読むだけで確かめた (この文書の 0.)。試しの書きものは /tmp に置き、
     季節を 1 回進める時間は写し (SOC_DATA=/tmp/...) で測った。リポジトリのコードとデータは変えていない -->

# ダッシュボードの内側の記録: 作り方の仕様書 (日本語の要約)

本人と決めたこと (2026-10-09。`docs/dashboard_data_model.md` の 5.) を、記録のファイルにするための仕様。ダッシュボードの見せ方 (画面) は、この記録ができてから相談する。ダッシュボードに出すのは村の人の記録だけ (記録がない時代は、考古学の証拠を今の言葉で説明する) と決めたので、記録は内側で全部そろえておき、何を見せるかは見せる側で決める。

**作るもの** (`sim/society/data/records/` に新しく作る。state.json・答え・お題は変えない)
- **人** (`people.json`): 番号 (P001〜)、名前・男女・生まれた日・村に来た日と来かた・親・亡くなった日と死因の種類 (飢え・ザガ・病・年・子・その他。出来事「死」の文から読む)・村を出た日
- **家** (`households.json`): 番号 (H01〜)、名前・できた日・終わった日
- **だれがどの家に、いつからいつまでいたか** (`membership.json`): 入ったわけ (はじめから・生まれた・よそから来た) と出たわけ (亡くなった・飢えで村を出た・家ごと村を出た など)
- **季節ごとの行** (1 行 = 1 季節): 村 (`season_village.jsonl`)・家 (`season_household.jsonl`)・人 (`season_person.jsonl`)。たたき台の ②③④ の列と、⑤ フェーズの条件の進み具合 (条件ごとの今の値・目標・そろったか。村の行の中)
- **出し入れの帳簿** (`ledger.jsonl`): 家 (と村) × 季節 × 物 × 理由。「季節のはじめの残り + 入った − 出た = 季節の終わりの残り」がたどれる。合わない分は「記録にない差」の行にする
- **年の名前** (`year_names.json`)
- **季節の終わりの控え** (`snapshots.jsonl`): 今の値しか残らないもの (家ごとのヤギ・家の倉の中身・持ち物・技能・空腹・土器・鎌・条件の値など) を、季節が終わるたびに 1 行ずつ書き足す (書き足すだけで、書きかえない)
- **列の説明** (`columns.json`): 列ごとに、意味・単位・出どころ・「だれが知りうるか」の札 (【調】あとから調べる人に分かる /【シ】シミュレーションだから分かる /【村】村の人がつけた記録。G6 から)
- 気持ち・言葉・性格は記録に入れない (決めた通り、今のアプリの欄に日付つきで残る)。記録には「答えたか」「何回話したか」だけを入れる

**過去の分**: 大きな見つけもの。季節を進めるたびに state.json を git にコミットしてきたので、Society 2.0 のすべての季節の終わり (始まりの 489 日目と、509〜2009 日目の 51 回) の state が git に残っている。これはその日の本当の値の記録なので、1 回だけ git から読み出して控えに入れれば、たたき台で「×」(今の値しかない) だった列 (家ごとのヤギ・家の倉・持ち物・技能・空腹・村の蓄えへの出し入れ) も、過去の分がそろう。git が使えないときは、出来事・答え・お題から組み立てられる分だけ作り、残りは空 (null) にする。

**確かめたこと** (読むだけ。くわしくは 0.)
- git の 52 回分の state は、どれも今の state.json の出来事とつながっている (取りやめた G1 の 1 回目は入らない)
- 帳簿は、**家の倉 (草の種)・ヤギ・土器・鎌は、51 季節すべてで「記録にない差」が 0** になった。刈った草の種は、畑ごと・入った倉ごとに組み立て直せる。ヤギは 1 頭ずつの番号で追える
- **村 (村の蓄え + 大人の手元の食べ物)** は、全体では 1 季節に 100 kcal (木の実 1 つかみ) 以内で合った。物ごとには、木の実・草の種・芋で 1 季節に最大 32 つかみ (本) ほどずれる。採集の出来事が、量を物ごとに整数に丸めて書いているため (合計は正しいが、どの物が半端だったかは記録にない)。このずれは「記録にない差」の行に出る
- 知っている値と合った: 14年30日目 (1709 日目) 22 人 (大人 15・子 7)・家族 8・ヤギ 10 頭・土器 340 個・鎌 34 本・ナギの家の倉 草の種 7,795 つかみ。15年60日目 (1859 日目) 25 人・家族 9・ヤギ 17 頭
- **ちがいが 1 つ**: 頼まれた文には「1859 日目のナギの家の倉 7,795 つかみ」とあったが、記録では 7,795 つかみは 1709〜1799 日目の値で、1859 日目は **12,137 つかみ** (15年の夏に 4,342 つかみ刈って足した。1829・1859 日目のお題にも 12,137 とある)。試しは記録の値で確かめる
- 季節の集まりの出来事は、前の季節の終わりの日の日付で記録されている。どこからが集まりかは、出来事の種類と文で 51 回とも正しく分けられた (git の値とくらべた)

**世界を変えない**: 記録は、季節が終わったあとに state を読むだけで作る (乱数も使わない)。step.py は、季節を進めて保存したあとで、控えを 1 行足し、記録を作り直す。記録を作るのに失敗しても、季節は進んだまま止まらない (終わりのコードも変わらない)。写しで、前のコードと新しいコードに同じ答えを渡して何季節も回し、state.json とアプリのデータが 1 バイトも違わないことを確かめる。

**年の名前** (今から): 1 年に 1 回、年の終わりの季節の集まり (春の終わり。次は 2039 日目) のお題に「年の名前」の節を足す。この 1 年 (次なら 1920〜2039 日目) のおもな出来事を見せ、家族の代表 (とまとめ役) が、その年いちばん大きな出来事で名前をつける (答えの year_name)。同じ名前を書いた人の、家族の大人の数を足して、いちばん多い名前に決まる。同じなら、名前を書いた人でいちばん年上の人の名前。決まると出来事「年の名前」が残り、state の era2 の year_names に入る。決まった名前は、そのあとの季節のお題と気持ちのお題に「村で覚えている年の名前」として出る (まだ 1 つもないうちは、お題は今と同じ)。だれも名前を書かなければ、名前はつかず、state も出来事も今とまったく同じ。

**年齢の区分**: 乳飲み子 0〜2・子 3〜11・手伝える子 12〜14・大人 15〜54・年寄り 55〜 (境目は仮)。記録の行には区分と、内側の記録としての正確な年齢の両方を持つ。

**かかる時間** (見込み): 記録を全部作り直すのに 2〜3 秒 (17 MB の state を読むのに約 0.5 秒。季節を 1 回進めるのは今 約 11 秒)。git から過去の控えを作るのは 1 回だけで、約 20〜30 秒。

**本人に確かめること** (おすすめを先に書いた)
1. 過去の分に、git に残る季節ごとの state.json を使う (**おすすめ**) / 使わない (家ごとのヤギ・家の倉・技能・空腹などの過去の分は空になる)
2. 記録のための書きとめを、世界の仕組みの中に 3 か所だけ入れる (**おすすめ**): 家の人が家の倉から食べた量・子が家の倉から食べた量・よその家の倉から取った量。今は出来事に残らない (取ったのは 1 季節の 1 回目だけ) ので、入れないと、村の蓄えが尽きた季節に、家の倉の帳簿が「記録にない差」になる。書きとめるだけで、state.json にも世界の進み方にも何も足さない / 入れない
3. 帳簿の「村」には、大人の手元の食べ物もふくめる (**おすすめ**)。日々の「蓄えに入れる・取る」は村の決まりで自動に行い、物ごとの量は記録に残らないため。家ごとの「村の蓄えに入れた・取った」(G5 から。草の種にした量) は、帳簿にメモの行として残す
4. 年の名前は、半分をこえなくても、いちばん多い名前に決める (**おすすめ**。答えは自由な文なので、同じ名前がそろうことは少なく、「半分をこえたら」にすると、ほとんどの年に名前がつかない) / 大人の半分をこえたときだけ決める
5. 年の名前のお題に、この 1 年のおもな出来事 (15 まで) を見せる (**おすすめ**) / 見せない (覚えていることだけで決める)
6. お題の中では、年を「1920〜2039 日目の年」のように日で書く (**おすすめ**。今のお題は日の数で書いているので)。「16年」という数え方は記録の中だけ
7. 記録のファイル (records/) も、季節ごとにデータといっしょにコミットする (**おすすめ**。season_step.sh は data/ をまとめてコミットするので、そのまま入る。1 季節に 60〜80 KB ふえる)
8. もめごと (⑧) と掟 (⑦) の小さな写しも records/ に作る (**おすすめ**。ダッシュボードが 16 MB のアプリのデータを読まなくてすむ)

**作った (2026-10-09 夜、クラウド)**: 本人は引き継ぎのため不在だったので、1・3〜8 はおすすめの通りで作った。2 (世界の仕組みの中の書きとめ) は入れていない (村の蓄えが尽きた季節に、家の倉の帳簿が「記録にない差」になる)。本人が違う方を選んだら直す。確かめは 8. の試し (tools/test_records.py、24 通る) と、前のコードとの比べ (世界は同じ)。

(もとの予定) 次にすること: 1〜8 を決めてから、この文書の 7. のコードを入れ、8. の試し A〜H で確かめる。そのあと 1 回だけ、過去の控えを git から作り (records/ に足すだけ)、記録を作る。見せ方 (ダッシュボードの画面) は、記録ができてから相談する。

---

# Dashboard records: implementation spec (English details)

Scope: internal records for the dashboard (decisions of 2026-10-09 in `docs/dashboard_data_model.md` §5). Hard rule: **the world must not change** — same RNG draws, same outcomes, same `state.json` bytes — except, for year names only, the new optional answer field `year_name`, the new event type 「年の名前」, the new key `state["era2"]["year_names"]` and extra prompt text, all of which appear only when a name is actually given.

Code layout (all new code is stdlib-only, like the rest of `sim/society`):

| File | Status | What |
|---|---|---|
| `sim/society/records.py` | new | snapshot capture (read-only), snapshot loading/validation, age classes, death causes, day labels |
| `sim/society/tools/build_records.py` | new | deterministic builder (CLI + `build()`) |
| `sim/society/tools/backfill_snapshots.py` | new | one-time: past snapshots from git history |
| `sim/society/tools/test_records.py` | new | tests A–H (unittest; long A/B runs behind a flag) |
| `sim/society/era2.py` | changed | `meeting_first`, `CRITERIA_PARTS`/`criteria_progress`, year names, optional `LEDGER_NOTES` |
| `sim/society/step.py` | changed | snapshot after a season, run the builder, print the year-name event |
| `world.py`, `characters.py`, `knowledge.py`, `resume.py`, app, `season_step.sh`, workflow | unchanged | |

---

## 0. What was verified (read-only, on the real data)

Prototype scripts lived in `/tmp` (not in the repo). Nothing under `sim/society/data` was written; `sha256(state.json)` was unchanged afterwards. One `step.py season` and one `step.py export` were timed on a scratch copy (`SOC_DATA=/tmp/rec/scratch`).

| Check | Result |
|---|---|
| Season-end states in git | `git log -- sim/society/data/state.json` in `875cd15..HEAD` (after the reset of the abandoned G1 run 1) has a commit for day 489 (start, `f96d8f9`) and for every season end 509…2009 (52 states). Days 1229, 1529, 1559, 1589, 1709 have two commits (the season run, then a 「再開」/お題の作り直し commit); the **first** is the season output. For all 52, the state's last event equals the current state's event with the same id (lineage OK). Reading all 52 states: 15–25 s. |
| Event ids | `state["events"][i]["id"] == i` for all 40,988 events, `next_event == len(events)`. |
| Meeting boundary | A meeting's events are dated with the previous season-end day and come after that day's season-end events. The rule in §3.4 reproduces the exact boundary (`next_event` of the git state) for all 51 meetings 489…1979. |
| Representatives | For all 51 meetings the season answer file names equal the answerers derived from the git state (all adults before 1259; from 1259 the oldest adult of each household, ties by people order). |
| Criteria parts | `CRITERIA_PARTS` (§7.2) agrees with the `CRITERIA` lambdas on every indicator set kept in `era_log` and `era_info` (5 sets × 5 eras). |
| Harvest replay | Replaying 収穫 events against the fields that were 実った at the previous season end (§4.3) reproduces every field's final `harvested` for all 12 summers 629…1949. |
| House stores (草の種) | start + 刈った + つぐない受け取り − つぐない払い − 虫 = end, residual **0** for every house in all 51 seasons. 1709: ナギの家 0 + 7,798 − 2.74 = 7,795.26. 1829: ナギ +4,342, トワ +8,684. 1859: トワ −14 → ケト +14 (M1). 1949: トワ +5,692, 川辺 +6,798, ユノ +4,094. 1979: 川辺 −247 → トワ +247 (M2). |
| Goats by id | Each season: new ids (`next_goat` difference) = caught events + kids born; ids that disappeared = the count in 「いなくなった」 events; residual **0** in all 51 seasons. |
| Pots, sickles | made (`土器`/`道具` events, `data.count`) − broken (「割れた」 events) closes exactly in all 51 seasons. |
| Village food (store + adults' hands) | Total residual ≤ 100 kcal per season (1079, 1979: ±100; rounded feast words). Per item ≤ 32.4 木の実 / 19.2 草の種 / 18.9 芋 units per season, because 採集 events write each kind rounded to whole units (the exact total is in `data.kcal`, the split is not); 38 of 51 seasons have some item off by ≥ 1 unit. |
| Known values | 1709 (14年30日目): 22 people (15/7), 8 households, 10 goats (6 ♀), 340 pots, 34 sickles, store 草の種 168,396 / 木の実 6,465 / 芋 18, 323 store-days, ナギの家 7,795.26, 12 fields ripe, 50,400 harvested, 30,518 fallen (1,270 + 4 × 7,312), ヨナ 72 pots in 30 days of 土器づくり and 30 tree picks, skill 土器 1.0. 1859 (15年60日目): 25 people (16/9), 9 households, 17 goats (9 ♀), 614 pots, 24 sickles, 339 store-days, ナギの家 **12,137.26**, トワ 8,670, ケト 14. 2009: 27 people (16/11), 9 households with adults + ユノの家 (children only), 32 goats (22 ♀), 554 pots, 22 sickles. **Discrepancy:** the task statement gives "Nagi house store 7,795 at day 1859"; the records show 7,795.26 for 1709–1799 and 12,137.26 for 1829–2009. Tests use the recorded values. |
| Timing | `json.load` of state.json ≈ 0.5 s; replay + ledger prototypes for all 51 seasons ≈ 0.2 s more; `step.py export` ≈ 7 s; one `step.py season` ≈ 11 s. |

---

## 1. Storage: `sim/society/data/records/`

Path is `DATA / "records"` (`DATA` from step.py, so `SOC_DATA` copies get their own records). The real `sim/society/data/records/` is the only thing this work may add under `sim/society/data`.

### 1.1 Files

| File | Rows (now) | Written by | Kind |
|---|---|---|---|
| `snapshots.jsonl` | 1 per round end (52 after backfill) | step.py after each season; backfill tool once | **input**, append-only, never rewritten |
| `people.json` | 1 per person ever in the state (35) | builder | derived |
| `households.json` | 1 per household (10) | builder | derived |
| `membership.json` | 1 per person × household stay (35) | builder | derived |
| `season_village.jsonl` | 1 per season end (51) | builder | derived |
| `season_household.jsonl` | 1 per season × household with a living member (~330) | builder | derived |
| `season_person.jsonl` | 1 per season × person present (~750) | builder | derived |
| `ledger.jsonl` | season × holder × item × reason (~5,000) | builder | derived |
| `year_names.json` | 1 per year since year 4 | builder | derived |
| `laws.json`, `disputes.json` | 151 / 3 (extras, §1.11) | builder | derived |
| `columns.json` | 1 per column | builder (static table) | derived |
| `meta.json` | 1 object | builder | derived |

Only `snapshots.jsonl` holds information that exists nowhere else. Every other file can be deleted and rebuilt byte-identically.

Size now ≈ 3–4 MB; each season adds ≈ 15 KB of snapshot + 50–60 KB of derived rows.

### 1.2 Conventions

- **Days** are state days. `day_label(d) = f"{d // 120}年{d % 120 + 1}日目"`, `season_label(d) = f"{d // 120}年の{world.season(d)}"` (1709 → 「14年30日目」「14年の夏」). Year y = days 120y … 120y+119 = 夏・秋・冬・春.
- **Season key** `season_end_day` D with (D+1) % 30 == 0, covering D−29 … D. The first Society 2.0 season is 490…509 (`days: 20`).
- **Meeting attribution**: the meeting held at state day D−30 (events dated D−30) opened season D and belongs to season D's row (answers in `answers/day{D−30}/`). §3.4.
- **IDs** (derived, never written into the state): persons `P001`… in `state["people"]` order (the list is append-only; nothing removes people); households `H01`… by first appearance of the household name in that order (H01 川辺の家, H02 ナギの家, H03 ケトの家, H04 トワの家, H05 ユノの家, H06 フウの家, H07 アルの家, H08 クラの家, H09 セキの家, H10 スイの家); holder `"村"` for the village; laws `L…`, disputes `M…`, event ids and goat ids as in the state. A household named `"-"` (era2 `_house(state, None)`) never had contents; if it ever does, it becomes holder `H00` 「家のない人」.
- **Units** (item → unit, kcal per unit): 草の種 つかみ 80 · 木の実 つかみ 100 · 芋 本 250 · 干し肉 切れ 500 · 肉 (ルクの肉) 切れ 600 · 魚 匹 300 · ピク (ピクの肉) 匹 800 · 乳 (ヤギの乳) 杯 150 · ヤギ 頭 · 土器 個 · 鎌 本. Food rows also carry exact `kcal`.
- **Numbers**: unit amounts and kcal rounded to 2 decimals at output (computation in full float); counts are ints; ratios 3 decimals.
- **null vs 0**: `null` = not known (not recorded, or no snapshot); `0` = known zero. Every season row has `snapshot: true/false` (whether end-of-round state values came from a valid snapshot).
- **Tags** (in `columns.json`, historical_records.md §5.1): 【調】 knowable by a later archaeologist/historian (bones, house sizes, goat bones, sickles, pots, field counts), 【シ】 only the simulation knows (kcal, hunger, skills, exact days, names before writing, laws/disputes before writing), 【村】 recorded by villagers (none before G6).
- **Not in records**: feeling text, said text, personality, trust (decision: they stay in the app — `people[].feeling` with `feeling_day`, and the 話す events). Records keep only `answered` and `said` counts.
- **JSON style**: UTF-8, `ensure_ascii=False`, `separators=(",", ":")`. `.json` files are arrays written one element per line (`"[\n" + ",\n".join(rows) + "\n]\n"`) for small git diffs; `.jsonl` one object per line. Key order is fixed by the builder; row order §3.6. **No timestamps** anywhere.

### 1.3 `people.json`

One row per entry of `state["people"]`.

| key | example (ナギ) | source | tag |
|---|---|---|---|
| `id` | `"P006"` | list order | – |
| `name`, `sex` | `"ナギ"`, `"女"` | state | シ / 調 |
| `born_day` | `-3211` | `p.born_day` | 調 (as an age range) |
| `born_day_exact` | `true` | `false` for people who died before day 489 (Society 1.0): `era2.start` computed their `born_day` from the age at death, not the age at 489 | – |
| `origin` | `"よそから来た"` | `p.origin`: None → `"はじめから"`, `"生まれた"`, `"よそから来た"` | 調 (isotopes) |
| `came_day` | `629` | founders 0; born: `born_day`; joined: day of the 「加わる」 event naming them (`resume._joined_day`) | 調 |
| `came_with` | `["P007"]` | other names in the same 「加わる」 event | シ |
| `mother_id` | `null` | `p.mother` when `origin == "生まれた"` (biological mother; fathers are not modelled) | 調 (aDNA) |
| `guardian_id` | `null` | `p.mother` when `origin == "よそから来た"`: the adult the child came with (era2 `_settle_visitors`; may be a man, e.g. シノ ← フウ) | シ |
| `parent_ids` | `[]` | `[mother_id]` if any | 調 |
| `died_day` | `1679` | day of the 「死」 event whose `who` is the person | 調 |
| `death_cause` | `"病"` | `records.death_cause(text)` §6 | 調 (partly) |
| `death_event` | `30874` | event id | – |
| `age_at_death` | `40` | `(died_day − born_day) // 120` (equals the age in the text; tests check it) | 調 |
| `left_day`, `left_why` | `null` | `p.left`; why from the event that day: 「去る」 with 「ひどく空腹」 → `"飢えで村を出た"`, 「追って」 → `"母を追って村を出た"`, 「分かれる」 → `"家ごと村を出た"` | 調 (weak) |
| `status` | `"亡くなった"` | `"生きている"` / `"亡くなった"` / `"村を出た"` | – |
| `household_id` | `"H02"` | last membership row | 調 (house) |

Current causes: イサ 飢え (32), ルオ ザガ (84), リオ 子 (1019), テオ 子 (1649), ナギ 病 (1679), ユノ 病 (1829), カイ 病 (1949), フウ 病 (1979).

### 1.4 `households.json`

| key | example | source |
|---|---|---|
| `id`, `name` | `"H05"`, `"ユノの家"` | §1.2 |
| `origin` | `"よそから来た群れ"` | 川辺の家 `"はじめから"`; others the joining group (future: `"分かれた"` with `origin_household_id`) |
| `founder_ids` | `["P014","P015"]` | members whose `why_in` is はじめから/よそから来た at `first_day` |
| `first_day` | `1019` | min `from_day` of members (川辺の家 0) |
| `adults_last_day` | `1949` | last day an adult member was present (ユノの家: カイ died 1949; only children since) — null while adults remain |
| `last_day` | `null` | day the last member died/left; null while someone remains |
| `left_village_day`, `fission` | `null` | `g5.fissions` (day, people, goats, store, fields, dispute) |
| `home_built_day`, `home_start_day` | `1669`, `1650` | `era2.homes[h]` |

### 1.5 `membership.json`

One row per stay. Today every person has exactly one stay (era2 never moves people between households), but the table is built as intervals so future moves (marriage, fission into a new household) only add rows.

| key | meaning | rule |
|---|---|---|
| `person_id`, `household_id` | | |
| `from_day` | entered | founders 0; born: `born_day`; joined: `came_day` |
| `to_day` | left (inclusive, null = still) | death day / `left_day` |
| `why_in` | `"はじめから"`, `"生まれた"` (mother's household), `"よそから来た"` (group household) | same rule as `era2._sync_households` |
| `why_out` | `null`, `"亡くなった"`, `"飢えで村を出た"`, `"母を追って村を出た"`, `"家ごと村を出た"` | |
| `evidence` | event ids (加わる / 生まれる / 死 / 去る / 分かれる) | |
| `assigned_from_state_day` | `1109` | the state first carried `household` on day 1109 (git); earlier stays apply the same rule retroactively (era2 `_sync_households` is retroactive by design) |

### 1.6 `season_village.jsonl` (④ and ⑤)

One row per season end D. Sources: E = events of the season slice (§3.4), S = snapshot at D (or at D−30 for start values), A = answers, St = `state["stats"]`, F = final `era2.fields`, L = laws.

| key | content | source | exact | tag |
|---|---|---|---|---|
| `season_end_day`, `season_start_day`, `days`, `year`, `season`, `label` | 1709, 1680, 30, 14, 夏, 「14年の夏」 | | | – |
| `rounds` | `[{"meeting_day","meeting_first","event_first","event_end","snapshot"}]` (usually 1; 2+ only after a famine break) | S / §3.4 | yes | – |
| `era`, `era_end`, `advanced`, `substeps` | era during the season (previous round's `era`), era after `check`, bool, F entered (区切り events) | S, E | yes | シ |
| `population`, `adults`, `children`, `by_age_class`, `by_sex` | at D | membership + `born_day` (+S cross-check) | yes | 調 |
| `households_with_adults`, `households_with_members` | 8, 8 (2009: 9, 10) | membership | yes | 調 |
| `births`, `deaths` (`[{id,cause}]`), `joined`, `left`, `came_of_age`, `visitors_rejected` | person ids | E (生まれる, 死, 加わる, 去る, 分かれる, 大人になる) | yes | 調 |
| `store` (`{item: units}`), `store_kcal`, `store_days` | 草の種 168,396 …, 323 | S (`store_days` = `era2.store_days` at D) | yes (S) | シ (amount 調 as storage capacity) |
| `eaten` (`{item: units}`), `eaten_share`, `farm_share_season` | 木の実 96 % … | St (`eaten_by_kind`, `eaten_sown`) for days of the season | yes | シ (調: plant/bone ratios) |
| `fields` | `{"sown": n, "seed": つかみ, "ripe": 12, "harvested": 50,400, "fallen": 30,518, "failed": n, "trampled": つかみ}` | F + E (畑, 収穫, ヤギ trample) + §4.3 | yes | 調 (counts) / シ |
| `pests`, `pests_safe` | 62, 175,000 | E 「虫」 (`data.amount`, text) | yes | シ |
| `goats` | `{"count":10,"female":6,"male":4,"adult":n,"by_holder":{"H01":3,"村":7},"wild":n}` | S | yes | 調 (bones) |
| `pots`, `sickles`, `pots_made`, `pots_broken`, `sickles_made`, `sickles_broken` | 340, 34, … | S, E | yes | 調 |
| `homes_built`, `home_sizes` (`{H: m²}`), `house_gini` | 5, …, 0.375 | S `homes` | yes | 調 |
| `rain_nights`, `rain_outside_people`, `rain_outside_person_nights` | | E 「雨」 `data.outside` | yes | シ |
| `wealth_gini`, `no_wealth` | 0.843 | S `era_info.indicators` (G4+) | yes | シ |
| `laws` | `{"in_force": n, "adopted": [L…], "abolished": [L…], "proposed": [L…], "penalty_laws": n}` | E 「掟」 (text → law id), L (`day` = meeting day) | yes | シ |
| `g5` | `{"stage","leader_id","leader_elected","disputes_new":[M…],"disputes_settled":[M…],"judged","penalties":[{M,from,to,amount}],"feast":{"held":bool,"cost":{item:units}},"joint","fission":H|null,"stress"}` | E + S + `g5.disputes` | yes | シ (調: feast refuse) |
| `answered` | `{"season": n, "feeling": n, "reps": n}` | A file names | yes | シ |
| `year_named` | `{"year": 15, "name": "…"}` if the meeting that opened this season named a year | `era2.year_names` | yes | 村 (oral) |
| `criteria` | `{"era": "G5", "items": [{"key","label","op","target","value","met"}], "all_met": bool}` | S `era_info.indicators` + `era2.criteria_progress` | yes (S) | シ |
| `snapshot` | bool | | | – |

### 1.7 `season_household.jsonl` (③)

One row per season × household that had a living member at any time in the season.

| key | content | source | exact | tag |
|---|---|---|---|---|
| `season_end_day`, `household_id` | | | | |
| `status` | `"村にいる"` / `"大人がいない"` / `"村を出た"` | membership | yes | – |
| `members`, `adults`, `children`, `by_age_class` | ids at D | membership | yes | 調 |
| `rep_id` | oldest adult at the meeting (ties: people order) when `rep_mode` was on, else null; cross-checked with answer file names | membership + A (+S `season.reps`) | yes | シ |
| `leader_member` | bool | S `g5.leader` | yes | シ |
| `home` | `{"started","built_day","size","work_hours"}` | S `homes` | yes | 調 (size) |
| `keep` | bool (the season's 家の倉 choice) | S `houses[h].keep` (fallback: rep's `keep` answers since G4) | yes | シ |
| `store` | `{item: units}` at D | S | yes | シ (調: storage bins) |
| `goats` | `{"count","female","male","adult","kids_born","caught","lost","eaten"}` | S + §4.5 | yes | 調 |
| `wealth_kcal` | 623,621 (G4+) | S indicators `wealth` | yes | シ |
| `fields` | `{"sown","seed","ripe","harvested_own_fields","harvested_by_members","fallen","trampled"}` | F + §4.3 | yes | 調 (count) |
| `village_flow` | `{"in": つかみ, "out": つかみ}` (G5 `last_flow`, adults, 草の種にして) | S `g5.last_flow` | rounded to つかみ | シ |
| `disputes` | `{"raised":[M…],"against":[M…],"paid":つかみ,"received":つかみ}` | `g5.disputes` + E | yes | シ |
| `inherit` | `[{"dead_id","heir_id","what","to_village":bool}]` | E 「受けつぎ」 | yes | 調 (weak) |
| `jobs` | `{activity: adult-days}` | E (§1.8 rule) | yes | シ |
| `rain_outside_person_nights` | | E | yes | シ |
| `snapshot` | bool | | | |

### 1.8 `season_person.jsonl` (②)

One row per season × person present at any time in the season (born, joined, died or left during it included).

| key | content | source | exact | tag |
|---|---|---|---|---|
| `season_end_day`, `person_id`, `household_id` | | membership | | |
| `present_from`, `present_to`, `status_at_end` | days; `"生きている"`/`"亡くなった"`/`"村を出た"` | membership | yes | – |
| `age`, `age_class`, `child` | exact age at D (internal), class (§6), bool | `born_day` | yes | 調 (class) |
| `is_rep`, `is_leader` | at the meeting | §1.7, S | yes | シ |
| `answered` | `"season"` / `"feeling"` / null | A file names | yes | シ |
| `said` | `{"count": n, "to": ["みんな", "P002"]}` (no text) | E 「話す」 in the meeting slice | yes | シ |
| `jobs` | `[{"from_day","activity","place","with":[ids],"decided_by"}]` — 1 entry per round | S `people[].plan` (fallback A) | yes | シ |
| `decided_by` | `"自分"` (own answer) / `"代表が割り振った"` (name in rep's `family`) / `"代表と同じ仕事"` (rep answered, name not in `family`) / `"加わった季節"` (joined at that meeting: most common job) / `"答えなし (前と同じ)"` | A | yes | シ |
| `job_amounts` | `{"sow","pick","plant","harvest","eat_goat"}` | S `season.jobs` (fallback A) | yes | シ |
| `days_by_activity` | `{"採集": 28, "休む (けが)": 2, …}` | E: per day the person's first activity event (step.py `ACT_BY_EVENT`; 狩り by `data.hunters`); 休む while `plan.activity != 休む` → 「休む (けが)」 | yes | シ |
| `outputs` | `{"gathered": {item: units}, "tree_picked": つかみ, "tree_pick_evenings": n, "hunted": {item: units}, "milk": 杯, "harvested": つかみ, "sown": つかみ, "planted": つかみ, "pots": n, "sickles": n, "goats_caught": n, "house_work_days": n}` | E | yes (gathered split rounded, §4.7) | シ (調 for pots/sickles) |
| `injuries`, `rain_outside_nights` | | E 「けが」, 「雨」 | yes | 調 (healed fractures) / シ |
| `skills`, `hunger`, `fatigue`, `injured_days_left`, `items` | at D | S | yes (S) | シ |
| `laws` | `{"proposed":[L…],"votes":{"yes":n,"no":n,"by":"自分"|P…}}` | L (`proposer`, `day`) + A `votes` | yes | シ |
| `knowledge_added` | n | `state["knowledge_log"]` (`who`, `day` = meeting day, `op == "追加"`) | yes | シ |
| `snapshot` | bool | | | |

### 1.9 `ledger.jsonl` (家 × 季節 × 物 × 理由)

One row per season × holder × item × reason (+ start/end rows). For each (season, holder, item) the rows satisfy

`残り(start) + Σ 動き = 残り(end)` exactly (in kcal for food), with `記録にない差` as the last 動き.

| key | content |
|---|---|
| `season_end_day` | D |
| `holder` | `"H02"` / `"村"` (`holder_name` alongside) |
| `item`, `unit` | §1.2 |
| `kind` | `"残り"` (start/end), `"動き"` (flow), `"メモ"` (not part of the balance) |
| `reason` | fixed vocabulary, §4.2 (`季節のはじめの残り`, `季節の終わりの残り`, …, `記録にない差`) |
| `amount` | units, signed for 動き (+ in, − out); null if unknown |
| `kcal` | food only, signed, exact |
| `source` | `"snapshot"`, `"events"`, `"replay"`, `"notes"`, `"balance"` |
| `detail` | optional: `{"events":[ids]}`, `{"by_household":{"H03":140}}`, `{"goats":[ids]}`, `{"dispute":"M1"}` |

Rows with zero start, zero end and no flows are omitted. If start or end is unknown (no snapshot), the stock rows have `amount: null` and no `記録にない差` row is written (`detail: {"balance": "unknown"}` on the first flow row).

### 1.10 `year_names.json`

One row per year y from 4 (Society 2.0 began at 489 = 4年10日目) to the current year.

| key | content |
|---|---|
| `year`, `first_day`, `last_day` | 16, 1920, 2039 |
| `asked` | the year-end meeting prompts contained 「## 年の名前」 (builder reads `prompts/day{120y+119}/season/*.md`) |
| `name` | decided name or null |
| `decided_day`, `event_id`, `weight`, `adults` | from `era2.year_names` |
| `proposals` | `[{"person_id","name","weight"}]` |
| `why_none` | `"年の名前を決める前の年"` / `"だれも名前を書かなかった"` / `"まだ終わっていない"` |
| `harvest` | つかみ harvested in the year (the "one measured value" of annals, historical_records ⑩) |

### 1.11 Extras: `laws.json`, `disputes.json`

- `laws.json`: `{id, text, proposer_id, proposed_day, status, adopted_day, abolished_day, penalty, label}` — adoption/abolition days from 「掟」 events (`掟「{text}」が採用された` / `が廃止された`, matched to the law by exact text), so earlier changes are not lost when `changed` is overwritten.
- `disputes.json`: `g5.disputes` with household ids, `season_end_day` of the start and of the end, event ids.

### 1.12 `columns.json`, `meta.json`

- `columns.json`: `[{table, column, label_ja, unit, tag, source, exact, since_day, note}]` from a static table in the builder (one entry per column above). The display layer reads tags from here.
- `meta.json`: `{"schema": 1, "state_day", "state_next_event", "seasons", "snapshots": {"valid", "invalid", "live", "git"}, "missing_snapshot_days": [...], "ledger": {"exact_accounts_max_residual", "village_food_max_residual": {item: units}}}` — no timestamps, so rebuilds are byte-identical.

---

## 2. Snapshots (`snapshots.jsonl`)

### 2.1 What and when

Values that exist only as current state are captured once per **round** (a `step.py season` run: normally a full season; after a famine break, part of one). step.py captures the snapshot right after `era2.check` (and the hold/フェーズ log), **before** `save`, appends it after `save`, i.e. the snapshot describes exactly the state that is saved and committed. The 「全員いない」 exit path captures one too.

### 2.2 Row schema (v1)

```json
{"v":1,"day":1709,"season_end":1709,"source":"live",
 "meeting_first":30880,"event_first":30898,"event_end":32211,"sig":"3c1f…",
 "era":"G5","era_info":{…as in state…},"hold":true,
 "village":{"store":{"草の種":13471680.0,…},"store_days":323,"pots":340,"sickles":34,"wild_goats":10,"next_goat":18},
 "goats":[{"id":9,"sex":"メス","born":1529,"owner":null},…],
 "houses":{"ナギの家":{"keep":true,"store":{"草の種":623620.554}},…},
 "homes":{"ナギの家":{"start":1620,"built":1636,"size":20,"work":…},…},
 "fields":[{…fields in state 育つ/実った, copied…}],
 "people":{"ヨナ":{"alive":true,"age":31,"household":"アルの家","child":false,"left":null,"food":{"草の種":1200.0},
           "hunger":0,"fatigue":0.0,"injured":0,"reserve":…,"skills":{"採集":1,"狩り":0.25,"道具":0.32,"火":0.32,"土器":1},"items":{…},
           "plan":{"activity":"土器づくり","place":"camp","with":["アル"]},"pot_work":…,"sickle_work":…,"knowledge":…,"last_birth":…},
           "ナギ":{"alive":false,"age":40,"household":"ナギの家","child":false,"left":null,"food":{}}, …},
 "season":{"jobs":{…},"craft_days":{…},"specialists":[…],"tended_run":12,"step_day":1680,"rep_mode":true,"reps":["セナ",…]},
 "g5":{"stage":2,"leader":null,"leader_day":null,"last_flow":{…},"feast_day":1950,"feasts":3,"settled":3,"judged":0,"penalties":0,"joint":0,"votes":{…},"call":null,"next":3,"open":[]},
 "laws":{"L0":"採用",…},
 "year_names":0,
 "notes":null}
```

- `meeting_first` = step.py's `before` (first id of the meeting that opened the round); `event_first` = `simulate_season`'s return (= `era2.last_first`); `event_end` = `state["next_event"]` after check; `sig` = `event_sig(state, event_end − 1)`.
- `notes` = aggregated `era2.LEDGER_NOTES` of the round (§4.9): `[{"why","household","from","kind","kcal"}]`; `[]` = captured, nothing happened; `null` = not captured (backfilled rows, or instrumentation not adopted).
- Not captured (bulky or not needed): events, knowledge texts, heard, trust, personality, terrain, plants, planted, stats (already complete in the state).

### 2.3 Purity

`records.snapshot` only reads: `.get` everywhere, copies via `json.loads(json.dumps(x))`, and the only era2 calls are pure (`store_days`, `_reps`). It must not call `era2._house`, `era2._g5` (they `setdefault`), `answerers`/`feelers` (they call `_sync_households`). Test A4 compares `json.dumps(state, sort_keys=True)` before and after.

### 2.4 Validity and duplicates

A row is **valid** for the current state iff `row.event_end <= state["next_event"]` and `event_sig(state, row.event_end − 1) == row.sig` (the row's history is a prefix of the current history). Invalid rows (from an abandoned/rolled-back run) are ignored and counted in `meta.json`. Per `day`, among valid rows the builder takes `source == "live"` over `"git:…"`, then the last in file order. Malformed lines are skipped with a warning. Builder output does not depend on line order (test D).

### 2.5 Backfill from git (one-time)

`python3 sim/society/tools/backfill_snapshots.py [--data DIR] [--repo ROOT] [--path sim/society/data/state.json] [--dry-run]`

1. `git log --format=%H --reverse -- <path>` (oldest first).
2. For each commit: `git show <sha>:<path>` → state; skip if no `era2` or `day < era2.start_day`; skip unless lineage holds against the current state (`events[next_event−1]` equal in day/type/who/text); keep the **first** commit per day.
3. For consecutive kept states, `meeting_first(day_i) = next_event(state_{i−1})`; `event_first = era2.last_first`.
4. `row = records.snapshot(old_state, meeting_first, event_first, source=f"git:{sha[:7]}", notes=None)` (tolerant of old schemas through `.get`).
5. Append rows (sorted by day) only for days with no valid row yet; print a table day → sha. Idempotent; `--dry-run` writes nothing. Reads git only; never touches `state.json`.

On the real data this yields 52 rows (489, 509…2009). Runtime 20–30 s.

### 2.6 Failure handling

Snapshot errors print 「記録: 季節の終わりの控えを作れなかった (…)」 and return None; the season result, `save`, prompts, export and the exit code are unaffected. A missing row can later be filled by the backfill tool (season_step.sh commits the state every season).

---

## 3. Builder (`sim/society/tools/build_records.py`)

### 3.1 Interface

- CLI: `python3 sim/society/tools/build_records.py [--data DIR] [--check] [--quiet]` (default DIR: `$SOC_DATA` or `sim/society/data`). `--check` also verifies ledger closure (§4.8) and exits 1 if an exact account does not close.
- API: `build(data_dir, quiet=False) -> dict` (summary used by `--check` and tests).
- step.py runs it as a **subprocess** after `save`/`write_prompts`/`export` (`timeout=300`). A subprocess cannot touch the in-memory state and isolates crashes; the cost is one extra 0.5 s load. Non-zero exit → warning only.
- Output: with `--quiet` one line (「記録: 51 季節・帳簿 5,0xx 行 (…秒)」). The builder never prints event texts or villager-written names (the workflow stops on `/フェーズが .* に進んだ/` in step.py's output).

### 3.2 Read-only guarantees

- Opens `state.json`, answers, prompts and `snapshots.jsonl` for reading only; writes only inside `DATA/records/` (never `snapshots.jsonl`).
- Allowed era2 calls (pure): `meeting_first`, `criteria_progress`, `CRITERIA_PARTS`, `store_days`, `_reps`, `gini`, `season`/`YEAR`/`SEASON_DAYS`/`CHILD_EAT`/`GOAT_WORTH`/`GRAIN`/`UNITS`. Forbidden: `_house`, `_g5`, `_sync_households`, `answerers`, `feelers` and anything calling them (they write into the state through `setdefault` or household assignment).
- Writes are atomic (`tmp` + `os.replace`) and skipped when the bytes are unchanged.

### 3.3 Algorithm

1. **Load**: state; valid snapshots by day (§2.4); index of `answers/day*/{season,feeling}/*.json` (parsed with `characters.parse`); events by id (list index).
2. **IDs and stays**: persons, households, membership (§1.3–1.5), `born_day`-based ages.
3. **Rounds** (§3.4): round-end days `R = sorted({e2.start_day} ∪ valid snapshot days ∪ season ends in (start_day, state.day] ∪ answer days ≥ start_day)`; each round (r₋₁, r] gets `meeting_first`, `event_first`, `event_end` (snapshot values, else §3.4 rule; for the last round with `r == state.day`: `event_end = state.next_event`). Seasons = rounds grouped by `records.season_end(r)`.
4. **Per season**: one pass over the season's event slice `[meeting_first(first round), event_end(last round))` collecting everything for the village, household and person rows; stats rows for days in (D−30, D]; answers of each round's meeting day.
5. **Harvest replay** (§4.3), **goats by id** (§4.5), **ledger** (§4).
6. **Year names**, laws, disputes, columns, meta.
7. **Write** all files.

### 3.4 Rounds and the meeting boundary

Event order on a round-end day d: last day's daily events → `_field_season` (畑) → `_season_end` events → step.py フェーズ → (next command) the meeting: 話す, 掟, G5 meeting (もめごと/収める/裁き/罰/祭り/まとめ役/共同の仕事), 加わる/去る (visitors), ヤギを食べる, 年の名前 (new) → 話す (feelings) → day d+1.

Exact boundaries come from snapshots (`meeting_first`/`event_end`). Without a snapshot, `era2.meeting_first(state, d)` (§7.2) scans day d's events backwards while they are meeting events and returns the first meeting id (or `last id + 1` if none). Meeting events are: types 話す, 掟, 収める, 裁き, 罰, 祭り, 共同の仕事, 加わる, ヤギを食べる, 年の名前 always; もめごと only with 「話し合ったが」 (season-end disputes say 言い出した/重なった/言わなくなった); 去る only with 「受け入れられず」 (famine leaves happen mid-season); まとめ役 unless the text ends with 「村にまとめ役がいなくなった」 (death/leaving, logged at season end). Verified 51/51 against git.

### 3.5 Harvest destination and other derivations

Column sources are in §1.3–1.10. Rules that need more than a lookup:

- **Representative at a meeting**: oldest adult of the household at that meeting (ages at d = `(d − born_day) // 120`; ties by people order), only when `rep_mode` was on (snapshot `season.rep_mode` of the previous round; fallback: the 「家族」 event of 1259 and the count of adults > 12). Must match the answer file names (test B).
- **Leader**: `g5.leader` of snapshots; fallback `g5.leaders` + 「まとめ役」 events.
- **Laws per meeting**: 「掟」 events in the meeting slice, matched by exact text to `state["laws"]`.
- **Store-days, wealth, ginis, criteria**: from the snapshot (`era_info.indicators`, `village.store_days`) — never recomputed from the current state for past seasons.

### 3.6 Determinism and performance

- Row order: village by D; household by (D, household id); person by (D, person id); ledger by (D, holder [村, H01…], item order [草の種, 木の実, 芋, 干し肉, 肉, 魚, ピク, 乳, ヤギ, 土器, 鎌, 食べ物 (草の種にして)], start, flows in §4.2 order, 記録にない差, end).
- No dict iteration over unsorted keys in output; floats rounded at output only; no time, no randomness, no environment-dependent paths in outputs.
- Budget on the real 17–20 MB state: full rebuild **≤ 5 s** (expected 2–3 s; fail the test above 15 s). Snapshot capture ≤ 0.2 s. step.py season overhead (with the subprocess) ≤ 5 s on top of ≈ 11 s.

---

## 4. Ledger derivation

Preference: derivation from events and era2 data. Instrumentation only where the engine leaves no trace (§4.9).

### 4.1 Accounts

| holder | items | start/end values |
|---|---|---|
| `H##` 家の倉 | foods in `era2.house[h].store` (草の種 in practice) | snapshot `houses[h].store` |
| `H##` ヤギ | ヤギ (owner == household) | snapshot `goats` by owner |
| `村` 食べ物 | all foods in `state.store` **plus adults' hands** (`people[].food` of living adults) | snapshot `village.store` + `people[].food` |
| `村` ヤギ | goats with `owner` None/missing | snapshot `goats` |
| `村` 土器・鎌 | pots, sickles | snapshot `village.pots/sickles` |

Why hands are in 村: era2 `_feed` moves food between hands and the village store every day automatically (the village rule); those moves are not recorded by kind, but everything that enters or leaves hands∪store is (§0: total residual ≤ 100 kcal per season). The per-household G5 view of those moves (`g5.last_flow`) is kept as `メモ` rows.

### 4.2 Flow table

| holder · item | reason (in this order) | sign | source | exact |
|---|---|---|---|---|
| 村 · food | 採った | + | 「採集」 text words, scaled to `data.kcal` | total yes; split rounded |
| 村 · 木の実 | 木から取った | + | 「木から取る」 `data.food` | yes |
| 村 · 肉/魚/ピク | 狩った | + | 「狩り」: しとめた → 肉 `MEAT_KCAL`; small catches from words | yes |
| 村 · 乳 | 乳をしぼった | + | 「乳」 `data.amount` × 150 | yes |
| 村 · 草の種 | 刈った (村の蓄えに入った) | + | replay §4.3 | yes |
| 村 · 干し肉 | ヤギをつぶした | + | 「ヤギを食べる」 n × 20 × 600 | yes |
| 村 · food | 家にだれもいなくなり、村のものになった | + | 「受けつぎ」 (村のものになった) words; residual absorbs rounding | rounded |
| 村 · food | 家の倉から食べた / 家の倉から食べた (子) / よその家の倉から取った | + | notes §4.9 | yes (if adopted) |
| 村 · food | 食べた | − | `stats.eaten_by_kind` of the season's days (adults + children) | yes |
| 村 · 草の種 | まいた (畑) | − | 「畑」 with `who` and `data.seed` | yes |
| 村 · 木の実 | 種として埋めた | − | 「種まき」 「…木の実 n つかみ を種として埋めた」 | yes |
| 村 · food | 腐った | − | 「腐る」 words scaled to `data.kcal` | total yes |
| 村 · 草の種 | 虫やネズミ | − | §4.4 | yes |
| 村 · food | 祭り | − | 「祭り」 「…を使った」 words | rounded (≤ 0.5 unit/kind) |
| 村 · food | 雨で傷んだ | − | 「雨」 「…が濡れて傷んだ」 (only without a roof; not in Society 2.0 so far) | rounded |
| 村 · 肉→干し肉 | 干した | −/+ | 「干す」 words (干し肉 = 0.8 × meat) | rounded |
| 村 · food | 亡くなった人の手元 / 村を出た人の手元 | − | end snapshot `people[].food` of those alive at start and not at end | yes |
| 村 · food | 記録にない差 | ± | balance | – |
| H · 草の種 | 刈った (自分の家の畑) | + | replay §4.3 (`detail.by_household`: harvesters' households) | yes |
| H · food | 罰・つぐないで受け取った / 罰・つぐないで払った | ± | 「収める」/「裁き」 「XがYに … を払った」 (+ 「罰」 for the law id) | yes for whole つかみ; rounded if the payer's store ran out |
| H · 草の種 | 虫やネズミ | − | §4.4 | yes |
| H · food | 家の人が食べた / 子が食べた / よその家の人に取られた | − | notes §4.9 | yes (if adopted) |
| H · food | だれもいなくなり、村のものになった | − | 「受けつぎ」 | rounded |
| H · food | 村を出て持っていった | − | `g5.fissions[].store` + 「分かれる」 | yes |
| H · food | 記録にない差 | ± | balance | – |
| H/村 · ヤギ | 捕まえた / 生まれた / いなくなった (世話が足りない) / いなくなった (草が足りない。2026-10-10 から。「ヤギ」の `data.goat_ids`) / つぶした / 罰・つぐないで渡した / 受け取った / 持ち主がいなくなり村のものになった / 村を出て持っていった / 記録にない差 | ± | §4.5 | yes |
| 村 · 土器 | 作った / 割れた / 記録にない差 | ± | 「土器」 `data.count`; 「道具」 (who None) 「村の土器が n 個 割れた」 | yes |
| 村 · 鎌 | 作った / 割れた / 記録にない差 | ± | 「道具」 with who and 「鎌を n 本作った」 (`data.count`); 「村の鎌が n 本 割れた」 | yes |
| H · 食べ物 (草の種にして) | 村の蓄えに入れた (大人) / 村の蓄えから取った (大人。家の畑にまいた村の草の種をふくむ) | メモ | snapshot `g5.last_flow` (G5) | rounded つかみ |

Within-household inheritance (heir in the same household) moves nothing between holders: it is recorded in `season_household.inherit`, not in the ledger.

Word parsing: `(木の実|芋|ルクの肉|魚|ピクの肉|草の種|干し肉|ヤギの乳) (\d+) (つかみ|本|切れ|匹|杯)` with `FOOD_NAME` reversed (ルクの肉 → 肉, ピクの肉 → ピク, ヤギの乳 → 乳). When `data.kcal` exists, scale the parsed kinds so their sum equals it.

### 4.3 Harvest replay (exact; who harvested which field into which store)

Inputs for summer season D (fields ripen at the end of the previous spring): `ripe` = fields with `state == "実った"` in the snapshot at D−30, in `era2.fields` order (fallback without snapshot: final fields that have `yield` and were sown in the autumn of year D//120 − 1); `rem[f] = yield − harvested` at that snapshot (fallback: `yield`); `owner[f]` from that snapshot (fallback: `f.owner`, or the sower's household at `f.day`, unless a 分かれる/empty-house 受けつぎ for that household happened before D−29); harvester household from membership; `keep[h]` from the snapshot at D (keep can only change at the meeting that opened the season); `built_event[h]` = id of 「…の住まいができた」 (`data.size == 20`).

```
for e in season events of type 収穫, in id order:
    hh = household(e.who, e.day)
    order = ripe sorted stably by (owner[f] != hh) if era(e.day) >= G4 else ripe
    f = first f in order with rem[f] > 0
    assert rem[f] >= e.data.amount
    rem[f] -= e.data.amount
    to_house = era(e.day) >= G4 and owner[f] and keep[owner[f]] and built_event.get(owner[f], ∞) < e.id
    credit (owner[f] if to_house else 村) with amount; record harvester household in detail
check: rem[f] == final yield − final harvested for every f   (else: mark the season's replay "unverified")
```

This mirrors `era2._harvest` (own-household fields first since G4, one 収穫 event per field touched, `_store_of` destination) and `_field_work`/evening calls interleave correctly because only event order matters. 「落ちた」 per field = final `yield − harvested`.

### 4.4 Pest shares (虫やネズミ)

`_storage_season` removes `g_i / G × lost` from every store i (village store and all house stores; 草の種 only) at the season end, so with the snapshot values after the loss, `share_i = g_after_i × lost / G_after` where `G_after = Σ g_after_i` and `lost = data.amount` of the 「虫」 event. Exact (residual 0 in §0).

### 4.5 Goats by id

With snapshots at D−30 (P) and D (C): `new = range(P.next_goat, C.next_goat)`; `gone = (P ∪ new) − C`.
- 捕まえた: new ids whose `born != D` (kids are born with `born == D`), credited to the catcher's household (= recorded `owner`); count must equal 「…子ヤギ (…) を捕まえて」 events.
- 生まれた: new ids with `born == D`, credited to `owner` (the mother's owner); sum equals 「子ヤギが n 頭生まれた」.
- つぶした: ids in P gone, ≤ the 「ヤギを食べる」 count at the meeting (era2 eats oldest males first) — classify the first n of the gone ids that match that order.
- 村を出て持っていった: gone ids whose owner is the fission household (`g5.fissions`), except ids in a 「ヤギ」 event's `data.goat_ids` (the grass loss runs earlier in the same season end).
- いなくなった: remaining gone ids; total must equal 「ヤギ n 頭がいなくなった」 + 「ヤギ n 頭がやせていなくなった」. Ids in `data.goat_ids` → いなくなった (草が足りない) (2026-10-10 から); the rest → いなくなった (世話が足りない).
- Owner changes P → C: to None with an empty-house 受けつぎ → 「持ち主がいなくなり村のものになった」 (out of H, into 村); a → b with a 収める/裁き 「… ヤギ n 頭 を払った」 → 罰・つぐない; anything else → 記録にない差 (should never occur).

Without snapshots goat holders cannot be reconstructed (owner of a lost goat is not in the event) → rows null.

### 4.6 Penalties, feasts, fission, empty houses

- Penalty/compensation text: `。{payer}が{receiver}に {words} を払った` in 収める/裁き (words may include `ヤギ n 頭`); law id from the paired 「罰」 event. Food moves house→house (both holders), goats per §4.5.
- Feast: 「祭り」 `…村の蓄えから {words} を使った` → 村 out. The exact total is `FEAST_DAYS × _need` at the meeting; words are rounded per kind.
- Fission: `g5.fissions[i]` (`store` kcal, `goats` count) + snapshot diff → H out 「村を出て持っていった」; the leaving people's hands → 村 out 「村を出た人の手元」.
- Empty house (`_inherit`, nobody left): house store → 村, goats → owner None, fields → owner None.

### 4.7 The 村 food account

As §4.1/§4.2. Expected residuals: total ≤ 100 kcal per season; per item tens of units (gathering-split rounding). The `記録にない差` row for 村 food carries `detail: {"why": "採集の記録は、物ごとの量を整数に丸めて書いている"}` when |total residual| ≤ 100 kcal; otherwise `detail.why = "わからない"` and `--check` prints it.

### 4.8 Balancing rule and checks

For every (season, holder, item) with known start and end: `diff = end − start − Σ flows` (kcal for food, count otherwise). Write `記録にない差` iff |diff| ≥ 0.005 kcal for food (so the kcal column always closes; e.g. 689 村 魚: 0.67 kcal, 0.002 units) or diff ≠ 0 for counts. `--check` and test C require `diff == 0` (|diff| < 1e-6 kcal or exact count) for: all H food accounts, all goat accounts, 村 土器 and 鎌, and (if notes adopted) seasons with notes.

### 4.9 Optional instrumentation: `era2.LEDGER_NOTES` (recommended)

Three engine flows leave no trace: adults eating from their own house store and children eating from it (`_feed`, only when the village store runs short) and repeated steals (`_steal` logs only the first per household pair per season). Derivation cannot recover them; without notes they land in `記録にない差`. The instrumentation writes **nothing into the state**, uses no RNG and changes no control flow:

```python
# 記録のための書きとめ (ダッシュボードの帳簿用。2026-10-xx。docs/dashboard_records_spec.md 4.9)。出来事に残らない食べ物の動きを書きとめるだけで、
#   state には入れず、世界の進み方にも使わない。step.py が季節ごとに読んで空にする
LEDGER_NOTES = []


def _note(state, why, h, by, frm=None):
    if by:
        LEDGER_NOTES.append({"day": state["day"], "why": why, "household": h, "from": frm, "by": dict(by)})


def take_notes():
    """書きとめをまとめて返し、空にする (step.py が使う)"""
    out = {}
    for n in LEDGER_NOTES:
        for k, v in n["by"].items():
            key = (n["why"], n["household"], n["from"], k)
            out[key] = out.get(key, 0) + v
    LEDGER_NOTES.clear()
    return [{"why": w, "household": h, "from": f, "kind": k, "kcal": round(v, 3)} for (w, h, f, k), v in sorted(out.items(), key=str)]
```

Hooks (same calls, same arguments, same order; only the returned dict is kept in a name):

```python
# _feed, adults (was: got += sum(_move_food(_house(...)["store"], p["food"], None, keep - have - got).values()))
                by = _move_food(_house(state, p.get("household"))["store"], p["food"], None, keep - have - got)
                _note(state, "家の人が食べた", p.get("household"), by)
                got += sum(by.values())
# _feed, children (was: for k, v in _move_food(_house(...)["store"], got_items, None, need - sum(by.values())).items(): ...)
            hb = _move_food(_house(state, c.get("household"))["store"], got_items, None, need - sum(by.values()))
            _note(state, "子が食べた", c.get("household"), hb)
            for k, v in hb.items():
                by[k] = by.get(k, 0) + v
# _steal, right after: by = _move_food(hs[h]["store"], p["food"], None, want)
        _note(state, "よその家の人に取られた", h, by, frm=mine)
```

Ledger mapping: 家の人が食べた → H out + 村 in (「家の倉から食べた」); 子が食べた → H out + 村 in (「家の倉から食べた (子)」; the eating itself is already in `stats`); よその家の人に取られた → H(from) out + 村 in (「よその家の倉から取った」, `detail.thief_household`). If not adopted, delete §4.9 and these rows; nothing else changes.

---

## 5. Year names (era2.py)

### 5.1 Rules

- **When**: the meeting that ends a year, i.e. prompts written at state day d with `(d + 1) % YEAR == 0` and the answers read at that state day. Next: d = 2039 (names year 16 = days 1920–2039). The extra prompt text appears only in that meeting's season prompts.
- **Who**: everyone who answers the season prompt (representatives, and the leader if not a representative). Feelers do not propose; they see the remembered list.
- **Answer field**: `"year_name": "…"` (string). Normalised by `_year_name_text`: NFKC, strip spaces and `「」『』"'“”。`, cut to `YEAR_NAME_MAX = 20` characters; ignored if empty, a placeholder (`...`, `…`, `null`, `なし`), multi-line, or containing a workflow stop phrase (`STOP_WORDS = ("フェーズが", "Society 2.0 が終わった")` — step.py prints this event and the workflow stops on `/フェーズが .* に進んだ/`). Non-year-end answers' `year_name` is ignored.
- **Weight**: `len(fam)` as already computed in `apply_answers` for that answer (a representative counts for the family adults who did not answer themselves; a non-representative leader counts 1; without `rep_mode` everyone counts 1).
- **Decision**: sum weights per identical normalised name; the largest sum wins (**plurality**, recommended — decision 4). Tie: among tied names, the one proposed by the oldest answerer (`age`, then people order — same as the elder rule). No proposals → no name, no event, no state change.
- **Once per year**: if `year_names` already has the year, do nothing.

### 5.2 Code

```python
import unicodedata

# ---------------- 年の名前 (口で伝える年代記。2026-10-09 本人と決めた。docs/dashboard_records_spec.md 5.) ----------------
# 年の終わりの季節の集まり (年の最後の日 (day + 1) % YEAR == 0 の終わりに書くお題と、その答え) で、季節の答えをする人 (家族の代表と、まとめ役) が、
#   終わった年に、その年いちばん大きな出来事で名前をつける。決まった名前は、そのあとのお題に「村で覚えている年の名前」として出る
# 【文献】年の名前 (メソポタミア)・年の記録 (エジプト)・冬の数え (ラコタ) (docs/research/historical_records.md 5.2 の ⑩)
# 決め方: 同じ名前を書いた人の、家族の大人の数 (その答えが数える大人の数) を足して、いちばん多い名前。同じなら、その名前を書いた人でいちばん年上の人の名前
#   (同じ年なら人の並びで先。長老の決め方と同じ)。乱数は使わない。だれも書かなければ名前はつかない (state も出来事も変わらない)
YEAR_NAME_MAX = 20
YEAR_EVENTS = ("フェーズ", "区切り", "段階", "分かれる", "死", "生まれる", "加わる", "去る", "まとめ役", "受けつぎ", "祭り", "住まい", "もめごと",
               "収める", "裁き", "罰", "大人になる", "ヤギ", "ヤギを食べる", "虫", "蓄えが尽きる", "家族")  # お題に見せる出来事 (前のものほど先に残す)
STOP_WORDS = ("フェーズが", "Society 2.0 が終わった")  # ワークフローが止まる文と重なる名前は読まない (step.py が出来事を表示するため)


def year_end(state):
    """この集まりが、年の終わりの集まりか"""
    return (state["day"] + 1) % YEAR == 0


def _year_name_text(v):
    s = unicodedata.normalize("NFKC", v if isinstance(v, str) else "").strip().strip("「」『』\"'“”。 ").strip()
    if not s or s in ("...", "null", "なし") or "\n" in s or any(w in s for w in STOP_WORDS):
        return ""
    return s[:YEAR_NAME_MAX]


def _year_digest(state):
    """年の名前のお題: この 1 年のおもな出来事 (読むだけ)"""
    y = state["day"] // YEAR
    ev = state["events"][meeting_first(state, y * YEAR - 1):]  # この年の最初の季節の集まりから (出来事の id は並びの番号と同じ)
    big = [e for e in ev if e["type"] in YEAR_EVENTS and not (e["type"] == "住まい" and "size" not in (e.get("data") or {}))
           and not (e["type"] == "ヤギ" and e.get("who"))]  # 建てた日ごとの記録と、1 頭ずつ捕まえたのは入れない (下で数でまとめる)
    if len(big) > 15:
        big = sorted(sorted(big, key=lambda e: (YEAR_EVENTS.index(e["type"]), e["id"]))[:15], key=lambda e: e["id"])
    rows = [f"- [出来事 {e['id']}] {e['text']}" for e in big]
    caught = sum(1 for e in ev if e["type"] == "ヤギ" and e.get("who"))
    harv = sum((e.get("data") or {}).get("amount", 0) for e in ev if e["type"] == "収穫")
    rows += ([f"- 野生の子ヤギを {caught} 頭捕まえた"] if caught else []) + ([f"- 畑で刈った草の種: 合わせて {harv} つかみ"] if harv else [])
    return "\n".join(rows) or "- (大きな出来事はなかった)"


def _year_end_text(state):
    """年の終わりの集まりのお題の節 (ほかの集まりでは空)"""
    if not year_end(state):
        return ""
    y = state["day"] // YEAR
    return (f"\n## 年の名前 (1 年に 1 回)\n{y * YEAR}〜{state['day']} 日目の 1 年が、今日で終わった。村では、年に、その年いちばん大きな出来事で名前をつけ、"
            f"口で伝えて覚えている。この 1 年のおもな出来事:\n{_year_digest(state)}\n"
            f"この年の名前を、あなたの言葉で 1 つ書く (year_name、{YEAR_NAME_MAX} 字まで)。家族の代表の答えは、家族の大人みんなの答えとして数える。"
            "同じ名前を書いた人の家族の大人の数を足して、いちばん多い名前に決まる (同じなら、書いた人でいちばん年上の人の名前)\n")


def _year_names_text(state):
    """村で覚えている年の名前 (古い年から)。まだなければ空 (お題は前と同じ)"""
    names = state["era2"].get("year_names") or []
    if not names:
        return ""
    last = (state["day"] + 1) // YEAR - 1
    rows = [f"- {x['year'] * YEAR}〜{x['year'] * YEAR + YEAR - 1} 日目の年: 「{x['name']}」" + (" (去年)" if x["year"] == last else "") for x in names]
    return "\n## 村で覚えている年の名前\n村では、年を、その年いちばん大きな出来事の名前で呼び、口で伝えて覚えている (古い年から)。\n" + "\n".join(rows) + "\n"


def _year_name(state, props, n):
    """年の名前を決める (props: [(答えた人, 名前, 家族の大人の数)])"""
    e2, y = state["era2"], state["day"] // YEAR
    if any(x["year"] == y for x in e2.get("year_names", [])):
        return
    w, by = {}, {}
    for p, t, k in props:
        w[t] = w.get(t, 0) + k
        by.setdefault(t, []).append(p)
    top = max(w.values())
    order = {q["name"]: i for i, q in enumerate(state["people"])}
    best = min((t for t in w if w[t] == top), key=lambda t: min((-q["age"], order[q["name"]]) for q in by[t]))
    eid = log(state, "年の名前", None, f"{y}年 ({y * YEAR}〜{state['day']} 日目) は「{best}」と呼ぶことになった "
              f"(同じ名前を書いた家族の大人 {top} 人分 / 大人 {n} 人)", year=y, name=best)
    e2.setdefault("year_names", []).append({"year": y, "name": best, "day": state["day"], "event": eid, "weight": top, "adults": n,
                                            "proposals": [{"who": p["name"], "name": t, "weight": k} for p, t, k in props]})
```

Hooks in `apply_answers` (nothing else in the function changes):

```python
    yname = [] if year_end(state) else None  # 年の名前 (年の終わりの集まりだけ読む)
    for name, raw in answers.items():
        ...                                    # (unchanged, through the `if not own: … elif …: fam = …` block)
        t = _year_name_text(a.get("year_name")) if yname is not None else ""
        if t:
            yname.append((p, t, len(fam)))
        ...                                    # (unchanged)
    ...
    _eat_goats(state)
    if yname:
        _year_name(state, yname, len(alive))   # 集まりの最後に (ほかの集まりの出来事の並びは変わらない)
```

Prompt changes (all empty strings unless a name exists or it is a year-end meeting, so other prompts stay byte-identical):

- `season_prompt`: insert `{_year_names_text(state)}` right before `{_g5_text(state)}`; insert `{_year_end_text(state)}` right after `{vis}`; in 「## いま」 add, after `{g5_now}`, `yname_now = f"{7 + bool(g5_now)}. この 1 年の名前を決める (year_name。上の「年の名前」を見て)\n" if year_end(state) else ""` and number the feeling item `{7 + bool(g5_now) + year_end(state)}` (equals today's `8 if g5_now else 7` when not a year end); in the JSON template insert `' "year_name": "...",\n' if year_end(state) else ""` before ` "feeling"`.
- `feeling_prompt`: insert `{_year_names_text(state)}` right after `{_village(state)}`.
- Do **not** add 「年の名前」 to `G5_EVENTS` (the list already shows the name).

### 5.3 State, events, step.py

- State: `state["era2"]["year_names"] = [{"year","name","day","event","weight","adults","proposals":[{"who","name","weight"}]}]`, created only when the first name is decided.
- Event: type 「年の名前」, `who` None, `data = {"year", "name"}`, logged at the meeting (dated with the year's last day).
- step.py: in the season summary loop add `or (e["id"] >= before and e["type"] == "年の名前")` so the line is printed.
- App: unchanged (the event shows in the event log). A year-name strip can come with the dashboard.

### 5.4 Records

`year_names.json` (§1.10); `season_village.year_named` on the season whose opening meeting decided it; the builder detects "asked" from the year-end prompts.

---

## 6. Age classes and death causes (`records.py`)

```python
# 【仮定】年齢の区分 (2026-10-09 本人と決めた。境目は仮)。正確な年齢は内側の記録にだけ持つ
AGE_CLASSES = (("乳飲み子", 0, 2), ("子", 3, 11), ("手伝える子", 12, 14), ("大人", 15, 54), ("年寄り", 55, None))
DEATH_CAUSES = (("飢え", r"飢えで死んだ"), ("ザガ", r"ザガ.*殺された"), ("病", r"病で亡くなった"), ("年", r"年をとって亡くなった"),
                ("子", r"\(\d+ 歳\) が亡くなった$"))  # 子の死 (病・けが・飢えの区別は記録にない)


def age_class(age):
    """年齢 (歳) → 区分 (生まれる前は None)"""
    if age is None or age < 0:
        return None
    return next(n for n, lo, hi in AGE_CLASSES if age >= lo and (hi is None or age <= hi))


def age_on(p, day):
    """その日の年齢 (era2 の季節の終わりの年のとり方と同じ: (日 − 生まれた日) // 1 年)"""
    return None if p.get("born_day") is None else (day - p["born_day"]) // era2.YEAR


def death_cause(text):
    """出来事「死」の文 → 死因の種類"""
    return next((n for n, pat in DEATH_CAUSES if re.search(pat, text)), "その他")


def day_label(day):
    return f"{day // era2.YEAR}年{day % era2.YEAR + 1}日目"


def season_label(day):
    return f"{day // era2.YEAR}年の{world.season(day)}"


def season_end(day):
    """その日をふくむ季節の終わりの日"""
    return day + world.SEASON_DAYS - 1 - day % world.SEASON_DAYS
```

`大人` (15) coincides with era2's `ADULT`; at season ends `child` is removed exactly when `age_on ≥ 15`, so class and flag agree in all rows (test B). Ages before 489 for people who died in Society 1.0 are not meaningful (no ageing then); their rows exist only in `people.json`.

---

## 7. Code changes

### 7.1 `sim/society/records.py` (new)

Docstring: 「ダッシュボードの内側の記録 (docs/dashboard_records_spec.md)。世界の進み方には使わない: state を読むだけで、変えない・乱数を使わない」. Contents: §6 functions; `SNAP_V = 1`; `_kinds(foods)`; `event_sig(state, eid)` = first 16 hex of `sha1(f"{day}|{type}|{who}|{text}")`; `snapshot(state, meeting_first=None, event_first=None, source="live", notes=None)` (§2.2); `append_snapshot(data_dir, row)` (mkdir, open `"a"`, one line, flush); `load_snapshots(data_dir, state)` (§2.4).

### 7.2 `sim/society/era2.py`

1. `meeting_first(state, day)` and `MEETING_EVENTS` (§3.4), pure, placed before the year-name section:

```python
MEETING_EVENTS = ("話す", "掟", "もめごと", "収める", "裁き", "罰", "祭り", "まとめ役", "共同の仕事", "加わる", "去る", "ヤギを食べる", "年の名前")


def _meeting_event(e):
    t, x = e["type"], e["text"]
    if t not in MEETING_EVENTS:
        return False
    if t == "もめごと":
        return "話し合ったが" in x  # 季節の終わりの「言い出した」「重なった」「言わなくなった」は、集まりの前
    if t == "去る":
        return "受け入れられず" in x  # 蓄えが尽きて出ていくのは、季節の途中
    if t == "まとめ役":
        return not x.endswith("村にまとめ役がいなくなった")  # 亡くなった・村を出たのは、季節の終わり
    return True


def meeting_first(state, day):
    """day 日の終わりの季節の集まりの、最初の出来事の id (集まりの出来事がなければ、その日の次の id)。読むだけ
    (集まりの出来事は、季節の終わりの出来事のあとに、同じ日の日付で記録される。2026-10-09 に、git に残る 51 回の集まりで、すべて合うことを確かめた)"""
    ev = state["events"]
    i = len(ev)
    while i > 0 and ev[i - 1]["day"] > day:
        i -= 1
    end = i
    while i > 0 and ev[i - 1]["day"] == day and _meeting_event(ev[i - 1]):
        i -= 1
    return ev[i]["id"] if i < end else (ev[end - 1]["id"] + 1 if end else 0)
```

2. `CRITERIA_PARTS` and `criteria_progress(era, ind)` next to `CRITERIA` (data + a pure function; test B asserts `all(met) == CRITERIA[era][1](ind)` on every snapshot):

```python
# 条件の中身 (ダッシュボードの「条件 × 季節」のため。CRITERIA と同じ中身を、値と目標の形でも持つ。合っているかは試しで確かめる)
CRITERIA_PARTS = {
    "G1": [("population", ">=", 10, "人 (子をふくむ)"), ("children_1y", ">=", 2, "村で生まれて 1 歳をこえた子"), ("joined", ">=", 1, "よそから来た人")],
    "G2": [("harvest_2y", "is", True, "畑の収穫が 2 年続く"), ("goats", ">=", 5, "飼うヤギ"), ("farm_share", ">=", 0.5, "1 年に食べた量のうち育てたものの割合")],
    "G3": [("surplus_2y", "is", True, "余りの年が 2 年続く"), ("specialists", ">=", 1, "作ることに 20 日以上使った人")],
    "G4": [("owned", "is", True, "家ごとの持ち物がある"), ("inherits", ">=", 1, "受けつぎ")],
    "G5": [("g5_stage", ">=", 2, "第 2 段"), ("households", ">=", 6, "家族"), ("leader", "set", None, "まとめ役がいる"),
           ("penalty_laws", ">=", 3, "罰のある掟"), ("judged", ">=", 2, "まとめ役の裁き"), ("penalties", ">=", 1, "罰を払わせた")],
}


def criteria_progress(era, ind):
    """条件ごとの、今の値・目標・そろったか (読むだけ)"""
    ok = {">=": lambda v, t: v is not None and v >= t, "is": lambda v, t: v is t or v == t, "set": lambda v, t: bool(v)}
    items = [{"key": k, "label": lab, "op": op, "target": t, "value": ind.get(k), "met": ok[op](ind.get(k), t)}
             for k, op, t, lab in CRITERIA_PARTS.get(era, [])]
    return {"era": era, "items": items, "all_met": bool(items) and all(x["met"] for x in items)}
```

3. Year names (§5.2) and its hooks in `apply_answers`, `season_prompt`, `feeling_prompt`; `import unicodedata`.
4. Optional `LEDGER_NOTES`, `_note`, `take_notes` and the three hooks (§4.9).

### 7.3 `sim/society/step.py`

```python
import records  # noqa: E402  (ダッシュボードの内側の記録。読むだけで、世界の進み方には使わない)
import subprocess  # noqa: E402

RECORDS_ON = os.environ.get("SOC_RECORDS", "1") != "0"  # 0 なら記録を作らない (試し用)


def _snap(state, before, first):
    """季節のあとの控え (records/snapshots.jsonl の 1 行)。読むだけ。失敗しても季節は進んだまま"""
    notes = era2.take_notes() if hasattr(era2, "take_notes") else None
    if not RECORDS_ON:
        return None
    try:
        return records.snapshot(state, meeting_first=before, event_first=first, notes=notes)
    except Exception as ex:  # 記録の失敗で、世界を止めない
        print(f"記録: 季節の終わりの控えを作れなかった ({type(ex).__name__}: {ex})")
        return None


def _records(snap):
    """控えを 1 行足して、記録を作り直す (保存のあと。失敗しても季節は進んだまま。終わりのコードも変えない)"""
    if not RECORDS_ON:
        return
    try:
        if snap:
            records.append_snapshot(DATA, snap)
        r = subprocess.run([sys.executable, str(Path(__file__).parent / "tools" / "build_records.py"), "--data", str(DATA), "--quiet"],
                           timeout=300)
        if r.returncode:
            print(f"記録: 記録を作れなかった (終わりのコード {r.returncode})。python3 sim/society/tools/build_records.py で作り直せる")
    except Exception as ex:
        print(f"記録: 記録を作れなかった ({type(ex).__name__}: {ex})。python3 sim/society/tools/build_records.py で作り直せる")
```

Season branch (new lines marked ★; order of everything else unchanged):

```python
        before = state["next_event"]
        if hasattr(era2, "take_notes"):
            era2.take_notes()                                   # ★ 前の書きとめを捨てる
        feels = read_feelings(state)
        era2.apply_answers(state, read_answers(state, "season"))
        era2.apply_feelings(state, feels)
        first = era2.simulate_season(state)
        state["era2"]["last_first"] = first
        if not any(p["alive"] for p in state["people"]):
            snap = _snap(state, before, first)                  # ★
            save(state)
            export(state)
            _records(snap)                                      # ★
            ...                                                 # (unchanged message, sys.exit(4))
        if era2.check(state):
            ...                                                 # (unchanged)
        snap = _snap(state, before, first)                      # ★ 保存の前に読む (同じ state)
        save(state)
        write_prompts(state, "season")
        export(state)
        _records(snap)                                          # ★
        for e in state["events"]:                               # (+ 「年の名前」, §5.3)
```

`season_step.sh` already commits `sim/society/data` (records included). No other command changes; `export` is untouched.

### 7.4 `sim/society/tools/build_records.py` (new)

Module docstring with the CLI (§3.1). Sections: load → ids/people/households/membership → rounds/seasons → per-season pass (village/household/person rows) → replay/goats/ledger → year names/laws/disputes → columns/meta → atomic write. Constants: `ACT_BY_EVENT` (copied from step.py, plus 狩り), item order, reason order, `COLUMNS` table. Imports: `era2`, `world`, `records`, `characters` (for `parse`) via `sys.path.insert(0, <sim/society>)`.

### 7.5 `sim/society/tools/backfill_snapshots.py` (new)

§2.5. Prints `day sha source rows_added`. Exit 0 even if nothing to add.

---

## 8. Tests (`sim/society/tools/test_records.py`, unittest; never write to `sim/society/data` except where noted; never run `step.py season` on the real data)

Fast tests run by default (≈ 1 min). Long A/B runs: `python3 sim/society/tools/test_records.py --ab` (≈ 15–25 min; each season step ≈ 11 s). Code A = `git archive <base commit> sim/society` extracted to `/tmp/recab/codeA` (the code before this work); code B = working tree copied to `/tmp/recab/codeB`. Each variant has its own `SOC_DATA` copy.

**A. The world is unchanged (A/B on copies)**
- A1 Real answers, no year names: start from the git state of day 1709 (commit `5a17727`, `hold` false), copy `answers/day1709 … day1979` (season + feeling). Run 10 seasons with A and with B. After every season: `state.json` byte-identical; `app_data.json` byte-identical; season and feeling prompts byte-identical except the season prompts of day 1799 and 1919 (year ends), whose diff is exactly: the 「## 年の名前」 section, the inserted いま item, the renumbered 気持ち item, the `year_name` JSON line. B has `records/` (10 snapshot rows), A none.
- A2 Real answers with year names: as A1, but B′'s copies of `answers/day1799` and `day1919` get `year_name` added (two reps write the same name to test weights; one writes `"..."`). Compare A with B′: (i) B′ events with 「年の名前」 removed equal A's events in (day, type, who, text, data); (ii) states equal after removing `era2.year_names` and mapping B′ ids to A ids (shift by the number of removed events with smaller id) in `next_event`, `era2.last_first`, `g5.meet_first`, `g5.disputes[*].event`/`because`; (iii) every prompt after day 1799 contains 「## 村で覚えている年の名前」; (iv) `year_names` equals an independent re-implementation of §5.1 in the test.
- A3 Synthetic run: from a copy of today's state (2009), 8 seasons (2009→2249, year ends 2039 and 2159) with a deterministic answer generator (job rotation over `acts2`, `keep` true for odd households, `feast` every third season, `judge` 「つぐなう」 for open disputes, accept visitors, `year_name` only in B′). A vs B byte-identical; A vs B′ as A2.
- A4 Purity: for the current state and each of the 52 git states, `json.dumps(state, sort_keys=True)` is equal before and after `records.snapshot`; the builder and backfill leave `sha256` and `mtime` of the real `state.json`, answers and prompts unchanged (the builder writes only into a scratch `--data` copy's `records/`; the real data is only read).
- A5 (if §4.9 adopted) Famine on a copy: empty the copy's village store, put 草の種 in two house stores, run 1 season with A and B: states byte-identical; B's snapshot `notes` non-empty; ledger for those houses closes with 0 residual; recomputed without notes, the residual equals the notes.

**B. Backfill against known values** (backfill + build into a scratch `records/` from the real data, read-only)
- 52 valid snapshot rows (489, 509…2009), 0 invalid; 51 village rows; first season `days == 20`.
- 1709: population 22, adults 15, children 7, households_with_adults 8, goats 10 (female 6), pots 340, sickles 34, store 草の種 168,396 / 木の実 6,465 / 芋 18, store_days 323, fields ripe 12 / harvested 50,400 / fallen 30,518, pests 62, wealth_gini 0.843, house_gini 0.375, homes_built 5, H02 store 7,795.26 and wealth 623,621, H01 goats 3 (wealth 90,000), era G4 → era_end G5 (advanced). ヨナ (P023): job 土器づくり, `days_by_activity.土器づくり` 30, pots 72, tree_pick_evenings 30, skill 土器 1.0.
- 1859: population 25 (16/9), households 9, goats 17 (female 9), pots 614, sickles 24, store_days 339, H02 12,137.26, H04 トワ 8,670, H03 ケト 14; the feast with cost 木の実 1,236 and the joining of セキ・ホノ・ルネ (P028–P030) belong to season 1859 (meeting 1829); G5 stage 2 opened in season 1859.
- 2009: population 27 (16/11), households_with_adults 9, households_with_members 10 (H05 status 大人がいない), goats 32 (female 22), pots 554, sickles 22, house stores H01 6,551 / H02 12,137.26 / H03 14 / H04 14,609 / H05 4,094.
- people.json: 35 rows with the ids of §1.2; causes as §1.3; `age_at_death` equals the age in each 死 text; membership 35 rows, households as in §1.2.
- Every meeting: the season answer file names equal the answerers derived from membership and ages (all adults before 1259; from 1259 the oldest adult of each household, ties by people order, plus a non-representative leader) — verified 51/51 with the git states; `criteria_progress(...).all_met == CRITERIA[era][1](indicators)`; `age_class(age) == "大人"` ⇔ not `child` for living people.
- Prompts cross-check (G4+): village store, goats, pots, sickles and every house's store in the season prompt of day D match the records (after rounding).

**C. Ledger closure**: for all 51 seasons, `記録にない差` is absent (|diff| < 1e-6 kcal / exact count) for every H food account, every goat account, 村 土器 and 村 鎌; the 村 food total residual ≤ 100 kcal; per-item residuals are reported (expected ≤ ~35 units). Specific rows: 1709 H02 草の種 刈った +7,798 and 虫 −2.74; 1829 H02 +4,342, H04 +8,684; 1859 H04 −14 / H03 +14 (M1); 1949 H04 +5,692, H01 +6,798, H05 +4,094; 1979 H01 −247 / H04 +247 (M2); goats 2009 生まれた 15, いなくなった 6; 1889 生まれた 9, いなくなった 3.

**D. Determinism**: build twice → identical bytes; build on a copy of the data dir → identical; shuffled `snapshots.jsonl` lines → identical; an extra invalid row (wrong `sig`) → ignored, counted in `meta.json`.

**E. Boundaries**: `era2.meeting_first` equals the git `next_event` for all 51 meetings; with snapshots removed, the builder's rows are identical except the snapshot-only columns (null) and `snapshot: false`.

**F. Year-name units** (in memory on the git state of day 1919, a year end, and on a non-year-end state): weights from family sizes; tie → oldest proposer; normalisation (`「 豊かな年 」` = `豊かな年`); `"..."`/`なし`/multi-line/`フェーズが…` ignored; non-year-end `year_name` ignored; second call for the same year ignored; no proposals → state identical to A; prompts at 1919 contain the digest with ≤ 15 events + harvest line; prompts after a name contain the list with 「(去年)」 on the newest.

**G. step.py smoke** (scratch `SOC_DATA`): one season → exit 0, `snapshots.jsonl` +1 line, records rebuilt, `meta.state_day` updated; with `build_records.py` replaced by a failing stub → exit 0, `state.json` saved, warning printed, the snapshot line still appended; `SOC_RECORDS=0` → no `records/` written; the 「全員いない」 path (copy with everyone dead after the season) still exits 4 with a snapshot.

**H. Performance** (real data, read-only, output to scratch): builder full rebuild ≤ 5 s (fail > 15 s); `records.snapshot` ≤ 0.2 s; backfill ≤ 60 s; step.py season wall time B − A ≤ 5 s (measured in A1).

---

## 9. Risks and notes

- **Old states in git** were written by older code; `records.snapshot` must use `.get` with defaults everywhere (e.g. no `house` before G4, no `household` before 1109, goats without `owner`). Values are taken as they were at the time, which is the point.
- **Event ids = list indexes** (true today; `log` appends). `meeting_first` and `_year_digest` rely on it; test E guards it.
- **Free-text names** are shown back to all villagers in later prompts; the normalisation guard keeps them short, single-line and away from workflow stop phrases.
- **Famine breaks** create 2+ rounds per season; never happened yet (all 52 answer days are season ends); covered by the round model and test A5.
- **Fission and new households**: membership/households already model intervals and `origin_household_id`; ledger holders leave via 「村を出て持っていった」.
- **G6** (design pending): other villages become new holders (`V1`…), new items (黒曜石) and reasons (交換・貸した・返した); villagers' own records (印・数え札・粘土の板) go into a separate 【村】 file later. The ledger vocabulary and `columns.json` tags are open for that.
- **Superseded**: `sim/society/app/records_demo.html` was built from a `/tmp` builder; the dashboard should read `records/` instead.
- **Size**: records grow by ≈ 60–80 KB per season (committed with the data each season).

## 10. Decisions for 本人 (recommendation first)

1. Use the season-end states kept in git for the past (recommended) / do not (past values of goats per house, house stores, skills, hunger, village-store flows stay null).
2. Add the 3-point `LEDGER_NOTES` instrumentation (recommended; nothing enters `state.json`) / do not (eating from house stores and repeated steals appear as 記録にない差).
3. The 村 food account includes adults' hands (recommended) / village store only (then most daily flows are unknown by kind).
4. Year name by plurality of family-adult weights (recommended) / only with a majority of adults (most years unnamed).
5. Show the year's main events (≤ 15) in the year-end prompt (recommended) / do not.
6. In prompts, refer to years by day range (recommended); 「16年」 only in records.
7. Commit `records/` with the data every season (recommended).
8. Also write `laws.json` and `disputes.json` (recommended).
