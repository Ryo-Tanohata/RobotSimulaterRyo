"""よその便り (史実のヒント。docs/society_phase/G7_design.md 4.C・6.2 の「便り」) の試し。本物の data にはさわらない (写しはメモリの中か /tmp)

  PYTHONUTF8=1 python3.13 sim/society/tools/test_hints.py

- 札の表: 11 枚・禁じた言葉・220 字・出典の印・運び手の数・ハッシュがちがうと止まる
- 来る数 λ・ポワソン・段の混ぜ方・札の選び方 (くり返し 3 回・使った札を抜く・ない段の順)・空振り
- 届く: 聞く人 (1〜3 人・見本の家の大人・商人のときは交換に行った人が先)・出来事の文に話の中身がない・群れ (来たところをつけない・λ で数えない)
- 知っている人・知識の札「よその便り」(しまったあとも)・試す (待つ・開く・教える人・できる)・きっかけ (塩 67)・捕らえた職人・同じ state から同じ結果
本物の state.json が G6 でないとき (もう G7 に入ったあと) は、G6 の state が要る試しをとばす。
"""
import copy
import json
import os
import random
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
sys.path[:0] = [str(SOC), str(HERE)]
import era2  # noqa: E402
import hints  # noqa: E402
import test_g7 as T  # noqa: E402
import world  # noqa: E402


def g7_state():
    if not T.is_g6(T.real_state()):
        raise unittest.SkipTest("本物の state が G6 でない")
    return T.g7_state()


def _h(st):
    return st["era2"]["g7"]["hints"]


class A_Cards(unittest.TestCase):
    def test_cards(self):
        cs = hints.cards()
        self.assertEqual(hints.check_cards(), [])
        g7 = {k: c for k, c in cs.items() if c["stage"] == "G7"}
        self.assertEqual(len(g7), 11, "G7 の札は 11 枚 (7. の 7)")
        n = {}
        for c in g7.values():
            for x in c["carrier"]:
                n[x] = n.get(x, 0) + 1
        self.assertEqual(n, {"旅人": 2, "商人": 4, "教えを説く人": 3, "よそから来た人": 2, "捕らえた職人": 1})
        for st in hints.STAGES[1:]:
            self.assertTrue(1 <= sum(1 for c in cs.values() if c["stage"] == st) <= 4, st)
        self.assertEqual(cs["H7-06"]["needs"], {"牛": 2})
        self.assertEqual(cs["H7-10"]["teach"], "土器")

    def test_check_finds_bad(self):
        cs = copy.deepcopy(hints.cards())
        cs["H7-01"]["text"] = "王の話" + "あ" * 230
        bad = hints.check_cards(cs)
        self.assertTrue(any("王" in b for b in bad) and any("字" in b for b in bad))

    def test_hash_changed(self):
        st = g7_state()
        self.assertIsNone(hints.cards_changed(st))
        tmp = Path(tempfile.mkdtemp(prefix="g7h_", dir="/tmp"))
        old = hints.CARDS
        try:
            f = tmp / "hint_cards.json"
            shutil.copy(old, f)
            hints.CARDS = f
            self.assertIsNone(hints.cards_changed(st))
            d = json.loads(f.read_text(encoding="utf-8"))
            d["cards"][0]["text"] += "。"
            f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            self.assertIn("変わった", hints.cards_changed(st))
            n = len(st["events"])
            self.assertIsNone(hints.cards_note(st, "試しで直した"))
            self.assertIsNone(hints.cards_changed(st))
            self.assertEqual(st["events"][n]["type"], "区切り")
            self.assertEqual(_h(st)["cards_log"][-1]["note"], "試しで直した")
        finally:
            hints.CARDS = old
            hints._CACHE.clear()
            shutil.rmtree(tmp, ignore_errors=True)


