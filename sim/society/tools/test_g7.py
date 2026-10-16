"""G7 (王と役所) の土台の試し (docs/society_phase/G7_design.md 6.1・6.2 の一部)。本物の data にはさわらない (写しは /tmp に作って消す)

  PYTHONUTF8=1 python3.13 sim/society/tools/test_g7.py            # 全部 (前のコードとくらべる試しは数分かかる)
  PYTHONUTF8=1 python3.13 sim/society/tools/test_g7.py A_Gate      # 一部だけ

- A: G7 に入るまで、新しい仕組みは何もしない (塩・鍵・関数の値・g7.py を読みこまない)
- B: 前のコード (G7 を足す前のコミット) と新しいコードで、同じ答えの季節 (G6・G5) と Society 1.0 の数日を回し、state・お題・乱数の塩が同じ
  (python3.13 と python3 (3.11) の両方。3.11 があれば)
- C: 第 4 部の終わりで止まる → status・who・resume・season が断る → next_part で G7 に入る (step.py を写しで動かす)
- D: 史実のずれの直し (G7 に入ってからだけ)・はじめの集落・地域の天気
- E: 止まるわけ (部の終わり・次の G を待つ・相談) と、ワークフローの止まる合図 (HOLD の行)
本物の state.json が G6 でないとき (もう G7 に入ったあと) は、G6 の state が要る試しをとばす。
"""
import copy
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
ROOT = SOC.parent.parent
sys.path.insert(0, str(SOC))
import era2  # noqa: E402
import region  # noqa: E402
import world  # noqa: E402

REAL = Path(os.environ.get("SOC_REAL_DATA") or (SOC / "data"))
NEW_SALTS = {47, 53, 59, 61, 67, 71, 79}
_TEXT = None


def real_text():
    """本物の state.json の中身 (読むだけ。1 回だけ読む)"""
    global _TEXT
    if _TEXT is None:
        _TEXT = (REAL / "state.json").read_text(encoding="utf-8")
    return _TEXT


def real_state():
    return json.loads(real_text())


def is_g6(st):
    return st.get("era") == "G6" and "g7" not in (st.get("era2") or {})


def tmpdir():
    return Path(tempfile.mkdtemp(prefix="g7s_test_", dir="/tmp"))


def sha(s):
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, str) else s).hexdigest()


def part_end(st):
    """写しの中だけで、第 4 部の終わり (町と記録がそろった) にする (step.py season の "end" と同じ手順)"""
    D = st["day"]
    subs = st["era2"].setdefault("substeps", [])
    for f, name in (("F3", "町"), ("F4", "物と数を分けて記す")):
        if not any(x["g"] == "G6" and x["f"] == f for x in subs):
            subs.append({"g": "G6", "f": f, "name": name, "day": D})
    r = era2.check(st)
    assert r == "end", r
    st["hold"] = True
    g = st["era2"]["g6"]["end"]
    world.log(st, "フェーズ", None, f"第 4 部の終わり (G6): 町 ({g['town']} 日目) と記録 ({g['record']} 日目) がそろった (先にそろったのは {g['first']})。Society 2.0 は G7 から続ける")
    return st


def g7_state(fill=0.0):
    """本物の G6 の state の写しを、第 4 部の終わりにしてから G7 に入れる (メモリの中だけ)"""
    import g7
    st = part_end(real_state())
    g7.enter(st, fill)
    return st


