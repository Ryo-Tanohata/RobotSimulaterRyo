<!-- 設計書 (まだコードにはしていない)。2026-10-08、本人の PC のセッションで、ワークフローで作った:
     3 つの角度 (史実 / 動き / 小さく正しく) の設計 → 2 人の判定役が採点 (史実 90・動き 89.75・小さく 76.25) → 史実の案をもとに、ほかの案のよいところを足してまとめた。
     まとめ役は、写しのデータ (1559 日目) の上で、メモリの中だけで試し回しをしている (この文書の 0.)。リポジトリのコードはまだ変えていない -->

# G5 リーダーと決まり: 設計書 (日本語の要約)

- **第 1 段 (集まり・長老・祭り)**: 家どうしのもめごと (ヤギが畑を荒らした / 家の倉 / 村の蓄えの取りすぎ / よその家の畑を刈った) が、家の数が多いほど起きる (家どうしの組の数 H(H−1)/2 に比べる)。季節の集まりで、家族の代表が「つぐなう / ゆるす」を答え、半分をこえればおさまる。決まらなければ長老 (争っていない家の、いちばん年上の大人) が決める。祭りは村の全員の 3 日分の食べ物を使い、もめごとの半分を仲直りさせる
- **第 2 段 (まとめ役・罰・裁き)**: 第 1 段でまとまったとき (家族 6 つ以上・G5 で 1 年・まとめ役なしで 2 回おさめた) か、もめごとが 2 季節おさまらないとき (ゆきづまり) に、まとめ役を選ぶ欄と、掟に罰をつける欄が出る。選ぶかどうかは人が決める。まとめ役は自分の家のもめごとは裁けない。共同の仕事を呼びかけられる (従うかは各人)
- **村が分かれる**: もめごとが 2 季節おさまらないと、言い出した家が村を出ていくことがある (1 年に 1 つの家まで。家が 3 つ・大人が 6 人より少なくならない)
- **G5 の条件 (第 2 段)**: 家族が 6 つ以上で、まとめ役がいる。罰のある掟が 3 つ以上採用。まとめ役が 2 回以上裁いた。罰を 1 回以上払わせた。第 1 段・第 2 段に入ったときは止まらずに記録する
- **G5 の前は何も変わらない**: すべて G5 に入ってから働く。G3・G4 の結果が前と同じになることを確かめるための記録 (前と後で state.json が同じになるか) は、本人の PC で取った (この PC の一時フォルダの台本で取った値。家の PC では、この文書の 13. の試し方で確かめる)
- **本人に確かめること**: この文書の 15. (おすすめは書いてある通り)。数はすべて【仮定】

次にすること: この設計書の通りにコードを書き (`era2.py` 約 330 行・`step.py`・`resume.py`)、13. の試し方で確かめ、計画書の 5. に G5 の節を足す。

---

# G5 リーダーと決まり: final implementation spec

This spec takes design "history" as its base and grafts in the best parts of "dynamics" and "minimal". Every fatal flaw the judges listed is fixed; §16 maps each flaw to its fix. All edit points were re-checked against the current `sim/society/era2.py` (HEAD `d4bd5e03`, 1007 lines).

## 0. What was verified, and how

All checks ran in memory: the patched `era2` source was exec'd as a module against a deep copy of `data/state.json` (day 1559). No repo file was written.

| Check | Result |
|---|---|
| **Pre-G5 invariance, G3.** One season with the real `answers/day1559`. | Next-season prompts byte-identical to HEAD. `state.json` identical once the 16 new indicator keys are removed. No `g5` key. |
| **Pre-G5 invariance, G4.** 3 seasons forced to G4, with scripted `keep`, `eat_goat`, goat catching, and G5 fields (`judge`, `feast`, `leader`, `penalty`) present in the answers. | Same result as G3; the G5 fields were ignored. All gated G5 functions were replaced by stubs that raise, and none fired. `_rng` salts used were only {3, 7, 11, 31}; 37 was never used. |
| `answerers()` | Identical to HEAD in both rep mode and non-rep mode. |
| **G5, policy "coop."** Judge everything つぐなう, feast every 3rd season, elect タヒ (not a rep), one penalty law per season. | Stage 2 opened via まとまり at the end of season 4. タヒ was elected 15/15 at the season-5 meeting. The leader judged 3 disputes and 3 penalties were paid. **G6 reached at the end of season 8 (day 1799).** |
| **G5, policy "divide."** Reps split つぐなう/ゆるす, no feast, everyone writes their own name for leader. | The elder broke ties and disputes settled. Stage 2 opened via まとまり. No leader, no fission, criterion not met after 12 seasons. |
| **G5, policy "silent."** No G5 fields. | Stage 2 opened via ゆきづまり at the end of season 3, and a household left the same season. A second household left 8 seasons later (gap ≥ 1 year). Households 8 → 6, adults never below 11. Rep mode switched off cleanly when adults reached 12. |
| **Unit checks** | All passed: parsers, `_pay` (store first, then rounded goats), theft events and incidents, the elder tie-break, the elder in the minority, TALK_MAX capacity, leader recusal, unlimited leader judgments, feast reconciliation and cost, election 7/16 (no) and 9/16 (yes) with rep weighting, recall by なし, dead leader cleared, fission taking a newborn with no household yet, and the fission guards. |
| **Rendered prompts** | Stage 1, stage 2 rep, and stage 2 non-rep leader all render correctly; see §10.4. |

**Note for the implementer.** On this machine a Bash heredoc of about 16k characters gets truncated, and about 40k gives ENAMETOOLONG. Put test scripts in the scratchpad directory and run them from there.

---

## 1. Overview and decisions

| Question | Decision | Why |
|---|---|---|
| How stage 1 works | **Assembly and elder.** At each season meeting, each open dispute (oldest first, at most `TALK_MAX = 2`) is settled if more than half of adults pick the same answer (つぐなう or ゆるす). Rep weighting applies. Otherwise the **長老** decides: the eldest adult not in either disputing household, whose choice must have at least as many votes as any other.<br>**Feast.** Held on a majority vote. Costs 3 days of the whole village's food from the village store. Reconciles the oldest half of open disputes, halves the dispute probability that season, and blocks fission that season. | Johnson's "sequential hierarchy" means household heads (here the reps) deciding by consensus, plus ritual. The feast follows Hilazon Tachtit, Göbekli Tepe and Bandy 2004. |
| How stage 2 works | A **まとめ役** is elected by more than half of adults (rep-weighted). The leader judges any number of disputes, but not ones involving their own household; this happens before the assembly. The leader can start a feast alone, and can make one `call` for joint work, which each person is free to follow or not.<br>**Penalty laws (罰)**: a law can carry a penalty tied to one dispute kind. While it is adopted, every incident of that kind becomes a dispute, and a つぐなう verdict pays the law's amount. | Johnson's "simultaneous hierarchy", Stein 1994 (ritual mobilization of staples), Fried (a leader who calls but cannot compel). |
| **Gate (stage 1 → 2)** | **Soft gate, two doors.** The leader field and the penalty field (with their FACTS text) appear only after stage 2 opens. It opens either through **まとまり**, when the stage-1 milestone is reached (success), or through **ゆきづまり**, when a dispute has stayed unsettled for 2 seasons (failure). Earliest opening: end of G5 season 3 via ゆきづまり, end of season 4 via まとまり. | This keeps the user's order (stage 1, then stage 2) without building a success-only ladder: the Johnson caveat in periodization §5. Showing `leader` from season 1 would prime haiku to elect someone at once, so stage 1 would never be observed. Nothing forces a leader; a leader can be recalled with 「なし」, and penalty laws can be abolished by the usual law vote. |
| Stage-1 milestone | All of: households H ≥ 6, no leader, at least 1 year in G5, and at least 2 disputes settled without a leader (by assembly, elder or feast). Logged as event `段階`, stored in `g5.stage1`. | Tied to scalar stress (H ≥ 6) and to the village actually holding together for a year. |
| Hold at stage 1 or stage 2? | **No.** Both are logged (`段階`), printed by step.py, and reported every 5 seasons. The only hold is the automatic one when G5 → G6. The log text never contains 「フェーズが…に進んだ」, which is the regex the workflow stops on. | A hold triggers the full phase routine (report, evaluation, 8–9 minute video). G5 is a single phase, and 第 3 部 already ends there. |
| Does the criterion require stage 1? | **No.** If the village skips stage 1 (ゆきづまり first, then a leader), the report records it as a deviation from the textbook order. `g5.open.how` and `g5.stage1` hold the facts. | Requiring it could leave the run stuck forever, and the order is our interpretation. |
| Fission | Only the complainant household (`from`) can leave. The full rules are in §9. | Ethnographic fission: the dissatisfied faction moves out. Bandy 2004. |

---

## 2. State schema

Everything is created lazily, by G5 code paths only, so `state.json` is unchanged before G5.

```python
state["era2"]["g5"] = {
  "start": 1619,                 # G5 の最初の集まりの日 (_g5() を最初に呼んだ日 = G4→G5 の日)
  "stage": 1,                    # 1 / 2
  "open": None,                  # {"day": d, "how": "まとまり" | "ゆきづまり"}  第 2 段に入った日
  "stage1": None,                # 第 1 段の目安を記録した日 (int) / None
  "disputes": [ {                # もめごと
      "id": "M0", "kind": "ヤギ"|"倉"|"蓄え"|"刈る",
      "from": "アルの家",          # 言い出した家 (損をした家)
      "against": "トワの家",       # 相手の家
      "day": 1589, "harm": 269,   # 草の種のつかみ
      "what": "…", "because": [27301], "event": 27305,
      "status": "収まっていない"|"収まった"|"なくなった"|"去った",
      # 収まったとき:
      "verdict": "つぐなう"|"ゆるす"|"仲直り", "by": "まとめ役"|"集まり"|"長老"|"祭り",
      "judge": "タヒ"|None, "paid": 50, "law": "L130"|None, "end": 1649 } ],
  "next": 0,                     # 次のもめごとの番号
  "leader": None, "leader_day": None,          # まとめ役の名前、選ばれた集まりの日 (step_day)
  "leaders": [ {"name", "day"} ],              # 選ばれた順
  "votes": None,                 # {"day", "votes": {"タヒ": 9, "なし": 2}, "adults": 16}  前の集まりの票 (お題に見せる)
  "call": None,                  # {"by", "activity", "day"}  まとめ役の呼びかけ (次の集まりで、応じた人を数える)
  "settled": 0,                  # まとめ役のいないときに、集まり・長老・祭りで収めた数 (第 1 段)
  "judged": 0,                   # まとめ役が裁いた数
  "penalties": 0,                # 罰の掟で、実際に何か払われた数
  "feasts": 0, "feast_day": None, "joint": 0,
  "fissions": [ {"day", "household", "people", "goats", "store", "fields", "dispute"} ],  # G6 の「ほかの村」の種にもなる
  "last_fission": None,
  "flow": {}, "reap": {}, "incidents": [],     # この季節だけ (季節の終わりに空にする)
  "last_flow": {"川辺の家": [入れた, 取った]},   # 前の季節 (草の種のつかみ。お題に見せる)
  "meet_first": None,            # この前の集まりの最初の出来事の番号 (集まりの出来事をお題に見せる)
}
state["laws"][i]["penalty"] = {"for": "ヤギ", "pay": 50}   # G5 の第 2 段で提案した掟だけ。law["text"] の後ろに「 (罰: …)」をつける
field["lost"] = 0.2      # 育っている畑だけ (ヤギに荒らされた)。実るときに実りを (1 − lost) 倍。G5 の前はない
person["left"] = day     # 前からある (村を出た)。村が分かれたときにも使う
```

---

## 3. Code

### 3.1 New section in `era2.py`

**Where:** after `_inherit` (ends L499) and before `def _sow` (L502). Also add `import re` after `import random` (L11).

