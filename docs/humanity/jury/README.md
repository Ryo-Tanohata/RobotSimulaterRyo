# 陪審団による評定 (D08・D10)

職務特性モデル (Hackman & Oldham) の 5 項目を、仮想の陪審員に独立に評定させたときの材料と結果です。
接地度の「意味」と「結果」の軸は、ここの陪審団の平均を正式な評定として使っています (`../score_grounding.py`・`sim/society/grounding.py`)。

| ファイル | 中身 |
|---|---|
| `jobs.json` | 評定した 33 の仕事 (テックツリーの代表者・別例・シナリオ 20、村の仕事 13)。評定の答えが透けないよう、仕事の中身だけを書いた説明 |
| `personas.json` | 陪審員 14 体 (正式な 12 人と、モデルの違いを見るための入れ替え 2 体 `J3s`・`J4s`)。人物・モデル・時代のまとまり |
| `prompt.md` | 陪審員へのお題のひな形。`prompts/` はそこから作った 1 人分ずつのお題 |
| `make_prompts.py` | `prompt.md`・`personas.json`・`jobs.json` から `prompts/<id>.md` を作る |
| `answers/` | 陪審員の答え (1〜7 の評定) |
| `creator_ratings.json` | 作り手 (Claude) が先に付けた評定。陪審団の平均に置き換える前の値で、比べるために残す |
| `analyze_jury.py` | 集計。陪審員どうしの一致 (級内相関、Shrout & Fleiss 1979)、作り手との一致、モデル・人物・時代の違い、ブラウナーの順位 |
| `results.json` | 集計の結果。`per_job` の `jury_ratings` が正式な評定 (12 人の平均) |

## 動かし方

スクリプトは `PYTHONUTF8=1` を付けて `python3.13` で動かす (本人の PC は `py -3`)。

1. 陪審員を足すときは `personas.json` に足し、`python3.13 docs/humanity/jury/make_prompts.py` で `prompts/<id>.md` を作る。作り方: `prompt.md` の `{PERSONA}` に人物 (`label`)、`{NOTE}` に人物の説明 (`note`)、`{ID}` に陪審員の ID を入れ、`{JOBS}` に仕事の一覧 (`jobs.json` の順に 1 行ずつ `- {id} {title}: {desc}`) を入れる。今の 14 人分のお題は、これで 1 バイトも違わずに作り直せる (`--check` を付けると、書かずに同じかだけ確かめる)
2. 1 人に 1 体のサブエージェント (`personas.json` の `model`) に、お題を読んで JSON だけを `answers/<id>.json` に書かせる。ほかのファイルは読ませない
3. `python3.13 docs/humanity/jury/analyze_jury.py` で集計し、`python3.13 docs/humanity/score_grounding.py` でテックツリーを、`sim/society/grounding.py` の表を陪審団の平均に合わせて直す (村の表は手で写す)

## 分かっていること (2026-10-14)

- 陪審員どうしの一致はとても高い (級内相関 0.77〜0.89)。ただし同じ会社のモデルなので、本当の合意とは言えない
- 人物よりモデルの違いのほうが評定を動かす (同じ人物でモデルを変えると 0.64〜0.87 点ずれ、同じモデルで人物を変えると 0.46 点)
- 人物は自分と同じ種類の仕事を高く見る
- 1 人あたり約 7 万トークン (ほとんどはサブエージェントの起動の分)