class B_Draw(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = g7_state()

    def st(self):
        return copy.deepcopy(self.base)

    def test_lambda(self):
        st = self.st()
        lo, hi = hints._window(st)
        for o in era2._g6(st)["others"]:
            o["contacts"] = []
        st["events"] = [e for e in st["events"] if not (e["type"] == "加わる" and lo <= e["day"] <= hi)]
        st["events"] = [e for e in st["events"] if not (e["type"] == "蓄えが尽きる" and lo <= e["day"] <= hi)]
        hard = hints._bad_year(st, lo, hi) or hints._debt_year(st, lo, hi)
        lam = sum(w for _, w, _ in hints.terms(st, "V0"))
        self.assertAlmostEqual(lam, 0.4 if hard else 0.3)
        os_ = sorted(era2._g6(st)["others"], key=lambda o: int(o["id"][1:]))
        os_[0]["contacts"], os_[1]["contacts"] = [hi], [hi - 10]
        world.log(st, "加わる", None, "よそから来た ア・イ が、村に加わった (賛成 1 / 1)")
        world.log(st, "加わる", None, "よそから来た ウ が、村に加わった (賛成 1 / 1)", hint="Y9")  # 便りの群れは数えない
        t = hints.terms(st, "V0")
        self.assertAlmostEqual(sum(w for _, w, _ in t), (0.4 if hard else 0.3) + 0.3 + 0.3)
        self.assertEqual([f for c, _, f in t if c == "商人"], [os_[0]["id"], os_[1]["id"]])
        self.assertEqual(sum(1 for c, _, _ in t if c == "よそから来た人"), 1)

    def test_no_trade_no_merchant(self):
        st = self.st()
        for o in era2._g6(st)["others"]:
            o["contacts"] = []
        lo, hi = hints._window(st)
        st["events"] = [e for e in st["events"] if not (e["type"] == "加わる" and lo <= e["day"] <= hi)]
        cs = {c for c, _, _ in hints.terms(st, "V0")}
        self.assertNotIn("商人", cs)
        self.assertNotIn("よそから来た人", cs)

    def test_poisson(self):
        rng = random.Random(5)
        for lam in (0.3, 1.1):
            xs = [hints.poisson(rng, lam) for _ in range(10000)]
            self.assertAlmostEqual(sum(xs) / len(xs), lam, delta=lam * 0.03 + 0.01)

    def test_cap_and_stage_mix(self):
        rng = random.Random(9)
        n = [0, 0, 0]
        for _ in range(20000):
            s, _ = hints._pick_stage(rng, 0)
            n[0 if s == 0 else 1 if s == 1 else 2] += 1
        for got, want in zip(n, hints.STAGE_MIX):
            self.assertAlmostEqual(got / 20000, want, delta=0.02)
        st = self.st()
        old = hints.terms
        try:
            hints.terms = lambda state, rid: [("旅人", 30.0, None)]
            _h(st)["ledger"], _h(st)["plan"], _h(st)["lam"] = [], [], []
            hints._year_plan(st, random.Random(1))
            self.assertTrue(all(x["n"] <= hints.HINT_CAP for x in _h(st)["lam"]))
            self.assertEqual(sum(1 for r in _h(st)["ledger"] if r["to"] == "V0"), 3)
        finally:
            hints.terms = old

    def test_pick_card_order_and_repeat(self):
        st = self.st()
        rng = random.Random(3)
        c, s = hints._pick_card(st, rng, "V0", 0, 0, "旅人")
        self.assertIn(c, ("H7-01", "H7-07"))
        _h(st)["seen"]["V0"] = {"H7-01": 3, "H7-07": 3}
        c, s = hints._pick_card(st, rng, "V0", 0, 0, "旅人")
        self.assertEqual(hints.STAGES[s], "G8", "今の段になければ次の段")
        _h(st)["used"]["V0"] = ["H8-03"]
        c, s = hints._pick_card(st, rng, "V0", 0, 0, "旅人")
        self.assertEqual(hints.STAGES[s], "G11", "次の段もなければ先の段 (前の段 G6 には札がない)")
        _h(st)["used"]["V0"] += ["H11-01", "H13-02"]
        self.assertEqual(hints._pick_card(st, rng, "V0", 0, 0, "旅人"), (None, None), "どこにもなければ空振り")

    def test_same_state_same_plan(self):
        a, b = self.st(), self.st()
        for st in (a, b):
            _h(st)["ledger"], _h(st)["plan"], _h(st)["lam"], _h(st)["next"] = [], [], [], 1
            st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
            hints._year_plan(st, era2._rng(st, era2.HINT_SALT))
        self.assertEqual(_h(a)["ledger"], _h(b)["ledger"])


class C_Deliver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = g7_state()

    def st(self):
        return copy.deepcopy(self.base)

    def deliver(self, st, card, carrier, frm=None):
        h = _h(st)
        y = f"Y{h['next']}"
        h["next"] += 1
        r = {"y": y, "card": card, "carrier": carrier, "to": "V0", "from": frm, "drawn": st["day"], "due": st["day"], "stage": "G7", "stage_got": "G7",
             "u": [], "status": "待つ", "delivered": None, "listeners": [], "outcome": []}
        h["ledger"].append(r)
        hints._deliver_v0(st, random.Random(7), r)
        return r

    def test_listeners_and_text(self):
        st = self.st()
        r = self.deliver(st, "H7-01", "旅人")
        self.assertEqual(r["status"], "届いた")
        self.assertTrue(1 <= len(r["listeners"]) <= 3)
        sample = set(st["era2"]["g7"]["sample"])
        for n in r["listeners"]:
            self.assertIn(next(p for p in st["people"] if p["name"] == n).get("household"), sample)
        e = next(e for e in st["events"] if e["id"] == r["event"])
        c = hints.cards()["H7-01"]
        self.assertEqual(e["type"], "よその便り")
        self.assertEqual(e["data"]["text"], c["text"])
        for w in c["words"] + [c["text"][:10]]:
            self.assertNotIn(w, e["text"], "出来事の文に話の中身を入れない")
        p = next(p for p in st["people"] if p["name"] == r["listeners"][0])
        self.assertEqual(p["heard"][-1]["text"], c["text"])
        txt = hints.text(st, p)
        self.assertIn("## よその便り", txt)
        self.assertIn("何もしなくてもよい", txt)
        other = next(q for q in era2.adults(st) if q["name"] not in r["listeners"])
        self.assertEqual(hints.text(st, other), "", "聞いた人のお題にだけ出す")
        for k in hints.FORBIDDEN:
            self.assertNotIn(k, e["text"])

    def test_merchant_meets_traders_first(self):
        st = self.st()
        o = era2._g6(st)["others"][0]
        o["known"] = o["known"] or 1
        st["era2"]["step_day"] = st["day"] - 29
        names = sorted(p["name"] for p in era2.adults(st) if p.get("household") in st["era2"]["g7"]["sample"])[:1]
        era2._g6(st)["trip_log"] = [{"who": names[0], "to": o["id"], "start": st["day"] - 5, "end": st["day"] - 2}]
        r = self.deliver(st, "H7-02", "商人", o["id"])
        self.assertIn(names[0], r["listeners"])

    def test_gone_merchant_misses(self):
        st = self.st()
        r = self.deliver(st, "H7-02", "商人", "N999")
        self.assertEqual(r["status"], "空振り")

    def test_group_and_settle(self):
        st = self.st()
        r = self.deliver(st, "H7-10", "よそから来た人")
        v = st["era2"]["visitors"][-1]
        self.assertEqual(v["hint"], r["y"])
        self.assertNotIn("from", v)
        # 季節の終わりの G6 の「来たところ」(塩 41) は、便りの群れにつけない
        era2._g6_season_end(st, 1.0)
        self.assertNotIn("from", v)
        n0 = len(st["people"])
        lo, hi = st["day"] + 1 - era2.YEAR, st["day"]
        j0 = hints._joined_groups(st, lo, hi)
        era2._settle_visitors(st, {v["name"]: [(p["name"], True) for p in era2.adults(st)]}, len(era2.adults(st)))
        self.assertEqual(hints._joined_groups(st, lo, hi), j0, "便りの群れを受け入れても、次の年の λ はふえない")
        new = st["people"][n0:]
        self.assertTrue(new and all(p["skills"].get("土器") == hints.TEACH_SKILL for p in new if not p.get("child")))
        e = next(e for e in reversed(st["events"]) if e["type"] == "加わる")
        self.assertEqual(e["data"]["hint"], r["y"])
        self.assertIn("受け入れた", [o[0] for o in r["outcome"]])
        self.assertIn("H7-10", _h(st)["used"]["V0"])
        # 教える人と同じ日に土器づくり: 腕の伸びが 2 倍
        q = next(p for p in era2.adults(st) if p["name"] not in {x["name"] for x in new})
        t = new[0]
        t["today"], q["today"] = {"activity": "土器づくり"}, {"activity": "土器づくり"}
        self.assertEqual(hints.craft_step(st, q, "土器づくり", 0.02), 0.04)
        self.assertEqual(hints.craft_step(st, t, "土器づくり", 0.02), 0.02)

    def test_knowledge_label(self):
        st = self.st()
        r = self.deliver(st, "H7-03", "教えを説く人")
        import knowledge
        p = next(p for p in era2.adults(st) if p["name"] not in r["listeners"])
        knowledge.apply_updates(st, p, [{"op": "add", "text": "書いた決まり", "because": [r["event"]], "confidence": 1.0}])
        k = next(k for k in p["knowledge"] if k["text"] == "書いた決まり")
        self.assertEqual(k["label"], "よその便り")
        hints._scan_knowledge(st)
        self.assertEqual(k["card"], "H7-03")
        self.assertTrue(hints.knows(st, p["name"], "H7-03"))
        import archive
        self.assertIn("よその便り", archive.KEEP_TYPES)
        self.assertIn("きっかけ", archive.KEEP_TYPES)


class D_Try(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = g7_state()

    def test_wait_open_try_done(self):
        st = copy.deepcopy(self.base)
        r = C_Deliver.deliver(None, st, "H7-06", "よそから来た人")
        t = _h(st)["tech"]["H7-06"]
        self.assertIsNone(t["open"], "牛がいないので待つ")
        self.assertEqual(t["wait"], st["day"])
        self.assertEqual(hints.open_techs(st), [])
        st["era2"]["cattle"] = [{"id": i, "sex": "メス", "born": st["day"] - 3 * era2.YEAR, "owner": None} for i in (1, 2)]
        hints._tech_season(st)
        self.assertEqual(hints.open_techs(st), ["H7-06"])
        a, b = sorted(r["listeners"])[0], None
        pa = next(p for p in st["people"] if p["name"] == a)
        st["era2"]["g7"]["jobs7"] = {a: {"try": "H7-06"}}
        pa["today"] = {"activity": "試す", "work_h": 6}
        pa["plan"] = {"activity": "試す", "place": "camp", "with": []}
        hints.try_day(st, pa, pa["today"])
        self.assertEqual(t["first"], st["day"])
        self.assertAlmostEqual(t["progress"], 0.6)
        self.assertEqual(pa["skills"]["試す:H7-06"], 0.12)
        # 教える人 (腕 0.6 以上) と同じ日: 進み 2 倍・腕 +0.04
        knower2 = [n for n in _h(st)["knowers"]["H7-06"] if n != a]
        if knower2:
            b = next(p for p in st["people"] if p["name"] == knower2[0])
            b["skills"]["試す:H7-06"] = 0.7
            b["today"] = {"activity": "試す", "work_h": 6}
            st["era2"]["g7"]["jobs7"][b["name"]] = {"try": "H7-06"}
            p0 = t["progress"]
            hints.try_day(st, pa, pa["today"])
            self.assertAlmostEqual(t["progress"] - p0, 2 * (0.5 + 0.12), places=3)
            self.assertEqual(pa["skills"]["試す:H7-06"], 0.16)
        # できる: 進み 120 人日・1 年・牛 2 頭
        t["progress"] = 200.0
        hints._tech_season(st)
        self.assertIsNone(t["done"], "1 年たっていない")
        st["day"] += era2.YEAR
        hints._tech_season(st)
        self.assertEqual(t["done"], st["day"])
        # 腕を持つ人がいなくなったら戻る
        for p in st["people"]:
            p["skills"].pop("試す:H7-06", None)
        hints._tech_season(st)
        self.assertIsNone(t["done"])
        self.assertEqual(t["progress"], 100.0)

    def test_unknown_person_rests(self):
        import g7
        st = copy.deepcopy(self.base)
        st["era2"]["cattle"] = [{"id": i, "sex": "メス", "born": st["day"] - 3 * era2.YEAR, "owner": None} for i in (1, 2)]
        hints._open(st, "H7-06", "ヒント")
        p = era2.adults(st)[0]
        p["plan"] = {"activity": "試す", "place": "camp", "with": []}
        g7.job(st, p, {"activity": "試す", "try": "H7-06"})
        self.assertEqual(p["plan"]["activity"], "休む", "知らない人は試せない")

    def test_chance(self):
        st = copy.deepcopy(self.base)
        st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
        hints.chance(st)
        self.assertNotIn("H7-06", _h(st)["tech"], "牛がいなければ引かない")
        self.assertFalse(_h(st).get("chance_log"))
        st["era2"]["cattle"] = [{"id": i, "sex": "メス", "born": 0, "owner": None} for i in (1, 2)]
        st["era2"]["g7"]["past"] = [{"day": st["day"], "season": "春", "days": {"x": {"畑仕事": 400}}, "home": {}}]
        old = hints.cards()["H7-06"]["chance"]["p"]
        try:
            hints.cards()["H7-06"]["chance"]["p"] = 1.0
            hints.chance(st)
        finally:
            hints.cards()["H7-06"]["chance"]["p"] = old
        self.assertEqual(_h(st)["tech"]["H7-06"]["source"], "きっかけ")
        self.assertEqual(st["events"][-1]["type"], "きっかけ")
        self.assertEqual(len(_h(st)["chance_log"]), 1)

    def test_captives(self):
        st = copy.deepcopy(self.base)
        g = st["era2"]["g7"]
        oid = era2._g6(st)["others"][0]["id"]
        st["era2"]["step_day"] = st["day"] - 29
        g["region"]["wars"] = [{"id": "W1", "att": "V0", "def": oid, "day": st["day"] - 3, "done": st["day"] - 3, "att_win": True}]
        g["captives"] = {"day": st["day"], "choice": "連れて帰る"}
        n0 = len(st["people"])
        hints._captives(st, random.Random(4))
        new = st["people"][n0:]
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0]["origin"], "連れて来られた")
        self.assertEqual(new[0]["skills"]["土器"], hints.TEACH_SKILL)
        hints._captives(st, random.Random(4))
        self.assertEqual(len(st["people"]), n0 + 1, "同じ戦は 1 回だけ")
        # 負けた: 見込み 0.5 で、いちばん腕の高い大人が連れて行かれる
        st2 = copy.deepcopy(self.base)
        st2["era2"]["step_day"] = st2["day"] - 29
        st2["era2"]["g7"]["region"]["wars"] = [{"id": "W2", "att": oid, "def": "V0", "day": st2["day"] - 3, "done": st2["day"] - 3, "att_win": True}]
        best = sorted(era2.adults(st2), key=lambda q: (-hints._skill_of(q), -q["age"], q["name"]))[0]["name"]

        class R(random.Random):
            def random(self):
                return 0.1
        hints._captives(st2, R(0))
        p = next(p for p in st2["people"] if p["name"] == best)
        self.assertFalse(p["alive"])
        self.assertEqual(p["left"], st2["day"])