```python
# ---------------- G5 リーダーと決まり: もめごと・集まり・長老・祭り・まとめ役・罰・村が分かれる (2026-10-08 追加。G5 に入ってから働く) ----------------
# 2 段階 (計画 2.1。2026-10-08 本人と決めた): 第 1 段 集まり・長老・祭りでもめごとを収める → 第 2 段 決まったまとめ役・罰・裁き。村が分かれるのも起きてよい結果
# 【文献】Johnson 1982 (規模のストレス): 話し合いで決める単位が 6 ほどをこえると、決めるのが急に難しくなる。答えは (1) 家の長どうしの話し合いと儀礼で
#   まとまる「順番の階層」、(2) 決まった役をおく「同時の階層」、(3) 集団が分かれる、の 3 つ。Johnson は (1) を (2) に代わる平等な仕組みとして示した。
#   (1) → (2) の順はこの計画の解釈 (docs/research/society2_periodization.md 5.)。だから第 2 段 (まとめ役を選ぶ・掟に罰をつける) は、第 1 段でまとまっても
#   (まとまり)、集まりでもめごとが収まらなくても (ゆきづまり) 選べるようになるだけで、選ぶかどうかは人が決める。まとめ役は「なし」でやめさせられる
# 【仮定】もめごとは家どうしなので、話し合いの単位は家 (大人のいる家)。家族の代表 (家でいちばん年上の大人) の集まりは、家の長の「順番の階層」にあたる
# 【文献】ヒラゾン・タクティトの祭り (約 1.2 万年前)・ギョベクリ・テペ (前 9,600〜8,200 年ごろ): 目に見えるまとめ役なしに、祭りと儀礼で人が集まった
#   (docs/research/society2_periodization.md 3 の 5)。Bandy 2004: 決まりのない村は約 300 人で分かれる (人数を 1/10 にして 30 人)
# 【文献】Flannery 2002: 共同の倉から家ごとの倉へ。Stein 1994: ウバイド期のまとめ役は儀礼のために主食を集めた。Fried: ランク社会のまとめ役は呼びかけるが、従わせる力は弱い
# 【文献の目安】話し合いのコストは単位の数の 2 乗に比例 (docs/society2_research.md 9) → もめごとになる見込みを、家どうしの組の数 H(H−1)/2 に比べて決める
# 【仮定】数: もめごとになる見込み 0.3 × H(H−1)/30 (6 家族で 0.3、8 家族で 0.56、0.9 まで。祭りの季節は半分)。新しいもめごとは 1 季節に 3 つまで。
#   集まりで話し合えるのは古いものから 2 つまで。4 季節収まらないと、だれも言わなくなる。祭り = 村の全員の 3 日分。荒らされた畑は実りの 2 割を失う。
#   取りすぎ = 大人 1 人あたり 10 日分 (家の倉に食べ物がある家は 5 日分) をこえる差。刈り手の取り分は 1 割。払うのは 1000 つかみまで。
#   収まらないまま 2 季節で、1 季節に 0.5 × (人数 / 30) の見込みで言い出した家が出ていく (1 年に 1 つの家まで。残る村に家が 3 つ・大人が 6 人より少なくなるときは出ていかない)
G5_P, G5_MAX_P, MAX_NEW, TALK_MAX, DROP_AGE = 0.3, 0.9, 3, 2, 4
FEAST_DAYS, TRAMPLE, FREE_DAYS, REAP_SHARE, MAX_PAY = 3, 0.2, 10, 0.1, 1000
LEAVE_P, BANDY, MIN_HOMES, MIN_ADULTS = 0.5, 30, 3, 6
GRAIN = UNITS["草の種"][1]
DAY_FOOD = BASE_KCAL + 500  # 大人 1 人の 1 日分 (_need と同じ)
OPEN = "収まっていない"
KINDS = {"ヤギ": "家のヤギが、よその家の畑を荒らす", "倉": "よその家の倉から取って食べる",
         "蓄え": "村の蓄えに入れた量にくらべて、ほかの家より多く村の蓄えから取る", "刈る": "よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入る"}
G5_EVENTS = ("もめごと", "収める", "裁き", "罰", "祭り", "まとめ役", "分かれる", "段階", "共同の仕事", "倉から取る")  # お題と step.py で見せる


def _g5(state):
    return state["era2"].setdefault("g5", {
        "start": state["day"], "stage": 1, "open": None, "stage1": None, "disputes": [], "next": 0, "leader": None, "leader_day": None,
        "leaders": [], "votes": None, "call": None, "settled": 0, "judged": 0, "penalties": 0, "feasts": 0, "feast_day": None, "joint": 0,
        "fissions": [], "last_fission": None, "flow": {}, "reap": {}, "incidents": [], "last_flow": {}, "meet_first": None})


def _leader(state):
    """まとめ役の名前 (いなければ None。G5 の前は状態を作らずに None)"""
    return (state["era2"].get("g5") or {}).get("leader")


def _homes(state):
    """大人のいる家 (話し合いの単位)"""
    return sorted({p["household"] for p in adults(state) if p.get("household")})


def stress_p(state):
    """季節の終わりに、もめごとのもとが、もめごとになる見込み (家が多いほど高い。祭りをした季節は半分)"""
    h, g = len(_homes(state)), state["era2"].get("g5") or {}
    p = min(G5_MAX_P, G5_P * h * (h - 1) / 30)
    return p / 2 if g.get("feast_day") is not None and g.get("feast_day") == state["era2"].get("step_day") else p


def _flow(state, p, i, kcal):
    """G5: 家ごとに、村の蓄えに入れた量 (0)・取った量 (1)・家の倉を持つ家が自分の畑にまいた村の草の種 (2) を数える (大人の分だけ。子は村の蓄えで育つ決まり)"""
    if kcal > 0 and era_at_least(state, "G5"):
        _g5(state)["flow"].setdefault(p.get("household") or "-", [0, 0, 0])[i] += kcal


def _incident(state, kind, frm, against, kcal, what, eid=None):
    """もめごとのもと (世界で起きたこと)。季節の終わりに、もめごとになるか決める。frm = 損をした家 (言い出す家)、against = 相手の家"""
    if not frm or not against or frm == against or kcal <= 0:
        return
    inc = _g5(state)["incidents"]
    x = next((x for x in inc if (x["kind"], x["from"], x["against"]) == (kind, frm, against)), None)
    if not x:
        x = {"kind": kind, "from": frm, "against": against, "kcal": 0, "what": what, "events": []}
        inc.append(x)
    x["kcal"] += kcal
    x["events"] += [eid] if eid is not None else []


def _steal(state, p, want):
    """G5: ひどく空腹で、村の蓄えにも自分の家の倉にも食べ物がない大人は、よその家の倉 (多い家から) から取って食べる (出来事は家の組ごとに 1 季節 1 回)"""
    hs, mine, homes = state["era2"].get("house", {}), p.get("household"), _homes(state)
    for h in sorted([h for h in hs if h in homes and h != mine and hs[h]["store"]], key=lambda h: -sum(f["kcal"] for f in hs[h]["store"])):
        if want <= 0:
            break
        by = _move_food(hs[h]["store"], p["food"], None, want)
        want -= sum(by.values())
        new = not any((x["kind"], x["from"], x["against"]) == ("倉", h, mine) for x in _g5(state)["incidents"])
        eid = log(state, "倉から取る", p["name"], f"ひどく空腹の {p['name']} が、{h}の倉から {food_words(by)} を取って食べた", owner=h, home=mine) if new else None
        _incident(state, "倉", h, mine, sum(by.values()), f"{mine}の人が、{h}の倉から食べ物を取って食べた", eid)


def _g5_reap(state, p, owner, n, to_village):
    """刈った草の種 (G5): 村の蓄えに入れば、刈った人の家が入れた量。よその家の倉に入れば「刈る」のもと
    (よその家の畑を刈って、刈った人の家が損をすることはない。持ち主の倉か村の蓄えに入るため。損をするのは、取り分のない刈り手の家)"""
    if to_village:
        _flow(state, p, 0, n * GRAIN)
    elif owner and p.get("household") and owner != p["household"]:
        r = _g5(state)["reap"].setdefault(p["household"], {})
        r[owner] = r.get(owner, 0) + n


def _dispute(state, inc):
    g = _g5(state)
    d = {"id": f"M{g['next']}", "kind": inc["kind"], "from": inc["from"], "against": inc["against"], "day": state["day"],
         "harm": max(1, round(inc["kcal"] / GRAIN)), "what": inc["what"], "because": inc["events"], "status": OPEN}
    g["next"] += 1
    g["disputes"].append(d)
    # 注意: log() の引数名 kind・who・text を、データの名前に使わない (TypeError になる)
    d["event"] = log(state, "もめごと", None, f"もめごと [{d['id']}] ({d['kind']}): {d['from']}が、{d['against']}のことで不満を言い出した。"
                     f"{d['what']} (草の種にして 約 {d['harm']} つかみ 分)", dispute=d["id"], about=d["kind"])


def _g5_season_end(state, frac):
    """季節の終わり (G5。家族を決めた後): もめごとのもと → もめごと → 言われなくなる → 第 1 段・第 2 段 → 村が分かれる"""
    e2, g = state["era2"], _g5(state)
    rng = _rng(state, 37)  # G5 で足した乱数 (37 を 31 で割った余り 6 は、前からの塩 3・7・11・23・29・31 の余り 3・7・11・23・29・0 と重ならない)
    day, homes = state["day"], _homes(state)
    _check_leader(state)
    # (1) ヤギ: 世話をする人が少ない季節 (ヤギが逃げるのと同じ「世話 5 日より少ない」) は、家のヤギが、よその家の畑を荒らすことがある (【仮定】1 頭 0.1、0.6 まで)
    if e2.get("tended_run", 0) < 5 * frac:
        for h in sorted({x["owner"] for x in e2["goats"] if x.get("owner") in homes}):
            n = sum(1 for x in e2["goats"] if x.get("owner") == h)
            fl = [f for f in e2["fields"] if f["state"] in ("育つ", "実った") and f.get("owner") in homes and f["owner"] != h]
            if not fl or rng.random() >= min(0.6, 0.1 * n) * frac:
                continue
            f = rng.choice(fl)
            ripe = f["state"] == "実った"
            lost = int(((f["yield"] - f["harvested"]) if ripe else f["seed"] * 8) * TRAMPLE)
            if lost <= 0:
                continue
            if ripe:
                f["yield"] -= lost
            else:  # 育っている畑は、実るときに減る (減る量は平年の 8 倍で見積もる)
                f["lost"] = round(1 - (1 - f.get("lost", 0)) * (1 - TRAMPLE), 3)
            what = f"{h}のヤギが、{f['owner']}の畑を荒らした"
            eid = log(state, "ヤギ", None, f"世話をする人が少なく、{what} (草の種 約 {lost} つかみ 分)", owner=h, field=f["id"])
            _incident(state, "ヤギ", f["owner"], h, lost * GRAIN, what, eid)
    # (4) 刈る: よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入った (刈った人の家の取り分を 1 割とみる)
    for hh, row in sorted(g["reap"].items()):
        for o, n in sorted(row.items()):
            _incident(state, "刈る", hh, o, n * REAP_SHARE * GRAIN, f"{hh}の人が{o}の畑で刈った草の種 {n} つかみ は、みな{o}の倉に入った")
    # (3) 蓄え: 村の蓄えに入れた量にくらべて、ほかの家より多く取った家 (1 季節に 1 つの家まで。言い出すのは、いちばん多く入れた家)
    flow = {h: v for h, v in g["flow"].items() if h in homes}
    tin, tout = sum(v[0] for v in flow.values()), sum(v[1] + v[2] for v in flow.values())
    if len(flow) >= 2 and tin > 0 and tin >= 0.25 * tout:  # 【仮定】ほとんど蓄えで暮らした季節 (冬・春) は、だれの出し入れも目立たない
        r = max(1.0, tout / tin)  # 村みんなで蓄えを減らした季節は、入れた量の r 倍まで取っても多くない
        hs = e2.get("house", {})
        full = {h for h in flow if hs.get(h, {}).get("keep") and hs[h]["store"]}  # 【文献】Flannery 2002: 家の倉を持ちながら村の蓄えから取る家は目立つ
        over = {h: v[1] + v[2] - v[0] * r for h, v in flow.items()}
        need = {h: FREE_DAYS * DAY_FOOD * frac * sum(1 for q in adults(state) if q.get("household") == h) * (0.5 if h in full else 1) for h in flow}
        cand = [h for h in flow if need[h] > 0 and over[h] >= need[h]]
        frm = min(sorted(flow), key=over.get)
        if cand and over[frm] < 0:
            h = max(sorted(cand), key=lambda x: over[x] / need[x])
            i, o, s = flow[h]
            acts = "・".join(dict.fromkeys(q["plan"]["activity"] for q in adults(state) if q.get("household") == h))
            _incident(state, "蓄え", frm, h, over[h] / len(homes),  # 【仮定】言い出した家の損 = 取りすぎを村の家の数で割った分
                      f"この季節、{h}の大人は、村の蓄えから草の種にして 約 {round((o + s) / GRAIN)} つかみ 分を取り"
                      + (f" (家の畑にまいた村の草の種 {round(s / GRAIN)} つかみ をふくむ)" if s else "")
                      + f"、入れたのは 約 {round(i / GRAIN)} つかみ 分だった (おもな仕事: {acts}"
                      + (f"。家の倉に {food_words(holdings({'food': hs[h]['store']}))} がある" if h in full else "")
                      + f")。{frm}は 約 {round(flow[frm][0] / GRAIN)} つかみ 分を入れた")
    g["last_flow"] = {h: [round(v[0] / GRAIN), round((v[1] + v[2]) / GRAIN)] for h, v in sorted(flow.items())}
    g["flow"], g["reap"] = {}, {}
    # もめごとのもと → もめごと (家が多いほどなりやすい。罰のある掟にあたることは必ずなる。同じ家どうしの同じ中身で収まっていないものには重ねる)
    pen = {l["penalty"]["for"] for l in state["laws"] if l["status"] == "採用" and l.get("penalty")}
    p, new = stress_p(state), 0
    for inc in g["incidents"]:
        if inc["from"] not in homes or inc["against"] not in homes:
            continue
        old = next((d for d in g["disputes"] if d["status"] == OPEN and (d["kind"], d["from"], d["against"]) == (inc["kind"], inc["from"], inc["against"])), None)
        if old:
            old["harm"] += max(1, round(inc["kcal"] / GRAIN))
            old["because"] += inc["events"]
            log(state, "もめごと", None, f"もめごと [{old['id']}] に、また同じことが重なった: {inc['what']}", dispute=old["id"])
        elif new < MAX_NEW and (inc["kind"] in pen or rng.random() < p):
            _dispute(state, inc)
            new += 1
    g["incidents"] = []
    # 収まらないもめごと: どちらかの家に大人がいなくなった・DROP_AGE 季節たった → なくなった
    for d in [d for d in g["disputes"] if d["status"] == OPEN]:
        if d["from"] not in homes or d["against"] not in homes:
            d.update(status="なくなった", end=day)
        elif (day - d["day"]) // SEASON_DAYS >= DROP_AGE:
            d.update(status="なくなった", end=day)
            log(state, "もめごと", None, f"もめごと [{d['id']}] は、収まらないまま {DROP_AGE} 季節たち、だれも言わなくなった ({d['what']})", dispute=d["id"])
    stale = [d for d in g["disputes"] if d["status"] == OPEN and (day - d["day"]) // SEASON_DAYS >= 2]
    # 第 1 段の目安 (止まらずに記録する): 家族が 6 つ以上の村が、まとめ役なしに、G5 に入って 1 年以上、集まり・長老・祭りでもめごとを 2 回以上収めた
    H = len(homes)
    if not g["stage1"] and not g["leader"] and H >= 6 and g["settled"] >= 2 and day - g["start"] >= YEAR:
        g["stage1"] = day
        log(state, "段階", None, f"G5 の第 1 段: 家族が {H} つの村が、まとめ役なしに、集まり・長老の言葉・祭りで、もめごとを {g['settled']} 回収めてきた (祭り {g['feasts']} 回)")
        _open2(state, "まとまり", "村は、まとめ役なしに、もめごとを収めてきた")
    if stale:
        _open2(state, "ゆきづまり", f"もめごと [{stale[0]['id']}] が、集まりで収まらないまま 2 季節たった")
    # 村が分かれる: 収まらないまま 2 季節たったもめごとの、言い出した家が出ていくことがある (祭りをした季節は出ていかない。1 年に 1 つの家まで)
    pop = sum(1 for q in state["people"] if q["alive"])
    if g["feast_day"] != e2.get("step_day") and (g["last_fission"] is None or day - g["last_fission"] >= YEAR):
        for d in stale:
            if _can_leave(state, d["from"]) and rng.random() < LEAVE_P * min(1.0, pop / BANDY) * frac:
                _split(state, d)
                break


def _open2(state, how, why):
    """第 2 段: 季節の集まりで、まとめ役を選べるようになり、掟に罰をつけられるようになる (一度だけ。止まらずに記録する)"""
    g = _g5(state)
    if g["stage"] < 2:
        g["stage"], g["open"] = 2, {"day": state["day"], "how": how}
        log(state, "段階", None, f"G5 の第 2 段: {why}。これからは、季節の集まりで村のまとめ役を選べ、掟に罰をつけられる", how=how)


def _can_leave(state, h):
    """出ていけるのは大人のいる家で、残る村に家が 3 つ以上・大人が 6 人以上いるとき (【仮定】残る村が続くように)"""
    ads = adults(state)
    mine = sum(1 for q in ads if q.get("household") == h)
    return mine >= 1 and len(_homes(state)) - 1 >= MIN_HOMES and len(ads) - mine >= MIN_ADULTS


def _split(state, d):
    """村が分かれる: 言い出した家が、家の人みんな (子も、この季節に生まれた子も) で出ていく。家のヤギと家の倉の食べ物は持って行き、家の畑は村のものになる
    【文献】Johnson 1982 (分かれるのも規模のストレスへの答え)、PPNC で大きな村がばらけた (periodization 3 の 8)"""
    e2, g, h, day = state["era2"], _g5(state), d["from"], state["day"]
    ppl = sorted([q for q in state["people"] if q["alive"] and q.get("household") == h], key=lambda q: -q["age"])
    names = {q["name"] for q in ppl}
    ppl += [c for c in children(state) if c.get("mother") in names and c["name"] not in names]
    for q in ppl:
        q["alive"], q["left"] = False, day
    goats = [x for x in e2["goats"] if x.get("owner") == h]
    e2["goats"] = [x for x in e2["goats"] if x.get("owner") != h]
    st = _house(state, h)
    kcal, food = sum(f["kcal"] for f in st["store"]), food_words(holdings({"food": st["store"]}))
    st["store"] = []
    fields = [f for f in e2["fields"] if f.get("owner") == h and f["state"] in ("育つ", "実った")]
    for f in fields:
        f["owner"] = None
    for x in g["disputes"]:
        if x["status"] == OPEN and h in (x["from"], x["against"]):
            x.update(status="去った", end=day)
    g["fissions"].append({"day": day, "household": h, "people": [q["name"] for q in ppl], "goats": len(goats), "store": round(kcal),
                          "fields": len(fields), "dispute": d["id"]})
    g["last_fission"] = day
    took = "・".join(x for x in (f"ヤギ {len(goats)} 頭" if goats else "", f"家の倉の {food}" if kcal else "") if x)
    log(state, "分かれる", ppl[0]["name"], f"もめごと [{d['id']}] が収まらないまま 2 季節たち、{h}の "
        + "・".join(q["name"] + (" (子)" if q.get("child") else "") for q in ppl) + " が村を出ていった"
        + (f"。{took} を持って行った" if took else "") + (f"。{h}の畑 {len(fields)} 枚は村のものになった" if fields else ""),
        household=h, dispute=d["id"])
    _check_leader(state)


def _check_leader(state):
    """まとめ役が亡くなった・村を出たら、まとめ役はいなくなる"""
    g = _g5(state)
    q = next((q for q in state["people"] if q["name"] == g["leader"]), None) if g["leader"] else None
    if q and not q["alive"]:
        log(state, "まとめ役", q["name"], f"まとめ役の {q['name']} が{'村を出た' if q.get('left') else '亡くなった'}ので、村にまとめ役がいなくなった")
        g["leader"], g["leader_day"] = None, None


# ---- 季節の集まり (G5): 答えを読む ----

def _mid(v):
    """もめごとの番号 (「M3」「m3」「3」「[M3]」→ "M3"。番号がなければ "")"""
    m = re.search(r"\d+", str(v or ""))
    return f"M{int(m.group())}" if m else ""


def _num(v):
    """数 (「50 つかみ」のような文でも、はじめの数を読む。全角の数字も読む)"""
    m = re.search(r"\d+", str(v)) if v is not None and not isinstance(v, bool) else None
    return int(m.group()) if m else 0


def _do(v):
    """収め方: 「つぐなう」か「ゆるす」(どちらも書いたもの・どちらでもないもの (お題の「...」) は読まない)"""
    s = str(v or "")
    pay, free = any(w in s for w in ("つぐな", "償", "払")), any(w in s for w in ("ゆる", "許"))
    return "つぐなう" if pay and not free else "ゆるす" if free and not pay else None


def _judges(a):
    """judge: {"M3": "つぐなう"} / [{"id": "M3", "do": "ゆるす"}] / {"id": "M3", "do": ...} のどれでも読む"""
    j = a.get("judge")
    if isinstance(j, dict) and "id" in j:
        j = [j]
    if isinstance(j, list):
        j = {x.get("id"): next((x[k] for k in ("do", "judge", "verdict") if k in x), None) for x in j if isinstance(x, dict)}
    out = {}
    for k, v in (j.items() if isinstance(j, dict) else []):
        if _mid(k) and _do(v):
            out[_mid(k)] = _do(v)
    return out


def _who(state, v):
    """まとめ役に選ぶ人: 大人の名前 (まわりに字があってもよい。1 人だけのとき) か「なし」。どちらでもなければ None (null・「...」は数えない)"""
    s = v.strip() if isinstance(v, str) else ""
    names = [q["name"] for q in adults(state)]
    if s in names:
        return s
    hit = [n for n in names if n in s]
    hit = [n for n in hit if not any(n != m and n in m for m in hit)]  # 「ナギ」と「ナギ2」なら「ナギ2」
    if len(hit) == 1:
        return hit[0]
    return "なし" if not hit and any(w in s for w in ("なし", "いらない", "いない")) else None


def _yes(v):
    return v is True or str(v).strip().lower() in ("true", "はい", "する", "開く")


def _penalty(law, pen):
    """掟の罰 (G5 の第 2 段): {"for": ヤギ|倉|蓄え|刈る, "pay": 草の種のつかみ}。for がなければ掟の文から読む。「刈る 40」のような文でもよい。
    種類が 1 つに決まらないもの・数が 0 のもの (お題の例の写し) は罰なし。罰の文は掟の文の後ろにつける (お題・アプリ・採用の出来事に出る)"""
    if pen is None or isinstance(pen, bool) or pen == "":
        return
    d = pen if isinstance(pen, dict) else {"for": pen, "pay": pen}
    s, pay = str(d.get("for") or "").strip(), min(MAX_PAY, _num(d.get("pay")))
    kinds = [s] if s in KINDS else [k for k in KINDS if k in s] or [k for k in KINDS if k in law["text"]]
    if len(kinds) == 1 and pay > 0:
        law["penalty"] = {"for": kinds[0], "pay": pay}
        law["text"] += f" (罰: {KINDS[kinds[0]]}と、相手の家は、言い出した家に 草の種 {pay} つかみ を払う)"


def _g5_collect(state, c, p, a, fam):
    """季節の答えから、もめごとの収め方・祭り・まとめ役・呼びかけを集める (家族の代表の答えは、家族の大人みんなの答え)"""
    names = {q["name"] for q in fam}
    c["by"][p["name"]] = mine = _judges(a)
    for mid, v in mine.items():
        c["judge"].setdefault(mid, {}).setdefault(v, set()).update(names)
    if _yes(a.get("feast")):
        c["feast"] |= names
        c["feast_by"].add(p["name"])
    who = _who(state, a.get("leader"))
    if who:
        c["leader"].setdefault(who, set()).update(names)
    act = next((x for x in sorted(acts2(state), key=len, reverse=True) if x in str(a.get("call") or "")), None)
    if act:
        c["call"][p["name"]] = act


def _g5_meeting(state, c, n):
    """季節の集まり (G5。掟を決めたあと): 呼びかけに応じたか → もめごとを収める (まとめ役 → 集まり → 長老) → 祭り → まとめ役を選ぶ → 呼びかけ"""
    e2, g = state["era2"], _g5(state)
    g["meet_first"] = state["next_event"]  # この集まりからの出来事を、次のお題に見せる (集まりの出来事は 30 日の前に起きるので、前の季節のまとめに入らない)
    _check_leader(state)
    ads = {q["name"]: q for q in adults(state)}
    lead = g["leader"]  # お題を書いたときのまとめ役 (この集まりで選ばれた人は、次の集まりから)
    # 前の集まりのまとめ役の呼びかけに、この季節、大人の何人が応じたか (大人の半分をこえると「共同の仕事」。【文献】Fried)
    cl = g["call"]
    if cl:
        m = sum(1 for q in ads.values() if q["plan"]["activity"] == cl["activity"])
        ok = m * 2 > len(ads)
        g["joint"] += 1 if ok else 0
        log(state, "共同の仕事" if ok else "まとめ役", cl["by"], f"{cl['day']} 日目の集まりでの {cl['by']} の呼びかけ (みんなで {cl['activity']}) に、"
            f"この季節、大人 {len(ads)} 人のうち {m} 人が応じた")
        g["call"] = None
    # もめごとを収める: まとめ役 (自分の家のものでないもめごと。いくつでも) → 集まり (古いものから TALK_MAX まで。大人の半分をこえる人が同じ収め方)
    #   → 長老 (もめごとの家の人でない大人のうち、いちばん年上の人。その人の収め方が、ほかの収め方より少なくなければ)
    talked = 0
    for d in [d for d in g["disputes"] if d["status"] == OPEN]:
        parties = (d["from"], d["against"])
        v = c["by"].get(lead, {}).get(d["id"]) if lead in ads and ads[lead].get("household") not in parties else None
        if v:
            _verdict(state, d, v, "まとめ役", lead)
            continue
        if talked >= TALK_MAX:
            continue
        talked += 1
        tally = {k: len(s) for k, s in c["judge"].get(d["id"], {}).items()}
        top = max(tally.values(), default=0)
        elder = max([q for q in ads.values() if q.get("household") not in parties], key=lambda q: (q["age"], q["name"]), default=None)
        ev = c["by"].get(elder["name"], {}).get(d["id"]) if elder else None
        if top * 2 > n:
            _verdict(state, d, max(tally, key=tally.get), "集まり", None)
        elif ev and tally.get(ev, 0) >= top:
            _verdict(state, d, ev, "長老", elder["name"])
        elif tally:
            log(state, "もめごと", None, f"季節の集まりで、もめごと [{d['id']}] を話し合ったが、まとまらなかった ("
                + "・".join(f"{k} {x} 人" for k, x in sorted(tally.items())) + f" / 大人 {n} 人)", dispute=d["id"])
    # 祭り: 大人の半分をこえる人が望むか、まとめ役が望むと (【文献】Stein 1994)。まだ収まっていないもめごとの半分 (古いものから) が仲直りで収まる
    if len(c["feast"]) * 2 > n or lead in c["feast_by"]:
        cost = FEAST_DAYS * _need(state)
        if sum(f["kcal"] for f in state["store"]) >= cost:
            by = _move_food(state["store"], [], None, cost)
            g["feasts"] += 1
            g["feast_day"] = e2["step_day"]
            op = [d for d in g["disputes"] if d["status"] == OPEN]
            calm = op[:math.ceil(len(op) / 2)]
            for d in calm:
                _verdict(state, d, "仲直り", "祭り", None)
            alone = len(c["feast"]) * 2 <= n
            log(state, "祭り", lead if alone else None, (f"まとめ役の {lead} が決めて、" if alone else "")
                + f"季節のはじめに、村の全員で祭りをした (村の蓄えから {food_words(by)} を使った)"
                + (f"。もめごと {'・'.join('[' + d['id'] + ']' for d in calm)} は、祭りの場で仲直りして収まった" if calm else ""))
        else:
            log(state, "祭り", None, "祭りをしようとしたが、村の蓄えが足りなかった")
    # まとめ役を選ぶ (第 2 段から。大人の半分をこえる人が同じ人を書くと、その人。「なし」なら、まとめ役はいなくなる)
    tally = {k: len(v) for k, v in c["leader"].items()}
    if g["stage"] >= 2 and tally:
        g["votes"] = {"day": e2["step_day"], "votes": tally, "adults": n}
        best = max(sorted(tally), key=tally.get)
        if tally[best] * 2 > n and best == "なし" and lead:
            g["leader"], g["leader_day"] = None, None
            log(state, "まとめ役", lead, f"大人の半分をこえる人が「まとめ役はいらない」と答え、{lead} はまとめ役でなくなった (「なし」 {tally[best]} / {n})")
        elif tally[best] * 2 > n and best not in ("なし", lead):
            g["leader"], g["leader_day"] = best, e2["step_day"]
            g["leaders"].append({"name": best, "day": e2["step_day"]})
            log(state, "まとめ役", best, f"{best} ({ads[best].get('household')}) が、村のまとめ役に選ばれた (賛成 {tally[best]} / {n})"
                + (f"。{lead} に代わる" if lead else ""))
    # まとめ役の呼びかけ (次の季節にみんなでする仕事。応じるかは、それぞれが決める)
    act = c["call"].get(lead) if lead and g["leader"] == lead else None
    if act:
        g["call"] = {"by": lead, "activity": act, "day": e2["step_day"]}
        log(state, "まとめ役", lead, f"まとめ役の {lead} が、「次の季節は、みんなで {act} をしよう」と呼びかけた")


def _verdict(state, d, v, by, who):
    """もめごとが収まる。「つぐなう」なら、相手の家が言い出した家に払う (罰のある掟があれば罰の量、なければもめごとの分)"""
    g = _g5(state)
    law, paid, words = None, 0, ""
    if v == "つぐなう":
        law = next((l for l in reversed(state["laws"]) if l["status"] == "採用" and (l.get("penalty") or {}).get("for") == d["kind"]), None)
        paid, words = _pay(state, d["against"], d["from"], (law["penalty"]["pay"] if law else min(d["harm"], MAX_PAY)) * GRAIN)
    d.update(status="収まった", verdict=v, by=by, judge=who, paid=round(paid / GRAIN), law=law["id"] if law else None, end=state["day"])
    if by == "まとめ役":
        g["judged"] += 1
    elif not g["leader"]:
        g["settled"] += 1  # まとめ役のいない村が、集まり・長老・祭りで収めた (第 1 段)
    if by != "祭り":
        head = {"まとめ役": f"まとめ役の {who} が裁いた", "集まり": "季節の集まりで決まった",
                "長老": f"長老 (もめごとの家の人でない大人でいちばん年上) の {who} の言葉で決まった"}[by]
        res = (f"{d['from']}は{d['against']}をゆるした (払いはない)" if v == "ゆるす" else
               f"{d['against']}が{d['from']}に {words} を払った" + (f" (掟 [{law['id']}] の罰)" if law else "") if paid
               else f"{d['against']}には、払えるものがなかった")
        log(state, "裁き" if by == "まとめ役" else "収める", who, f"もめごと [{d['id']}] ({d['what']}) は、{head}: 「{v}」。{res}", dispute=d["id"], by=by)
    if law and paid > 0:  # 罰は、実際に何か払われたときだけ数える
        g["penalties"] += 1
        log(state, "罰", None, f"{d['against']}が、掟 [{law['id']}] の罰として、{d['from']}に {words} を払った", dispute=d["id"], law=law["id"])


def _pay(state, a, b, kcal):
    """a の家が b の家の倉に払う: a の家の倉の食べ物から。足りない分は、いちばん近い頭数のヤギで払う (1 頭 = GOAT_WORTH。足りない分がヤギ半頭分より
    少なければヤギは渡さない)【仮定】。ヤギも食べ物もなければ払えない"""
    got = []
    by = _move_food(_house(state, a)["store"], got, None, kcal)
    _house(state, b)["store"].extend(got)
    paid, n = sum(by.values()), 0
    words = [food_words(by)] if food_words(by) != "なし" else []
    for x in [x for x in state["era2"]["goats"] if x.get("owner") == a]:
        if kcal - paid < GOAT_WORTH / 2:
            break
        x["owner"] = b
        paid += GOAT_WORTH
        n += 1
    if n:
        words.append(f"ヤギ {n} 頭")
    return paid, "・".join(words)
```

