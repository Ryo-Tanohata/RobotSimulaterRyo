"""論文 2・実験 4 (exp4.py・step.py exp4・era2._feed のつなぎ) の試し。本物の data にはさわらない (state はメモリの中か /tmp の写し)

  PYTHONUTF8=1 python3.13 sim/society/tools/test_exp4.py

- 組なし: お題 (季節・年・気持ち) は 1 字も変わらない。毎日の決まり (era2._feed) も前と同じ (ひどく空腹の人は、よその家の倉から自動で取る)
- B0・B1: 節と欄は足りない家の人だけ / strip で今のお題に戻る / 禁じた言葉がない / 数が state と同じ / B1 は代表のお題に暮らしの節も
- 毎日の決まり: 村の蓄え・よその家の倉 (印のない倉だけ。もめごとのもと「倉」) / 30 日分で止まる / 取らないなら何も動かない / 自動で取る決まりは止まる
- 答えを読む・広げる・季節の終わりに残す / take の読み方
- 断る: 本物の村・知らない組・組の入れかえ・実験 3 の写し・season でない段階。step.py exp4 を写しで動かす・本物の村では断る
- 数え方 (exp4_measure): 節からの読み方・人ごとの傾き
"""
import copy
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
sys.path[:0] = [str(SOC), str(HERE)]
import era2  # noqa: E402
import exp3  # noqa: E402
import exp4  # noqa: E402
import exp4_measure as M  # noqa: E402
import g7  # noqa: E402

REAL = SOC / "data"
START = "726c5340"
_S = {}


def real():
    if "s" not in _S:
        _S["s"] = json.loads((REAL / "state.json").read_text(encoding="utf-8"))
    return copy.deepcopy(_S["s"])


def old_state():
    """本物の 12599 日目 (実験 3・4 のはじめの state)。浅いクローンでコミットがなければ None"""
    if "o" not in _S:
        r = subprocess.run(["git", "-C", str(SOC.parent.parent), "show", f"{START}:sim/society/data/state.json"], capture_output=True)
        _S["o"] = json.loads(r.stdout) if r.returncode == 0 else None
    return copy.deepcopy(_S["o"]) if _S["o"] else None


def states():
    out = [("今", real())]
    o = old_state()
    if o:
        out.append(("12599", o))
    return out


def prompts(state):
    """{名前: (人, 季節か年のお題, "代表")} と {名前: (人, 気持ちのお題, "気持ち")}"""
    first = g7.since(state)
    out = {}
    for n in era2.answerers(state):
        p = next(q for q in state["people"] if q["name"] == n)
        t = g7.year_prompt(state, p, first) if state["era2"]["g7"].get("ask") == "年" else era2.season_prompt(state, p, first)
        out[n] = (p, t, "代表")
    for n in era2.feelers(state):
        p = next(q for q in state["people"] if q["name"] == n)
        out[n] = (p, era2.feeling_prompt(state, p, first), "気持ち")
    return out


def add(state, p, t, role):
    return exp4.apply(state, p, t) if role == "代表" else exp4.apply_feeling(state, p, t)