# ---------------------------------------------------------------- A
class A_Gate(unittest.TestCase):
    """G7 に入るまで、新しい仕組みは何もしない"""

    def test_salts(self):
        new = (era2.HINT_SALT, era2.WEATHER_SALT, era2.REGION_SALT, era2.SAMPLE_SALT, era2.CHANCE_SALT, era2.SICK_SALT, era2.FILL_SALT)
        self.assertEqual(set(new), NEW_SALTS)
        self.assertEqual(len({s % 31 for s in era2._SALTS}), len(era2._SALTS))
        self.assertEqual({s % 31 for s in new}, {16, 22, 28, 30, 5, 9, 17})
        src = "\n".join((SOC / f).read_text(encoding="utf-8") for f in ("era2.py", "g7.py", "region.py", "world.py"))
        used = {int(x) for x in re.findall(r"_rng\(state, (\d+)\)", src)}
        self.assertFalse(used & NEW_SALTS, "新しい塩は名前 (HINT_SALT など) で使う")

    def test_order(self):
        self.assertEqual(era2.ORDER2[-1], "G7")
        self.assertEqual(era2.NAMES2["G7"], "王と役所")
        self.assertLessEqual(set(era2.CRITERIA), set(era2.ORDER2))
        self.assertTrue(era2.era_at_least({"era": "G7"}, "G6") and era2.era_at_least({"era": "G7"}, "G3"))
        self.assertFalse(era2.era_at_least({"era": "G6"}, "G7"))
        self.assertEqual(era2.PART_END["G6"], 4)
        self.assertNotIn("G7", era2.PART_END)
        self.assertEqual([x[0] for x in era2.SUBSTEPS["G7"]], ["F1", "F2", "F3", "F4", "F5", "F6"])

    def test_world_g_at_least(self):
        old = ("G3", "G4", "G5", "G6")  # 前の書き方
        for e in ("F1", "F6", "G1", "G2", "G3", "G4", "G5", "G6", None):
            self.assertEqual(world._g_at_least({"era": e}, "G3"), e in old, e)
        self.assertTrue(world._g_at_least({"era": "G7"}, "G3"))
        self.assertTrue(world._g_at_least({"era": "G7"}, "G7"))
        self.assertFalse(world._g_at_least({"era": "G6"}, "G7"))

    def test_g6_helpers(self):
        st = real_state()
        if not is_g6(st):
            self.skipTest("本物の state が G6 でない")
        loaded = "g7" in sys.modules  # ほかの試しが先に読みこんでいなければ、ここでも読みこまないこと
        self.assertEqual(era2._whats(st), era2.WHATS)
        self.assertFalse(era2._fix(st))
        acts = era2.ACTS2 + era2.ACTS_G3 + era2.ACTS_G6 + ([era2.ACT_RECORD] if st["era2"]["g6"]["open"]["数え札"] else [])
        self.assertEqual(era2.acts2(st), acts)
        ha = sum(row.count("g") + row.count("h") for row in st["terrain"]) * world.CELL ** 2 / 10000
        self.assertEqual(era2.pasture_cap(st), int(round(ha * era2.PASTURE_PER_HA / 10)) * 10)
        ind = era2.indicators(st)
        self.assertFalse([k for k in ind if k.startswith("g7")])
        self.assertEqual(era2.hold_why(st), (None, ""))
        self.assertEqual(world._tree_days(st, {"day": st["day"] + 5}), 20)
        self.assertFalse(world._g7_fix(st))
        if not loaded:
            self.assertNotIn("g7", sys.modules, "G6 の state では g7.py を読みこまない")

    def test_no_g7_keys_in_g6(self):
        st = real_state()
        if not is_g6(st):
            self.skipTest("本物の state が G6 でない")
        e2 = st["era2"]
        for k in ("g7", "ahead", "cattle", "walls"):
            self.assertNotIn(k, e2)
        for o in e2["g6"]["others"]:
            self.assertFalse({"cell", "land", "cattle_f", "pots_f"} & set(o))
        for p in st["people"]:
            self.assertNotIn("eve_h", p)


# ---------------------------------------------------------------- B
RUNNER = r'''
import hashlib, json, sys
from pathlib import Path
code, state_f, ans, mode = sys.argv[1:5]
sys.path.insert(0, code)
import world
def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
st = json.loads(Path(state_f).read_text(encoding="utf-8"))
out = {}
if mode == "days":  # Society 1.0: era2 を読みこまずに 1 日ずつ
    for _ in range(3):
        world.simulate_day(st)
        world.evening(st, [], [], [])
    out["era2_loaded"] = "era2" in sys.modules
    out["prompts"] = ""
    out["check"] = None
    out["salts"] = []
else:
    import era2
    salts = []
    rng0 = era2._rng
    def rng(state, salt):
        salts.append(salt)
        return rng0(state, salt)
    era2._rng = rng
    def read(kind, who):
        d = Path(ans) / kind
        return {n: (d / f"{n}.json").read_text(encoding="utf-8") for n in who if (d / f"{n}.json").exists()}
    feels = read("feeling", era2.feelers(st))
    era2.apply_answers(st, read("season", era2.answerers(st)))
    era2.apply_feelings(st, feels)
    first = era2.simulate_season(st)
    st["era2"]["last_first"] = first
    out["check"] = repr(era2.check(st))
    who = set(era2.answerers(st))
    ps = [era2.season_prompt(st, p, first) for p in st["people"] if p["name"] in who]
    ps += [era2.feeling_prompt(st, next(q for q in st["people"] if q["name"] == n), first) for n in era2.feelers(st)]
    out["prompts"] = sha("\n\0".join(ps))
    out["n_prompts"] = len(ps)
    out["salts"] = sorted(set(salts))
out["state"] = sha(json.dumps(st, ensure_ascii=False, sort_keys=True))
out["g7_loaded"] = "g7" in sys.modules
out["day"] = st["day"]
print(json.dumps(out))
'''