### 3.2 Hooks in existing `era2.py` functions

Every hook is a no-op before G5; invariance was verified (§0).

**Top of file, L10–11:** add `import re` after `import random`.

**`apply_answers` (L113–170):**

```python
# after L120-121 (e2["step_day"] = ... / talk = []):
    g5 = era_at_least(state, "G5")
    reps = _reps(state) if g5 and e2.get("rep_mode") else set()
    c5 = {"judge": {}, "by": {}, "feast": set(), "feast_by": set(), "leader": {}, "call": {}}  # G5: 季節の集まりの答え

# L135-136 becomes:
        if isinstance(prop, dict) and prop.get("text"):
            knowledge.propose(state, p, prop["text"], prop.get("because"))
            if g5 and _g5(state)["stage"] >= 2:  # G5 の第 2 段から、掟に罰をつけられる
                _penalty(state["laws"][-1], prop.get("penalty"))

# after L138 (fam = family(...) if e2.get("rep_mode") else [p] ...):
        own = not (g5 and e2.get("rep_mode")) or name in reps  # G5: 家族の代表でないまとめ役は、自分の分だけ答える
        if not own:
            fam = [p]
        elif g5 and e2.get("rep_mode"):  # 代表の答えに、自分で答えたまとめ役の分は入れない
            fam = [q for q in fam if q is p or q["name"] not in answers]

# L154: "... if q is p else 0,"  ->  "... if q is p and own else 0,"
# L157: if era_at_least(state, "G4") and own and "keep" in a and p.get("household"):

# after L161 (still inside `for name, raw in answers.items():`, 8-space indent):
        if g5:
            _g5_collect(state, c5, p, a, fam)

# between L168 and L169:
    if g5:
        _g5_meeting(state, c5, len(alive))  # 掟を決めてから (この集まりで採用された罰の掟も、この集まりで使う)
```