class E_Season(unittest.TestCase):
    """季節の終わりの便り: 同じ state から同じ結果。塩 47 は 1 日 1 回 (G7 に入る前は作らない)"""

    def test_same(self):
        base = g7_state()
        a, b = copy.deepcopy(base), copy.deepcopy(base)
        for st in (a, b):
            st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
            hints.season_end(st)
        self.assertEqual(json.dumps(_h(a), sort_keys=True, ensure_ascii=False), json.dumps(_h(b), sort_keys=True, ensure_ascii=False))

    def test_salt_once_per_day(self):
        st = g7_state()
        st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
        seen = []
        old = era2._rng

        def spy(state, salt):
            seen.append(salt)
            return old(state, salt)
        era2._rng = spy
        try:
            hints.season_end(st)
            hints.chance(st)
        finally:
            era2._rng = old
        self.assertEqual(seen.count(era2.HINT_SALT), 1)
        self.assertLessEqual(seen.count(era2.CHANCE_SALT), 1)

    def test_parts_off(self):
        world.G7_PARTS["hints"] = False
        try:
            st = T.g7_state() if T.is_g6(T.real_state()) else None
            if st is None:
                self.skipTest("本物の state が G6 でない")
            self.assertEqual(_h(st)["ledger"], [], "便りを止めると、引かない")
            self.assertFalse(hints.on(st))
        finally:
            world.G7_PARTS["hints"] = True


if __name__ == "__main__":
    unittest.main(verbosity=2)