def _git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)


def base_commit():
    """G7 のコードを足す前のコミット (g7.py を初めて足したコミットの親。まだコミットしていなければ HEAD)"""
    r = _git("log", "--diff-filter=A", "--format=%H", "--", "sim/society/g7.py")
    if r.returncode:
        return None
    hs = r.stdout.decode().split()
    return f"{hs[-1]}^" if hs else "HEAD"


def pythons():
    """くらべる Python (python3.13 と、ちがう版の python3 があれば両方)"""
    out = [sys.executable]
    p3 = shutil.which("python3")
    if p3:
        v = subprocess.run([p3, "-c", "import sys;print(sys.version_info[:2])"], capture_output=True, text=True).stdout.strip()
        if v != str(sys.version_info[:2]):
            out.append(p3)
    return out


class B_SameAsOld(unittest.TestCase):
    """前のコードと新しいコードで、G6・G5・Society 1.0 が同じに進む (state・お題・乱数の塩)"""

    @classmethod
    def setUpClass(cls):
        cls.base = base_commit()
        if cls.base is None:
            raise unittest.SkipTest("git が使えない")
        cls.tmp = tmpdir()
        old = cls.tmp / "old"
        old.mkdir()
        files = [f"sim/society/{f.name}" for f in sorted(SOC.glob("*.py")) if f.name not in ("g7.py", "region.py")]
        a = _git("archive", cls.base, "--", *files)
        if a.returncode:
            raise unittest.SkipTest(f"前のコードを取り出せない ({a.stderr.decode()[:200]})")
        subprocess.run(["tar", "-x", "-C", str(old)], input=a.stdout, check=True)
        cls.old = old / "sim" / "society"
        (cls.tmp / "runner.py").write_text(RUNNER, encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "tmp", None):
            shutil.rmtree(cls.tmp, ignore_errors=True)

    def run_both(self, state_f, ans, mode):
        res = {}
        for py in pythons():
            for name, code in (("old", self.old), ("new", SOC)):
                env = dict(os.environ, PYTHONUTF8="1", PYTHONHASHSEED="0")
                r = subprocess.run([py, str(self.tmp / "runner.py"), str(code), str(state_f), str(ans), mode], capture_output=True, text=True, env=env,
                                   cwd=str(self.tmp))
                self.assertEqual(r.returncode, 0, r.stderr[-2000:])
                res[(py, name)] = json.loads(r.stdout.strip().splitlines()[-1])
            o, n = res[(py, "old")], res[(py, "new")]
            for k in ("state", "prompts", "check", "salts", "day"):
                self.assertEqual(o[k], n[k], f"{mode} {py} {k}")
            self.assertFalse(n["g7_loaded"], "G7 の前は g7.py を読みこまない")
            self.assertFalse(set(n["salts"]) & NEW_SALTS, "G7 の前は新しい塩を引かない")
        return res

    def test_g6_season(self):
        st = real_state()
        if not is_g6(st):
            self.skipTest("本物の state が G6 でない")
        D = st["day"]
        days = sorted(int(p.name[3:]) for p in (REAL / "answers").glob("day*") if p.name[3:].isdigit() and int(p.name[3:]) <= D)
        if not days:
            self.skipTest("答えがない")
        ans = REAL / "answers" / f"day{days[-1]}"  # その日の答えがまだなければ、いちばん新しい答えをそのまま使う (どちらのコードにも同じ答え)
        f = self.tmp / "g6.json"
        f.write_text(real_text(), encoding="utf-8")
        res = self.run_both(f, ans, "season")
        self.assertGreater(res[(sys.executable, "new")]["n_prompts"], 0)

    def _git_state(self, commit):
        r = _git("show", f"{commit}:sim/society/data/state.json")
        if r.returncode:
            self.skipTest(f"{commit} の state がない")
        f = self.tmp / f"{commit}.json"
        f.write_bytes(r.stdout)
        return f

    def _git_answers(self, commit, day):
        d = self.tmp / f"ans{day}"
        a = _git("archive", commit, f"sim/society/data/answers/day{day}")
        if a.returncode:
            self.skipTest(f"{day} 日目の答えがない")
        subprocess.run(["tar", "-x", "-C", str(self.tmp)], input=a.stdout, check=True)
        shutil.move(str(self.tmp / "sim/society/data/answers" / f"day{day}"), d)
        return d

    def _commit(self, msg):
        r = _git("log", "--format=%H", "-F", f"--grep={msg}")
        hs = r.stdout.decode().split()
        if not hs:
            self.skipTest(f"「{msg}」のコミットがない")
        return hs[-1]

    def test_g5_season(self):
        c = self._commit("社会シミュレーション: 1709 日目から (季節)")  # このコミットの state は 1739 日目 (G5)
        f = self._git_state(c)
        ans = self._git_answers(self._commit("社会シミュレーション: 1739 日目から (季節)"), 1739)
        self.assertEqual(json.loads(f.read_text(encoding="utf-8"))["era"], "G5")
        self.run_both(f, ans, "season")

    def test_society1_days(self):
        f = self._git_state(self._commit("社会シミュレーション: 488 日目"))
        st = json.loads(f.read_text(encoding="utf-8"))
        self.assertTrue(st["era"].startswith("F"))
        res = self.run_both(f, self.tmp, "days")
        self.assertFalse(res[(sys.executable, "new")]["era2_loaded"], "Society 1.0 では era2 を読みこまない")