**`_feed` (L339–344)** becomes:

```python
        if have > keep:
            _flow(state, p, 0, sum(_move_food(p["food"], state["store"], None, have - keep).values()))
        elif have < keep:
            got = sum(_move_food(state["store"], p["food"], None, keep - have).values())
            _flow(state, p, 1, got)
            if have + got < keep and era_at_least(state, "G4"):  # 村の蓄えが足りないときは、家の倉から
                got += sum(_move_food(_house(state, p.get("household"))["store"], p["food"], None, keep - have - got).values())
                if have + got < keep and p["hunger"] >= 0.6 and era_at_least(state, "G5"):  # G5: それでも足りず、ひどく空腹 (前からの 0.6) なら、よその家の倉から
                    _steal(state, p, keep - have - got)
```

**`_sow`:** after L504 (`by = _move_food(state["store"], [], "草の種", ...)`):

```python
    if era_at_least(state, "G5") and _house(state, p.get("household"))["keep"]:  # G5: 家の倉を持つ家が、村の草の種を自分の畑にまいた
        _flow(state, p, 2, by.get("草の種", 0))
```

**`_harvest`:** L527 becomes:

```python
            st = _store_of(state, f.get("owner"))
            st.append({"kind": "草の種", "kcal": n * UNITS["草の種"][1], "day": day, "sown": True})
            if era_at_least(state, "G5"):
                _g5_reap(state, p, f.get("owner"), n, st is state["store"])
```

**`_field_season`:** L556 becomes:

```python
                f["yield"] = int(f["seed"] * ratio * min(1.0, 0.3 + 0.7 * f["work"] / need) * (1 - f.get("lost", 0)))  # lost: G5 でヤギに荒らされた分
```

**`_season_end`:** between L700 and L701:

```python
    _sync_households(state)
    if era_at_least(state, "G5"):  # 家族を決めてから (この季節に生まれた子も母の家に入る)。村が分かれて大人が 12 人以下になれば、次の _note_mode で代表の方式が終わる
        _g5_season_end(state, frac)
    _note_mode(state)
```

**`answerers` (L756–765)** is replaced by:

```python
def _reps(state):
    """家族の代表 (家族でいちばん年上の大人) の名前"""
    reps = {}
    for p in sorted(adults(state), key=lambda q: -q["age"]):
        reps.setdefault(p.get("household") or p["name"], p["name"])
    return set(reps.values())


def answerers(state):
    """季節のはじめに答える人 (G5: まとめ役は、家族の代表でなくても答える。代表は家族でいちばん年上の大人のまま (計画 4))"""
    ads = adults(state)
    if not state["era2"].get("rep_mode"):
        return [p["name"] for p in ads]
    _sync_households(state)
    who = _reps(state) | {_leader(state)}
    return [p["name"] for p in ads if p["name"] in who]
```

**Indicators and CRITERIA:**
- After L791, add `**_g5_indicators(state),`.
- Insert `_g5_indicators` after `_g4_indicators` (after L801). The code is in §11.
- Add the `"G5"` entry before the closing `}` of `CRITERIA` (L814). Its text is in §11.

**RNG:** one new stream, `_rng(state, 37)`, used only in `_g5_season_end`. Theft, feasts and elections are deterministic.

### 3.3 Prompt code

Place `FACTS_G5`, `FACTS_G5_2`, `_g5_facts` and `_g5_text` after `FACTS2` (L925–929) and before `def season_prompt` (L932). Their exact text is in §10.

---

## 4. Disputes

