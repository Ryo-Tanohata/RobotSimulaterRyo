"""ダッシュボードの内側の記録を作る (docs/dashboard_records_spec.md 3.)

  python3 sim/society/tools/build_records.py [--data DIR] [--check] [--quiet]

state.json・答え・お題・records/snapshots.jsonl (季節の終わりの控え) を読むだけで、records/ の中の記録を作り直す:
人 (people.json)・家 (households.json)・だれがどの家にいたか (membership.json)・季節ごとの行 (season_village / season_household /
season_person .jsonl)・出し入れの帳簿 (ledger.jsonl)・年の名前 (year_names.json)・掟 (laws.json)・もめごと (disputes.json)・
列の説明 (columns.json)・まとめ (meta.json)。
世界の進み方には使わない (state を変えない・乱数を使わない)。時刻を入れないので、何度作っても同じバイト列になる。
--data: データの置き場所 (ふだんは $SOC_DATA か sim/society/data)
--check: 帳簿が合うかを確かめる (家の倉・ヤギ・土器・鎌に「記録にない差」があれば、終わりのコード 1)
--quiet: 1 行だけ表示する (step.py が季節のあとに呼ぶ)
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import characters  # noqa: E402
import era2  # noqa: E402
import records  # noqa: E402
import world  # noqa: E402

SCHEMA = 1
YEAR, SDAYS = era2.YEAR, world.SEASON_DAYS
FOODS = ("草の種", "木の実", "芋", "干し肉", "肉", "魚", "ピク", "乳")
COUNTED = {"ヤギ": "頭", "土器": "個", "鎌": "本"}
FLOW_ITEM = "食べ物 (草の種にして)"
ITEMS = FOODS + tuple(COUNTED) + (FLOW_ITEM,)
UNIT = {k: world.UNITS[k] for k in FOODS}  # (単位, 1 単位の kcal)。乳は era2 が足す
NAME2KIND = {v: k for k, v in world.FOOD_NAME.items()}
WORD_RE = re.compile(r"(木の実|芋|ルクの肉|魚|ピクの肉|草の種|干し肉|ヤギの乳) (\d+) (つかみ|本|切れ|匹|杯)")
PAY_RE = re.compile(r"。(\S+?)が(\S+?)に (.+?) を払った")
GOATS_RE = re.compile(r"ヤギ (\d+) 頭")
ACT_BY_EVENT = {"採集": "採集", "探索": "探索", "休む": "休む", "道具": "道具づくり", "火": "火おこし", "種まき": "種まき",
                "畑仕事": "畑仕事", "ヤギの世話": "ヤギの世話", "ヤギを捕まえる": "ヤギを捕まえる", "土器": "土器づくり", "住まい": "住まいを建てる",
                "狩り": "狩り"}  # step.py の ACT_BY_EVENT と同じ (+ 狩り)
START, END, DIFF = "季節のはじめの残り", "季節の終わりの残り", "記録にない差"
FLOWS = ("採った", "木から取った", "狩った", "乳をしぼった", "刈った (村の蓄えに入った)", "刈った (自分の家の畑)", "ヤギをつぶした",
         "家にだれもいなくなり、村のものになった", "家の倉から食べた", "家の倉から食べた (子)", "よその家の倉から取った",
         "捕まえた", "生まれた", "作った", "罰・つぐないで受け取った", "持ち主がいなくなり村のものになった",
         "食べた", "まいた (畑)", "種として埋めた", "腐った", "虫やネズミ", "祭り", "雨で傷んだ", "干した",
         "亡くなった人の手元", "村を出た人の手元", "家の人が食べた", "子が食べた", "よその家の人に取られた",
         "だれもいなくなり、村のものになった", "村を出て持っていった", "いなくなった (世話が足りない)", "つぶした", "罰・つぐないで払った",
         "割れた", "村の蓄えに入れた (大人)", "村の蓄えから取った (大人)")
WHY_ROUND = "採集の記録は、物ごとの量を整数に丸めて書いている"
EPS = 1e-6


# ---------------- 小さな道具 ----------------

def r2(x):
    return None if x is None else round(x, 2) + 0.0  # -0.0 を 0.0 に


def units(kind, kcal):
    return kcal / UNIT[kind][1]


def words(text):
    """「木の実 12 つかみ、芋 2 本」→ {物: 単位の数}"""
    out = {}
    for name, n, _ in WORD_RE.findall(text or ""):
        k = NAME2KIND.get(name, name)
        out[k] = out.get(k, 0) + int(n)
    return out


def kcal_of(w, total=None):
    """{物: 単位の数} → {物: kcal}。total (正しい合計) があれば、合計がそれになるように割り振る (物ごとの量は丸めのぶんずれる)"""
    k = {x: n * UNIT[x][1] for x, n in w.items() if x in UNIT}
    s = sum(k.values())
    if total is not None and s > 0:
        k = {x: v * total / s for x, v in k.items()}
    return k


def add(d, k, v):
    d[k] = d.get(k, 0) + v


def food_units(kc):
    """{物: kcal} → {物: 単位の数} (物の並び順)"""
    return {k: r2(units(k, kc[k])) for k in FOODS if kc.get(k)}


def jdump(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


# ---------------- 読み込み ----------------

def load_answers(data, start):
    """answers/dayNNNN/{season,feeling}/名前.json → {日: {"season": {名前: 答え}, "feeling": {名前: 答え}}}"""
    out = {}
    root = data / "answers"
    if not root.exists():
        return out
    for d in sorted(root.iterdir()):
        m = re.fullmatch(r"day(\d+)", d.name)
        if not m or int(m.group(1)) < start:
            continue
        day = int(m.group(1))
        row = {}
        for kind in ("season", "feeling"):
            sub = d / kind
            if sub.is_dir():
                row[kind] = {f.stem: characters.parse(f.read_text(encoding="utf-8")) for f in sorted(sub.glob("*.json"))}
        if any(row.values()):
            out[day] = row
    return out


class Builder:
    def __init__(self, data):
        self.data = Path(data)
        self.state = json.loads((self.data / "state.json").read_text(encoding="utf-8"))
        st = self.state
        self.e2 = st.get("era2") or {}
        self.start = self.e2.get("start_day")
        self.ev = st["events"]
        self.ids_ok = all(e["id"] == i for i, e in enumerate(self.ev))
        self.snaps, self.snap_stats = records.load_snapshots(self.data, st)
        self.answers = load_answers(self.data, self.start if self.start is not None else 10 ** 9)
        self.warnings = []
        self.people = st["people"]
        self.byname = {p["name"]: p for p in self.people}
        self.pid = {p["name"]: f"P{i + 1:03d}" for i, p in enumerate(self.people)}
        hs = []
        for p in self.people:
            h = p.get("household")
            if h and h not in hs and h != "-":
                hs.append(h)
        self.hid = {h: f"H{i + 1:02d}" for i, h in enumerate(hs)}
        self.hid["-"] = "H00"
        self.hname = {v: k for k, v in self.hid.items()}
        self.stats = {s["day"]: s for s in st.get("stats", [])}
        self._index_events()

    def warn(self, msg):
        self.warnings.append(msg)

    def P(self, name):
        return self.pid.get(name, name)

    def H(self, h):
        return self.hid.get(h) if h else None

    # ---- 出来事の索引 (全部を 1 回だけ見る) ----
    def _index_events(self):
        self.death, self.joined_ev, self.born_ev, self.left_ev, self.built_ev = {}, {}, {}, {}, {}
        self.law_ev = []  # (出来事, 採用|廃止, 文)
        for e in self.ev:
            t, x, who, d = e["type"], e["text"], e.get("who"), e.get("data") or {}
            if t == "死" and who and who not in self.death:
                self.death[who] = e
            elif t == "加わる" and x.startswith("よそから来た "):
                names = x[len("よそから来た "):].split(" が、")[0].split("・")
                for n in names:
                    self.joined_ev.setdefault(n, (e, names))
            elif t == "生まれる":
                m = re.search(r"名前は (\S+) \(", x)
                if m:
                    self.born_ev.setdefault(m.group(1), e)
            elif t in ("去る", "分かれる"):
                self.left_ev.setdefault(e["day"], []).append(e)
            elif t == "住まい" and d.get("size") is not None and d.get("household") and d["household"] not in self.built_ev:
                self.built_ev[d["household"]] = e["id"]
            elif t == "掟":
                m = re.fullmatch(r"掟「(.*)」が(採用|廃止)された \(.*\)", x, re.S)
                if m:
                    self.law_ev.append((e, m.group(2), m.group(1)))

    # ---------------- 人・家・だれがどの家に ----------------
    def build_people(self):
        start = self.start
        self.mem = {}  # 名前 → 1 つの滞在 (今は 1 人 1 行)
        self.t_in, self.t_out = {}, {}
        people = []
        first_hh = {}
        for day in sorted(self.snaps):
            for n, sp in self.snaps[day]["people"].items():
                if sp.get("household") and n not in first_hh:
                    first_hh[n] = day
        for p in self.people:
            n = p["name"]
            origin = p.get("origin") or "はじめから"
            de = self.death.get(n)
            died = de["day"] if de and not p["alive"] and not p.get("left") else None
            exact = not (died is not None and start is not None and died < start)
            if origin == "生まれた":
                came, ev_in, with_ = p.get("born_day"), self.born_ev.get(n), []
            elif origin == "よそから来た":
                je = self.joined_ev.get(n)
                came, ev_in = (je[0]["day"], je[0]) if je else (None, None)
                with_ = [self.P(m) for m in (je[1] if je else []) if m != n]
            else:
                came, ev_in, with_ = 0, None, []
            left, why, lev = p.get("left"), None, None
            if left is not None:
                for e in self.left_ev.get(left, []):
                    if e["type"] == "分かれる" and n in e["text"]:
                        why, lev = "家ごと村を出た", e
                    elif e["type"] == "去る" and (e.get("who") == n or n in e["text"]):
                        why, lev = ("母を追って村を出た" if "追って" in e["text"] else "飢えで村を出た"), e
                    if why:
                        break
                why = why or "村を出た"
            age_death = None
            if died is not None:
                age_death = (died - p["born_day"]) // YEAR if exact and p.get("born_day") is not None else p.get("age")
            mother = p.get("mother")
            hh = self.H(p.get("household"))
            people.append({
                "id": self.P(n), "name": n, "sex": p.get("sex"), "born_day": p.get("born_day"), "born_day_exact": exact,
                "origin": origin, "came_day": came, "came_with": with_,
                "mother_id": self.P(mother) if mother and origin == "生まれた" else None,
                "guardian_id": self.P(mother) if mother and origin == "よそから来た" else None,
                "parent_ids": [self.P(mother)] if mother and origin == "生まれた" else [],
                "died_day": died, "death_cause": records.death_cause(de["text"]) if died is not None else None,
                "death_event": de["id"] if died is not None else None, "age_at_death": age_death,
                "left_day": left, "left_why": why,
                "status": "生きている" if p["alive"] else "村を出た" if left is not None else "亡くなった",
                "household_id": hh})
            out_day = died if died is not None else left
            self.mem[n] = {"person_id": self.P(n), "household_id": hh, "from_day": came, "to_day": out_day,
                           "why_in": origin, "why_out": "亡くなった" if died is not None else why,
                           "evidence": [x["id"] for x in (ev_in, de if died is not None else lev) if x],
                           "assigned_from_state_day": first_hh.get(n)}
            # 季節の中での順: 集まりで加わった人は、その日の季節の終わりのあと (次の季節から)
            self.t_in[n] = (came if came is not None else 0) + (0.5 if origin == "よそから来た" else 0)
            self.t_out[n] = out_day
        self.people_rows = people
        self.membership = [self.mem[p["name"]] for p in self.people]
        hrows = []
        for h, i in sorted(self.hid.items(), key=lambda kv: kv[1]):
            ms = [p for p in self.people if p.get("household") == h]
            if not ms:
                continue
            first = min(self.mem[p["name"]]["from_day"] or 0 for p in ms)
            founders = [self.P(p["name"]) for p in ms if self.mem[p["name"]]["why_in"] in ("はじめから", "よそから来た")
                        and (self.mem[p["name"]]["from_day"] or 0) == first]
            alive = [p for p in ms if p["alive"]]
            adults_now = [p for p in alive if not p.get("child")]
            last_adult = None
            if alive and not adults_now:  # 大人がいなくなった日: 大人だった人が最後にいた日
                last_adult = max((self.mem[p["name"]]["to_day"] for p in ms if not p.get("child") and self.mem[p["name"]]["to_day"] is not None),
                                 default=None)
            fis = next((f for f in ((self.e2.get("g5") or {}).get("fissions") or []) if f.get("household") == h), None)
            home = (self.e2.get("homes") or {}).get(h) or {}
            hrows.append({"id": i, "name": h, "origin": "はじめから" if h == "川辺の家" or all(self.mem[p["name"]]["why_in"] != "よそから来た" for p in ms)
                          else "よそから来た群れ",
                          "founder_ids": founders, "first_day": first, "adults_last_day": last_adult,
                          "last_day": None if alive else max((self.mem[p["name"]]["to_day"] or 0) for p in ms),
                          "left_village_day": fis["day"] if fis else None,
                          "fission": ({"day": fis["day"], "people": [self.P(x) for x in fis.get("people", [])], "goats": fis.get("goats"),
                                       "store_kcal": fis.get("store"), "fields": fis.get("fields"), "dispute": fis.get("dispute")} if fis else None),
                          "home_built_day": home.get("built"), "home_start_day": home.get("start")})
        self.household_rows = hrows

    def present(self, n, D):
        """季節 D のあいだに村にいたか"""
        ti, to = self.t_in[n], self.t_out[n]
        return ti <= D and (to is None or to > D - SDAYS)

    def alive_at(self, n, day):
        """day 日の終わり (季節の終わりの出来事のあと、集まりの前) に村にいるか"""
        ti, to = self.t_in[n], self.t_out[n]
        return ti <= day and (to is None or to > day)

    def age(self, n, day):
        return records.age_on(self.byname[n], day)

    def is_adult(self, n, day, snap=None):
        sp = (snap or {}).get("people", {}).get(n) if snap else None
        if sp is not None and sp.get("alive"):
            return not sp.get("child")
        a = self.age(n, day)
        return a is not None and a >= era2.ADULT

    # ---------------- 回 (round) と季節 ----------------
    def build_rounds(self):
        st, start = self.state, self.start
        days = {start} | set(d for d in self.snaps if start <= d <= st["day"])
        days |= {d for d in range(start + 1, st["day"] + 1) if (d + 1) % SDAYS == 0}
        days |= {d for d in self.answers if start <= d <= st["day"]}
        days = sorted(days)
        rounds = []
        for a, r in zip(days, days[1:]):
            s = self.snaps.get(r)
            mf = s["meeting_first"] if s and s.get("meeting_first") is not None else records.meeting_first(st, a)
            if s and s.get("event_first") is not None:
                ef = s["event_first"]
            else:
                ef = next((e["id"] for e in self.ev[mf:] if e["day"] > a), st["next_event"])
            if s:
                ee = s["event_end"]
            elif r == st["day"]:
                ee = st["next_event"]
            else:
                ee = records.meeting_first(st, r)
            rounds.append({"start": a, "end": r, "meeting_day": a, "meeting_first": mf, "event_first": ef, "event_end": ee, "snapshot": s is not None})
        self.rounds = rounds
        self.seasons = {}
        for rd in rounds:
            self.seasons.setdefault(records.season_end(rd["end"]), []).append(rd)

    def era_on(self, day):
        """day 日の終わり (判定のあと) のフェーズ"""
        era = None
        for x in self.state.get("era_log", []):
            if x["day"] <= day:
                era = x["era"]
        return era

    # ---------------- 1 季節 ----------------
    def season(self, D, rds):
        a = rds[0]["start"]
        P, C = self.snaps.get(a), self.snaps.get(D)
        mf, end = rds[0]["meeting_first"], rds[-1]["event_end"]
        ev = self.ev[mf:end]
        era = (P or {}).get("era") or self.era_on(a)
        era_end = (C or {}).get("era") or self.era_on(D)
        meeting_ids = set()
        for rd in rds:
            meeting_ids |= set(range(rd["meeting_first"], rd["event_first"]))
        present = [p["name"] for p in self.people if self.present(p["name"], D)]
        alive_end = [n for n in present if self.alive_at(n, D)]
        hh = {p["name"]: p.get("household") for p in self.people}

        # ---- 出来事を 1 回だけ見る ----
        act = {}           # 名前 → {日: 仕事}
        out = {}           # 名前 → 成果
        said = {}
        inj, rain_out = {}, {}
        sown_ev, harvest_ev, caught_ev = [], [], []
        demo = {"births": [], "deaths": [], "joined": [], "left": [], "came_of_age": [], "visitors_rejected": []}
        fields_ev = {"ripened": 0, "failed": 0, "fallen": 0, "trampled": 0, "trampled_by": {}}
        pests = {"amount": 0, "safe": None, "events": []}
        pots = {"made": 0, "broken": 0}
        sick = {"made": 0, "broken": 0}
        goat_ev = {"kids": 0, "lost": 0, "eaten": 0, "caught": 0}
        laws = {"adopted": [], "abolished": []}
        g5 = {"leader_elected": None, "new": [], "settled": [], "judged": 0, "payments": [], "feast": None, "joint": 0, "fission": None,
              "penalty_laws": []}
        inherit = []
        flows_v = {}       # 村の食べ物: 理由 → {物: kcal}
        year_named = None
        substeps = []

        def o(n):
            return out.setdefault(n, {"gathered": {}, "tree_picked": 0, "tree_pick_evenings": 0, "hunted": {}, "milk": 0, "harvested": 0,
                                      "sown": 0, "planted": 0, "pots": 0, "sickles": 0, "goats_caught": 0, "house_work_days": 0})

        def mark(n, day, a_):
            act.setdefault(n, {}).setdefault(day, a_)

        for e in ev:
            t, x, who, d, day = e["type"], e["text"], e.get("who"), e.get("data") or {}, e["day"]
            if t in ACT_BY_EVENT and e["id"] not in meeting_ids:
                if t == "狩り" and d.get("hunters"):
                    for n in d["hunters"]:
                        mark(n, day, "狩り")
                elif who and not (t == "種まき" and "を種として埋めた" in x) and not (t == "道具" and who is None):
                    mark(who, day, ACT_BY_EVENT[t])
            if t == "採集" and who:
                k = kcal_of(words(x), d.get("kcal"))
                for kk, v in k.items():
                    add(o(who)["gathered"], kk, v)
                    add(flows_v.setdefault("採った", {}), kk, v)
            elif t == "木から取る" and who:
                n = sum(words(d.get("food") or x).values())
                o(who)["tree_picked"] += n
                o(who)["tree_pick_evenings"] += 1
                add(flows_v.setdefault("木から取った", {}), "木の実", n * UNIT["木の実"][1])
            elif t == "狩り":
                if "しとめた" in x:
                    k = d.get("killer") or who
                    add(o(k)["hunted"], "肉", world.MEAT_KCAL)
                    add(flows_v.setdefault("狩った", {}), "肉", world.MEAT_KCAL)
                else:
                    for kk, v in kcal_of(words(x)).items():
                        add(o(who)["hunted"], kk, v)
                        add(flows_v.setdefault("狩った", {}), kk, v)
            elif t == "乳" and who:
                o(who)["milk"] += d.get("amount", 0)
                add(flows_v.setdefault("乳をしぼった", {}), "乳", d.get("amount", 0) * UNIT["乳"][1])
            elif t == "収穫" and who:
                o(who)["harvested"] += d.get("amount", 0)
                harvest_ev.append(e)
            elif t == "畑":
                if who and d.get("seed") is not None:
                    o(who)["sown"] += d["seed"]
                    sown_ev.append(e)
                    add(flows_v.setdefault("まいた (畑)", {}), "草の種", d["seed"] * UNIT["草の種"][1])
                elif "実らなかった" in x:
                    fields_ev["failed"] += 1
                elif "実った" in x:
                    fields_ev["ripened"] += 1
                elif "落ちてしまった" in x:
                    m = re.search(r"約 (\d+) つかみ", x)
                    fields_ev["fallen"] += int(m.group(1)) if m else 0
            elif t == "種まき" and who and "を種として埋めた" in x:
                n = words(x).get("木の実", 0)
                o(who)["planted"] += n
                add(flows_v.setdefault("種として埋めた", {}), "木の実", n * UNIT["木の実"][1])
            elif t == "土器" and who:
                o(who)["pots"] += d.get("count", 0)
                pots["made"] += d.get("count", 0)
            elif t == "道具":
                if who and d.get("count"):
                    o(who)["sickles"] += d["count"]
                    sick["made"] += d["count"]
                elif who is None:
                    m = re.search(r"村の(土器|鎌)が (\d+)", x)
                    if m:
                        (pots if m.group(1) == "土器" else sick)["broken"] += int(m.group(2))
            elif t == "ヤギ":
                if who:
                    o(who)["goats_caught"] += 1
                    caught_ev.append(e)
                    goat_ev["caught"] += 1
                elif "子ヤギが" in x:
                    m = re.search(r"子ヤギが (\d+) 頭生まれた", x)
                    goat_ev["kids"] += int(m.group(1)) if m else 0
                elif "いなくなった" in x:
                    m = GOATS_RE.search(x)
                    goat_ev["lost"] += int(m.group(1)) if m else 0
                elif d.get("field") is not None:
                    m = re.search(r"約 (\d+) つかみ", x)
                    lost = int(m.group(1)) if m else 0
                    fields_ev["trampled"] += lost
                    fo = re.search(r"、(\S+?)の畑を荒らした", x)
                    if fo:
                        add(fields_ev["trampled_by"], fo.group(1), lost)
            elif t == "ヤギを食べる":
                m = GOATS_RE.search(x)
                n = int(m.group(1)) if m else 0
                goat_ev["eaten"] += n
                add(flows_v.setdefault("ヤギをつぶした", {}), "干し肉", n * era2.GOAT_MEAT * world.UNITS["肉"][1])
            elif t == "腐る":
                for kk, v in kcal_of(words(x), d.get("kcal")).items():
                    add(flows_v.setdefault("腐った", {}), kk, v)
            elif t == "干す":
                w = kcal_of(words(x))
                for kk, v in w.items():
                    add(flows_v.setdefault("干した", {}), kk, -v)
                    add(flows_v["干した"], "干し肉", round(v * 0.8))
            elif t == "雨":
                for n in d.get("outside") or []:
                    add(rain_out, n, 1)
                if d.get("kcal"):
                    for kk, v in kcal_of(words(x.split("蓄えの")[-1]), d["kcal"]).items():
                        add(flows_v.setdefault("雨で傷んだ", {}), kk, v)
            elif t == "虫":
                pests["amount"] += d.get("amount", 0)
                pests["events"].append(e["id"])
                m = re.search(r"土器に入れていた 約 (\d+) つかみ", x)
                if m:
                    pests["safe"] = (pests["safe"] or 0) + int(m.group(1))
            elif t == "祭り" and "を使った" in x:
                k = words(x.split("村の蓄えから")[-1])
                g5["feast"] = {"event": e["id"], "words": k}
                g5["settled"] += re.findall(r"\[(M\d+)\]", x.split("を使った")[-1])
            elif t in ("収める", "裁き"):
                g5["settled"].append(d.get("dispute"))
                if t == "裁き":
                    g5["judged"] += 1
                m = PAY_RE.search(x)
                if m:
                    payer, recv, w = m.group(1), m.group(2), m.group(3)
                    gm = GOATS_RE.search(w)
                    g5["payments"].append({"event": e["id"], "dispute": d.get("dispute"), "from": payer, "to": recv,
                                           "food": kcal_of(words(w)), "goats": int(gm.group(1)) if gm else 0})
            elif t == "罰":
                g5["penalty_laws"].append({"dispute": d.get("dispute"), "law": d.get("law")})
            elif t == "もめごと" and "言い出した" in x:
                g5["new"].append(d.get("dispute"))
            elif t == "まとめ役" and "まとめ役に選ばれた" in x:
                g5["leader_elected"] = who
            elif t == "共同の仕事":
                g5["joint"] += 1
            elif t == "分かれる":
                g5["fission"] = d.get("household")
            elif t == "受けつぎ":
                m = re.search(r"が亡くなり、(.+?の家)(?:の|には)", x)
                h = m.group(1) if m else None
                to_v = "村のものになった" in x
                rest = x.split("が亡くなり、", 1)[-1]
                wm = re.search(r"ので、(.+)は村のものになった", rest) if to_v else re.search(r"の家の(.+)は、", rest)
                inherit.append({"event": e["id"], "household": h, "dead": d.get("dead") or (x.split(" が亡くなり")[0] if " が亡くなり" in x else None),
                                "heir": who, "what": wm.group(1) if wm else None, "to_village": to_v, "words": words(x)})
            elif t == "死" and who:
                demo["deaths"].append(who)
            elif t == "生まれる":
                m = re.search(r"名前は (\S+) \(", x)
                if m:
                    demo["births"].append(m.group(1))
            elif t == "加わる" and x.startswith("よそから来た "):
                demo["joined"] += x[len("よそから来た "):].split(" が、")[0].split("・")
            elif t == "去る":
                if "受け入れられず" in x:
                    demo["visitors_rejected"].append({"event": e["id"], "group": x[len("よそから来た "):].split(" たち")[0] if x.startswith("よそから来た ") else None})
            elif t == "大人になる" and who:
                demo["came_of_age"].append(who)
            elif t == "話す" and who:
                said.setdefault(who, {"count": 0, "to": []})
                said[who]["count"] += 1
                to = d.get("to", "みんな")
                said[who]["to"].append(to if to == "みんな" else self.P(to))
            elif t == "けが" and who:
                add(inj, who, 1)
            elif t == "住まい" and who and d.get("household"):
                o(who)["house_work_days"] += 1
            elif t == "掟":
                m = re.fullmatch(r"掟「(.*)」が(採用|廃止)された \(.*\)", x, re.S)
                if m:
                    lid = self.law_of.get(e["id"])
                    (laws["adopted"] if m.group(2) == "採用" else laws["abolished"]).append(lid)
            elif t == "年の名前":
                year_named = {"year": d.get("year"), "name": d.get("name"), "event": e["id"]}
            elif t == "区切り":
                substeps.append({"g": d.get("g"), "f": d.get("f"), "day": day})
        demo["left"] = [n for n in present if self.t_out[n] is not None and self.byname[n].get("left") is not None
                        and D - SDAYS < self.t_out[n] <= D]

        # ---- 畑の収穫をたどり直す (どの畑を刈って、どの倉に入ったか。spec 4.3) ----
        harvest = self.replay(D, a, P, C, harvest_ev, era)

        # ---- 食べた量 (日ごとの記録) ----
        eaten, eaten_total, eaten_sown, rain_nights = {}, 0, 0, 0
        for day in range(D - SDAYS + 1, D + 1):
            s = self.stats.get(day)
            if not s or day <= a:
                continue
            for kk, v in (s.get("eaten_by_kind") or {}).items():
                add(eaten, kk, v)
            eaten_total += s.get("eaten", 0)
            eaten_sown += s.get("eaten_sown", 0)
            rain_nights += 1 if s.get("rain") else 0

        # ---- ヤギ (1 頭ずつの番号で。spec 4.5) ----
        goats = self.goats(D, P, C, caught_ev, goat_ev, inherit, g5, hh)

        ctx = {"D": D, "a": a, "P": P, "C": C, "rds": rds, "ev": ev, "era": era, "era_end": era_end, "present": present,
               "alive_end": alive_end, "act": act, "out": out, "said": said, "inj": inj, "rain_out": rain_out, "sown_ev": sown_ev,
               "demo": demo, "fields_ev": fields_ev, "pests": pests, "pots": pots, "sick": sick, "goat_ev": goat_ev, "laws": laws,
               "g5": g5, "inherit": inherit, "flows_v": flows_v, "harvest": harvest, "eaten": eaten, "eaten_total": eaten_total,
               "eaten_sown": eaten_sown, "rain_nights": rain_nights, "goats": goats, "year_named": year_named, "substeps": substeps,
               "hh": hh}
        ledger = self.ledger(ctx)
        return self.village_row(ctx), self.household_rows_for(ctx), self.person_rows(ctx), ledger

    # ---- 畑の収穫をたどり直す ----
    def replay(self, D, a, P, C, harvest_ev, era):
        final = {f["id"]: f for f in self.e2.get("fields", [])}
        res = {"to": {}, "by_field": {}, "verified": None, "ripe": [], "by_household": {}}
        if not harvest_ev and not P:
            return res
        if P is not None:
            ripe = [dict(f) for f in P.get("fields", []) if f.get("state") == "実った"]
            for f in ripe:
                f["rem"] = f["yield"] - f.get("harvested", 0)
        elif world.season(D) != "夏":  # 畑が実っているのは夏だけ
            ripe = []
        else:  # 控えがないとき: 前の年の秋にまいて、実りのある畑
            y = D // YEAR - 1
            ripe = [dict(f, rem=f["yield"]) for f in self.e2.get("fields", []) if f.get("yield") is not None
                    and y * YEAR + 2 * SDAYS <= f["day"] < y * YEAR + 3 * SDAYS]
        for f in ripe:
            if "owner" not in f:  # G4 の前にまいた畑: 刈るときに、まいた人の家のものになる (era2._harvest と同じ)
                f["owner"] = self.byname.get(f.get("by"), {}).get("household")
        res["ripe"] = ripe
        g4 = era in era2.ORDER2 and era2.ORDER2.index(era) >= era2.ORDER2.index("G4")
        keep = {h: v.get("keep") for h, v in ((C or {}).get("houses") or {}).items()}
        ok = True
        for e in harvest_ev:
            h = self.byname.get(e["who"], {}).get("household")
            order = sorted(ripe, key=lambda f: f.get("owner") != h) if g4 else ripe
            f = next((f for f in order if f["rem"] > 0), None)
            amt = (e.get("data") or {}).get("amount", 0)
            if f is None or f["rem"] < amt:
                ok = False
                if f is None:
                    add(res["to"], "村", amt)
                    continue
            f["rem"] -= amt
            ow = f.get("owner")
            to_house = g4 and ow and keep.get(ow) and self.built_ev.get(ow, 10 ** 12) < e["id"]
            dst = ow if to_house else "村"
            add(res["to"], dst, amt)
            res["by_household"].setdefault(dst, {})
            add(res["by_household"][dst], h or "-", amt)
            add(res["by_field"], f["id"], amt)
        for f in ripe:
            fin = final.get(f["id"])
            if fin is None or fin.get("yield") is None or f["rem"] != fin["yield"] - fin.get("harvested", 0):
                ok = False
        res["verified"] = ok if (P is not None and ripe) else (None if not ripe else False)
        return res

    # ---- ヤギ ----
    def goats(self, D, P, C, caught_ev, goat_ev, inherit, g5, hh):
        res = {"known": P is not None and C is not None, "flows": {}, "check": {}, "by_holder_end": {}}
        if C is not None:
            for g in C["goats"]:
                add(res["by_holder_end"], g.get("owner") or "村", 1)
        if not res["known"]:
            return res
        pg = {g["id"]: g for g in P["goats"]}
        cg = {g["id"]: g for g in C["goats"]}
        new = list(range(P["village"].get("next_goat") or 0, C["village"].get("next_goat") or 0))
        kids = [i for i in new if cg.get(i, {}).get("born") == D]
        caught = [i for i in new if i not in kids]
        fl = res["flows"]

        def f(holder, reason, n, ids):
            row = fl.setdefault((holder or "村", reason), [0, []])
            row[0] += n
            row[1] += ids

        owner0 = {i: g.get("owner") for i, g in pg.items()}
        for i, e in zip(caught, caught_ev):  # 捕まえた順に番号がつく
            owner0[i] = cg[i].get("owner") if i in cg else hh.get(e["who"])
        for i in caught[len(caught_ev):]:
            owner0[i] = cg.get(i, {}).get("owner")
        for i in caught:
            f(owner0[i], "捕まえた", 1, [i])
        for i in kids:
            owner0[i] = cg[i].get("owner")
            f(owner0[i], "生まれた", 1, [i])
        gone = [i for i in sorted(set(pg) | set(new)) if i not in cg]
        n_eat = goat_ev["eaten"]
        cand = sorted([g for g in P["goats"] if g["sex"] == "オス"], key=lambda g: g["born"]) + \
            sorted([g for g in P["goats"] if g["sex"] != "オス"], key=lambda g: g["born"])
        eaten = [g["id"] for g in cand[:n_eat] if g["id"] in gone]
        fis = g5.get("fission")
        left = [i for i in gone if i not in eaten and fis and owner0.get(i) == fis]
        lost = [i for i in gone if i not in eaten and i not in left]
        for i in eaten:
            f(owner0[i], "つぶした", -1, [i])
        for i in left:
            f(owner0[i], "村を出て持っていった", -1, [i])
        for i in lost:
            f(owner0[i], "いなくなった (世話が足りない)", -1, [i])
        empty = {x["household"] for x in inherit if x["to_village"]}
        paid = {}
        for pm in g5["payments"]:
            if pm["goats"]:
                add(paid, (pm["from"], pm["to"]), pm["goats"])
        for i in sorted(set(cg) & set(owner0)):
            a_, b_ = owner0.get(i), cg[i].get("owner")
            if a_ == b_:
                continue
            if a_ and b_ is None and a_ in empty:
                f(a_, "持ち主がいなくなり村のものになった", -1, [i])
                f(None, "持ち主がいなくなり村のものになった", 1, [i])
            elif a_ and b_ and paid.get((a_, b_), 0) > 0:
                paid[(a_, b_)] -= 1
                f(a_, "罰・つぐないで払った", -1, [i])
                f(b_, "罰・つぐないで受け取った", 1, [i])
            else:
                f(a_, DIFF, -1, [i])
                f(b_, DIFF, 1, [i])
        res["check"] = {"caught": (len(caught), goat_ev["caught"]), "kids": (len(kids), goat_ev["kids"]),
                        "lost": (len(lost), goat_ev["lost"]), "eaten": (len(eaten), n_eat)}
        res["ids"] = {"new": new, "kids": kids, "caught": caught, "eaten": eaten, "lost": lost, "left": left, "owner0": owner0}
        return res

    # ---------------- 帳簿 (spec 4) ----------------
    def ledger(self, c):
        D, P, C = c["D"], c["P"], c["C"]
        rows = []
        known = P is not None and C is not None
        # 村の食べ物 = 村の蓄え + 大人の手元
        def village_food(S, day):
            if S is None:
                return None
            k = dict(S["village"]["store"])
            for sp in S["people"].values():
                if sp.get("alive") and not sp.get("child"):
                    for kk, v in (sp.get("food") or {}).items():
                        add(k, kk, v)
            return k
        v0, v1 = village_food(P, c["a"]), village_food(C, D)
        fv = {r: dict(k) for r, k in c["flows_v"].items()}
        # 収穫 (村の蓄えに入った)
        if c["harvest"]["to"].get("村"):
            fv["刈った (村の蓄えに入った)"] = {"草の種": c["harvest"]["to"]["村"] * UNIT["草の種"][1]}
        # 祭り: 文の物ごとの量を、集まりのときの 3 日分の合計に合わせる
        fe = c["g5"]["feast"]
        if fe:
            total = era2.FEAST_DAYS * self.need(P) if P is not None else None
            fv["祭り"] = kcal_of(fe["words"], total)
        # 食べた
        fv["食べた"] = dict(c["eaten"])
        # 虫やネズミ (村の蓄えの分け前)
        shares = self.pest_shares(c)
        if shares is not None and shares.get("村"):
            fv["虫やネズミ"] = {"草の種": shares["村"]}
        # 亡くなった人・村を出た人の手元
        if known:
            for n, sp in P["people"].items():
                if sp.get("alive") and not sp.get("child") and not C["people"].get(n, {}).get("alive"):
                    why = "村を出た人の手元" if C["people"].get(n, {}).get("left") is not None else "亡くなった人の手元"
                    for kk, v in (C["people"].get(n, {}).get("food") or {}).items():
                        add(fv.setdefault(why, {}), kk, v)
        # 家の倉 (H)
        fh = {}
        for h, n in c["harvest"]["to"].items():
            if h != "村":
                fh.setdefault((h, "刈った (自分の家の畑)"), {})["草の種"] = n * UNIT["草の種"][1]
        for pm in c["g5"]["payments"]:
            for kk, v in pm["food"].items():
                add(fh.setdefault((pm["to"], "罰・つぐないで受け取った"), {}), kk, v)
                add(fh.setdefault((pm["from"], "罰・つぐないで払った"), {}), kk, v)
        if shares is not None:
            for h, v in shares.items():
                if h != "村" and v:
                    fh[(h, "虫やネズミ")] = {"草の種": v}
        notes = (C or {}).get("notes")
        for nt in notes or []:
            h, kk, v = nt.get("household") or "-", nt.get("kind"), nt.get("kcal", 0)
            if nt.get("why") == "家の人が食べた":
                add(fh.setdefault((h, "家の人が食べた"), {}), kk, v)
                add(fv.setdefault("家の倉から食べた", {}), kk, v)
            elif nt.get("why") == "子が食べた":
                add(fh.setdefault((h, "子が食べた"), {}), kk, v)
                add(fv.setdefault("家の倉から食べた (子)", {}), kk, v)
            elif nt.get("why") == "よその家の人に取られた":
                add(fh.setdefault((h, "よその家の人に取られた"), {}), kk, v)
                add(fv.setdefault("よその家の倉から取った", {}), kk, v)
        # 家にだれもいなくなった・家ごと村を出た: 家の倉は空になるので、出た量は家の帳簿の残りから (物ごとに正しい)
        houses0 = {h: v["store"] for h, v in ((P or {}).get("houses") or {}).items()}
        houses1 = {h: v["store"] for h, v in ((C or {}).get("houses") or {}).items()}
        for x in c["inherit"]:
            if not x["to_village"] or not x["household"]:
                continue
            h = x["household"]
            if known:
                left = self._left_over(h, houses0.get(h, {}), houses1.get(h, {}), fh)
            else:
                left = kcal_of(x["words"])
            for kk, v in left.items():
                add(fh.setdefault((h, "だれもいなくなり、村のものになった"), {}), kk, v)
                add(fv.setdefault("家にだれもいなくなり、村のものになった", {}), kk, v)
        fis = c["g5"]["fission"]
        if fis and known:
            for kk, v in self._left_over(fis, houses0.get(fis, {}), houses1.get(fis, {}), fh).items():
                add(fh.setdefault((fis, "村を出て持っていった"), {}), kk, v)

        sign = {"食べた": -1, "まいた (畑)": -1, "種として埋めた": -1, "腐った": -1, "虫やネズミ": -1, "祭り": -1, "雨で傷んだ": -1,
                "亡くなった人の手元": -1, "村を出た人の手元": -1, "家の人が食べた": -1, "子が食べた": -1, "よその家の人に取られた": -1,
                "だれもいなくなり、村のものになった": -1, "村を出て持っていった": -1, "罰・つぐないで払った": -1, "干した": 1}
        src = {"刈った (村の蓄えに入った)": "replay", "刈った (自分の家の畑)": "replay", "食べた": "stats", "虫やネズミ": "snapshot",
               "亡くなった人の手元": "snapshot", "村を出た人の手元": "snapshot", "家の倉から食べた": "notes", "家の倉から食べた (子)": "notes",
               "よその家の倉から取った": "notes", "家の人が食べた": "notes", "子が食べた": "notes", "よその家の人に取られた": "notes",
               "だれもいなくなり、村のものになった": "balance", "村を出て持っていった": "balance",
               "家にだれもいなくなり、村のものになった": "balance"}
        det = {"刈った (村の蓄えに入った)": {"by_household": {self.H(h) or "H00": n for h, n in sorted(c["harvest"]["by_household"].get("村", {}).items())}}
               if c["harvest"]["by_household"].get("村") else None,
               "虫やネズミ": {"events": c["pests"]["events"]} if c["pests"]["events"] else None,
               "祭り": {"events": [fe["event"]]} if fe else None}
        res_v = {}
        # 村の食べ物
        for kk in FOODS:
            fl = []
            for r in FLOWS:
                if r in fv and fv[r].get(kk):
                    fl.append((r, sign.get(r, 1) * fv[r][kk], src.get(r, "events"), det.get(r)))
            s0 = v0.get(kk, 0) if v0 is not None else None
            s1 = v1.get(kk, 0) if v1 is not None else None
            diff = self.emit(rows, D, "村", kk, s0, fl, s1, food=True, why=None)
            if diff is not None:
                res_v[kk] = diff
        # 村の食べ物の「記録にない差」の理由 (合計が 100 kcal 以内なら、丸めのため)
        tot = sum(res_v.values()) if res_v else 0
        for row in rows:
            if row["reason"] == DIFF and row["holder"] == "村":
                row["detail"] = {"why": WHY_ROUND if abs(tot) <= 100 + EPS else "わからない", "total_kcal": r2(tot)}
        exact = []
        gf = c["goats"]["flows"]

        def goat_rows(out, holder):
            """ヤギの帳簿 (holder: 家の名前か 村)。控えがなければ、持ち主ごとの数は分からない"""
            hid = "村" if holder == "村" else (self.H(holder) or "H00")
            if not known:
                if holder == "村" and C is not None:
                    self.emit(out, D, "村", "ヤギ", None, [], len(C["goats"]), food=False, holder_name="村 (持ち主ごとは分からない)")
                return
            fl = [(r, n, "snapshot", {"goats": ids}) for (h, r), (n, ids) in sorted(gf.items(), key=lambda kv: FLOWS.index(kv[0][1]) if kv[0][1] in FLOWS else 99)
                  if h == holder and r != DIFF]
            s0 = sum(1 for g in P["goats"] if (g.get("owner") or "村") == holder)
            s1 = sum(1 for g in C["goats"] if (g.get("owner") or "村") == holder)
            d_ = self.emit(out, D, hid, "ヤギ", s0, fl, s1, food=False, holder_name=holder)
            if d_ is not None:
                exact.append(("ヤギ", holder, d_))

        out_rows = rows  # 村の食べ物
        rows = []
        goat_rows(rows, "村")
        for item, key, st in (("土器", "pots", c["pots"]), ("鎌", "sickles", c["sick"])):
            s0 = P["village"].get(key) if P else None
            s1 = C["village"].get(key) if C else None
            d_ = self.emit(rows, D, "村", item, s0, [("作った", st["made"], "events", None), ("割れた", -st["broken"], "events", None)], s1, food=False)
            if d_ is not None:
                exact.append((item, "村", d_))
        out_rows += rows
        # 家ごと (H01 から)
        hs = set(houses0) | set(houses1) | {h for (h, _) in fh}
        if known:
            hs |= {g.get("owner") for g in P["goats"] + C["goats"]} | {h for (h, _) in gf}
        hs = sorted(hs - {None, "村"}, key=lambda h: self.H(h) or "H00")
        last_flow = (((C or {}).get("g5") or {}).get("last_flow") or {})
        for h in hs:
            rows = []
            hid = self.H(h) or "H00"
            for kk in FOODS:
                fl = [(r, sign.get(r, 1) * fh[(h, r)][kk], src.get(r, "events"),
                       ({"by_household": {self.H(x) or "H00": n for x, n in sorted(c["harvest"]["by_household"].get(h, {}).items())}}
                        if r == "刈った (自分の家の畑)" else None))
                      for r in FLOWS if (h, r) in fh and fh[(h, r)].get(kk)]
                s0 = houses0.get(h, {}).get(kk, 0) if P is not None else None
                s1 = houses1.get(h, {}).get(kk, 0) if C is not None else None
                d_ = self.emit(rows, D, hid, kk, s0, fl, s1, food=True, holder_name=h)
                if d_ is not None:
                    exact.append((kk, h, d_))
            goat_rows(rows, h)
            if h in last_flow:
                i_, o_ = last_flow[h]
                for r, n in (("村の蓄えに入れた (大人)", i_), ("村の蓄えから取った (大人)", o_)):
                    rows.append(self.lrow(D, hid, h, FLOW_ITEM, "メモ", r, n, None, "snapshot", None))
            out_rows += rows
        c["exact"] = exact
        c["village_residual"] = res_v
        return out_rows

    def _left_over(self, h, s0, s1, fh):
        """家の倉が空になったとき、出ていった量 = はじめ + ほかの動き − 終わり (物ごと)"""
        sign = {"罰・つぐないで払った": -1, "虫やネズミ": -1, "家の人が食べた": -1, "子が食べた": -1, "よその家の人に取られた": -1}
        out = {}
        for kk in FOODS:
            v = s0.get(kk, 0) - s1.get(kk, 0)
            for (hh, r), k in fh.items():
                if hh == h and r not in ("だれもいなくなり、村のものになった", "村を出て持っていった"):
                    v += sign.get(r, 1) * k.get(kk, 0)
            if abs(v) > EPS:
                out[kk] = v
        return out

    def need(self, S):
        """集まりのときの、村の全員の 1 日分 (era2._need と同じ。控えの年齢から)"""
        n = 0
        for sp in S["people"].values():
            if not sp.get("alive"):
                continue
            if sp.get("child"):
                n += next((k for a_, k in era2.CHILD_EAT if (sp.get("age") or 0) < a_), era2.CHILD_EAT[-1][1])
            else:
                n += world.BASE_KCAL + 500
        return n

    def pest_shares(self, c):
        """虫やネズミの分け前: 季節の終わりの、それぞれの倉の草の種に比べて (spec 4.4)。戻り値 {家|村: kcal}"""
        C, amt = c["C"], c["pests"]["amount"]
        if not amt:
            return {}
        if C is None:
            return None
        g = {"村": C["village"]["store"].get("草の種", 0)}
        for h, v in (C.get("houses") or {}).items():
            if v["store"].get("草の種"):
                g[h] = v["store"]["草の種"]
        fis = c["g5"]["fission"]
        if fis:  # 虫のあとで家ごと村を出た家の倉 (控えには残らない。g5.fissions の量で見積もる)
            f = next((x for x in ((self.e2.get("g5") or {}).get("fissions") or []) if x.get("household") == fis and x.get("day") == c["D"]), None)
            if f and f.get("store"):
                g[fis] = f["store"]
        tot = sum(g.values())
        if tot <= 0:
            return None
        return {h: x * amt * UNIT["草の種"][1] / tot for h, x in g.items()}

    def lrow(self, D, holder, hname, item, kind, reason, amount, kcal, source, detail):
        return {"season_end_day": D, "holder": holder, "holder_name": hname, "item": item,
                "unit": UNIT[item][0] if item in UNIT else COUNTED.get(item, "つかみ"), "kind": kind, "reason": reason,
                "amount": amount, "kcal": kcal, "source": source, "detail": detail}

    def emit(self, rows, D, holder, item, s0, flows, s1, food, why=None, holder_name=None):
        """1 つの帳簿 (季節 × 持ち主 × 物): はじめの残り + 動き = 終わりの残り。戻り値: 記録にない差 (kcal か数。分からなければ None)"""
        hname = holder_name if holder_name is not None else ("村" if holder == "村" else self.hname.get(holder))
        flows = [f for f in flows if f[1] and abs(f[1]) > (EPS if food else 0)]
        if not flows and not s0 and not s1:
            return None
        u = (lambda v: r2(units(item, v))) if food else (lambda v: v)
        k = (lambda v: r2(v)) if food else (lambda v: None)
        rows.append(self.lrow(D, holder, hname, item, "残り", START, None if s0 is None else u(s0), None if s0 is None else k(s0), "snapshot", None))
        diff = None
        for i, (r, v, src, det) in enumerate(flows):
            if i == 0 and (s0 is None or s1 is None):
                det = dict(det or {}, balance="unknown")
            rows.append(self.lrow(D, holder, hname, item, "動き", r, u(v), k(v), src, det))
        if s0 is not None and s1 is not None:
            diff = s1 - s0 - sum(v for _, v, _, _ in flows)
            if (food and abs(diff) >= 0.005) or (not food and diff != 0):  # 食べ物は kcal で見る (単位で 0.005 より小さい差も、kcal の列では見える)
                rows.append(self.lrow(D, holder, hname, item, "動き", DIFF, u(diff), k(diff), "balance", None))
        rows.append(self.lrow(D, holder, hname, item, "残り", END, None if s1 is None else u(s1), None if s1 is None else k(s1), "snapshot", None))
        return diff

    # ---------------- 村の行 ----------------
    def village_row(self, c):
        D, a, P, C = c["D"], c["a"], c["P"], c["C"]
        alive = c["alive_end"]
        ages = {n: self.age(n, D) for n in alive}
        adults = [n for n in alive if self.is_adult(n, D, C)]
        by_class, by_sex = {}, {}
        for n in alive:
            add(by_class, records.age_class(ages[n]), 1)
            add(by_sex, self.byname[n].get("sex"), 1)
        hw = {self.byname[n].get("household") for n in adults}
        hm = {self.byname[n].get("household") for n in alive}
        ind = ((C or {}).get("era_info") or {}).get("indicators") or {}
        store = C["village"]["store"] if C else None
        eaten = c["eaten"]
        tot = sum(eaten.values())
        fe = c["fields_ev"]
        hv = c["harvest"]
        ripe = hv["ripe"]
        final = {f["id"]: f for f in self.e2.get("fields", [])}
        fallen = sum(max(0, (final.get(f["id"], {}).get("yield") or 0) - (final.get(f["id"], {}).get("harvested") or 0)) for f in ripe)
        goats = None
        if C:
            gl = C["goats"]
            goats = {"count": len(gl), "female": sum(1 for g in gl if g.get("sex") == "メス"), "male": sum(1 for g in gl if g.get("sex") == "オス"),
                     "adult": sum(1 for g in gl if g.get("born") is not None and D - g["born"] >= YEAR),
                     "by_holder": {(self.H(h) if h != "村" else "村"): n for h, n in sorted(c["goats"]["by_holder_end"].items(), key=lambda kv: (kv[0] != "村", self.H(kv[0]) or ""))},
                     "wild": C["village"].get("wild_goats")}
        homes = (C or {}).get("homes") or {}
        built = {h: v for h, v in homes.items() if v.get("built") is not None}
        laws_in = sum(1 for s in ((C or {}).get("laws") or {}).values() if s == "採用") if C else None
        proposed = [l["id"] for l in self.state.get("laws", []) if l.get("day") == a and l.get("proposer")]
        g5row = None
        if c["era"] == "G5" or (C and C.get("g5")):
            g = (C or {}).get("g5") or {}
            fe5 = c["g5"]["feast"]
            g5row = {"stage": g.get("stage"), "leader_id": self.P(g["leader"]) if g.get("leader") else None,
                     "leader_elected": self.P(c["g5"]["leader_elected"]) if c["g5"]["leader_elected"] else None,
                     "disputes_new": c["g5"]["new"], "disputes_settled": [m for m in c["g5"]["settled"] if m],
                     "judged": c["g5"]["judged"],
                     "penalties": [{"dispute": x["dispute"], "law": x["law"]} for x in c["g5"]["penalty_laws"]],
                     "payments": [{"dispute": p["dispute"], "from": self.H(p["from"]), "to": self.H(p["to"]),
                                   "food": food_units(p["food"]), "goats": p["goats"]} for p in c["g5"]["payments"]],
                     "feast": {"held": fe5 is not None, "cost": {k: n for k, n in sorted(fe5["words"].items(), key=lambda kv: FOODS.index(kv[0]))} if fe5 else {}},
                     "joint": c["g5"]["joint"], "fission": self.H(c["g5"]["fission"]) if c["g5"]["fission"] else None,
                     "stress": ind.get("stress")}
        ans = self.answers.get(a, {})
        crit = None
        if C and ind:
            crit = records.criteria_progress(c["era"], ind, D)
        eras = c["era"]
        return {
            "season_end_day": D, "season_start_day": max(D - SDAYS + 1, a + 1), "days": D - a, "year": D // YEAR, "season": world.season(D),
            "label": records.season_label(D),
            "rounds": [{"meeting_day": r["meeting_day"], "meeting_first": r["meeting_first"], "event_first": r["event_first"],
                        "event_end": r["event_end"], "snapshot": r["snapshot"]} for r in c["rds"]],
            "era": eras, "era_end": c["era_end"], "advanced": eras != c["era_end"], "substeps": c["substeps"],
            "population": len(alive), "adults": len(adults), "children": len(alive) - len(adults),
            "by_age_class": {k: by_class[k] for k, _, _ in records.AGE_CLASSES if k in by_class},
            "by_sex": {k: by_sex[k] for k in sorted(by_sex, key=str)},
            "households_with_adults": len(hw - {None}), "households_with_members": len(hm - {None}),
            "births": [self.P(n) for n in c["demo"]["births"]],
            "deaths": [{"id": self.P(n), "cause": records.death_cause(self.death[n]["text"]) if n in self.death else None} for n in c["demo"]["deaths"]],
            "joined": [self.P(n) for n in c["demo"]["joined"]], "left": [self.P(n) for n in c["demo"]["left"]],
            "came_of_age": [self.P(n) for n in c["demo"]["came_of_age"]], "visitors_rejected": c["demo"]["visitors_rejected"],
            "store": food_units(store) if store is not None else None, "store_kcal": r2(sum(store.values())) if store is not None else None,
            "store_days": C["village"].get("store_days") if C else None,
            "eaten": food_units(eaten), "eaten_kcal": r2(tot),
            "eaten_share": {k: round(eaten[k] / tot, 3) for k in FOODS if eaten.get(k)} if tot else {},
            "farm_share_season": round(c["eaten_sown"] / tot, 3) if tot else None,
            "fields": {"sown": len(c["sown_ev"]), "seed": sum((e.get("data") or {}).get("seed", 0) for e in c["sown_ev"]),
                       "ripe": len(ripe), "harvested": sum(hv["by_field"].values()) if ripe else sum(c["out"].get(n, {}).get("harvested", 0) for n in c["out"]),
                       "fallen": fallen if ripe else fe["fallen"], "fallen_logged": fe["fallen"], "ripened_for_next": fe["ripened"],
                       "failed": fe["failed"], "trampled": fe["trampled"], "replay_verified": hv["verified"]},
            "pests": c["pests"]["amount"], "pests_safe": c["pests"]["safe"],
            "goats": goats,
            "pots": C["village"].get("pots") if C else None, "sickles": C["village"].get("sickles") if C else None,
            "pots_made": c["pots"]["made"], "pots_broken": c["pots"]["broken"], "sickles_made": c["sick"]["made"], "sickles_broken": c["sick"]["broken"],
            "homes_built": len(built) if C else None,
            "home_sizes": {self.H(h): v.get("size") for h, v in sorted(built.items(), key=lambda kv: self.H(kv[0]) or "")} if C else None,
            "house_gini": ind.get("house_gini") if C else None,
            "rain_nights": c["rain_nights"], "rain_outside_people": len(c["rain_out"]), "rain_outside_person_nights": sum(c["rain_out"].values()),
            "wealth_gini": ind.get("gini") if "wealth" in ind else None, "no_wealth": ind.get("no_wealth") if "wealth" in ind else None,
            "laws": {"in_force": laws_in, "adopted": c["laws"]["adopted"], "abolished": c["laws"]["abolished"], "proposed": proposed,
                     "penalty_laws": ind.get("penalty_laws") if C else None},
            "g5": g5row,
            "answered": {"season": len(ans.get("season") or {}), "feeling": len(ans.get("feeling") or {}),
                         "reps": len([n for n in (ans.get("season") or {}) if n in self.reps_at(a, P)])},
            "year_named": c["year_named"],
            "criteria": crit,
            "snapshot": C is not None,
        }

    # ---- 代表 ----
    def reps_at(self, a, P):
        """集まり (a 日) の家族の代表 (家でいちばん年上の大人。同じ年なら人の並びで先)。代表で答える決まりのときだけ"""
        key = (a, id(P))
        if key in getattr(self, "_reps_cache", {}):
            return self._reps_cache[key]
        self._reps_cache = getattr(self, "_reps_cache", {})
        on = (P or {}).get("season", {}).get("rep_mode") if P else self.rep_mode_fallback(a)
        reps = {}
        if on:
            ads = [p for p in self.people if self.alive_at(p["name"], a) and self.is_adult(p["name"], a, P)]
            for p in sorted(ads, key=lambda q: -(self.age(q["name"], a) or 0)):
                reps.setdefault(p.get("household") or p["name"], p["name"])
        self._reps_cache[key] = set(reps.values())
        return self._reps_cache[key]

    def rep_mode_fallback(self, a):
        ev = next((e for e in self.ev if e["type"] == "家族"), None)
        if ev is None or ev["day"] > a:
            return False
        return sum(1 for p in self.people if self.alive_at(p["name"], a) and self.is_adult(p["name"], a)) > era2.REP_FROM

    def leader_at(self, a, P):
        return ((P or {}).get("g5") or {}).get("leader")

    # ---------------- 家の行 ----------------
    def household_rows_for(self, c):
        D, a, P, C = c["D"], c["a"], c["P"], c["C"]
        reps = self.reps_at(a, P)
        leader = ((C or {}).get("g5") or {}).get("leader")
        ind = ((C or {}).get("era_info") or {}).get("indicators") or {}
        out = []
        hs = sorted({self.byname[n].get("household") for n in c["present"]} - {None}, key=lambda h: self.H(h))
        final = {f["id"]: f for f in self.e2.get("fields", [])}
        for h in hs:
            ms = [n for n in c["present"] if self.byname[n].get("household") == h]
            alive = [n for n in ms if self.alive_at(n, D)]
            ads = [n for n in alive if self.is_adult(n, D, C)]
            by_class = {}
            for n in alive:
                add(by_class, records.age_class(self.age(n, D)), 1)
            status = ("村を出た" if c["g5"]["fission"] == h else "村にいる" if ads else "大人がいない" if alive else "だれもいない")
            rep = next((n for n in ms if n in reps), None)
            home = ((C or {}).get("homes") or {}).get(h)
            hv = c["harvest"]
            own = [f for f in hv["ripe"] if f.get("owner") == h]
            g = c["goats"]
            gl = [x for x in (C or {}).get("goats", []) if x.get("owner") == h] if C else None
            gflow = {r: n for (hh, r), (n, _) in g["flows"].items() if hh == h} if g["known"] else {}
            pays = c["g5"]["payments"]
            disputes = {"raised": [], "against": [], "paid": 0, "received": 0}
            for dd in ((self.e2.get("g5") or {}).get("disputes") or []):
                if dd["id"] in c["g5"]["new"]:
                    if dd["from"] == h:
                        disputes["raised"].append(dd["id"])
                    if dd["against"] == h:
                        disputes["against"].append(dd["id"])
            for p in pays:
                gr = sum(units(k, v) for k, v in p["food"].items() if k == "草の種")
                if p["from"] == h:
                    disputes["paid"] += gr
                if p["to"] == h:
                    disputes["received"] += gr
            disputes["paid"], disputes["received"] = r2(disputes["paid"]), r2(disputes["received"])
            jobs = {}
            for n in ms:
                if self.is_adult(n, D, C) or (C and C["people"].get(n, {}).get("alive") is False):
                    for x in c["act"].get(n, {}).values():
                        add(jobs, x, 1)
            lf = (((C or {}).get("g5") or {}).get("last_flow") or {}).get(h)
            out.append({
                "season_end_day": D, "household_id": self.H(h), "status": status,
                "members": [self.P(n) for n in alive], "adults": len(ads), "children": len(alive) - len(ads),
                "by_age_class": {k: by_class[k] for k, _, _ in records.AGE_CLASSES if k in by_class},
                "rep_id": self.P(rep) if rep else None, "leader_member": bool(leader and self.byname.get(leader, {}).get("household") == h),
                "home": ({"started": home.get("start"), "built_day": home.get("built"), "size": home.get("size"), "work_hours": home.get("work")}
                         if home else None),
                "keep": (((C or {}).get("houses") or {}).get(h) or {}).get("keep", False) if C else None,
                "store": food_units(((C or {}).get("houses") or {}).get(h, {}).get("store", {})) if C else None,
                "goats": ({"count": len(gl), "female": sum(1 for x in gl if x.get("sex") == "メス"), "male": sum(1 for x in gl if x.get("sex") == "オス"),
                           "adult": sum(1 for x in gl if x.get("born") is not None and D - x["born"] >= YEAR),
                           "kids_born": gflow.get("生まれた", 0), "caught": gflow.get("捕まえた", 0),
                           "lost": -gflow.get("いなくなった (世話が足りない)", 0), "eaten": -gflow.get("つぶした", 0)} if gl is not None else None),
                "wealth_kcal": (ind.get("wealth") or {}).get(h) if "wealth" in ind else None,
                "fields": {"sown": sum(1 for e in c["sown_ev"] if self.byname.get(e["who"], {}).get("household") == h),
                           "seed": sum(e["data"]["seed"] for e in c["sown_ev"] if self.byname.get(e["who"], {}).get("household") == h),
                           "ripe": len(own), "harvested_own_fields": sum(hv["by_field"].get(f["id"], 0) for f in own),
                           "harvested_by_members": sum(c["out"].get(n, {}).get("harvested", 0) for n in ms),
                           "fallen": sum(max(0, (final.get(f["id"], {}).get("yield") or 0) - (final.get(f["id"], {}).get("harvested") or 0)) for f in own),
                           "trampled": c["fields_ev"]["trampled_by"].get(h, 0)},
                "village_flow": {"in": lf[0], "out": lf[1]} if lf else None,
                "disputes": disputes,
                "inherit": [{"dead_id": self.P(x["dead"]) if x["dead"] else None, "heir_id": self.P(x["heir"]) if x["heir"] else None,
                             "what": x["what"], "to_village": x["to_village"], "event": x["event"]} for x in c["inherit"] if x["household"] == h],
                "jobs": {k: jobs[k] for k in sorted(jobs)},
                "rain_outside_person_nights": sum(c["rain_out"].get(n, 0) for n in ms),
                "snapshot": C is not None,
            })
        return out

    # ---------------- 人の行 ----------------
    def person_rows(self, c):
        D, a, P, C = c["D"], c["a"], c["P"], c["C"]
        reps = self.reps_at(a, P)
        lead = self.leader_at(a, P)
        ans = self.answers.get(a, {})
        sea, fee = ans.get("season") or {}, ans.get("feeling") or {}
        joined_here = set(c["demo"]["joined"])
        out = []
        for n in c["present"]:
            p = self.byname[n]
            h = p.get("household")
            to = self.t_out[n]
            st_end = "生きている" if self.alive_at(n, D) else ("村を出た" if p.get("left") is not None else "亡くなった")
            ref = D if to is None or to > D else to
            age = self.age(n, ref)
            sp1 = (C or {}).get("people", {}).get(n) if C else None
            adult_meeting = self.alive_at(n, a) and self.is_adult(n, a, P)
            # 仕事 (回ごと)
            jobs, decided = [], None
            joined_adult = n in joined_here and (self.age(n, a) or 0) >= era2.ADULT  # 集まりで加わった大人 (子は仕事をしない)
            if adult_meeting or joined_adult:
                if n in sea:
                    decided = "自分"
                elif joined_adult:
                    decided = "加わった季節"
                else:
                    rep = next((r for r in sea if r in reps and self.byname[r].get("household") == h and h), None)
                    if rep:
                        fam = sea[rep].get("family") if isinstance(sea[rep].get("family"), dict) else {}
                        decided = "代表が割り振った" if fam.get(n) else "代表と同じ仕事"
                    else:
                        decided = "答えなし (前と同じ)"
                for rd in c["rds"]:
                    S = self.snaps.get(rd["end"])
                    plan = ((S or {}).get("people", {}).get(n) or {}).get("plan") if S else None
                    if plan is None:
                        plan = self.plan_from_answers(n, h, sea, reps)
                    if plan:
                        jobs.append({"from_day": rd["start"] + 1, "activity": plan.get("activity"), "place": plan.get("place"),
                                     "with": [self.P(w) for w in plan.get("with") or []], "decided_by": decided})
            ja = ((C or {}).get("season", {}).get("jobs") or {}).get(n) if C else None
            days = {}
            plan_act = jobs[-1]["activity"] if jobs else None
            for _, x in sorted(c["act"].get(n, {}).items()):
                if x == "休む" and plan_act and plan_act != "休む":
                    x = "休む (けが)"
                add(days, x, 1)
            o = c["out"].get(n)
            outputs = None
            if o:
                outputs = dict(o)
                outputs["gathered"] = food_units(o["gathered"])
                outputs["hunted"] = food_units(o["hunted"])
            sd = c["said"].get(n)
            lw = self.laws_by_person(n, a, sea, reps, h)
            kn = sum(1 for x in self.state.get("knowledge_log", []) if x.get("who") == n and x.get("day") == a and x.get("op") == "追加")
            alive1 = sp1 and sp1.get("alive")
            out.append({
                "season_end_day": D, "person_id": self.P(n), "household_id": self.H(h),
                "present_from": int(max(self.t_in[n], D - SDAYS + 1, a + 1)), "present_to": ref, "status_at_end": st_end,  # 最初の季節は 490 日目から
                "age": age, "age_class": records.age_class(age),
                "child": (bool(sp1.get("child")) if alive1 else (age is not None and age < era2.ADULT)),
                "is_rep": n in reps, "is_leader": bool(lead and lead == n),
                "answered": "season" if n in sea else "feeling" if n in fee else None,
                "said": {"count": sd["count"], "to": sd["to"]} if sd else {"count": 0, "to": []},
                "jobs": jobs, "decided_by": decided,
                "job_amounts": ({k: ja.get(k) for k in ("sow", "pick", "plant", "harvest", "eat_goat")} if ja else None),
                "days_by_activity": {k: days[k] for k in sorted(days)},
                "outputs": outputs,
                "injuries": c["inj"].get(n, 0), "rain_outside_nights": c["rain_out"].get(n, 0),
                "skills": (sp1.get("skills") if alive1 else None), "hunger": (sp1.get("hunger") if alive1 else None),
                "fatigue": (sp1.get("fatigue") if alive1 else None), "injured_days_left": (sp1.get("injured") if alive1 else None),
                "items": (self.counts(sp1.get("items")) if alive1 else None),
                "laws": lw if adult_meeting else {"proposed": lw["proposed"], "votes": None}, "knowledge_added": kn,
                "snapshot": C is not None,
            })
        return out

    @staticmethod
    def counts(items):
        """持ち物の一覧 → {物: 数} (同じ物が何十も並ぶため)"""
        out = {}
        for x in items or []:
            add(out, x, 1)
        return {k: out[k] for k in sorted(out)}

    def plan_from_answers(self, n, h, sea, reps):
        a_ = sea.get(n)
        if a_ is None:
            rep = next((r for r in sea if r in reps and self.byname[r].get("household") == h and h), None)
            if not rep:
                return None
            fam = sea[rep].get("family") if isinstance(sea[rep].get("family"), dict) else {}
            job = fam.get(n) or sea[rep].get("job") or sea[rep].get("plan")
        else:
            job = a_.get("job") or a_.get("plan")
        if isinstance(job, str):
            job = {"activity": job}
        return job if isinstance(job, dict) else None

    def laws_by_person(self, n, a, sea, reps, h):
        proposed = [l["id"] for l in self.state.get("laws", []) if l.get("proposer") == n and l.get("day") == a]
        src, by = None, None
        if n in sea:
            src, by = sea[n], "自分"
        else:
            rep = next((r for r in sea if r in reps and self.byname[r].get("household") == h and h), None)
            if rep:
                src, by = sea[rep], self.P(rep)
        yes = no = 0
        for v in (src or {}).get("votes") or []:
            if isinstance(v, dict) and v.get("id"):
                ag = v.get("agree")
                if ag is True:
                    yes += 1
                elif ag is False:
                    no += 1
        return {"proposed": proposed, "votes": {"yes": yes, "no": no, "by": by}}

    # ---------------- 年の名前・掟・もめごと ----------------
    def build_laws(self):
        laws = self.state.get("laws", [])
        self.law_of = {}
        adopted, abolished = {}, {}
        by_text = {}
        for l in laws:
            by_text.setdefault(l["text"], []).append(l)
        for e, what, text in self.law_ev:
            cands = [l for l in by_text.get(text, []) if (l.get("day") or 0) <= e["day"]]
            if what == "採用":
                l = next((l for l in cands if l["id"] not in adopted), cands[-1] if cands else None)
                if l:
                    adopted.setdefault(l["id"], e["day"])
            else:
                l = next((l for l in cands if l["id"] in adopted and l["id"] not in abolished), cands[-1] if cands else None)
                if l:
                    abolished.setdefault(l["id"], e["day"])
            if l:
                self.law_of[e["id"]] = l["id"]
        self.laws_rows = [{"id": l["id"], "text": l["text"], "proposer_id": self.P(l["proposer"]) if l.get("proposer") else None,
                           "proposed_day": l.get("day"), "status": l.get("status"), "adopted_day": adopted.get(l["id"]),
                           "abolished_day": abolished.get(l["id"]), "penalty": l.get("penalty"), "label": l.get("label")} for l in laws]

    def build_disputes(self):
        g = self.e2.get("g5") or {}
        self.disputes_rows = [{"id": d["id"], "kind": d.get("kind"), "from": self.H(d.get("from")), "against": self.H(d.get("against")),
                               "day": d.get("day"), "season_end_day": records.season_end(d["day"]) if d.get("day") is not None else None,
                               "harm": d.get("harm"), "what": d.get("what"), "status": d.get("status"), "verdict": d.get("verdict"),
                               "by": d.get("by"), "judge_id": self.P(d["judge"]) if d.get("judge") else None, "paid": d.get("paid"),
                               "law": d.get("law"), "end_day": d.get("end"),
                               "end_season_end_day": (records.season_end(d["end"] + 1) if d.get("end") is not None and d.get("by") is not None
                                                      else records.season_end(d["end"]) if d.get("end") is not None else None),
                               "event": d.get("event"), "because": d.get("because") or []}
                              for d in g.get("disputes") or []]

    def build_year_names(self):
        st = self.state
        names = {x["year"]: x for x in self.e2.get("year_names") or []}
        harv = {}
        for e in self.ev:
            if e["type"] == "収穫" and e["day"] >= self.start:
                add(harv, e["day"] // YEAR, (e.get("data") or {}).get("amount", 0))
        rows = []
        for y in range(self.start // YEAR, st["day"] // YEAR + 1):
            last = y * YEAR + YEAR - 1
            pdir = self.data / "prompts" / f"day{last:03d}" / "season"
            asked = pdir.is_dir() and any("## 年の名前" in f.read_text(encoding="utf-8") for f in sorted(pdir.glob("*.md")))
            x = names.get(y)
            done = last < st["day"] or (last == st["day"] and x is not None)
            rows.append({"year": y, "first_day": y * YEAR, "last_day": last, "asked": asked, "name": x["name"] if x else None,
                         "decided_day": x.get("day") if x else None, "event_id": x.get("event") if x else None,
                         "weight": x.get("weight") if x else None, "adults": x.get("adults") if x else None,
                         "proposals": [{"person_id": self.P(q["who"]), "name": q["name"], "weight": q["weight"]} for q in x.get("proposals", [])] if x else [],
                         "why_none": None if x else ("まだ終わっていない" if not done else "だれも名前を書かなかった" if asked else "年の名前を決める前の年"),
                         "harvest": harv.get(y, 0)})
        self.year_rows = rows

    # ---------------- 全部 ----------------
    def build(self):
        self.build_people()
        self.build_laws()
        self.build_rounds()
        self.village, self.house_rows, self.person_rows_all, self.ledger_rows = [], [], [], []
        self.exact, self.vres = [], {}
        for D in sorted(self.seasons):
            v, hs, ps, lg = self.season(D, self.seasons[D])
            self.village.append(v)
            self.house_rows += hs
            self.person_rows_all += ps
            self.ledger_rows += lg
        self.build_disputes()
        self.build_year_names()


# ---------------- 列の説明 ----------------
# (表, 列, 意味, 単位, 札, 出どころ, 正確か, いつから, メモ)。札: 調 = あとから調べる人に分かる / シ = シミュレーションだから分かる / 村 = 村の人がつけた記録
COLUMNS = [
    ("people", "id", "人の番号", None, "-", "state の people の並び", True, None, "記録をつなぐための番号"),
    ("people", "name", "名前", None, "シ", "state", True, None, "文字の前は名前は残らない"),
    ("people", "sex", "男女", None, "調", "state", True, None, "骨から"),
    ("people", "born_day", "生まれた日", "日", "調", "state", True, None, "調べる人には年齢の幅で分かる"),
    ("people", "born_day_exact", "生まれた日が正確か", None, "-", "Society 1.0 で亡くなった人は false", True, None, None),
    ("people", "origin", "来かた", None, "調", "state", True, None, "はじめから・生まれた・よそから来た (歯の同位体)"),
    ("people", "came_day", "村に来た日", "日", "調", "出来事「加わる」・生まれた日", True, None, None),
    ("people", "came_with", "いっしょに来た人", None, "シ", "出来事「加わる」", True, None, None),
    ("people", "mother_id", "母", None, "調", "state (生まれた子)", True, None, "父は記録にない (古い DNA で分かる)"),
    ("people", "guardian_id", "いっしょに来た大人", None, "シ", "state (よそから来た子)", True, None, None),
    ("people", "parent_ids", "親", None, "調", "mother_id", True, None, None),
    ("people", "died_day", "亡くなった日", "日", "調", "出来事「死」", True, None, None),
    ("people", "death_cause", "死因の種類", None, "調", "出来事「死」の文", True, None, "飢え・ザガ・病・年・子・その他 (骨で一部分かる)"),
    ("people", "death_event", "死の出来事の番号", None, "-", "出来事", True, None, None),
    ("people", "age_at_death", "亡くなった年齢", "歳", "調", "生まれた日と亡くなった日", True, None, None),
    ("people", "left_day", "村を出た日", "日", "調", "state", True, None, None),
    ("people", "left_why", "村を出たわけ", None, "シ", "出来事「去る」「分かれる」", True, None, None),
    ("people", "status", "今", None, "-", "state", True, None, "生きている・亡くなった・村を出た"),
    ("people", "household_id", "家", None, "調", "membership の最後の行", True, None, "家の跡"),
    ("households", "id", "家の番号", None, "-", "人の並びで家の名前が出た順", True, None, None),
    ("households", "name", "家の名前", None, "シ", "state", True, None, None),
    ("households", "origin", "家のはじまり", None, "調", "はじめから・よそから来た群れ", True, None, None),
    ("households", "founder_ids", "家をはじめた人", None, "シ", "membership", True, None, None),
    ("households", "first_day", "家ができた日", "日", "調", "membership", True, None, None),
    ("households", "adults_last_day", "大人がいなくなった日", "日", "調", "membership", True, None, "大人が残っていれば null"),
    ("households", "last_day", "家の人がだれもいなくなった日", "日", "調", "membership", True, None, None),
    ("households", "left_village_day", "家ごと村を出た日", "日", "調", "g5.fissions", True, 1709, None),
    ("households", "fission", "家ごと村を出たときのこと", None, "シ", "g5.fissions", True, 1709, None),
    ("households", "home_built_day", "住まいができた日", "日", "調", "era2.homes", True, 1529, "家の跡"),
    ("households", "home_start_day", "住まいを建てはじめた日", "日", "調", "era2.homes", True, 1529, None),
    ("membership", "person_id", "人", None, "-", "", True, None, None),
    ("membership", "household_id", "家", None, "調", "state", True, None, None),
    ("membership", "from_day", "入った日", "日", "調", "はじめから 0・生まれた日・加わった日", True, None, None),
    ("membership", "to_day", "出た日", "日", "調", "亡くなった日・村を出た日", True, None, "null = 今もいる"),
    ("membership", "why_in", "入ったわけ", None, "調", "はじめから・生まれた・よそから来た", True, None, None),
    ("membership", "why_out", "出たわけ", None, "調", "亡くなった・飢えで村を出た・母を追って村を出た・家ごと村を出た", True, None, None),
    ("membership", "evidence", "もとの出来事の番号", None, "-", "出来事", True, None, None),
    ("membership", "assigned_from_state_day", "state に家が書かれた最初の日", "日", "-", "季節の終わりの控え", True, None,
     "それより前は、同じ決まりであとから家を決めた"),
    ("season_village", "season_end_day", "季節の終わりの日", "日", "-", "", True, 489, "1 行 = 1 季節"),
    ("season_village", "season_start_day", "季節のはじめの日", "日", "-", "", True, 489, None),
    ("season_village", "days", "日数", "日", "-", "", True, 489, "最初の季節は 20 日"),
    ("season_village", "year", "年", "年", "-", "日 ÷ 120", True, 489, "記録の中だけの数え方"),
    ("season_village", "season", "季節", None, "-", "world.season", True, 489, None),
    ("season_village", "label", "呼び方", None, "-", "", True, 489, "「14年の夏」"),
    ("season_village", "rounds", "回 (集まりから次の集まりまで)", None, "-", "控え・出来事", True, 489, "ふつうは 1 つ"),
    ("season_village", "era", "フェーズ (季節のあいだ)", None, "シ", "控え", True, 489, None),
    ("season_village", "era_end", "フェーズ (季節の終わりの判定のあと)", None, "シ", "控え", True, 489, None),
    ("season_village", "advanced", "フェーズが進んだか", None, "シ", "", True, 489, None),
    ("season_village", "substeps", "入った F", None, "シ", "出来事「区切り」", True, 1589, None),
    ("season_village", "population", "人数 (子をふくむ)", "人", "調", "membership", True, 489, "墓と家の数から幅で"),
    ("season_village", "adults", "大人", "人", "調", "membership と年齢", True, 489, None),
    ("season_village", "children", "子", "人", "調", "membership と年齢", True, 489, None),
    ("season_village", "by_age_class", "年齢の区分ごとの人数", "人", "調", "年齢", True, 489, "乳飲み子 0〜2・子 3〜11・手伝える子 12〜14・大人 15〜54・年寄り 55〜 (境目は仮)"),
    ("season_village", "by_sex", "男女ごとの人数", "人", "調", "state", True, 489, None),
    ("season_village", "households_with_adults", "大人のいる家", "家", "調", "membership", True, 489, None),
    ("season_village", "households_with_members", "人のいる家", "家", "調", "membership", True, 489, None),
    ("season_village", "births", "生まれた子", None, "調", "出来事「生まれる」", True, 489, None),
    ("season_village", "deaths", "亡くなった人と死因", None, "調", "出来事「死」", True, 489, None),
    ("season_village", "joined", "よそから加わった人", None, "調", "出来事「加わる」", True, 489, None),
    ("season_village", "left", "村を出た人", None, "調", "state", True, 489, None),
    ("season_village", "came_of_age", "大人になった人", None, "シ", "出来事「大人になる」", True, 489, None),
    ("season_village", "visitors_rejected", "受け入れなかった群れ", None, "シ", "出来事「去る」", True, 489, None),
    ("season_village", "store", "村の蓄え (物ごと)", "単位", "シ", "控え", True, 489, "調べる人には倉の大きさで分かる"),
    ("season_village", "store_kcal", "村の蓄え", "kcal", "シ", "控え", True, 489, None),
    ("season_village", "store_days", "村の蓄えが今の人数で何日分か", "日", "シ", "控え (era2.store_days)", True, 489, None),
    ("season_village", "eaten", "食べたもの (物ごと)", "単位", "シ", "stats", True, 489, "調べる人には植物と骨の割合で"),
    ("season_village", "eaten_kcal", "食べた量", "kcal", "シ", "stats", True, 489, None),
    ("season_village", "eaten_share", "食べたものの割合", "割合", "シ", "stats", True, 489, None),
    ("season_village", "farm_share_season", "育てたものの割合 (この季節)", "割合", "シ", "stats", True, 489, None),
    ("season_village", "fields", "畑 (まいた・実った・刈った・落ちた・実らなかった・荒らされた)", "枚 / つかみ", "調", "出来事・畑のたどり直し", True, 489,
     "調べる人には畑の数。量はシ"),
    ("season_village", "pests", "虫やネズミに食べられた草の種", "つかみ", "シ", "出来事「虫」", True, 1529, None),
    ("season_village", "pests_safe", "土器に入れて無事だった草の種", "つかみ", "シ", "出来事「虫」", True, 1529, None),
    ("season_village", "goats", "ヤギ (数・メス・オス・大人・持ち主ごと・野生)", "頭", "調", "控え", True, 489, "骨から"),
    ("season_village", "pots", "村の土器", "個", "調", "控え", True, 1529, "かけら"),
    ("season_village", "sickles", "村の鎌", "本", "調", "控え", True, 1529, "石の刃"),
    ("season_village", "pots_made", "作った土器", "個", "調", "出来事「土器」", True, 1529, None),
    ("season_village", "pots_broken", "割れた土器", "個", "調", "出来事「道具」", True, 1529, None),
    ("season_village", "sickles_made", "作った鎌", "本", "調", "出来事「道具」", True, 1529, None),
    ("season_village", "sickles_broken", "割れた鎌", "本", "調", "出来事「道具」", True, 1529, None),
    ("season_village", "homes_built", "家族の住まいの数", "軒", "調", "控え", True, 1529, "家の跡"),
    ("season_village", "home_sizes", "家ごとの住まいの広さ", "m²", "調", "控え", True, 1529, None),
    ("season_village", "house_gini", "家の大きさの差 (ジニ係数)", None, "調", "控え (era_info)", True, 1529, None),
    ("season_village", "rain_nights", "雨の夜", "夜", "シ", "stats", True, 489, None),
    ("season_village", "rain_outside_people", "雨の夜に外で寝た人", "人", "シ", "出来事「雨」", True, 1529, None),
    ("season_village", "rain_outside_person_nights", "雨の夜に外で寝た、のべの夜", "人・夜", "シ", "出来事「雨」", True, 1529, None),
    ("season_village", "wealth_gini", "持ち物の差 (ジニ係数)", None, "シ", "控え (era_info)", True, 1589, None),
    ("season_village", "no_wealth", "持ち物のない家", "家", "シ", "控え (era_info)", True, 1589, None),
    ("season_village", "laws", "掟 (採用中・採用・廃止・提案・罰のある掟)", "本", "シ", "出来事「掟」・state", True, 489, "文字の前は残らない"),
    ("season_village", "g5", "G5 (段・まとめ役・もめごと・裁き・罰・祭り・共同の仕事・分かれた家)", None, "シ", "出来事・控え", True, 1709,
     "祭りは食べ残しの跡で調べられる"),
    ("season_village", "answered", "答えた人の数 (季節・気持ち・代表)", "人", "シ", "答えのファイル", True, 489, None),
    ("season_village", "year_named", "この季節をはじめた集まりで決まった年の名前", None, "村", "era2.year_names", True, 2039, "口で伝える年代記"),
    ("season_village", "criteria", "フェーズの条件 (今の値・目標・そろったか)", None, "シ", "控え (era_info) と条件の中身", True, 489, None),
    ("season_village", "snapshot", "季節の終わりの値が控えから取れたか", None, "-", "", True, 489, None),
    ("season_household", "season_end_day", "季節の終わりの日", "日", "-", "", True, 489, "1 行 = 1 季節 × 1 家"),
    ("season_household", "household_id", "家", None, "-", "", True, 489, None),
    ("season_household", "status", "家のようす", None, "-", "membership", True, 489, "村にいる・大人がいない・村を出た・だれもいない"),
    ("season_household", "members", "季節の終わりの家の人", None, "調", "membership", True, 489, None),
    ("season_household", "adults", "大人", "人", "調", "", True, 489, None),
    ("season_household", "children", "子", "人", "調", "", True, 489, None),
    ("season_household", "by_age_class", "年齢の区分ごとの人数", "人", "調", "", True, 489, None),
    ("season_household", "rep_id", "家族の代表 (集まりのとき)", None, "シ", "membership と年齢 (答えのファイルで確かめる)", True, 1259, None),
    ("season_household", "leader_member", "まとめ役がいる家か", None, "シ", "控え", True, 1709, None),
    ("season_household", "home", "住まい (建てはじめ・できた日・広さ・働いた時間)", None, "調", "控え", True, 1529, "広さは家の跡"),
    ("season_household", "keep", "家の倉を持つか (この季節)", None, "シ", "控え", True, 1589, None),
    ("season_household", "store", "家の倉 (物ごと)", "単位", "シ", "控え", True, 1589, "倉の跡"),
    ("season_household", "goats", "家のヤギ (数・生まれた・捕まえた・いなくなった・つぶした)", "頭", "調", "控え・ヤギの番号", True, 1589, None),
    ("season_household", "wealth_kcal", "家の持ち物 (家の倉 + ヤギ)", "kcal", "シ", "控え (era_info)", True, 1589, None),
    ("season_household", "fields", "家の畑", "枚 / つかみ", "調", "出来事・畑のたどり直し", True, 489, None),
    ("season_household", "village_flow", "村の蓄えに入れた・取った (大人、草の種にして)", "つかみ", "シ", "控え (g5.last_flow)", True, 1739, None),
    ("season_household", "disputes", "もめごと (言い出した・言われた・払った・受け取った)", None, "シ", "g5.disputes・出来事", True, 1709, None),
    ("season_household", "inherit", "受けつぎ", None, "調", "出来事「受けつぎ」", True, 1589, None),
    ("season_household", "jobs", "大人の仕事ののべ日数", "人・日", "シ", "出来事", True, 489, None),
    ("season_household", "rain_outside_person_nights", "雨の夜に外で寝た、のべの夜", "人・夜", "シ", "出来事「雨」", True, 1529, None),
    ("season_household", "snapshot", "季節の終わりの値が控えから取れたか", None, "-", "", True, 489, None),
    ("season_person", "season_end_day", "季節の終わりの日", "日", "-", "", True, 489, "1 行 = 1 季節 × 1 人"),
    ("season_person", "person_id", "人", None, "-", "", True, 489, None),
    ("season_person", "household_id", "家", None, "調", "membership", True, 489, None),
    ("season_person", "present_from", "この季節にいたはじめの日", "日", "-", "membership", True, 489, None),
    ("season_person", "present_to", "この季節にいた終わりの日", "日", "-", "membership", True, 489, None),
    ("season_person", "status_at_end", "季節の終わり", None, "-", "membership", True, 489, "生きている・亡くなった・村を出た"),
    ("season_person", "age", "年齢 (正確な値。内側の記録だけ)", "歳", "シ", "生まれた日", True, 489, "見せるのは区分"),
    ("season_person", "age_class", "年齢の区分", None, "調", "年齢", True, 489, "乳飲み子 0〜2・子 3〜11・手伝える子 12〜14・大人 15〜54・年寄り 55〜 (境目は仮)"),
    ("season_person", "child", "子か (世界の仕組みで)", None, "シ", "控え", True, 489, None),
    ("season_person", "is_rep", "家族の代表か (集まりのとき)", None, "シ", "membership と年齢", True, 1259, None),
    ("season_person", "is_leader", "まとめ役か (集まりのとき)", None, "シ", "控え", True, 1709, None),
    ("season_person", "answered", "答えたお題", None, "シ", "答えのファイル", True, 489, "season・feeling・null"),
    ("season_person", "said", "集まりで話した数と相手 (文は入れない)", "回", "シ", "出来事「話す」", True, 489, None),
    ("season_person", "jobs", "仕事・場所・いっしょにする人・だれが決めたか (回ごと)", None, "シ", "控え (plan)", True, 489, None),
    ("season_person", "decided_by", "仕事をだれが決めたか", None, "シ", "答え", True, 489, "自分・代表が割り振った・代表と同じ仕事・加わった季節・答えなし (前と同じ)"),
    ("season_person", "job_amounts", "まく・取る・埋める・刈る・つぶすの量", None, "シ", "控え (era2.jobs)", True, 489, None),
    ("season_person", "days_by_activity", "仕事ごとの日数", "日", "シ", "出来事", True, 489, None),
    ("season_person", "outputs", "成果 (採った・木から取った・狩った・乳・刈った・まいた・埋めた・土器・鎌・捕まえた・住まい)", None, "シ", "出来事", True, 489,
     "土器と鎌は調べる人にも分かる"),
    ("season_person", "injuries", "けが", "回", "調", "出来事「けが」", True, 489, "治った骨折の跡"),
    ("season_person", "rain_outside_nights", "雨の夜に外で寝た夜", "夜", "シ", "出来事「雨」", True, 1529, None),
    ("season_person", "skills", "技能 (季節の終わり)", None, "シ", "控え", True, 489, None),
    ("season_person", "hunger", "空腹 (季節の終わり)", None, "シ", "控え", True, 489, None),
    ("season_person", "fatigue", "疲れ (季節の終わり)", None, "シ", "控え", True, 489, None),
    ("season_person", "injured_days_left", "けがで休む残りの日", "日", "シ", "控え", True, 489, None),
    ("season_person", "items", "持ち物", None, "シ", "控え", True, 489, None),
    ("season_person", "laws", "掟の提案と投票", None, "シ", "state の laws と答え", True, 489, None),
    ("season_person", "knowledge_added", "新しく覚えたこと", "件", "シ", "knowledge_log", True, 489, None),
    ("season_person", "snapshot", "季節の終わりの値が控えから取れたか", None, "-", "", True, 489, None),
    ("ledger", "season_end_day", "季節の終わりの日", "日", "-", "", True, 489, "家 × 季節 × 物 × 理由"),
    ("ledger", "holder", "持ち主 (村 か 家)", None, "-", "", True, 489, "村 = 村の蓄え + 大人の手元"),
    ("ledger", "item", "物", None, "-", "", True, 489, None),
    ("ledger", "unit", "単位", None, "-", "", True, 489, None),
    ("ledger", "kind", "残り・動き・メモ", None, "-", "", True, 489, "メモは釣り合いに入れない"),
    ("ledger", "reason", "理由", None, "シ", "", True, 489, "はじめの残り + 動き = 終わりの残り。合わない分は「記録にない差」"),
    ("ledger", "amount", "量 (入るは +、出るは −)", "単位", "シ", "控え・出来事・たどり直し・書きとめ", True, 489, "分からなければ null"),
    ("ledger", "kcal", "量 (食べ物だけ)", "kcal", "シ", "", True, 489, None),
    ("ledger", "source", "出どころ", None, "-", "snapshot・events・replay・stats・notes・balance", True, 489, None),
    ("ledger", "detail", "くわしく", None, "-", "", True, 489, None),
    ("ledger", "holder_name", "持ち主の名前", None, "シ", "", True, 489, "家の名前か 村"),
    ("year_names", "year", "年", "年", "村", "", True, 489, None),
    ("year_names", "first_day", "年のはじめの日", "日", "-", "年 × 120", True, 489, None),
    ("year_names", "last_day", "年の終わりの日", "日", "-", "年 × 120 + 119", True, 489, "この日の集まりで名前を決める"),
    ("year_names", "asked", "年の名前を聞いたか", None, "-", "お題", True, 2039, None),
    ("year_names", "name", "年の名前", None, "村", "era2.year_names", True, 2039, "村の人が口で伝える"),
    ("year_names", "decided_day", "名前が決まった日", "日", "シ", "era2.year_names", True, 2039, None),
    ("year_names", "event_id", "出来事「年の名前」の番号", None, "-", "era2.year_names", True, 2039, None),
    ("year_names", "weight", "決まった名前を書いた家族の大人の数", "人", "シ", "era2.year_names", True, 2039, None),
    ("year_names", "adults", "集まりの大人の数", "人", "シ", "era2.year_names", True, 2039, None),
    ("year_names", "proposals", "だれがどの名前を書いたか (家族の大人の数)", None, "シ", "era2.year_names", True, 2039, None),
    ("year_names", "why_none", "名前がないわけ", None, "-", "", True, 489, "年の名前を決める前の年・だれも名前を書かなかった・まだ終わっていない"),
    ("year_names", "harvest", "その年に刈った草の種", "つかみ", "シ", "出来事「収穫」", True, 489, "年代記の数の記録の見本"),
    ("laws", "id", "掟の番号", None, "-", "state の laws", True, None, None),
    ("laws", "text", "掟の文", None, "シ", "state の laws", True, None, "文字の前は残らない"),
    ("laws", "proposer_id", "言い出した人", None, "シ", "state の laws", True, None, None),
    ("laws", "proposed_day", "言い出した日 (集まりの日)", "日", "シ", "state の laws", True, None, None),
    ("laws", "status", "今", None, "シ", "state の laws", True, None, None),
    ("laws", "adopted_day", "採用された日", "日", "シ", "出来事「掟」", True, None, None),
    ("laws", "abolished_day", "廃止された日", "日", "シ", "出来事「掟」", True, None, None),
    ("laws", "penalty", "罰", None, "シ", "state の laws", True, 1859, "G5 の第 2 段から"),
    ("laws", "label", "掟の札", None, "シ", "state の laws", True, None, None),
    ("disputes", "id", "もめごとの番号", None, "-", "g5.disputes", True, 1709, None),
    ("disputes", "kind", "もめごとの種類", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "from", "言い出した家", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "against", "言われた家", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "day", "言い出した日", "日", "シ", "g5.disputes", True, 1709, None),
    ("disputes", "season_end_day", "言い出した季節", "日", "-", "", True, 1709, None),
    ("disputes", "harm", "損 (草の種にして)", "つかみ", "シ", "g5.disputes", True, 1709, None),
    ("disputes", "what", "何があったか", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "status", "今", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "verdict", "決まったこと", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "by", "だれが収めたか", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "judge_id", "裁いたまとめ役", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "paid", "払った量", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "law", "使った罰の掟", None, "シ", "g5.disputes", True, 1709, None),
    ("disputes", "end_day", "終わった日", "日", "シ", "g5.disputes", True, 1709, None),
    ("disputes", "end_season_end_day", "終わった季節", "日", "-", "", True, 1709, None),
    ("disputes", "event", "言い出した出来事の番号", None, "-", "g5.disputes", True, 1709, None),
    ("disputes", "because", "もとの出来事の番号", None, "-", "g5.disputes", True, 1709, None),
]


def columns():
    return [{"table": t, "column": c, "label_ja": lab, "unit": u, "tag": tag, "source": src, "exact": ex, "since_day": since, "note": note}
            for t, c, lab, u, tag, src, ex, since, note in COLUMNS]


# ---------------- 書き出し ----------------

def write(path, text, written):
    """中身が同じなら書かない。書くときは tmp に書いてから置きかえる"""
    b = text.encode("utf-8")
    if path.exists() and path.read_bytes() == b:
        return
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_bytes(b)
        os.replace(tmp, path)
    finally:  # 途中で失敗しても、tmp を残さない (data/ ごとコミットされるため)
        if tmp.exists():
            tmp.unlink()
    written.append(path.name)


def as_array(rows):
    return "[\n" + ",\n".join(jdump(r) for r in rows) + "\n]\n" if rows else "[]\n"


def as_lines(rows):
    return "".join(jdump(r) + "\n" for r in rows)


def build(data_dir, quiet=False, check=False):
    """記録を作り直す。戻り値: まとめ (試しと --check が使う)"""
    t0 = time.time()
    data = Path(data_dir)
    b = Builder(data)
    if b.start is None:
        print("記録: Society 2.0 がまだ始まっていないので、記録は作らない")
        return {"seasons": 0}
    b.build()
    bad = []
    vmax = {}
    for row in b.ledger_rows:
        if row["reason"] != DIFF:
            continue
        if row["holder"] == "村" and row["item"] in FOODS:
            vmax[row["item"]] = max(vmax.get(row["item"], 0), abs(row["amount"]))
        else:
            bad.append(row)
    snap_days = set(b.snaps)
    missing = [D for D in sorted(b.seasons) if D not in snap_days]
    meta = {"schema": SCHEMA, "state_day": b.state["day"], "state_next_event": b.state["next_event"], "seasons": len(b.village),
            "snapshots": {"valid": b.snap_stats["valid"], "invalid": b.snap_stats["invalid"], "malformed": b.snap_stats["malformed"],
                          "live": b.snap_stats["live"], "git": b.snap_stats["git"]},
            "missing_snapshot_days": missing,
            "ledger": {"rows": len(b.ledger_rows), "exact_accounts_with_difference": len(bad),
                       "exact_accounts_max_residual": max((abs(r["amount"]) for r in bad), default=0),
                       "village_food_max_residual": {k: vmax[k] for k in FOODS if k in vmax},
                       "village_food_max_residual_kcal": max((abs(v["detail"]["total_kcal"]) for v in b.ledger_rows
                                                              if v["reason"] == DIFF and v["holder"] == "村" and v["detail"]), default=0)},
            "harvest_replay_unverified": [v["season_end_day"] for v in b.village if v["fields"]["replay_verified"] is False],
            "event_ids_are_indexes": b.ids_ok}
    out = data / "records"
    out.mkdir(parents=True, exist_ok=True)
    written = []
    write(out / "people.json", as_array(b.people_rows), written)
    write(out / "households.json", as_array(b.household_rows), written)
    write(out / "membership.json", as_array(b.membership), written)
    write(out / "season_village.jsonl", as_lines(b.village), written)
    write(out / "season_household.jsonl", as_lines(b.house_rows), written)
    write(out / "season_person.jsonl", as_lines(b.person_rows_all), written)
    write(out / "ledger.jsonl", as_lines(b.ledger_rows), written)
    write(out / "year_names.json", as_array(b.year_rows), written)
    write(out / "laws.json", as_array(b.laws_rows), written)
    write(out / "disputes.json", as_array(b.disputes_rows), written)
    write(out / "columns.json", as_array(columns()), written)
    write(out / "meta.json", jdump(meta) + "\n", written)
    dt = time.time() - t0
    if quiet:
        print(f"記録: {len(b.village)} 季節・帳簿 {len(b.ledger_rows):,} 行 ({dt:.1f} 秒)")
    else:
        print(f"記録: {out} に書いた ({len(b.village)} 季節・家の行 {len(b.house_rows)}・人の行 {len(b.person_rows_all)}・帳簿 {len(b.ledger_rows):,} 行。"
              f"控え {b.snap_stats['valid']} (使えない {b.snap_stats['invalid']})。{dt:.1f} 秒)")
        for w in b.warnings:
            print("記録:", w)
    summary = {"builder": b, "meta": meta, "bad": bad, "seconds": dt, "written": written}
    if check:
        for r in bad:
            print(f"記録にない差: {r['season_end_day']} 日目 {r['holder']} {r['item']} {r['amount']}")
        for r in b.ledger_rows:
            if r["reason"] == DIFF and r["holder"] == "村" and (r.get("detail") or {}).get("why") == "わからない":
                print(f"村の食べ物の記録にない差 (わからない): {r['season_end_day']} 日目 {r['item']} {r['amount']}")
        if meta["harvest_replay_unverified"]:
            print("畑のたどり直しが合わない季節:", meta["harvest_replay_unverified"])
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    s = build(a.data, quiet=a.quiet, check=a.check)
    if a.check and s.get("bad"):
        sys.exit(1)


if __name__ == "__main__":
    main()
