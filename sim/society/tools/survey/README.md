# 論文 2・実験 1: LLM に修士論文の 54 問を答えさせる (村なし)

事前登録: [docs/research/humanity/paper2_exp1_prereg.md](../../../../docs/research/humanity/paper2_exp1_prereg.md) (文面・人数・仮説・決めの線はそちらが正)。
問いの出どころ: [docs/research/humanity/thesis2017_questionnaire.md](../../../../docs/research/humanity/thesis2017_questionnaire.md)。

| ファイル | 中身 |
|---|---|
| `items.py` | 54 問・規範の数・グレーゾーンの 14 問・人間の表 3・条件 (C0〜C4 と人数) |
| `personas.py` → `personas.json` | 人格 100 人 (種 20261029。ビッグファイブの z・年齢・性別・都道府県・見せるための MBTI ラベル) |
| `prompts.py` → `prompts/<ID>.md`・`respondents.json` | 1 人 1 枚の紙 (290 枚)。C1_k と C2_k は同じ人格 P(k) |
| `survey_workflow.js` | Workflow の台本。1 人 1 agent。ファイルは書かず、答えを返す |
| `save_answers.py` | Workflow の返した値 (か journal.jsonl) から `answers/<ID>.json` を書く |
| `analyze.py` | `answers/` → `out/` (summary.md・表・図) |
| `test_survey.py` | LLM を使わない試し (人工の答えで最後まで動くか) |

```
python3 personas.py && python3 prompts.py    # 作り直し (同じものができる)
python3 test_survey.py                       # 試し
```

## 回し方 (メインのセッション。本人が費用を決めてから)

1. **試しの回 (10 人):** Workflow に `scriptPath: sim/society/tools/survey/survey_workflow.js`、
   `args: {"root": "/home/user/RobotSimulaterRyo", "limit": 2}`。
2. **答えをしまう:** Workflow の結果に出る記録の場所 (transcriptDir) の `journal.jsonl` を渡す (結果の文が長くて切れても、journal には全部ある)。
   試しの回は本番とまぜない:
   `cd sim/society/tools/survey && python3 save_answers.py --dir answers_pilot <transcriptDir>/journal.jsonl`
   (返した値を JSON のファイルに書いたなら、そのファイルを渡してもよい。`{"respondent_id", "answers"}` の形をみな拾う)。
   形・中身・トークンを見て、よければ本番へ。`answers_pilot/` は分析に使わない。
3. **本番:** `args: {"root": "/home/user/RobotSimulaterRyo"}` (290 人)。条件を分けて回すなら `"conditions": ["C0", "C3", "C4"]` など。
   止まったあとの続きは、`answers/` にある ID を `"done": ["C1_001", …]` で渡すと、とばす。
   `python3 save_answers.py <transcriptDir>/journal.jsonl` → `answers/` に書き、足りない ID を表示する。
4. **分析:** `python3 analyze.py` → `out/summary.md` ほか。答えと out/ をコミットする。

台本は、答えがない・ID が違うときに 1 回だけ聞き直す。それでもだめな ID は返り値の `missing` に入る (prereg 9.)。

# 論文 2・実験 2: 性格の言葉でなく「暮らし・立場・損得」を持たせる

事前登録: [docs/research/humanity/paper2_exp2_prereg.md](../../../../docs/research/humanity/paper2_exp2_prereg.md)。54 問・選択肢・順は実験 1 と同じ。

| ファイル | 中身 |
|---|---|
| `items.py` の `CONDITIONS_EXP2` | D1 (sonnet 100)・D2 (sonnet 100 + 最近のまわりの様子)・D3 (opus 30)。わけを書く 5 問・ダウンロードの 5 問・はみ出しやすい時 4 つ |
| `situations.py` → `situations.json` | 暮らし 100 人 (種 20261029。分布は仮定)。D2 の 4 つの様子 (16 通りを同じ数ずつ) もここ |
| `prompts_exp2.py` → `prompts_exp2/<ID>.md`・`respondents_exp2.json` | 1 人 1 枚 (230 枚)。D1_k・D2_k・D3_k は同じ暮らし S(k) |
| `survey_workflow_exp2.js` | Workflow の台本 (実験 1 と同じ作り。数 → わけ の順のスキーマ) |
| `save_answers.py --exp 2` | → `answers_exp2/<ID>.json` |
| `analyze.py --experiment 2` (`analyze_exp2.py`) | `answers_exp2/` → `out_exp2/`。部品は analyze.py をそのまま使い、実験 1 の `answers/` (C1・C4) ともくらべる |

```
python3 situations.py && python3 prompts_exp2.py   # 作り直し (同じものができる)
python3 test_survey.py                             # 試し (実験 1 と 2。人工の答えで仕込んだ効き目を見つけるか)
```

回し方 (メインのセッション。本人が費用を決めてから):

1. **試しの回 (6 人):** Workflow に `scriptPath: sim/society/tools/survey/survey_workflow_exp2.js`、`args: {"root": "/home/user/RobotSimulaterRyo", "limit": 2}`。
   `cd sim/society/tools/survey && python3 save_answers.py --exp 2 --dir answers_exp2_pilot <transcriptDir>/journal.jsonl`
   1 人あたりのトークン × 230 が 1,500 万をこえる見込みなら、止めて本人に報告 (prereg 6.)。
2. **本番:** `args: {"root": "/home/user/RobotSimulaterRyo"}` (230 人)。分けるなら `"conditions": ["D1"]` など。続きは `"done": [...]`。
   `python3 save_answers.py --exp 2 <transcriptDir>/journal.jsonl` → `answers_exp2/`
3. **分析:** `python3 analyze.py --experiment 2` → `out_exp2/summary.md` ほか。答えと out_exp2/ をコミットする。

## 実験 2 のわけの分け方 (探索)

`reasons_codebook.py`: `out_exp2/reasons.csv` (1,150 件) を、修士論文の 7 つの考え方 + 決まりに従う側のわけ 4 つで、正規表現の辞書だけで分ける (LLM は使わない)。
→ `out_exp2/reasons_coded.csv`・`reasons_summary.md`・`fig_reasons.png`。確かめの記録は `reasons_validation.md`。`--sample 60 --seed N` で確かめ用のくじ。