All four sources are flows that actually happened in the world, between two different households that have adults.

| Kind | Trigger (recorded) | Complainant (`from`) → accused (`against`) | Harm |
|---|---|---|---|
| **ヤギ** | At season end, when `tended_run < 5·frac` (the same condition as goats escaping). For each household owning n goats, with probability min(0.6, 0.1·n)·frac, one other household's growing or ripe field is trampled. Event `ヤギ` (already printed and digested). | Field owner → goat owner | Ripe field: 20% of what is left is removed from `yield`. Growing field: `lost` compounds by 20% and applies when it ripens; harm is estimated as seed × 8 × 0.2. |
| **倉** | In `_feed`, an adult with hunger ≥ 0.6 who is still short after the village store and their own house store takes from the fullest other house store. Event `倉から取る`, once per pair per season. | Robbed household → taker's household | kcal taken |
| **蓄え** | At season end, using per-household flows (adults only): in = deposits plus harvest put into the village store; out = takes plus village seed that keep households sowed in their own fields. Only seasons where in_total ≥ 0.25·out_total count; with r = max(1, out/in), over = out − in·r. A candidate needs over ≥ 10 adult-days × the household's adults × frac (half that if the household keeps a store with food in it). The highest over/need wins; at most one per season. | Biggest net giver → that household | over ÷ H |
| **刈る** | During `_harvest`: grain from another household's field went into that owner's house store (the owner has `keep`). | Harvester's household → field owner | grain × 0.1 (harvester's share) |

**Why "harvesting someone else's field" is not an owner → harvester dispute.** `_harvest` sends the grain to the owner's store, or to the village store when the owner has no keep, so the owner never loses anything. The real loss is the harvester's unpaid labour, which is the 刈る kind.

- **Probability.** p(H) = min(0.9, 0.3·H(H−1)/30): H = 4 gives 0.12, 6 gives 0.30, 8 (today) gives 0.56, 10 gives 0.90. It is halved in a feast season.
  - 【文献】Johnson 1982 (6 units)
  - 【文献の目安】the H² shape, research §9
  - 【仮定】the 0.3 constant
- **Penalty-law kinds always become disputes.** If an adopted penalty law covers the kind, p = 1.
- **Limits.**
  - At most 3 new disputes per season.
  - The same (kind, from, against) adds to an open dispute and is logged as 「また同じことが重なった」.
  - A dispute fades after 4 seasons (`なくなった`).
  - A dispute ends as `なくなった` if either household has no adults left.
- **Supply measured in memory.**
  - With keep households: about 3 刈る incidents every summer.
  - Even with no keep household at all: 蓄え candidates appeared every autumn (4 candidates each time); summers had none (everyone is a net giver at harvest) and winter/spring fail the 0.25 rule.
  - So supply is lower, but not zero, when no household keeps a store (see §14).
- **In the prompt** (`## 村の集まり`), each open dispute is shown like this:

  ```
  - [M2] (蓄え) ナギの家が言い出した。相手はクラの家 (1 季節 収まっていない。この季節の集まりでも収まらないと、季節の終わりに、ナギの家が村を出ていくことがある。この季節の集まりで話し合う): … (草の種にして 約 40 つかみ 分) [出来事 27200]
  ```

## 5. Settlement and judgment

Each open dispute is processed at the season meeting, oldest first, after the law votes are settled:

1. **Leader (stage 2).** The sitting leader (the one in office when the prompts were written) answered `judge` for it, and the leader's household is not a party. Event `裁き`, `judged += 1`. No limit on how many.
2. **Assembly.** Only for the oldest `TALK_MAX = 2` disputes the leader did not decide. Rep-weighted votes for one answer must be more than n/2, where n = all adults. Event `収める`, by="集まり".
3. **Elder.** The eldest adult not in either household. Their answer must have at least as many votes as any other answer. Event `収める`, by="長老".
4. **Otherwise.** If anyone voted, log `もめごと` 「…話し合ったが、まとまらなかった (つぐなう 6 人・ゆるす 5 人 / 大人 16 人)」. The dispute stays open.
5. **Feast.** If a feast is held, `⌈open/2⌉` of the oldest remaining disputes are closed as 仲直り (by="祭り").

**Effects of a verdict:**
- ゆるす: nothing is paid.
- つぐなう: the accused pays the complainant's house store the harm (capped at 1000 つかみ), or the penalty-law amount if one applies. Payment comes from the house store first, then in goats, each counted as 375 つかみ and rounded to the nearest whole goat. If nothing can be paid, that is logged honestly.

`settled` counts settlements made while there is no leader; `judged` counts leader judgments. The answer field is `"judge": {"M3": "つぐなう", "M4": "ゆるす"}`; the parser also accepts list forms.

## 6. Penalties (罰)

- **How a law gets one.** Only in stage 2: `"proposal": {..., "penalty": {"for": "ヤギ"|"倉"|"蓄え"|"刈る", "pay": N}}`.
  - Also accepted: a string like 「刈る 40」, digits embedded in text, full-width digits, and a missing `for` when the law text names exactly one kind.
  - N is clamped to 1–1000.
  - Copied placeholders, more than one kind, or a 0 amount mean no penalty.
  - The penalty clause is appended to `law["text"]`, so it appears in the prompt's law list, in the app, and in the `掟` adoption event.
  - `characters.py` and `knowledge.py` are unchanged.
- **How a violation is detected.** By dispute kind, so it always rests on a recorded incident. While the law is adopted, every incident of that kind becomes a dispute.
- **What it does in the world.**
  - On a つぐなう verdict (by leader, assembly or elder), the accused pays the law's amount instead of the harm, using `_pay`: house store first, then goats.
  - Food moves into the complainant's house store and counts in `wealth`; goats change owner.
  - `penalties += 1` and a `罰` event are logged **only when something was actually paid**.
- **Timing.** A penalty law adopted at a meeting can be used at the same meeting, because `_g5_meeting` runs after `settle_meeting`. In practice it is adopted at the meeting after it is proposed.

## 7. Leader (まとめ役)

- **Field.** `"leader": "..."`, shown only in stage 2. The `"..."` placeholder invites a name; copied verbatim it counts as no vote. `_who` reads a name inside free text, or 「なし/いらない/いない」.
- **Vote counting.**
  - Rep mode: a rep's answer counts for every adult in their household who did not answer themselves (`fam`).
  - Non-rep mode: one vote per adult.
  - More than n/2 for one name elects that person; this also replaces a sitting leader.
  - More than n/2 for 「なし」 removes the leader.
- **Visibility.** The last tally is stored and shown in the prompt as a world fact, to help votes converge.
- **Term and loss.** No fixed term. The leader is lost on death or on leaving (fission or famine), detected by `_check_leader` at the meeting and at season end, or by recall.
- **Rep mode.** The rep stays the household's eldest adult (plan §4, user-decided).
  - A non-rep leader **also** answers (`answerers`) and decides only their own job.
  - Their `keep` and `eat_goat` are ignored (`own=False`), and those lines are hidden in their prompt (`solo`).
  - The rep's prompt marks the leader with 「まとめ役なので、自分で答える」.
- **Powers.** Judges first and without limit, except disputes involving their own household. Can start a feast alone. Can make one `call` per season.
- **Joint work (`call`).** The call is evaluated at the next meeting against the plans just chosen. If more than half of adults follow, event `共同の仕事` and `joint += 1`; otherwise event `まとめ役` with the count. Not part of the criterion (§15).

## 8. Feasts (祭り)

- **Field.** `"feast": false` in the template. Accepted as yes: `true`, "true", 「はい」, 「する」, 「開く」.
- **Held when** more than half of adults want it (rep-weighted), or the sitting leader wants it.
- **Cost.** 3 × `_need(state)` from the village store (about 138k kcal today, about 1.7% of the store). If the store cannot cover it, log 「足りなかった」.
- **Effects.**
  - The oldest `⌈open/2⌉` disputes are reconciled.
  - The dispute probability is halved that season.
  - No fission that season.
  - It counts toward stage 1 through `settled`.
- **Logged** as `祭り`.
- Sources: 【文献】Hilazon Tachtit and Göbekli Tepe (periodization §3.5), Stein 1994; 【文献(記憶・要確認)】Munro & Grosman 2010; 【仮定】3 days, half, one season.

## 9. Fission (村が分かれる)

- **Conditions** (all at season end, after households are synced):
  - An open dispute is at least 2 seasons old, i.e. two meetings did not settle it.
  - There was no feast this season.
  - At least one year has passed since the last fission.
  - `_can_leave`: after leaving, the village keeps at least 3 households and at least 6 adults.
  - A roll below 0.5 × min(1, population/30) × frac succeeds; disputes are tried in order and at most one household leaves.
- **What leaves:**
  - All living members of the complainant household, adults and children, including the season's newborns whose mother is leaving. They get `alive=False` and `left=day`.
  - Its goats (removed) and its house store (emptied).