class A_Off(unittest.TestCase):
    def test_no_flag_same(self):
        for lab, s in states():
            for n, (p, t, role) in prompts(s).items():
                self.assertEqual(add(s, p, t, role), t, f"{lab} {n}")

    def test_no_flag_noop(self):
        s = old_state() or real()
        before = json.dumps(s, ensure_ascii=False, sort_keys=True)
        exp4.read_choices(s, {}, {})
        exp4.spread(s)
        exp4.season_end(s)
        self.assertEqual(json.dumps(s, ensure_ascii=False, sort_keys=True), before)

    def test_feed_off_steals(self):
        """組なし: ひどく空腹で、村の蓄えも家の倉もない人は、よその家の倉から自動で取る (前と同じ)。組があると取らない"""
        took_by = {}
        for on in (False, True):
            s = old_state()
            if not s:
                self.skipTest("12599 日目のコミットがない")
            if on:
                exp4.set_arm(s, "B0", "試し")
            p, rich = self._starving(s)
            before = exp3._house_kcal(s, rich)
            era2._feed(s, era2._rng(s, 3))
            took = before - exp3._house_kcal(s, rich)
            inc = [x for x in s["era2"]["g5"]["incidents"] if x["kind"] == "倉" and x["against"] == p["household"]]
            took_by[on] = took  # (その家の人と、親類の子も、その家の倉から食べる。自動で取った分だけ、組なしのほうが多く減る)
            self.assertEqual(bool(inc), not on)
        self.assertGreater(took_by[False], took_by[True])

    @staticmethod
    def _starving(s):
        """村の蓄えをからにし、印のない、食べ物のある家を 1 つ残し、ある足りない家の大人をひどく空腹にする"""
        s["store"] = []
        seals = s["era2"]["g6"]["seals"]
        have = [h for h in era2._homes(s) if exp3._house_kcal(s, h) > 0]
        rich = next(h for h in have if h not in seals)
        p = next(q for q in era2.adults(s) if q["household"] != rich and exp3._house_kcal(s, q["household"]) == 0)
        for q in era2.adults(s):
            q["food"] = []
        p["hunger"] = 0.7
        return p, rich


class B_Prompts(unittest.TestCase):
    def test_sections(self):
        for lab, s0 in states():
            for arm in ("B0", "B1"):
                s = copy.deepcopy(s0)
                exp4.set_arm(s, arm, "試し")
                n_add = 0
                for n, (p, t, role) in prompts(s).items():
                    x = add(s, p, t, role)
                    self.assertEqual(exp4.strip(x), t, f"{lab} {arm} {n}")
                    ask = exp4.asked(s, p)
                    self.assertEqual(x.count(exp4.HEAD), int(ask), f"{lab} {arm} {n}")
                    self.assertEqual('"take": "..."' in x, ask)
                    self.assertEqual(x.count(exp3.LIFE_HEAD), int(arm == "B1" and role == "代表"), f"{lab} {arm} {n}")
                    if ask:
                        n_add += 1
                        i = x.index(exp4.HEAD)
                        j = x.index(exp3.ANCHOR if role == "代表" else exp4.FEEL_ANCHOR)
                        self.assertLess(i, j)
                        for w in exp3.FORBIDDEN:
                            self.assertNotIn(w, x[i:j], f"{lab} {arm} {n}: {w}")
                        self.assertIn(f"約 {era2.store_days(s)} 日分", x[i:j])
                        json.loads(x[x.rindex("## 答えの形 (JSON)\n") + len("## 答えの形 (JSON)\n"):].replace("[出来事の番号]", "[]"))
                    if arm == "B1" and role == "代表":
                        self.assertLess(x.index(exp3.LIFE_HEAD), x.index(exp3.ANCHOR))
                        if ask:
                            self.assertLess(x.index(exp3.LIFE_HEAD), x.index(exp4.HEAD))
                if lab == "12599":
                    self.assertEqual(n_add, 36)  # 代表 12 + 気持ち 26 のうち、足りない家の人 (prereg 4.)

    def test_12599_facts(self):
        s = old_state()
        if not s:
            self.skipTest("12599 日目のコミットがない")
        exp4.set_arm(s, "B0", "試し")
        p = next(q for q in s["people"] if q["name"] == "キサ9")
        t = exp4.take_text(s, p)
        self.assertIn("あなたの家 (ハソ4の家) の倉: からっぽ", t)
        self.assertIn("大人 3 人、子 4 人", t)
        self.assertIn("約 23 日分", t)
        self.assertIn("食べ物のある家 3。そのうち、印 (封) のない家 1", t)
        self.assertIn("村の家 24 のうち 21 の家は", t)
        self.assertIn("倉 0 本、蓄え 0 本", t)
        rich = next(q for q in s["people"] if q["name"] == "ナセ20")
        self.assertFalse(exp4.asked(s, rich))  # いちばん多く持つ家 (211 日分) には聞かない
        f = M.section_facts(t)
        self.assertEqual((f["empty"], f["kids"], f["hungry"], f["store_days"], f["open"], f["signal"]), (True, 4, False, 23, 1, "なし"))

    def test_world_untouched(self):
        s = old_state() or real()
        exp4.set_arm(s, "B1", "試し")
        ps = prompts(s)
        before = json.dumps(s, ensure_ascii=False, sort_keys=True)
        for n, (p, t, role) in ps.items():
            add(s, p, t, role)
        self.assertEqual(json.dumps(s, ensure_ascii=False, sort_keys=True), before)