# ---------------------------------------------------------------- C
class C_NextPart(unittest.TestCase):
    """第 4 部の終わり → next_part (step.py を写しで動かす。記録の作り直しと古い年をしまうのは止める)"""

    @classmethod
    def setUpClass(cls):
        st = real_state()
        if not is_g6(st) or st["phase"] != "season" or st.get("hold"):
            raise unittest.SkipTest("本物の state が、季節の答えを待っている G6 でない")
        cls.tmp = tmpdir()
        cls.data = cls.tmp / "data"
        cls.data.mkdir()
        if (REAL / "archive").exists():
            shutil.copytree(REAL / "archive", cls.data / "archive")
        part_end(st)
        cls.D = st["day"]
        (cls.data / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        cls.env = dict(os.environ, SOC_DATA=str(cls.data), SOC_RECORDS="0", SOC_ARCHIVE="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "tmp", None):
            shutil.rmtree(cls.tmp, ignore_errors=True)

    def step(self, *args):
        return subprocess.run([sys.executable, str(SOC / "step.py"), *args], capture_output=True, text=True, env=self.env)

    def state_sha(self):
        return sha((self.data / "state.json").read_bytes())

    def test_1_part_end(self):
        before = self.state_sha()
        r = self.step("status")
        self.assertIn("第 4 部「町と文字」の終わり (G6)", r.stdout)
        w = self.step("who").stdout
        self.assertIn("HOLD part_end", w)
        self.assertIn("MODE season", w)
        self.assertRegex(w, r"(?m)^DAY \d+ season True$")
        r = self.step("resume")
        self.assertEqual(r.returncode, 3)
        self.assertIn("next_part", r.stdout)
        r = self.step("season")
        self.assertEqual(r.returncode, 3)
        self.assertRegex(r.stdout, r"(?m)^HOLD part_end$")
        self.assertEqual(self.state_sha(), before, "断ったときは何も変えない")

    def test_2_refusals(self):
        before = self.state_sha()
        r = self.step("next_part", "--fill", "2")
        self.assertEqual(r.returncode, 3)
        self.assertIn("--fill は 0 から 0.9 まで", r.stdout)
        a = self.data / "answers" / f"day{self.D:03d}" / "season"
        a.mkdir(parents=True)
        (a / "だれか.json").write_text("{}", encoding="utf-8")
        r = self.step("next_part")
        self.assertEqual(r.returncode, 3)
        self.assertIn("答えがもうある", r.stdout)
        shutil.rmtree(self.data / "answers")
        r = self.step("resume", "--fill", "0.1")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.state_sha(), before)

    def test_3_enter(self):
        r = self.step("next_part")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = json.loads((self.data / "state.json").read_text(encoding="utf-8"))
        D = self.D
        self.assertEqual(st["era"], "G7")
        self.assertFalse(st["hold"])
        self.assertEqual(st["day"], D)
        e = st["era_log"][-1]
        self.assertEqual((e["era"], e["day"], e["how"], e["fix_from"]), ("G7", D, "next_part", D + 1))
        g = st["era2"]["g7"]
        for k in ("start", "fix_from", "ends", "hold", "ask", "answer_day", "region", "offered", "role_days", "prev"):
            self.assertIn(k, g)
        self.assertEqual((g["start"], g["fix_from"], g["hold"], g["ask"]), (D, D + 1, None, "年" if (D + 1) % 30 == 0 else "寄る"))
        self.assertEqual(g["region"]["map_hash"], region.map_hash())
        self.assertIsNone(g["region"]["fill"], "--fill なしは、はじめの集落を置かない")
        for o in st["era2"]["g6"]["others"]:
            self.assertEqual(o["land"], region.land(tuple(o["cell"])))
            self.assertAlmostEqual(o["cattle_f"], o["people"] / 8)
        cells = [tuple(o["cell"]) for o in st["era2"]["g6"]["others"]]
        self.assertEqual(len(cells), len(set(cells)))
        ev = [x for x in st["events"] if x["day"] == D and x["type"] == "フェーズ"]
        self.assertEqual(ev[-1]["text"], "第 5 部「王と青銅」を始めた: フェーズ G7 (王と役所)")
        self.assertNotRegex(ev[-1]["text"], r"フェーズが .* に進んだ")
        self.assertEqual(st["era2"]["g6"]["end"]["day"], D, "G6 の終わりの記録は残す")
        # お題は書き直した (G7 の決まりの文が入る)
        ps = sorted((self.data / "prompts" / f"day{D:03d}" / "season").glob("*.md"))
        self.assertTrue(ps)
        txt = ps[0].read_text(encoding="utf-8")
        self.assertIn("守る・壁", txt)
        self.assertIn("3 年ほどで木の実の木が育つ", txt)
        w = self.step("who").stdout
        self.assertIn("PHASE G7", w)
        self.assertIn("MODE year", w)
        self.assertIn("HOLD none", w)
        app = json.loads((self.data / "app_data.json").read_text(encoding="utf-8"))
        self.assertEqual(app["era"]["era"], "G7")
        # 2 回目は断る
        before = self.state_sha()
        r = self.step("next_part")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(self.state_sha(), before)


# ---------------------------------------------------------------- D
class D_Fixes(unittest.TestCase):
    """史実のずれの直し (G7 に入ってからだけ)・はじめの集落・地域の天気 (メモリの中の写し)"""

    @classmethod
    def setUpClass(cls):
        if not is_g6(real_state()):
            raise unittest.SkipTest("本物の state が G6 でない")
        import g7
        cls.g7 = g7
        cls.base = g7_state()

    def st(self):
        return copy.deepcopy(self.base)

    def test_fill_and_known(self):
        import g7
        a, b = g7_state(0.1), g7_state(0.1)
        self.assertEqual(json.dumps(a["era2"]["g6"]["others"], sort_keys=True), json.dumps(b["era2"]["g6"]["others"], sort_keys=True), "同じ state から同じ集落")
        others = a["era2"]["g6"]["others"]
        fl = a["era2"]["g7"]["region"]["fill"]
        self.assertEqual(fl["share"], 0.1)
        self.assertGreaterEqual(sum(o["people"] for o in others), round(region.k_total() * 0.1))
        cells = [tuple(o["cell"]) for o in others]
        self.assertEqual(len(cells), len(set(cells)))
        for o in others:
            c = tuple(o["cell"])
            self.assertNotEqual(c, region.VILLAGE)
            if o["id"] in fl["placed"]:
                self.assertGreater(region.dist(c, region.VILLAGE), region.FILL_NEAR)
                self.assertEqual(o["known"] is not None, region.dist(c, region.VILLAGE) <= region.KNOWN_NEAR)
                self.assertTrue(0.3 * region.cap(c) - 1 <= o["people"] <= 0.6 * region.cap(c) + 1)
                self.assertEqual(o["days"], region.days(c))
        self.assertEqual(g7_state(0.0)["era2"]["g7"]["region"]["fill"], None)

    def test_region_numbers(self):
        self.assertEqual(region.k_total(), 5000)
        self.assertEqual(region.k_total(skip=()), 5120)
        n = {k: sum(r.count(k) for r in region.GRID) for k in region.K}
        self.assertEqual(n, {"r": 11, "a": 35, "w": 3, "h": 8, "s": 64})
        self.assertEqual(region.place_known("南", 1, set()), (5, 7))
        self.assertEqual(region.place_known("北", 2, set()), (5, 1))
        self.assertEqual(region.place_known("西", 2, set()), (1, 5))
        self.assertEqual(region.direction((9, 1)), "北東")
        self.assertEqual(region.days((9, 1)), 2)

    def test_weather(self):
        z, bad_r, bad = region.weather(random.Random(1), [("V0", (5, 5)), ("N1", (5, 7))])
        self.assertEqual((z, bad_r, bad), region.weather(random.Random(1), [("V0", (5, 5)), ("N1", (5, 7))]))
        st = self.st()
        g = self.g7
        st["day"] = (st["day"] // era2.YEAR + 2) * era2.YEAR - 1  # 次の年の最後の日 (まだ引いていない年)
        w1 = g._weather(st)
        w2 = g._weather(st)
        self.assertIs(w1, w2, "同じ年に 2 回は引かない")
        self.assertEqual(len(st["era2"]["g7"]["region"]["weather_log"]), len(self.base["era2"]["g7"]["region"]["weather_log"]) + 1)
        # 村が悪い年は、草で養えるヤギの数が 0.8 倍
        w1["bad"] = ["V0"]
        st["era2"]["g7"]["region"]["weather_log"][-1]["bad"] = ["V0"]
        st["day"] += 1
        cap = int(round(sum(row.count("g") + row.count("h") for row in st["terrain"]) * world.CELL ** 2 / 10000 * era2.PASTURE_PER_HA / 10)) * 10
        self.assertEqual(era2.pasture_cap(st), int(round(cap * 0.8 / 10)) * 10)
        self.assertEqual(g.bad_set(dict(st, day=st["day"] - 1)), {"V0"})

    def test_tree_days_and_evening(self):
        st = self.st()
        fx = st["era2"]["g7"]["fix_from"]
        self.assertEqual(world._tree_days(st, {"day": fx}), world.TREE_DAYS7)
        self.assertEqual(world._tree_days(st, {"day": fx - 1}), 20)
        p = era2.adults(st)[0]
        p["today"] = {"tree_got": 40}
        p["fatigue"] = 0.1
        self.g7.evening_cost(st, {p["name"]: 30})
        self.assertEqual(p["eve_h"], 3.0)
        self.assertEqual(p["fatigue"], 0.25)

    def test_pots_decay(self):
        st = self.st()
        e2 = st["era2"]
        grain = sum(f["kcal"] for f in st["store"] if f["kind"] == "草の種") / era2.GRAIN
        e2["house"] = {}
        e2["pots"] = 10 ** 6  # 全部土器の中
        before = grain
        era2._storage_season(st, 1.0)
        after = sum(f["kcal"] for f in st["store"] if f["kind"] == "草の種") / era2.GRAIN
        self.assertAlmostEqual(before - after, int(before * era2.POT_DECAY), delta=1)
        ev = st["events"][-1] if st["events"][-1]["type"] == "虫" else next(e for e in reversed(st["events"]) if e["type"] == "虫")
        self.assertIn("傷んだ", ev["text"])

    def test_vacant(self):
        st = self.st()
        e2 = st["era2"]
        h = "だれもいない家"
        e2.setdefault("house", {})[h] = {"store": [{"kind": "草の種", "kcal": 800, "day": 1}], "keep": True}
        e2["goats"].append({"id": 999999, "sex": "メス", "born": 1, "owner": h})
        n = len(st["store"])
        self.g7.vacant(st)
        self.assertEqual(e2["house"][h]["store"], [])
        self.assertIsNone(e2["goats"][-1]["owner"])
        self.assertEqual(len(st["store"]), n + 1)
        self.assertEqual(st["events"][-1]["type"], "受けつぎ")
        k = len(st["events"])
        self.g7.vacant(st)
        self.assertEqual(len(st["events"]), k, "2 回目は何もしない")

    def test_milk(self):
        st = self.st()
        e2 = st["era2"]
        mothers = sum(1 for g in e2["goats"] if g["sex"] == "メス" and st["day"] - g["born"] >= era2.YEAR)
        ads = era2.adults(st)[:3]
        for p in ads:
            p["today"] = {"activity": "ヤギの世話"}
        for p in era2.adults(st)[3:]:
            p["today"] = {"activity": "採集"}
        kid = next((c for c in era2.children(st) if self.g7.kid_age(c)), None)
        if kid:
            e2["g7"]["kid_jobs"] = {kid["name"]: "ヤギの世話"}
        m = self.g7.milk_shares(st, "春")
        self.assertEqual(sum(m.values()), 3 * mothers, "乳の合計は母ヤギの数で決まる")
        if kid:
            self.assertLessEqual(m[kid["name"]], m[ads[0]["name"]])
        self.assertEqual(self.g7.milk_shares(st, "秋"), {})

    def test_eat_young_males(self):
        st = self.st()
        e2 = st["era2"]
        e2["jobs"] = {"x": {"eat_goat": 1}}
        males = [g for g in e2["goats"] if g["sex"] == "オス"]
        if not males:
            self.skipTest("オスのヤギがいない")
        young = max(males, key=lambda g: g["born"])
        era2._eat_goats(st)
        self.assertNotIn(young["id"], {g["id"] for g in e2["goats"]})
        g6 = real_state()
        g6["era2"]["jobs"] = {"x": {"eat_goat": 1}}
        old = min((g for g in g6["era2"]["goats"] if g["sex"] == "オス"), key=lambda g: g["born"])
        era2._eat_goats(g6)
        self.assertNotIn(old["id"], {g["id"] for g in g6["era2"]["goats"]}, "G6 は前のまま、年上のオスから")

    def test_kids(self):
        st = self.st()
        kid = next((c for c in era2.children(st) if self.g7.kid_age(c)), None)
        small = next((c for c in era2.children(st) if c["age"] < 12 and c.get("household") == (kid or {}).get("household")), None)
        if not kid:
            self.skipTest("12〜14 歳の子がいない")
        rep = next(p for p in era2.adults(st) if p.get("household") == kid["household"])
        self.g7.new_season(st)
        fam = {kid["name"]: {"activity": "畑仕事"}}
        if small:
            fam[small["name"]] = {"activity": "畑仕事"}
        self.g7.kid_jobs(st, rep, fam)
        self.assertEqual(st["era2"]["g7"]["kid_jobs"], {kid["name"]: "畑仕事"}, "12〜14 歳だけ")
        self.g7.kid_jobs(st, rep, {kid["name"]: {"activity": "採集"}})
        self.assertEqual(st["era2"]["g7"]["kid_jobs"], {kid["name"]: "畑仕事"}, "畑仕事とヤギの世話だけ")
        n = len(st["events"])
        self.g7.kids_day(st, "冬", random.Random(1), {})
        self.assertTrue(any(e["type"] == "畑仕事" and e["who"] == kid["name"] for e in st["events"][n:]))
        self.assertEqual(st["era2"]["g7"]["season_days"][kid["name"]]["畑仕事"], 1)

    def test_births(self):
        class R(random.Random):
            def random(self):
                return 0.09  # 0.08 と 0.10 のあいだ

        def births(st):
            orig = era2._rng
            era2._rng = lambda state, salt: R(salt)
            try:
                n = len(st["events"])
                era2._season_end(st, 1.0)
            finally:
                era2._rng = orig
            return sum(1 for e in st["events"][n:] if e["type"] == "生まれる")

        g6 = real_state()
        st = self.st()
        for s in (g6, st):
            s["era2"]["step_day"] = s["day"] + 1
            s["era2"]["tended_run"] = 99
        self.assertGreater(births(g6), 0, "G6 は 0.10")
        self.assertEqual(births(st), 0, "G7 は 0.08")

    def test_ledger(self):
        st = self.st()
        e2, g = st["era2"], st["era2"]["g6"]
        if not g["open"].get("板"):
            self.skipTest("粘土の板が使えない")
        self.assertEqual(era2._whats(st), era2.WHATS + ("配給", "働いた日", "家畜"))
        keeper = era2.adults(st)[0]["name"]
        self.g7.new_season(st)
        for p in era2.adults(st):
            self.g7.count_day(st, p["name"], "採集")
        g["keep_days"] = {keeper: 30}
        g["jobs"] = {keeper: {"activity": "記録をつける", "what": ["配給", "働いた日", "家畜"], "how": "板"}}
        e2["step_day"] = st["day"] - 29
        era2._g6_records(st, 1.0)
        led = e2["g7"]["ledger"][-1]
        self.assertEqual(led["day"], st["day"])
        self.assertEqual({b["what"] for b in led["books"]}, {"働いた日", "家畜"} | ({"配給"} if any(v[1] for v in e2["g5"].get("flow", {}).values()) else set()))
        txt = self.g7.text(st, era2.adults(st)[0])
        self.assertIn("板の帳簿", txt)

    def test_prompt_fix_text(self):
        st = self.st()
        p = next(q for q in st["people"] if q["name"] in set(era2.answerers(st)))
        t = era2.season_prompt(st, p, st["era2"]["last_first"])
        for old, new in self.g7.FIX_TEXT[:3]:
            self.assertNotIn(old, t)
            self.assertIn(new, t)
        self.assertIn("守る・壁", t)
        self.assertIn("守る", t.split("2. この季節の主な仕事を決める (job)。仕事は ")[1].split("\n")[0])
        self.assertEqual(st["era2"]["g7"]["offered"], {"guard": st["day"]})


# ---------------------------------------------------------------- E
class E_Hold(unittest.TestCase):
    """止まるわけ (部の終わり・次の G を待つ・相談) と、ワークフローの止まる合図"""

    def setUp(self):
        if not is_g6(real_state()):
            self.skipTest("本物の state が G6 でない")

    def test_g6_end_once(self):
        st = part_end(real_state())
        self.assertEqual(era2.hold_why(st)[0], "part_end")
        st["hold"] = False
        self.assertFalse(era2.check(st), "G6 の終わりは一度だけ")

    def test_wait_and_phase(self):
        import g7
        st = g7_state()
        g = st["era2"]["g7"]
        st["era2"].setdefault("substeps", []).extend({"g": "G7", "f": f, "name": f, "day": st["day"]} for f in ("F3", "F4"))
        g["tribute2_day"] = st["day"]
        g["reached"] = {"F3": st["day"], "F4": st["day"]}
        self.assertEqual(era2.check(st), "wait")
        st["hold"] = True
        self.assertEqual(era2.hold_why(st)[0], "wait")
        self.assertFalse(era2.check(st), "待ちは一度だけ")
        # 台本の G8 (条件だけの G) を足すと、フェーズが進む
        saved = (list(era2.ORDER2), dict(era2.NAMES2), dict(era2.CRITERIA))
        try:
            era2.ORDER2.append("G8")
            era2.NAMES2["G8"] = "試しの G8"
            era2.CRITERIA["G8"] = ("試し", lambda i: True)
            st2 = g7_state()
            st2["era2"].setdefault("substeps", []).extend({"g": "G7", "f": f, "name": f, "day": st2["day"]} for f in ("F3", "F4"))
            st2["era2"]["g7"]["tribute2_day"] = st2["day"]
            st2["era2"]["g7"]["reached"] = {"F3": 1, "F4": 1}
            self.assertIs(era2.check(st2), True)
            self.assertEqual(st2["era"], "G8")
            st2["hold"] = True
            self.assertEqual(era2.hold_why(st2)[0], "phase")
            st2["hold"] = False
            self.assertEqual(era2.check(st2), "end", "G8 は第 5 部の終わり")
            st2["hold"] = True
            self.assertEqual(era2.hold_why(st2)[0], "part_end")
            self.assertFalse(era2.check(st2), "部の終わりは一度だけ")
            # 待ちから next_part で G8 に入る
            self.assertEqual(g7.enter_next(st), "G8")
            self.assertFalse(st["hold"])
            self.assertEqual(st["events"][-1]["text"], "フェーズ G8 (試しの G8) を始めた")
        finally:
            era2.ORDER2[:] = saved[0]
            era2.NAMES2.clear()
            era2.NAMES2.update(saved[1])
            era2.CRITERIA.clear()
            era2.CRITERIA.update(saved[2])

    def test_consult(self):
        st = g7_state()
        g = st["era2"]["g7"]
        st["day"] = g["start"] + 60 * era2.YEAR + (era2.YEAR - 1 - g["start"] % era2.YEAR)  # 60 年あとの年の最後の日
        self.assertEqual(era2.check(st), "consult")
        st["hold"] = True
        self.assertEqual(era2.hold_why(st)[0], "consult")
        st["hold"] = False
        self.assertFalse(era2.check(st), "同じわけでは一度だけ")
        g["stall"] = {"c1": {"best": 1, "since": (st["day"] + 1) // era2.YEAR - 16}}
        self.assertEqual(era2.check(st), "consult")
        self.assertFalse(era2.check(st))
        st["day"] -= 1  # 年の終わりでない日は見ない
        g["stall"]["c2"] = {"best": 0, "since": 0}
        self.assertFalse(era2.check(st))

    def test_workflow_regex(self):
        node = shutil.which("node")
        js = (SOC / "tools" / "society2_seasons_workflow.js").read_text(encoding="utf-8")
        m = re.search(r"match\((/\^HOLD [^\n]*?/m)\)", js)
        self.assertTrue(m, "ワークフローに HOLD の合図がある")
        self.assertIn("Society 2\\.0 が終わった", js, "前の合図も残す")
        if not node:
            self.skipTest("node がない")
        lines = ["* 掟「…仕事を止めて相談する」が採用された", "* 掟「第 5 部の終わり」が採用された", "* 掟「HOLD consult」が採用された"]
        code = (f"const re = {m.group(1)};\n"
                f"const bad = {json.dumps(chr(10).join(lines), ensure_ascii=False)};\n"
                "const good = bad + '\\nHOLD consult\\nseason exit=0\\n';\n"
                "console.log(JSON.stringify([bad.match(re), (good.match(re) || [])[1]]));")
        r = subprocess.run([node, "-e", code], capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout), [None, "consult"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