- **What stays:** its growing and ripe fields, which get `owner=None` (village). Other open disputes involving that household become `去った`. If the leader was a member, the leader is cleared.
- **Logs:**
  - Event `分かれる` (who = the household's eldest), e.g. 「…ユノの家の ユノ・カイ・ネム (子)・… が村を出ていった。ヤギ 1 頭・家の倉の 草の種 100 つかみ を持って行った。ユノの家の畑 1 枚は村のものになった」.
  - A record appended to `g5.fissions`, which can seed a neighbouring village in G6.
- **The "everyone died → roll back" rule.** Fission is a legitimate outcome and is never rolled back. Because of the guard it cannot empty the village, and `left` is not a death, so step.py exit 4 is unaffected. If adults drop to 12 or fewer, `_note_mode` turns rep mode off in the same season end.

---

## 10. Prompt changes (all empty before G5)

### 10.1 FACTS (place before `def season_prompt`)

```python
FACTS_G5 = ("もめごと: 家どうしのあいだで次の (1)〜(4) のことが起きると、季節の終わりに、損をした家が言い出して、もめごとになることがある。"
            "村の家が多いほど、もめごとになりやすい。祭りをした季節は、なりにくい。"
            "(1) ヤギ: 世話をする人が少ない季節に、家のヤギが、よその家の畑を荒らす (荒らされた畑は、実りが 2 割減る) "
            "(2) 倉: ひどく空腹の人が、村の蓄えにも自分の家の倉にも食べ物がないときに、よその家の倉から取って食べる (日々の食べ物の出し入れと同じく、自動で起きる) "
            "(3) 蓄え: ある家の大人が、村の蓄えに入れた量にくらべて、ほかの家より多く村の蓄えから取る (言い出すのは、いちばん多く入れた家。1 季節に 1 つの家まで。"
            f"大人 1 人あたり {FREE_DAYS} 日分の食べ物より少ない差では、もめごとにならない。家の倉に食べ物がある家は、半分の差でなる) "
            "(4) 刈る: よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入る (言い出すのは、刈った人の家)\n"
            "収める: もめごとは、季節の集まりで収める。収め方は「つぐなう」(相手の家が、言い出した家に払う) か「ゆるす」(払わずに収める)。"
            f"集まりで話し合えるのは、古いもめごとから {TALK_MAX} つまで。大人の半分をこえる人が同じ収め方を選ぶと、それに決まる。"
            "決まらないときは、もめごとの家の人でない大人のうち、いちばん年上の人 (長老) の選んだ収め方が、ほかの収め方より少なくなければ、それに決まる。"
            f"払う量は、もめごとの分 ({MAX_PAY} つかみまで)。家の倉の食べ物で払い、足りなければ、足りない分にいちばん近い頭数のヤギで払う "
            f"(1 頭を草の種 {GOAT_WORTH // GRAIN} つかみ 分とする)。払えるものがなければ払わない\n"
            "村を出る: もめごとが収まらないまま 2 季節たつと、言い出した家が、家の人みんな (子も) で村を出ていくことがある (1 年に 1 つの家まで)。"
            f"家のヤギと家の倉の食べ物は持って行き、家の畑は村のものになる。{DROP_AGE} 季節たっても収まらないもめごとは、だれも言わなくなる\n"
            f"祭り: 大人の半分をこえる人が望むと (feast)、季節のはじめに村の全員で祭りをする。村の蓄えから、村の全員の {FEAST_DAYS} 日分の食べ物を使う。"
            "祭りでは、まだ収まっていないもめごとの半分 (古いものから) が、仲直りして収まる。祭りをした季節は、だれも村を出ていかない\n")

FACTS_G5_2 = ("まとめ役: 大人の半分をこえる人が同じ人を選ぶと (leader)、その人が村のまとめ役になる。まとめ役は、亡くなるか、村を出るか、"
              "大人の半分をこえる人がほかの人か「なし」を選ぶまで続く。まとめ役は、家族の代表でなくても、季節の集まりで答える。"
              "まとめ役は、自分の家のものでないもめごとを、一人で、いくつでも裁ける (まとめ役の judge が、集まりより先に決まる。"
              "まとめ役が裁かなかったもめごとは、集まりで話し合う)。まとめ役が祭りをすると答えると、ほかの人の答えにかかわらず祭りをする。"
              "まとめ役は、次の季節にみんなでする仕事を呼びかけられる (call)。応じるかどうかは、それぞれが決める\n"
              f"罰: 掟を提案するときに、罰をつけられる (penalty)。罰は、もめごとのもと (1)〜(4) のどれか 1 つと、払う草の種のつかみ ({MAX_PAY} まで)。"
              "罰のある掟が採用されていると、その掟にあたることが起きたときは、必ずもめごとになる。そのもめごとが「つぐなう」に決まると、"
              "もめごとの分ではなく、罰の量を払う\n")


def _g5_facts(state):
    if not era_at_least(state, "G5"):
        return ""
    return FACTS_G5 + (FACTS_G5_2 if (state["era2"].get("g5") or {}).get("stage", 1) >= 2 else "")


def _g5_text(state):
    """G5 のお題の節: 村の家・まとめ役・票・罰のある掟・呼びかけ・祭り・まだ収まっていないもめごと・この前の集まりから起きたこと・村の蓄えへの出し入れ (見ればわかる事実だけ。状態は変えない)"""
    if not era_at_least(state, "G5"):
        return ""
    g = state["era2"].get("g5") or {}
    lead, two, since = g.get("leader"), g.get("stage", 1) >= 2, g.get("meet_first") or state["next_event"]
    homes = _homes(state)
    rows = [f"村の家族: {len(homes)} つ ({'、'.join(homes)})"]
    if two:
        hh = next((q.get("household") for q in adults(state) if q["name"] == lead), "")
        rows.append(f"まとめ役: {lead} ({hh}。{g['leader_day']} 日目から)" if lead else "まとめ役: いない")
        v = g.get("votes")
        if v:
            rows.append(f"{v['day']} 日目の集まりで、まとめ役に名前があがった人: "
                        + "、".join(f"{k} (大人 {x} 人分)" for k, x in sorted(v["votes"].items(), key=lambda kv: -kv[1])) + f" (大人 {v['adults']} 人)")
        rows.append("罰のある掟: " + ("、".join(l["id"] for l in state["laws"] if l["status"] == "採用" and l.get("penalty")) or "まだない"))
    c = g.get("call")
    if c:
        rows.append(f"{c['day']} 日目の集まりで、まとめ役の {c['by']} が「次の季節は、みんなで {c['activity']} をしよう」と呼びかけた (この季節のこと)")
    if g.get("feast_day") is not None:
        rows.append(f"前に祭りをしたのは {g['feast_day']} 日目 (これまで {g['feasts']} 回)")
    op = [d for d in g.get("disputes", []) if d["status"] == OPEN]
    rows.append("まだ収まっていないもめごと:" + ("" if op else " なし"))
    for i, d in enumerate(op):
        age = (state["day"] - d["day"]) // SEASON_DAYS
        when = ("前の季節の終わりに起きた" if age == 0 else f"{age} 季節 収まっていない。この季節の集まりでも収まらないと、季節の終わりに、"
                + (f"{d['from']}が村を出ていくことがある" if age + 1 < DROP_AGE else "だれも言わなくなる"))
        talk = "" if lead else "。この季節の集まりで話し合う" if i < TALK_MAX else f"。この季節の集まりでは話し合えない (古いものから {TALK_MAX} つまで)"
        rows.append(f"- [{d['id']}] ({d['kind']}) {d['from']}が言い出した。相手は{d['against']} ({when}{talk}): {d['what']}"
                    f" (草の種にして 約 {d['harm']} つかみ 分) [出来事 {d['event']}]")
    ev = [e for e in state["events"] if e["id"] >= since and e["type"] in G5_EVENTS]
    if ev:
        rows += ["この前の集まりから起きたこと:"] + [f"- [出来事 {e['id']}] {e['text']}" for e in ev[-12:]]
    if g.get("last_flow"):
        rows.append("前の季節の、家ごとの村の蓄えへの出し入れ (大人の分。草の種にして): "
                    + "、".join(f"{h} 入れた 約 {i}・取った 約 {o} つかみ" for h, (i, o) in g["last_flow"].items()))
    return "\n## 村の集まり (もめごと・祭り" + ("・まとめ役" if two else "") + ")\n" + "\n".join(rows) + "\n"
```

### 10.2 `season_prompt` edits (L932–1007)

```python
# after L933 (e2 = state["era2"]):
    g5, g = era_at_least(state, "G5"), e2.get("g5") or {}  # G5 の部分は、G5 の前はみな空の文字 (お題は前と同じ)
    lead, two = g.get("leader"), g.get("stage", 1) >= 2
    solo = bool(g5 and e2.get("rep_mode") and p["name"] not in _reps(state))  # 家族の代表でないまとめ役 (自分の分だけ答える)
# L946: keep = '"keep": false, ' if era_at_least(state, "G4") and not solo else ""
# L947: goat = '"eat_goat": 0, ' if e2["goats"] and not solo else ""
# L952: if e2.get("rep_mode") and not solo:
# L956: f"おなか {_hunger_word(q['hunger'])}{'、けが' if q.get('injured') else ''}{'。まとめ役なので、自分で答える' if q['name'] == lead else ''})" for q in fam]
# L962: f"\n- 掟の投票と、よそから来た人の受け入れ{'、もめごとの収め方・祭り・まとめ役の答え' if g5 else ''}は、家族の大人みんなの答えとして数える\n")
# L964: ... for q in [q for q in fam if q["name"] != lead][:2]) + '}, '
# after the `if e2.get("rep_mode") and not solo:` block (after L964), at function indentation:
    if solo:
        fam_txt = (f"\n## あなたはまとめ役\nあなたは {p.get('household')} の代表ではないが、村のまとめ役なので、季節の集まりで答える。決めるのは自分の仕事だけ "
                   "(家族の仕事・家の倉・ヤギをつぶす数は、家族の代表が決める)。掟の投票・受け入れ・もめごとの収め方・祭り・まとめ役の答えは、あなた一人の答えとして数える\n")
    op = [d["id"] for d in g.get("disputes", []) if d["status"] == OPEN] if g5 else []
    me5 = g5 and lead == p["name"]
    g5_now = ("7. 村の集まり (上の「村の集まり」を見て決める。どれも書かなくてもよい)\n"
              + ("   もめごと: まだ収まっていないもめごとの収め方を、番号ごとに「つぐなう」か「ゆるす」で書く (judge)\n" if op else "")
              + "   祭り: この季節のはじめに、村の全員で祭りをするか (feast: するなら true、しないなら false)\n"
              + ("   まとめ役: まとめ役にしたい人の名前を書く (leader。まとめ役はいらないなら「なし」、決めないなら null)\n"
                 '   罰: 掟を提案するときに罰をつけるなら、proposal の penalty に {"for": "ヤギ" か "倉" か "蓄え" か "刈る", "pay": 草の種のつかみ} を書く (つけないなら null)\n'
                 if two else "")
              + ("   あなたは村のまとめ役。あなたの家のものでないもめごとは、あなたの judge で決まる。次の季節にみんなでする仕事を 1 つ呼びかけられる (call: 仕事の名前。しないなら null)\n"
                 if me5 else "")) if g5 else ""
    g5_json = ("\n " + ('"judge": {' + ", ".join(f'"{i}": "..."' for i in op) + "}, " if op else "") + '"feast": false, '
               + ('"leader": "...", ' if two else "") + ('"call": null, ' if me5 else "")) if g5 else ""
    pen = ', "penalty": null' if g5 and two else ""
```

Template lines:
- **L968:** `...{FACTS_G4 if era_at_least(state, "G4") else ""}{_g5_facts(state)}`
- **L982:** `{_g5_text(state)}{vis}`
- **L993:** `...+ chr(10) if e2['goats'] and not solo else ''}`
- **L994:** `...+ chr(10) if era_at_least(state, "G4") and not solo else ''}5. 覚えていることを…`
- **L996:** `{g5_now}{8 if g5_now else 7}. 今の気持ちを一言`
- **L1003:** `...{fam_json}{keep}{g5_json}`
- **L1005:** ` "proposal": {{"text": "...", "because": [出来事の番号]{pen}}},`

### 10.3 Placeholder policy

| Field | Template value | Why |
|---|---|---|
| `judge` | `"..."` per open id | Invites an answer without favouring つぐなう or ゆるす. A copied `...` is no answer. |
| `feast` | `false` | Same pattern as `keep`; avoids a feast every season. |
| `leader` | `"..."` | Invites a name, so the run does not stall with no leader; a copied `...` is no vote. |
| `penalty` | `null` | A penalty only when someone deliberately writes one; the いま line shows the exact format. |
| `call` | `null` | Leader only; optional. |

### 10.4 Rendered stage-2 example, non-rep leader タヒ (checked in memory)

```
7. 村の集まり (上の「村の集まり」を見て決める。どれも書かなくてもよい)
   もめごと: まだ収まっていないもめごとの収め方を、番号ごとに「つぐなう」か「ゆるす」で書く (judge)
   祭り: この季節のはじめに、村の全員で祭りをするか (feast: するなら true、しないなら false)
   まとめ役: まとめ役にしたい人の名前を書く (leader。まとめ役はいらないなら「なし」、決めないなら null)
   罰: 掟を提案するときに罰をつけるなら、proposal の penalty に {"for": "ヤギ" か "倉" か "蓄え" か "刈る", "pay": 草の種のつかみ} を書く (つけないなら null)
   あなたは村のまとめ役。あなたの家のものでないもめごとは、あなたの judge で決まる。次の季節にみんなでする仕事を 1 つ呼びかけられる (call: 仕事の名前。しないなら null)
8. 今の気持ちを一言
...
 "job": {"activity": "採集", "place": "camp", "with": []}, "pick": 0, "plant": 0, "harvest": 0, 
 "judge": {"M0": "...", "M2": "...", "M3": "..."}, "feast": false, "leader": "...", "call": null, 
 "proposal": {"text": "...", "because": [出来事の番号], "penalty": null},
```

Prompt length grows by about 2.5k characters (25.0k → 27.6k).

---

## 11. Indicators and CRITERIA

```python
def _g5_indicators(state):
    """G5 の目安 (G5 の前は 0。家族の数は G4 の 5 季節ごとの報告にも使うので、いつも数える)"""
    base = {"households": len(_homes(state)), "g5_stage": 0, "stage1": None, "leader": None, "leader_seasons": 0, "disputes": 0,
            "disputes_open": 0, "settled": 0, "judged": 0, "penalty_laws": 0, "penalties": 0, "feasts": 0, "fissions": 0,
            "left_people": 0, "joint": 0, "stress": 0.0}
    g = state["era2"].get("g5")
    if not era_at_least(state, "G5") or not g:
        return base
    return base | {"g5_stage": g["stage"], "stage1": g["stage1"], "leader": g["leader"],
                   "leader_seasons": (state["day"] + 1 - g["leader_day"]) // SEASON_DAYS if g["leader"] else 0,
                   "disputes": g["next"], "disputes_open": sum(1 for d in g["disputes"] if d["status"] == OPEN),
                   "settled": g["settled"], "judged": g["judged"],
                   "penalty_laws": sum(1 for l in state["laws"] if l["status"] == "採用" and l.get("penalty")),
                   "penalties": g["penalties"], "feasts": g["feasts"], "fissions": len(g["fissions"]),
                   "left_people": sum(len(f["people"]) for f in g["fissions"]), "joint": g["joint"], "stress": round(stress_p(state), 2)}
```

```python
    # 2026-10-08: G5 は 2 段階 (計画 2.1)。条件は第 2 段。第 1 段 (集まり・長老・祭りでまとまる) は止まらずに記録する (出来事「段階」・指標 stage1)
    "G5": ("第 2 段: 家族が 6 つ以上で、まとめ役がいる。罰のある掟が 3 つ以上採用されている。まとめ役がもめごとを 2 回以上裁いた。罰を 1 回以上払わせた",
           lambda i: i["g5_stage"] >= 2 and i["households"] >= 6 and bool(i["leader"]) and i["penalty_laws"] >= 3
           and i["judged"] >= 2 and i["penalties"] >= 1),
```

**Stage-1 milestone** (logged, no hold): H ≥ 6, no leader, at least 1 year in G5, `settled` ≥ 2.

**Why the criterion cannot pass by accident, or in season 1.** None of the 106 existing adopted laws has a `penalty`, and each step below takes a deliberate answer:
- Disputes first appear at the end of G5 season 1.
- The penalty and leader fields exist only after the gate opens (earliest end of season 3).
- Penalty laws need a structured field plus a majority, so they are adopted at the next meeting at the earliest.
- A leader elected at a meeting judges only from the next meeting.
- A penalty counts only when something is actually paid.

The theoretical minimum is the end of season 5; the idealized coop run took 8.

---

## 12. step.py, resume.py and docs

**step.py, `season` branch:**

```python
        before = state["next_event"]  # G5: 季節の集まりで起きたこと (収める・裁き・罰・祭り・まとめ役) は、30 日を進める前の出来事
        era2.apply_answers(state, read_answers(state, "season"))          # L194
...
        for e in state["events"]:                                          # L211-213
            if (e["id"] >= first and e["type"] in ("掟", "死", "生まれる", "加わる", "去る", "訪れる", "畑", "ヤギ", "大人になる", "フェーズ", "家族", "虫", "受けつぎ")) \
                    or (e["id"] >= before and e["type"] in era2.G5_EVENTS):
                print("*", e["text"][:120])
...
        # after L218:
        if i.get("g5_stage"):
            print(f"G5 第 {i['g5_stage']} 段 / 家族 {i['households']} / まとめ役 {i['leader'] or 'いない'} / もめごと 残り {i['disputes_open']} "
                  f"(まとめ役なしで収めた {i['settled']}・まとめ役の裁き {i['judged']}) / 罰のある掟 {i['penalty_laws']}・罰 {i['penalties']} / "
                  f"祭り {i['feasts']} / 分かれた家 {i['fissions']} / 共同の仕事 {i['joint']} / 第 1 段 {'済み' if i['stage1'] else 'まだ'}")
```

None of this text matches the workflow's stop regex `/フェーズが .* に進んだ/`.

**resume.py L76:** `("けが", "死", "去る")` → `("けが", "死", "去る", "分かれる")`. No `分かれる` events exist before G5, so nothing changes.

**docs/society2_phase_plan.md §2 table, G5 row:** replace 「(第 1 段の条件は G5 を作るときに決める)」 with:

> 。罰を 1 回以上払わせた (2026-10-08 に足した。調べ 6(c))。第 1 段の目安 (止まらずに記録する): 家族が 6 つ以上で、まとめ役のいないまま G5 に入って 1 年以上たち、集まり・長老・祭りでもめごとを 2 回以上収めた

**docs/society2_phase_plan.md §5:** add after the G4 subsection:

```markdown
### G5 リーダーと決まり (2026-10-08 に作った。G5 に入ってから働く)
- **もめごと** (世界の仕組み): 家どうしのあいだで実際に起きたことからだけ生まれる。(1) ヤギ: 世話をする人が少ない季節に、家のヤギがよその家の畑を荒らす (畑の実りが 2 割減る。ヤギ 1 頭 1 季節 0.1、0.6 まで【仮定】) (2) 倉: ひどく空腹の人が、村の蓄えにも自分の家の倉にも食べ物がないとき、よその家の倉から取って食べる (3) 蓄え: 村の蓄えに入れた量にくらべて、ほかの家より多く取った家 (1 季節に 1 つ。大人 1 人あたり 10 日分をこえる差。家の倉に食べ物がある家は 5 日分。【文献】Flannery 2002 の共同の倉から家ごとの倉へ【仮定】数。冬・春のようにほとんど蓄えで暮らした季節は数えない) (4) 刈る: よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入った (刈り手の取り分を 1 割とみる【仮定】)
- よその家の畑を刈ったことで、畑の持ち主が言い出すもめごとにはしない (刈った草の種は持ち主の倉か村の蓄えに入り、持ち主は損をしないため)。損をするのは取り分のない刈り手の家なので、(4) にした
- もめごとになる見込みは家の数 H で増える: 0.3 × H(H−1)/30 (6 家族 0.3、8 家族 0.56、0.9 まで)。【文献】Johnson 1982 (決める単位が 6 ほどをこえるとストレスが急に増える)【文献の目安】話し合いのコストは単位の数の 2 乗に比例 (調べ 9)【仮定】0.3。祭りの季節は半分。罰のある掟にあたることは必ずもめごとになる。新しいもめごとは 1 季節に 3 つまで。同じ家どうしの同じ中身は重ねる。4 季節収まらないと、だれも言わなくなる
- **第 1 段 集まり・長老・祭り** (Johnson 1982 の「順番の階層」): 季節の集まりで、古いもめごとから 2 つまでを話し合い、大人の半分をこえる人が同じ収め方 (つぐなう: 相手の家が、もめごとの分を家の倉の食べ物、足りなければヤギで払う / ゆるす) を選ぶと決まる。決まらないときは、もめごとの家の人でない大人でいちばん年上の人 (長老) の収め方が、ほかより少なくなければそれに決まる。家族の代表の答えは家族の大人みんなの答え (家の長どうしの話し合い)
- **祭り** (人が決める: feast): 大人の半分をこえる人 (第 2 段でまとめ役がいれば、まとめ役だけでも) が望むと、村の蓄えから村の全員の 3 日分を使って祭りをする。まだ収まっていないもめごとの半分 (古いものから) が仲直りで収まり、その季節はもめごとが半分になり、だれも村を出ていかない。【文献】ヒラゾン・タクティトの祭り (約 1.2 万年前)、ギョベクリ・テペ (目に見えるまとめ役なしの共同の場)、Bandy 2004【仮定】3 日分・半分
- **村が分かれる**: 収まらないまま 2 季節たったもめごとは、季節ごとに 0.5 × (村の人数 / 30) の見込みで、言い出した家が、家の人みんな (子も) で、ヤギと家の倉の食べ物を持って村を出ていく (畑は村のものになる)。1 年に 1 つの家まで。残る村に家が 3 つ・大人が 6 人より少なくなるときは出ていかない。祭りの季節は出ていかない。【文献】Johnson 1982 (分かれるのも規模のストレスへの答え)、Bandy 2004 (決まりのない村は約 300 人で分かれる。1/10 にして 30 人)、PPNC で大きな村がばらけた【仮定】0.5・残る村の下限。分かれるのは起きてよい結果で、戻してやり直さない
- **第 1 段の目安** (止まらずに記録する。出来事「段階」): 家族が 6 つ以上で、まとめ役のいないまま G5 に入って 1 年以上たち、集まり・長老・祭りでもめごとを 2 回以上収めた
- **第 2 段へ** (止まらずに記録する。出来事「段階」): 第 1 段の目安に届く (まとまり) か、もめごとが集まりで収まらないまま 2 季節たつ (ゆきづまり) と、季節の集まりでまとめ役を選べ、掟に罰をつけられるようになる。選ぶかどうかは人が決める。【注意】Johnson は順番の階層を、同時の階層に代わる平等なしくみとして示した。第 1 段 → 第 2 段の順はこの計画の解釈 (本人と決めた 2 段階) なので、うまくいっても、ゆきづまっても第 2 段に入れるようにし、第 1 段を条件にはしない。どちらが先だったか (stage1 の日・open の日と how) を記録して報告する
- **まとめ役** (人が決める: leader。「同時の階層」、ウバイド期): 大人の半分をこえる人が同じ人を選ぶとなり、亡くなる・村を出る・半分をこえる人がほかの人か「なし」を選ぶまで続く。家族の代表 (家でいちばん年上の大人) でなくても答える (自分の分だけ)。自分の家のものでないもめごとを、集まりより先に、一人でいくつでも裁ける。祭りを一人で決められる (【文献】Stein 1994)。次の季節にみんなでする仕事を呼びかけられ (call)、応じるかはそれぞれが決める。大人の半分をこえる人が応じると「共同の仕事」(【文献】Fried)
- **罰** (人が決める: 掟の penalty。第 2 段から): もめごとのもと (ヤギ・倉・蓄え・刈る) のどれか 1 つと、払う草の種のつかみ (1000 まで)。罰のある掟が採用されていると、そのもめごとは必ず起き、「つぐなう」に決まると罰の量を払う (家の倉の食べ物、足りなければヤギ。1 頭 = 草の種 375 つかみ)。実際に何か払われたときだけ「罰を払わせた」と数える
- 条件 (第 2 段): 家族が 6 つ以上で、まとめ役がいる。罰のある掟が 3 つ以上採用されている。まとめ役がもめごとを 2 回以上裁いた。罰を 1 回以上払わせた
```

**sim/society/HANDOFF.md:**
- §1: change 「**まだ作っていない**: G5 (リーダーと決まり)・G6 …」 to 「G5 (リーダーと決まり) は作った (G5 に入ってから働く。計画 5 の G5)。**まだ作っていない**: G6 (交易・町・記録)」.
- §4: change the heading to 「### G5 (リーダーと決まり) の仕組み (2026-10-08 に作った。G5 に入ってから働く)」 and add as its first line 「中身は `docs/society2_phase_plan.md` の 5. G5。もめごとの中身は世界で実際に起きたこと (ヤギ・倉・蓄え・刈る) から作る」.

**sim/society/daily_run.md**, add to 「全員が亡くなった・立ち行かなくなったとき」:

> - G5 で家が村を出ていく (村が分かれる) のは起きてよい結果。戻してやり直さない (全員が亡くなったときだけ戻す)。G5 で 8 季節たってももめごとが 0、第 2 段に入って 8 季節たってもまとめ役がいない・罰のある掟が 0 のときは、5 季節ごとの報告で本人に相談する (相談なしに世界やお題を変えない)

---

## 13. Test plan

All tests run in a sandbox; scripts go in the scratchpad. None of them touch `sim/society/data`.

**A. Pre-G5 invariance.** This is mandatory; the synthesizer already passed it with this exact code.
- Build OLD from `git show HEAD:sim/society/era2.py` (`types.ModuleType` plus `exec`) and NEW from the edited file. Use deep copies of `data/state.json`.
- G3 run: 1 season with the real `answers/day1559/season/*.json`.
- G4 run: force `era="G4"` (append `era_log`) and run 3 seasons. Scripted answers per rep (sorted): activities `["畑仕事","採集","ヤギを捕まえる","ヤギの世話","土器づくり","採集","狩り","畑仕事"]` (the catcher's place is the wild-goat place), `pick` 10, `harvest` 40, `sow` 100, `keep` = (i even), `eat_goat` 1 for i == 1, a proposal with a `penalty` for i == season index, all proposed laws voted yes, plus `judge`/`feast`/`leader` fields.
- Each season runs `apply_answers` → `simulate_season` → `check`, then renders `season_prompt` for every name in `answerers`.
- Assert all of the following:
  - The prompts are equal.
  - `json.dumps(state, sort_keys=True)` is equal after removing these 16 keys from `era_info.indicators` and `era_log[*].indicators`: `households, g5_stage, stage1, leader, leader_seasons, disputes, disputes_open, settled, judged, penalty_laws, penalties, feasts, fissions, left_people, joint, stress`.
  - `"g5" not in state["era2"]`.
  - Monkeypatching `NEW._rng` to record salts shows that 37 never appears.
  - `answerers` is equal to HEAD in rep mode, and in non-rep mode (kill adults down to 12 and set `rep_mode=False`).

**B. Unit checks** (import the edited `era2`; deep copy of state with `era="G5"`). Expected values:
- `stress_p`: H = 4/6/8/10 gives 0.12/0.30/0.56/0.90. Within a feast season (`feast_day == step_day`) it is halved.
- `_penalty`:

  | Input | Result |
  |---|---|
  | `{"for":"ヤギ","pay":50}` | ヤギ/50 |
  | `{"for":"倉","pay":"草の種 30 つかみ"}` | 倉/30 |
  | `"刈る 40"` | 刈る/40 |
  | `5000` with law text naming ヤギ only | ヤギ/1000 |
  | `{"for":"蓄え","pay":"５０"}` | 蓄え/50 |
  | `{"pay":0}`, `True`, `"罰はない"`, `{"for":"ヤギ か 倉 か 蓄え か 刈る","pay":50}`, `{"for":"...","pay":0}` | None |

- `_judges`:

  | Input | Result |
  |---|---|
  | `{"M3":"つぐなう","4":"ゆるす"}` | `{"M3":"つぐなう","M4":"ゆるす"}` |
  | `[{"id":"[m3]","do":"償わせる"}]` | `{"M3":"つぐなう"}` |
  | `{"id":"M5","do":"許す"}` | `{"M5":"ゆるす"}` |
  | `{"M3":"..."}`, `{"M3":"つぐなう か ゆるす"}`, `"M3"` | `{}` |

- `_who`:

  | Input | Result |
  |---|---|
  | `"タヒ"`, `"タヒ (川辺の家) がいい"` | タヒ |
  | `"なし"`, `"まとめ役はいらない"` | なし |
  | `"..."`, `None`, `"セナかタヒ"` | None |

- `_pay`:
  - ケトの家 has a store of 100 つかみ and 2 goats; pay 600 つかみ → 100 つかみ plus 1 goat, and food is conserved.
  - Store empty, goats only, pay 50 → paid 0 and words "".
- `_steal`: one event per (thief household, victim) pair; incidents get the right totals (ナギの家 50, 川辺の家 7).
- Meeting, with 16 adults in rep mode:
  - Weights 3+2+2+1+2 = 10 → 集まり.
  - 8 vs 8 with elder セナ choosing ゆるす → 長老.
  - Elder in the minority → stays open.
  - 3 disputes answered by everyone → only 2 settle (TALK_MAX).
  - Leader タヒ judges 3 disputes; the one involving 川辺の家 goes to the assembly.
  - The leader alone holds a feast: store drops by 3×`_need`, and 2 of 3 disputes become by="祭り".
  - Leader votes are ignored in stage 1.
  - 7/16 does not elect; 9/16 (「タヒさん」 included) elects.
  - 「なし」 9/16 recalls.
  - A dead leader is cleared at the meeting.
- `_split`: a newborn (no household, mother in the leaving household) leaves too. Goats and store go; fields get `owner=None`; disputes become 去った; the leader is cleared.
- `_can_leave`: 4 households / 9 adults → True; 3 households → False.

**C. Multi-season policies in memory** (verified reference run; small differences are fine).
- Setup: `era="G5"`, `era_log` plus G4 (1529) and G5 (1559); goats owned round-robin across `_homes`; ripe fields owned by the household of `by`; `keep=True` for the first 4 `_homes`.
- Each season: answers for `answerers(S)` → `apply_answers` → `simulate_season` → `last_first` → `check`.
- Base answer for every policy (reps sorted, index i): job = `["畑仕事","採集","採集","ヤギの世話","土器づくり","採集","狩り","畑仕事"][i]`, `pick` 10, `harvest` 30, `sow` 150.
- coop adds: judge all つぐなう; feast when k%3 == 2; keep for i < 4. In stage 2 it also adds leader 「タヒ (川辺の家)」, call 「みんなで畑仕事」, and when i == k%8 a proposal with penalty `["刈る","蓄え","ヤギ","倉"][k%4]` at 「50 つかみ」. All proposed laws voted yes.
- divide adds: judge as a list with つぐなう for odd i and ゆるす for even i; `feast` 「"false"」; leader = own name in stage 2.
- silent adds no G5 fields, and rep 3 does 採集 instead of ヤギの世話, so goats go untended.

| Policy | Reference result |
|---|---|
| coop | Stage 2 via まとまり at day 1679. タヒ elected 15/15 at 1680 and answers as a 9th answerer. 3 `裁き` and 3 `罰` at 1710. G6 at day 1799 (season 8). |
| divide | Stage 2 via まとまり at 1679. No leader, no fission. `settled` 10 by 1919. Criterion never met. |
| silent | Stage 2 via ゆきづまり and a fission at 1649. Second fission at 1889. Households 8 → 6. Rep mode turns off at 12 adults. |

Hard invariants every season, for all policies:
- At most 3 new disputes.
- At most 1 fission per 120 days.
- At least 6 adults whenever a fission happened.
- The leader is an alive adult or None.
- `check` is False after season 1.
- No exceptions.
- The village never empties.

**D. step.py smoke test** with `SOC_DATA=<scratch>/g5`:
1. Copy `state.json`, force `era="G5"`, append `era_log`, set `hold=False`.
2. Write answers for `era2.answerers(state)` into `answers/day1559/season/`.
3. Run `PYTHONUTF8=1 SOC_DATA=… python sim/society/step.py season` twice.
4. Check: exit 0; `*` lines for G5 events (including meeting events in the second season); the `G5 第 1 段 / …` line; generated prompts containing `## 村の集まり` and `"judge"`, but not `"leader"` while in stage 1.

**E. Haiku dry run** (optional, before going live). In a scratch copy of the repo, force G5 and run the workflow with `{"steps": 2}`. Measure the share of parseable `judge`, `feast`, `leader` and `penalty` answers.

---

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Haiku never elect a leader, so G5 is stuck | `"leader": "..."` invites names. The last tally is shown. Rep weighting means 4–5 reps can reach a majority. If there is still no leader after 8 seasons in stage 2, raise it in the 5-season report; no automatic rule change. Staying leaderless is also a legitimate outcome (Johnson). |
| No penalty laws | The いま line shows the exact format; 「罰のある掟: まだない」 is shown; consult after 8 seasons. |
| Penalty never actually paid | Most accused households can pay: 刈る accused own a keep store, and 蓄え accused are favoured when they hold a store. Payment falls back to goats. The FACTS state the goat-rounding rule, so people can choose amounts of 188 つかみ or more. Only real payments count. |
| No disputes at all (thin supply) | Four independent sources. 蓄え works without any keep household (it produced autumn candidates in the test). 刈る runs every summer once keep households exist. If disputes stay at 0 for 8 seasons, report (FREE_DAYS and the 0.25 rule can be tuned; the user's OK is needed). |
| Stage 1 skipped by immediate priming | The leader and penalty fields are hidden until the gate opens; `stage1` and `open.how` are recorded. |
| Disputes spiral into mass fission | At most 3 new per season; merging; fade after 4 seasons; leader judgments unlimited; feasts reconcile half; at most 1 fission per year; guard of 3 households and 6 adults. Fission is `left`, not death, so no roll-back. |
| H < 6 for a long time after fissions | A legitimate 「止まる」 outcome (plan 2.1). Households regrow only through visitor groups; flag in reports. Possible future option: adults born in the village found new households. |
| Leader's `keep`/`eat_goat` overriding the rep (judge flaw) | `own=False` for a non-rep leader; the lines are hidden in their prompt; `fam` excludes self-answering members. |
| Trivial or accidental completion | Gate, structured penalty, adoption delay, judgments, real payment. Minimum is season 5; observed was 8. |
| Breaking pre-G5 behaviour | Every insert is gated; there is one new salt; invariance verified byte-for-byte (§0, test A). |
| `log()` keyword collision | Data keys used are `dispute`, `about`, `by`, `law`, `owner`, `home`, `field`, `household`, `how`; never `kind`, `who` or `text`. |
| Workflow stops at a stage change | No text contains 「フェーズが…に進んだ」. |
| Size | About 330 new lines in `era2.py` (section about 250 with comments, prompts about 70, hooks about 35), plus about 8 in `step.py`. `call` is separable (about 15 lines). |

## 15. Decisions for 本人 (recommendation first)

1. **Criterion adds 「罰を 1 回以上払わせた」** (research §6(c)). Recommend keeping it.
2. **No hold at stage 1 or stage 2.** Logged, printed and reported. A hold at stage 2 opening would take 3 lines in step.py.
3. **The criterion does not require stage 1.** Alternative: add `and i["stage1"]`.
4. **Joint work (`共同の仕事`) is tracked but not required.** Alternative: add `and i["joint"] >= 1` to the criterion.
5. **The complainant household is the one that leaves.** Fission is not rolled back.
6. **「よその家の畑を刈った」 is implemented as 刈る** (the harvester complains) because the owner loses nothing in this world.
7. **All numbers are 【仮定】:** 0.3 / 0.9 / 3 per season / 2 per meeting / 4-season fade / 3 feast days / 20% trample / 10 adult-days / 10% reap share / 1000 cap / 0.5 × pop/30 / 3 households and 6 adults remain / 1 fission per year.

## 16. Judges' flaws → fixes

| Flaw | Fix in this spec |
|---|---|
| Meeting events logged before `first` are invisible | `g5.meet_first` plus the "この前の集まりから起きたこと" list in `_g5_text`; `before` in step.py. |
| Newborn left behind in fission | `_g5_season_end` runs **after** `_sync_households`, and `_split` also takes children whose mother leaves (tested). |
| Tenure ≥ 4 criterion not in the plan | Dropped. |
| Null placeholders stall the run | `"leader": "..."` and `"judge": {id: "..."}`; `penalty` stays null with an explicit format line. |
| Penalties available in stage 1 | Penalty parsing is gated on `stage >= 2`, behind the same gate as the leader. |
| Off-by-one in the text | Stated correctly: failure-path gate at the end of G5 season 3 at the earliest, success path at season 4. |
| Non-rep leader's `keep` overrides the rep | `own` flag, prompt lines hidden. |
| Dispute supply can be zero | 蓄え for any household (keep favoured) plus 刈る; measured. |
| Penalty counted with no payment | Counted only when `paid > 0`. |
| Penalty laws not tied to a dispute kind | `penalty.for` is a kind; a law makes that kind's incidents always become disputes. |
| Payment taken from hand food at meeting time | House store, then goats only. |
| Leader judges own household's disputes | Recusal. |
| No explicit elder | 長老 = eldest non-party adult, tie or plurality. |
| No joint-work call | `call` plus the `共同の仕事` evaluation. |
| Backlog snowballs | DROP_AGE 4, MAX_NEW 3, TALK_MAX 2. |
| Leader replaces the user-decided eldest rep | Eldest-rep rule kept; the leader is an extra answerer. |
| Trivially early, or the stage-1 milestone just a label | Gate plus H ≥ 6 and 1-year milestone. |

**Files to edit:**
- `sim/society/era2.py`
- `sim/society/step.py`
- `sim/society/resume.py`
- `docs/society2_phase_plan.md`
- `sim/society/HANDOFF.md`
- `sim/society/daily_run.md`

**Unchanged:** `characters.py`, `knowledge.py`, `world.py`.
## 17. 作ったあとに直したこと (2026-10-08、クラウドのセッション)

この設計書のコードをそのまま `era2.py`・`step.py`・`resume.py` に入れ (コミット ba6461f)、13. の試し方 A〜D と、設計書とコードの照らし合わせを、ワークフローで写しを使って行った。A (G5 の前は何も変わらない) 41/41、B (関数ごと) 144/144、C (3 つのやり方) は参考の結果と同じ日に同じことが起き、D (step.py) は 2 季節とも正しく終わった。照らし合わせの確認役が、設計書のコードそのものの弱いところを見つけたので、次のように直した (どれも G5 に入ってから働く所で、A は直したあとも 41/41)。

1. `_who`: 「ソル (ナギの家)」のように家の名前を添えた票で、家の名前の中の人の名前 (ナギ) も数えてしまい、2 人に当たって票が捨てられていた。家の名前を取りのぞいてから名前を探す
2. `_verdict`: 半つかみより少ない払いも「罰を払わせた」と数え、記録には量が空のまま出ていた。半つかみより少ないものは払ったと数えない
3. お題: 第 1 段のお題に「まとめ役の答え」という言葉が出ていた (設計の「第 2 段まで、まとめ役を見せない」に反する)。第 2 段からにした
4. `_do`: 「払わなくてよい」「ゆるさない」のような打ち消しを読みちがえていた。打ち消しのある答えは、どちらとも読まない
5. `_steal`: 家のない人が取ると、もめごとのもとにならず、毎日記録が出る (今はそういう人はいない)。家のない人は取らない
6. 長老: 同じ年の大人がいると、長老 (名前の順) と家の代表 (人の並びの順) がちがう人になり、長老が答えないので長老の決めがはたらかなかった (今はそういう家はない)。長老も家の代表と同じく、同じ年なら人の並びで先の人にした。B の「川辺の家が当事者のときの長老」は、同じ 39 歳のハユとナギのうちナギになる (どちらも家の代表で答える)
7. `resume.py`: 村を出た家の、いちばん年上の人の履歴書にしか「分かれる」が出なかった。家の人みんなの履歴書に出す
8. お題の「前の季節の、家ごとの村の蓄えへの出し入れ」に、村を出た家が出ていた。今いる家だけにした

直さなかったこと (見え方だけ): 同じ季節の終わりに「また同じことが重なった」と「だれも言わなくなった」が続くことがある (言わなくなるまでの季節を、もめごとの起きた日から数えるため)。祭りの季節の終わりの指標 stress は半分の値で記録される (その季節のこと)