class C_World(unittest.TestCase):
    def _s(self):
        s = old_state()
        if not s:
            self.skipTest("12599 日目のコミットがない")
        exp4.set_arm(s, "B0", "試し")
        return s

    def test_store(self):
        s = self._s()
        p = next(q for q in s["people"] if q["name"] == "キサ9")
        h = p["household"]
        s["era2"]["g7"]["exp4"]["choice"] = {p["name"]: {"take": "村の蓄え", "src": "自分", "day": s["day"]}}
        v0, h0 = sum(f["kcal"] for f in s["store"]), exp3._house_kcal(s, h)
        fl0 = (s["era2"]["g5"]["flow"].get(h) or [0, 0, 0])[1]
        exp4.take_day(s, p)
        self.assertAlmostEqual(v0 - sum(f["kcal"] for f in s["store"]), exp4.TAKE_DAY, places=3)
        self.assertAlmostEqual(exp3._house_kcal(s, h) - h0, exp4.TAKE_DAY, places=3)
        self.assertAlmostEqual(s["era2"]["g5"]["flow"][h][1] - fl0, exp4.TAKE_DAY, places=3)
        self.assertEqual(s["era2"]["g7"]["exp4"]["now"][p["name"]]["村の蓄え"], exp4.TAKE_DAY)

    def test_other_house(self):
        s = self._s()
        seals = s["era2"]["g6"]["seals"]
        have = [h for h in era2._homes(s) if exp3._house_kcal(s, h) > 0]
        open_ = [h for h in have if h not in seals]
        shut = [h for h in have if h in seals]
        self.assertEqual(len(open_), 1)
        p = next(q for q in s["people"] if q["name"] == "キサ9")
        s["era2"]["g7"]["exp4"]["choice"] = {p["name"]: {"take": "よその家の倉", "src": "自分", "day": s["day"]}}
        k_open, k_shut = exp3._house_kcal(s, open_[0]), [exp3._house_kcal(s, h) for h in shut]
        exp4.take_day(s, p)
        self.assertAlmostEqual(k_open - exp3._house_kcal(s, open_[0]), exp4.TAKE_DAY, places=3)
        self.assertEqual(k_shut, [exp3._house_kcal(s, h) for h in shut])  # 印のある倉は動かない
        inc = [x for x in s["era2"]["g5"]["incidents"] if x["kind"] == "倉"]
        self.assertEqual([(x["from"], x["against"]) for x in inc], [(open_[0], p["household"])])
        self.assertFalse([e for e in s["events"] if e["day"] == s["day"] and e["type"] in ("倉から取る", "封")])  # だまって (出来事は書かない)

    def test_target_stops_and_none(self):
        s = self._s()
        p = next(q for q in s["people"] if q["name"] == "キサ9")
        h = p["household"]
        x = s["era2"]["g7"]["exp4"]
        x["choice"] = {p["name"]: {"take": "取らない", "src": "自分", "day": s["day"]}}
        before = json.dumps(s, ensure_ascii=False, sort_keys=True)
        exp4.take_day(s, p)
        self.assertEqual(json.dumps(s, ensure_ascii=False, sort_keys=True), before)
        x["choice"][p["name"]]["take"] = "村の蓄え"
        gap = exp4.TARGET_DAYS * exp4.house_need(s, h) - exp3._house_kcal(s, h)
        n = 0
        while exp4.short(s, h) and n < 1000:
            exp4.take_day(s, p)
            n += 1
        self.assertFalse(exp4.short(s, h))
        self.assertEqual(n, -(-gap // exp4.TAKE_DAY))
        k = exp3._house_kcal(s, h)
        exp4.take_day(s, p)
        self.assertEqual(exp3._house_kcal(s, h), k)

    def test_read_spread_end(self):
        s = self._s()
        ans = {n: json.dumps({"take": "村の蓄え", "take_why": "子が多い"}) for n in era2.answerers(s)}
        feels = {n: json.dumps({"feeling": "x", "take": "よその家の倉です"}) for n in era2.feelers(s)}
        exp4.read_choices(s, ans, feels)
        x = s["era2"]["g7"]["exp4"]
        asked = {q["name"] for q in era2.adults(s) if exp4.asked(s, q) and (q["name"] in ans or q["name"] in feels)}
        self.assertEqual(set(x["choice"]), asked)
        self.assertEqual({r["name"] for r in x["log"]}, asked)
        self.assertTrue(all(r["take"] in ("村の蓄え", "よその家の倉") for r in x["log"]))
        self.assertNotIn("ナセ20", x["choice"])
        sample = s["era2"]["g7"]["sample"]
        rep_of = g7._rep_of(s)
        d = next(h for h in sample if x["choice"].get(rep_of.get(h), {}).get("take") == "村の蓄え")
        other = next(h for h in era2._homes(s) if h not in sample)
        s["era2"]["g7"]["step"] = {"donor": {other: d}}
        exp4.spread(s)
        for q in era2.adults(s):
            if q["household"] == other:
                self.assertEqual(x["choice"][q["name"]], {"take": "村の蓄え", "src": "見本から広げた", "from": rep_of[d], "day": s["day"]})
        exp4.season_end(s)
        self.assertEqual(x["acts"][-1]["day"], s["day"])
        self.assertEqual(x["now"], {})

    def test_parse(self):
        self.assertEqual(exp4.parse_take("取らない"), "取らない")
        self.assertEqual(exp4.parse_take(" 村の蓄え "), "村の蓄え")
        self.assertEqual(exp4.parse_take("よその家の倉から"), "よその家の倉")
        self.assertIsNone(exp4.parse_take("村の蓄えからは取らない"))
        self.assertIsNone(exp4.parse_take("..."))
        self.assertIsNone(exp4.parse_take(None))


class D_Refuse(unittest.TestCase):
    def test_refusals(self):
        s = real()
        tmp = Path(tempfile.gettempdir()) / "exp4_x"
        self.assertIn("本物の村", exp4.refusal(s, "B0", REAL, REAL))
        self.assertIn("組は", exp4.refusal(s, "B9", tmp, REAL))
        self.assertIsNone(exp4.refusal(s, "B0", tmp, REAL))
        exp4.set_arm(s, "B0", "試し")
        self.assertIn("もう組 B0", exp4.refusal(s, "B1", tmp, REAL))
        self.assertIsNone(exp4.refusal(s, "B0", tmp, REAL))
        self.assertIsNone(exp4.set_arm(s, "B0", "試し"))
        s2 = real()
        exp3.set_arm(s2, "A0", "試し")
        self.assertIn("実験 3", exp4.refusal(s2, "B0", tmp, REAL))
        s3 = real()
        s3["phase"] = "evening"
        self.assertIn("season でない", exp4.refusal(s3, "B0", tmp, REAL))


class E_Step(unittest.TestCase):
    def _run(self, d, *args):
        env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
        return subprocess.run([sys.executable, str(SOC / "step.py"), *args], capture_output=True, text=True, env=env, cwd=str(SOC))

    def test_step_b0(self):
        s = real()
        if s.get("phase") != "season":
            self.skipTest("本物の村が season でない")
        d = Path(tempfile.mkdtemp(prefix="exp4_test_"))
        try:
            shutil.copy(REAL / "state.json", d / "state.json")
            r = self._run(d, "exp4", "B0", "--note", "試し")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            st = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(st["era2"]["g7"]["exp4"]["arm"], "B0")
            st["era2"]["g7"].pop("exp4")
            self.assertEqual(json.dumps(st, ensure_ascii=False, separators=(",", ":")), (REAL / "state.json").read_text(encoding="utf-8"))
            day = s["day"]
            for kind in ("season", "feeling", "council"):
                for f in sorted((REAL / "prompts" / f"day{day:03d}" / kind).glob("*.md")):
                    t = (d / "prompts" / f"day{day:03d}" / kind / f.name).read_text(encoding="utf-8")
                    self.assertEqual(exp4.strip(t), f.read_text(encoding="utf-8"), f"{kind} {f.name}")
            self.assertEqual(self._run(d, "exp4", "B1").returncode, 3)
            self.assertEqual(self._run(d, "exp3", "A0").returncode, 3)
            self.assertIn("実験 4 の組: B0", self._run(d, "status").stdout)
        finally:
            shutil.rmtree(d)

    def test_step_real_refused(self):
        before = (REAL / "state.json").stat().st_mtime_ns
        env = dict(os.environ, PYTHONUTF8="1")
        env.pop("SOC_DATA", None)
        r = subprocess.run([sys.executable, str(SOC / "step.py"), "exp4", "B0"], capture_output=True, text=True, env=env, cwd=str(SOC))
        self.assertEqual(r.returncode, 3)
        self.assertIn("本物の村", r.stdout)
        self.assertEqual((REAL / "state.json").stat().st_mtime_ns, before)


class G_EndToEnd(unittest.TestCase):
    def test_one_step(self):
        """写しで B0 を入れ、本物の 12599 日目の答えに take を足して step.py season を 1 回 → 選び・取った量・数え方がつながる"""
        if not old_state():
            self.skipTest("12599 日目のコミットがない")
        import exp3_replay as R
        w = Path(tempfile.mkdtemp(prefix="exp4_e2e_"))
        d = w / "data"
        try:
            d.mkdir()
            R.git_extract(START, [f"{R.D}/state.json", f"{R.D}/archive", f"{R.D}/app_data.json"], d)
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], capture_output=True, text=True, env=env, cwd=str(SOC))  # noqa: E731
            r = run("exp4", "B0")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            R.git_extract("689c3c0b", [f"{R.D}/answers/day12599"], d)  # 本物の答え (お題を書いたあとに置く)
            want = {}
            for kind in ("season", "feeling"):
                for f in sorted((d / "prompts" / "day12599" / kind).glob("*.md")):
                    if exp4.HEAD not in f.read_text(encoding="utf-8"):
                        continue
                    af = d / "answers" / "day12599" / kind / f"{f.stem}.json"
                    a = json.loads(af.read_text(encoding="utf-8"))
                    a["take"] = exp4.OPTIONS[len(want) % 3]
                    a["take_why"] = "試し"
                    want[f.stem] = a["take"]
                    af.write_text(json.dumps(a, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(len(want), 36)
            r = run("season")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            st = json.loads((d / "state.json").read_text(encoding="utf-8"))
            x = st["era2"]["g7"]["exp4"]
            self.assertEqual({r_["name"]: r_["take"] for r_ in x["log"]}, want)
            took = {k for a in x["acts"] for row in a["rows"].values() for k in row if k in exp4.OPTIONS}
            self.assertEqual(took, {"村の蓄え", "よその家の倉"})
            rows = M.read_run("B0_t", d, 12599, 12599)
            self.assertEqual(len(rows), 36)
            self.assertEqual({r_["name"]: r_["take"] for r_ in rows}, want)
            self.assertTrue(all(r_["house"] and r_["store_days"] == 23 for r_ in rows))
            wr = M.world_rows("B0_t", d, 12599, 12630)
            self.assertGreater(wr["took_grain_蓄え"], 0)
        finally:
            shutil.rmtree(w)


class F_Measure(unittest.TestCase):
    def test_persistence(self):
        rows = []
        for i, pat in enumerate(([1, 1, 1, 1], [0, 0, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 1])):
            for k, t in enumerate(pat):
                rows.append({"run": "B0_1", "day": 12599 + 30 * k, "pid": f"p{i}", "T": bool(t), "model": "sonnet", "role": "代表",
                             "hungry": False, "kids": 1, "empty": True})
        for r in rows:
            prev = [x for x in rows if x["pid"] == r["pid"] and x["day"] < r["day"]]
            r["prev"] = prev[-1]["T"] if prev else None
        d, n, a = M.persistence(rows)
        self.assertEqual(n, 18)
        self.assertGreater(d, 0.5)
        perm = M.perm_persistence(rows, 200, random.Random(1))
        self.assertLess(sum(perm) / len(perm), d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
