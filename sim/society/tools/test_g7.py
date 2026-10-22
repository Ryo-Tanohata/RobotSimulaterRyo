"""G7 (王と役所) の土台の試し (docs/society_phase/G7_design.md 6.1・6.2 の一部)。本物の data にはさわらない (写しは /tmp に作って消す)

  PYTHONUTF8=1 python3.13 sim/society/tools/test_g7.py            # 全部 (前のコードとくらべる試しは数分かかる)
  PYTHONUTF8=1 python3.13 sim/society/tools/test_g7.py A_Gate      # 一部だけ

- A: G7 に入るまで、新しい仕組みは何もしない (塩・鍵・関数の値・g7.py を読みこまない)
- B: 前のコード (G7 を足す前のコミット) と新しいコードで、同じ答えの季節 (G6・G5) と Society 1.0 の数日を回し、state・お題・乱数の塩が同じ
  (python3.13 と python3 (3.11) の両方。3.11 があれば)
- C: 第 4 部の終わりで止まる → status・who・resume・season が断る → next_part で G7 に入る (step.py を写しで動かす)
- D: 史実のずれの直し (G7 に入ってからだけ)・はじめの集落・地域の天気
- E: 止まるわけ (部の終わり・次の G を待つ・相談) と、ワークフローの止まる合図 (HOLD の行)
- F: 年 1 回の答えと見本の家 (4.A・4.F の 8): 見本の家の数と組・選び直し・手本・年の答えの読み方・広げた票・方針・ask・お題・欄が初めて出た日・
  ワークフローの year の形 (node)・「全部の家を見本にし、毎季節寄る」G7 が、同じ答えの G6 と同じ世界になる (6.2 の「同じになる試し」。数分かかる)
- G (SOC_SLOW=1 のときだけ。数分): 写しで step.py を回す (年の集まり → 答えのない季節) と、記録 (1 行 = 1 季節・decided_by・is_sample)
本物の state.json が G6 でないとき (もう G7 に入ったあと) は、G6 の state が要る試しをとばす。
"""
import copy
import hashlib
import json
import math
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
out["g7_loaded"] = any(m in sys.modules for m in ("g7", "region", "hints", "yardstick"))
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
        files = [f"sim/society/{f.name}" for f in sorted(SOC.glob("*.py")) if f.name not in ("g7.py", "region.py", "hints.py", "yardstick.py")]  # G7 で足したファイルは前のコードにない
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
        self.assertEqual(era2._whats(st), era2.WHATS + ("取り立て", "掟", "配給", "働いた日", "家畜"))  # 取り立て・掟は 4.F (part B で足した)
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
        self.assertEqual(st["era2"]["g7"]["offered"]["guard"], st["day"])  # ほかの欄は F_Year.test_offered


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
        # 2026-10-17: 前の合図 (「Society 2.0 が終わった」「フェーズが … に進んだ」) は、step.py の G6 の終わりの文と同じコミットで外した
        self.assertNotIn("Society 2\\.0 が終わった", js)
        self.assertNotIn("フェーズが .* に進んだ", js)
        step = (SOC / "step.py").read_text(encoding="utf-8")
        self.assertNotIn("Society 2.0 が終わった。町", step, "G6 の第 4 部の終わりの文は「Society 2.0 が終わった」と書かない")
        for code in ("part_end", "phase", "wait", "entrance", "consult"):
            self.assertIn(code, era2.HOLD_CODES)
        if not node:
            self.skipTest("node がない")
        lines = ["* 掟「…仕事を止めて相談する」が採用された", "* 掟「第 5 部の終わり」が採用された", "* 掟「HOLD consult」が採用された"]
        code = (f"const re = {m.group(1)};\n"
                f"const bad = {json.dumps(chr(10).join(lines), ensure_ascii=False)};\n"
                "const good = bad + '\\nHOLD consult\\nseason exit=0\\n';\n"
                "console.log(JSON.stringify([bad.match(re), (good.match(re) || [])[1]]));")
        r = subprocess.run([node, "-e", code], capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout), [None, "consult"])


# ---------------------------------------------------------------- F
YEAR_SRC = {"年の答え (自分)", "年の答え (代表が割り振った)", "年の答え (代表と同じ仕事)", "見本から広げた", "決まり (前の年と同じ)", "加わった季節",
            "答えなし (前と同じ)", "自分", "代表が割り振った", "代表と同じ仕事"}


def add_law(st, text="試しの掟"):
    """提案中の掟を 1 本足す (写しの中だけ)"""
    l = {"id": f"L{st['next_law']}", "text": text, "proposer": era2.adults(st)[0]["name"], "day": st["day"], "status": "提案", "votes": {},
         "because": [], "label": "知識の再現の疑い", "changed": st["day"]}
    st["next_law"] += 1
    st["laws"].append(l)
    return l


def year_answer(seas, **kw):
    """台本の年の答え (季節ごとの予定と 1 年の方針)"""
    a = {"say": [], "year": {s: {"job": {"activity": "採集", "place": "camp"}, "pick": 0, "plant": 0, "harvest": 0} for s in seas}, "feeling": "試しの気持ち"}
    a.update(kw)
    return json.dumps(a, ensure_ascii=False)


def to_year_end(st):
    """写しの日を、次の年の最後の日にする (年の集まりの答えを読む試しだけ。世界は進めない)"""
    st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
    st["era2"]["g7"]["ask"] = "年"
    return st


class F_Year(unittest.TestCase):
    """年 1 回の答えと見本の家 (4.A。メモリの中の写し。世界は進めない)"""

    @classmethod
    def setUpClass(cls):
        if not is_g6(real_state()):
            raise unittest.SkipTest("本物の state が G6 でない")
        import g7
        cls.g7 = g7
        cls.base = g7_state()

    def st(self):
        return copy.deepcopy(self.base)

    def test_size(self):
        self.assertEqual([self.g7.sample_size(h) for h in (5, 12, 13, 30, 42, 60, 100)], [5, 12, 12, 12, 17, 24, 25])

    def test_choose(self):
        st, g7 = self.st(), self.g7
        G, homes = st["era2"]["g7"], era2._homes(st)
        must = {h for h, v in G["sample"].items() if v["must"]}
        self.assertEqual(len(G["sample"]), max(g7.sample_size(len(homes)), len(must)))
        self.assertEqual(set(G["cells"]), set(homes))
        for c in set(G["cells"].values()):
            hs = [h for h in homes if G["cells"][h] == c]
            if len(hs) <= 2:
                self.assertTrue(set(hs) <= must, c)
            else:
                self.assertTrue(any(h in G["sample"] for h in hs), f"{c} に見本がある")
        roles = {p["household"] for p in era2.adults(st) if p["name"] in g7.role_people(st)}
        self.assertTrue(roles and roles <= must, "役の人の家はいつも見本")
        for c, w in G["weights"].items():
            rest = [h for h in homes if G["cells"][h] == c and h not in must]
            self.assertAlmostEqual(w, len(rest) / sum(1 for h in rest if h in G["sample"]), places=2)
        again = self.st()
        g7.choose(again, era2._rng(again, era2.SAMPLE_SALT))
        self.assertEqual(again["era2"]["g7"]["sample"], G["sample"], "同じ state から同じ見本")
        # まとめ役の家はいつも入る
        lead = next(p for p in era2.adults(st) if p["household"] not in G["sample"])
        st["era2"]["g5"]["leader"] = lead["name"]
        g7.choose(st, random.Random(3))
        self.assertIn(lead["household"], G["sample"])
        self.assertTrue(G["sample"][lead["household"]]["must"])
        self.assertIn(lead["name"], era2.answerers(st), "まとめ役は答える")

    def test_small_village(self):
        st, g7 = self.st(), self.g7
        homes = era2._homes(st)[:12]
        for p in st["people"]:
            if p["alive"] and p.get("household") not in homes:
                p["alive"] = False
        g7.choose(st, random.Random(1))
        g7.donors(st)
        self.assertEqual(set(st["era2"]["g7"]["sample"]), set(era2._homes(st)), "12 家以下なら全部")
        self.assertEqual(st["era2"]["g7"]["donor"], {})

    def test_rotation(self):
        st, g7 = self.st(), self.g7
        G, D = st["era2"]["g7"], st["day"]
        old = copy.deepcopy(G["sample"])
        for v in G["sample"].values():
            if not v["must"]:
                v["since"] = D + 1 - 3 * era2.YEAR  # 3 年続いた
        g7.choose(st, random.Random(7))
        new = G["sample"]
        for h, v in new.items():
            if not v["must"]:
                self.assertNotIn(h, old, "3 年続いた家は外れ、一度も見本になっていない家が先")
                self.assertEqual(v["since"], D)
        for h in old:
            if h not in new:
                self.assertEqual(G["sample_hist"][h], D)
        # 次は、見本だったのがいちばん前の家から (一度もなっていない家がなくなったら)
        self.assertEqual(len(new), len(old))

    def test_donors(self):
        st, g7 = self.st(), self.g7
        G = st["era2"]["g7"]
        homes = era2._homes(st)
        self.assertEqual(set(G["donor"]), set(homes) - set(G["sample"]))
        n_ad = {h: sum(1 for p in era2.adults(st) if p["household"] == h) for h in homes}
        for h, d in G["donor"].items():
            self.assertIn(d, G["sample"])
            self.assertEqual(G["cells"][d], G["cells"][h])
            best = min(abs(n_ad[s] - n_ad[h]) for s in G["sample"] if G["cells"][s] == G["cells"][h])
            self.assertEqual(abs(n_ad[d] - n_ad[h]), best, "大人の数がいちばん近い家")
        before = dict(G["donor"])
        self.assertEqual(g7.donors(st), before, "乱数を使わない")

    def test_cells_tie(self):
        st, g7 = self.st(), self.g7
        G = st["era2"]["g7"]
        reps = g7._rep_of(st)
        h = next(h for h in era2._homes(st) if sum(1 for p in era2.adults(st) if p["household"] == h) >= 2)
        rep = reps[h]
        other = next(p["name"] for p in era2.adults(st) if p["household"] == h and p["name"] != rep)
        G["past"] = [{"day": st["day"], "season": "冬", "days": {rep: {"採集": 10}, other: {"畑仕事": 10}}, "home": {}}]
        self.assertTrue(g7._cells(st)[h].endswith("×集める"), "日数が同じなら代表の仕事の組")
        G["past"] = [{"day": st["day"], "season": "冬", "days": {other: {"採集": 5, "土器づくり": 5}}, "home": {}}]
        self.assertTrue(g7._cells(st)[h].endswith("×作る"), "代表でも決まらなければ 作る → 畑 → 集める")

    def test_plan_and_part(self):
        st, g7 = self.st(), self.g7
        a = {"year": {"夏": {"job": "採集", "sow": 5}, "秋": {"job": {"activity": "畑仕事"}, "sow": 300}, "冬": "x"},
             "feast": ["秋", "春"], "seal_store": "冬と春", "judge_rule": "つぐなう", "accept_rule": {"よその群れ": True, "ほかの村から": "受け入れない"},
             "trade_rule": {"交換": "村", "貸して": False, "max": "500 つかみ", "not": ["N2", "3"]}, "call": {"activity": "畑仕事", "when": "冬"}}
        pl = g7._plan(a, st["day"], "夏")
        self.assertNotIn("sow", pl["year"]["夏"], "秋でない sow は読まない")
        self.assertEqual(pl["year"]["秋"]["sow"], 300)
        self.assertNotIn("冬", pl["year"])
        self.assertEqual(pl["policy"], {"feast": ["秋", "春"], "seal_store": ["冬", "春"], "judge_rule": "つぐなう",
                                        "accept_rule": {"よその群れ": True, "ほかの村から": False},
                                        "trade_rule": {"交換": "村", "貸して": False, "max": 500, "not": ["N2", "N3"]},
                                        "call": {"activity": "畑仕事", "when": "冬"}})
        w = g7._part(st, pl, "冬")
        self.assertTrue(w["_missing"], "季節が抜けた答えは決まりで")
        self.assertEqual((w["feast"], w["seal_store"]), (False, True))
        f = g7._part(st, pl, "秋", {"say": [{"to": "みんな", "text": "x"}], "votes": [], "call": "畑仕事"})
        self.assertEqual((f["sow"], f["feast"], f["call_when"]), (300, True, "冬"))

    def test_copy(self):
        st, g7 = self.st(), self.g7
        G = st["era2"]["g7"]
        reps = g7._rep_of(st)
        size = {h: len(era2.family(st, reps[h])) for h in era2._homes(st)}
        h, d = next((h, d) for h, d in sorted(G["donor"].items()) if size[h] >= 2 and size[d] >= 2)
        rep, drep = reps[h], reps[d]
        d2 = era2.family(st, drep)[1]["name"]
        da = {"job": {"activity": "交換に行く", "place": "camp", "to": "N1", "then": "畑仕事", "house": True, "with": [drep], "why": "x"},
              "family": {d2: {"activity": "ヤギの世話", "place": "camp", "why": "y"}}, "pick": 7, "eat_goat": 1, "say": [{"to": "みんな", "text": "z"}],
              "votes": [{"id": "L0", "agree": True, "reason": "r"}], "trade": {"T1": "家", "T2": "村"}, "proposal": {"text": "p"}, "feeling": "f", "leave": True}
        G["prev"][h] = {}
        common = {"activity": "採集", "place": "camp", "with": []}
        a = g7._copy(st, h, rep, d, drep, da, "春", common)
        self.assertEqual(a["job"], {"activity": "畑仕事", "place": "camp", "with": []}, "前の年にしていない交換に行くは、then に")
        fam = era2.family(st, rep)
        self.assertEqual(a["family"][fam[1]["name"]]["activity"], "ヤギの世話", "2 番目の大人は、手本の 2 番目の大人の仕事")
        self.assertEqual((a["pick"], a["eat_goat"]), (7, 1))
        self.assertEqual(a["votes"], [{"id": "L0", "agree": True}], "票はまねる。理由はまねない")
        self.assertEqual(a["trade"], {"T2": "村"}, "家の物で受けるのは、答えた家だけ")
        for k in ("say", "proposal", "feeling", "leave", "knowledge"):
            self.assertNotIn(k, a)
        G["prev"][h] = {"春": {"交換に行く": 30}}
        a = g7._copy(st, h, rep, d, drep, da, "春", common)
        self.assertEqual(a["job"]["activity"], "交換に行く")
        self.assertNotIn("house", a["job"])
        self.assertEqual(a["job"]["with"], [])

    def answers(self, st, seas, **kw):
        return {n: year_answer(seas, **kw) for n in era2.answerers(st)}

    def test_apply_year(self):
        st, g7 = self.st(), self.g7
        G = st["era2"]["g7"]
        l = add_law(st)
        sea = world.season(st["day"] + 1)
        ans = self.answers(st, [sea], votes=[{"id": l["id"], "agree": True}], judge_rule="ゆるす")
        quiet = next(n for n in era2.answerers(st) if G["sample"][next(p for p in era2.adults(st) if p["name"] == n)["household"]]["must"] is False)
        del ans[quiet]  # 答えない見本の家がひとつ
        feel = {p["name"]: p.get("feeling") for p in era2.adults(st)}
        g7.apply_year(st, ans)
        n = len(era2.adults(st))
        self.assertEqual(l["status"], "採用")
        qh = next(p for p in era2.adults(st) if p["name"] == quiet)["household"]
        q_ad = [p["name"] for p in era2.adults(st) if p["household"] == qh]
        txt = next(e["text"] for e in st["events"] if e["type"] == "掟" and "試しの掟" in e["text"])
        self.assertIn(f"/ {n})", txt)
        yes = int(re.search(r"賛成 (\d+)", txt).group(1))
        self.assertEqual(yes, n - len(q_ad), "見本の答えが手本でみんなに広がる (答えなかった家の大人だけ数えない)")
        src = G["src"]
        self.assertEqual(set(src), {p["name"] for p in era2.adults(st)})
        self.assertLessEqual(set(src.values()), YEAR_SRC)
        self.assertEqual(sum(1 for v in src.values() if v == "年の答え (自分)"), len(ans))
        self.assertTrue(all(src[x] == "答えなし (前と同じ)" for x in q_ad))
        for h, d in G["step"]["donor"].items():
            self.assertNotEqual(d, qh, "答えなかった見本の家はまねない")
        for p in era2.adults(st):
            if p["name"] not in ans:
                self.assertEqual(p.get("feeling"), feel[p["name"]], "答えなかった人の気持ちは変えない")
        self.assertEqual(G["step"]["answered"], sorted(ans))
        self.assertEqual(G["answer_day"], st["day"])

    def test_year_names(self):
        st, g7 = to_year_end(self.st()), self.g7
        ans = self.answers(st, list(g7.SEASONS), year_name="試しの名前")
        g7.apply_year(st, ans)
        e = next(e for e in reversed(st["events"]) if e["type"] == "年の名前")
        n = len(era2.adults(st))
        self.assertIn(f"大人 {n} 人分 / 大人 {n} 人", e["text"], "年の名前は、手本として受け持つ家の大人まで数える")
        self.assertEqual(st["era2"]["year_names"][-1]["name"], "試しの名前")

    def test_apply_plan(self):
        st, g7 = to_year_end(self.st()), self.g7
        e2, G = st["era2"], st["era2"]["g7"]
        ans = self.answers(st, list(g7.SEASONS), judge_rule="ゆるす", trade_rule={"交換": "村", "貸して": "村", "max": 5000, "not": ["N2"]},
                           accept_rule={"よその群れ": True}, feast=["冬"], seal_store=["秋"])
        g7.apply_year(st, ans)
        st["day"] += 30  # 夏の終わり (秋のはじめは答えのない季節)
        G["ask"] = g7.ask_next(st)
        self.assertIsNone(G["ask"])
        homes = era2._homes(st)
        g5 = e2["g5"]
        for i in range(3):
            g5["disputes"].append({"id": f"M{900 + i}", "kind": "倉", "from": homes[i], "against": homes[i + 1], "day": st["day"] - 30, "harm": 10,
                                   "what": "試し", "because": [], "status": era2.OPEN, "event": 0})
        for i, (o, n) in enumerate((("N1", 10), ("N2", 10), ("N3", 6000))):  # 受ける / 相手にしない村 / 上限をこえる
            e2["g6"]["offers"].append({"kind": "貸して", "give": {}, "want": {"草の種": n}, "id": f"T{900 + i}", "other": o, "day": st["day"], "goats_in": [],
                                       "mem": {"village": 1.0, "other": 1.0}})
        e2["visitors"] = [{"name": "テスオ", "members": [{"name": "テスオ", "sex": "女", "age": 20}], "day": st["day"]}]
        votes = {l["id"]: dict(l["votes"]) for l in st["laws"]}
        feel = {p["name"]: (p.get("feeling"), p.get("feeling_day")) for p in era2.adults(st)}
        n0 = st["next_event"]
        g7.apply_plan(st)
        ev = [e for e in st["events"] if e["id"] >= n0]
        settled = [e for e in ev if e["type"] == "収める"]
        self.assertEqual(len(settled), era2.TALK_MAX, "方針で収めるのは古いものから 2 つまで")
        self.assertTrue(all(era2.POLICY in e["text"] and (e.get("data") or {}).get("how") == "方針" for e in settled))
        loan = next(e for e in ev if e["type"] == "貸し借り")
        self.assertTrue(loan["text"].startswith(era2.POLICY))
        self.assertEqual([x["data"]["offer"] for x in ev if x["type"] == "よその村" and "受けなかった" in x["text"]], ["T901", "T902"], "相手にしない村・上限")
        self.assertEqual(loan["data"]["other"], "N1")
        self.assertTrue(era2._meeting_event(loan))
        self.assertTrue(any(e["type"] == "加わる" and "年の方針で" in e["text"] for e in ev))
        self.assertFalse(any(e["type"] in ("掟", "話す") for e in ev), "答えのない季節は、掟の投票も話もない")
        self.assertEqual({l["id"]: dict(l["votes"]) for l in st["laws"]}, {k: {} for k in votes} | {k: v for k, v in votes.items() if v})
        self.assertEqual(G["step"]["how"], "方針")
        self.assertEqual(G["src"]["テスオ"], "加わった季節")
        for p in era2.adults(st):
            if p["name"] in feel:
                self.assertEqual((p.get("feeling"), p.get("feeling_day")), feel[p["name"]], "答えのない季節は、気持ちを変えない")
        self.assertEqual(e2["g6"]["store_sealed"], e2["step_day"], "封をする季節 (秋)")
        # 同じ state からは同じ結果 (乱数は今のまま)
        a, b = to_year_end(self.st()), to_year_end(self.st())
        for x in (a, b):
            g7.apply_year(x, self.answers(x, list(g7.SEASONS)))
            x["day"] += 30
            x["era2"]["g7"]["ask"] = None
            g7.apply_plan(x)
        self.assertEqual(sha(json.dumps(a, sort_keys=True, ensure_ascii=False)), sha(json.dumps(b, sort_keys=True, ensure_ascii=False)))

    def test_leader_policy(self):
        st, g7 = to_year_end(self.st()), self.g7
        e2 = st["era2"]
        homes = era2._homes(st)
        lead = next(p for p in era2.adults(st) if p["household"] in e2["g7"]["sample"] and p["name"] in era2._reps(st))
        e2["g5"]["leader"] = lead["name"]
        ans = self.answers(st, list(g7.SEASONS))
        ans[lead["name"]] = year_answer(list(g7.SEASONS), judge_rule="つぐなう", call={"activity": "畑仕事", "when": "冬"})
        g7.apply_year(st, ans)
        self.assertEqual(e2["g5"]["call"]["when"], "冬")
        self.assertIn("「冬は、みんなで 畑仕事 をしよう」", st["events"][-1]["text"] if st["events"][-1]["type"] == "まとめ役"
                      else next(e["text"] for e in reversed(st["events"]) if e["type"] == "まとめ役"))
        st["day"] += 30
        st["era2"]["g7"]["ask"] = None
        others = [h for h in homes if h != lead["household"]]
        for i in range(4):
            e2["g5"]["disputes"].append({"id": f"M{950 + i}", "kind": "倉", "from": others[i], "against": others[i + 1], "day": st["day"] - 30, "harm": 1,
                                         "what": "試し", "because": [], "status": era2.OPEN, "event": 0})
        n0 = st["next_event"]
        g7.apply_plan(st)
        judged = [e for e in st["events"] if e["id"] >= n0 and e["type"] == "裁き"]
        self.assertEqual(len(judged), 4, "まとめ役の方針は、自分の家のもの以外ならいくつでも")
        self.assertIsNotNone(e2["g5"]["call"], "冬の呼びかけは、冬まで数えない")

    def test_ask_next(self):
        st, g7 = self.st(), self.g7
        G = st["era2"]["g7"]
        st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
        G["zoom"] = None
        self.assertEqual(g7.ask_next(st), "年")
        G["zoom"] = {"year": (st["day"] + 1) // era2.YEAR, "why": ["Z1"], "day": st["day"]}
        self.assertEqual(g7.ask_next(st), "寄る")
        st["day"] += 30
        self.assertEqual(g7.ask_next(st), "寄る", "寄る年は 4 季節とも")
        G["zoom"] = None
        self.assertIsNone(g7.ask_next(st))
        world.G7_PARTS["year"] = False
        try:
            self.assertEqual(g7.ask_next(st), "寄る")
        finally:
            world.G7_PARTS["year"] = True
        st["day"] += 7  # 季節の途中で区切った (蓄えが尽きた)
        n = len(st["events"])
        self.assertEqual(g7.ask_next(st), "集まり直し")
        self.assertEqual(G["zoom"]["why"], ["Z5"])
        self.assertEqual(st["events"][-1]["type"], "年の集まり")
        self.assertEqual(g7.ask_next(st), "集まり直し")
        self.assertEqual(len(st["events"]), n + 1, "出来事は一度だけ")
        st["day"] = (st["day"] // era2.SEASON_DAYS + 1) * era2.SEASON_DAYS - 1
        self.assertEqual(g7.ask_next(st), "寄る", "その年の残りの季節も寄る")

    def test_zoom(self):
        st, g7 = self.st(), self.g7
        st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
        self.assertIsNone(g7._zoom(st))
        st["era2"]["g7"]["region"]["yoru"] = {"year": (st["day"] + 1) // era2.YEAR, "Z1": ["Q1"], "Z3": []}
        self.assertEqual(g7._zoom(st)["why"], ["Z1"])
        st["store"] = []
        for h in st["era2"]["house"].values():
            h["store"] = []
        self.assertEqual(g7._zoom(st)["why"], ["Z1", "Z4"])
        n = len(st["events"])
        g7.year_turn(st)
        self.assertIn("季節ごとに集まって決める", st["events"][n]["text"])
        self.assertNotIn("見本", st["events"][n]["text"])

    def test_prompts(self):
        st, g7 = self.st(), self.g7
        G = st["era2"]["g7"]
        p = next(q for q in era2.adults(st) if q["name"] in era2.answerers(st))
        t = g7.year_prompt(st, p, g7.since(st))
        for w in ("見本", "手本", "まねる", "重み"):
            self.assertNotIn(w, t, "見本であることは書かない")
        for k in ("tax", "write", "loan", "guard", "others"):
            self.assertIn(era2.FACTS_G7[k].strip(), t)
        self.assertIn('"demand": null', t)
        self.assertIn('"tax": null, "rate": null', t)
        self.assertIn('"利子": 0', t)
        self.assertIn("1 年に 1 回の村の集まり", t)
        self.assertIn("(採用された掟のうち、古い", t)
        self.assertNotIn("year_name", t, "年の終わりでない日 (G7 に入った日) は年の名前を決めない")
        y = to_year_end(self.st())
        ty = g7.year_prompt(y, next(q for q in era2.adults(y) if q["name"] == p["name"]), g7.since(y))
        self.assertIn("## 年の名前 (1 年に 1 回)", ty)
        self.assertIn('"year_name": "..."', ty)
        self.assertEqual(ty.count('"job": {"activity": "採集"'), 4, "4 季節分の予定")
        self.assertIn('"秋": {"job"', ty)
        self.assertIn('"sow": 0}', ty)
        # 寄る季節のお題: 今の季節のお題に、わけの 1 行・短い掟・G7 の欄
        G["ask"], G["zoom"] = "寄る", {"year": (st["day"] + 1) // era2.YEAR, "why": ["Z4"], "day": st["day"]}
        z = era2.season_prompt(st, p, g7.since(st))
        self.assertIn("今年は季節ごとに集まる (わけ: 村の蓄えと家の倉を合わせても、30 日分より少ない)", z)
        self.assertIn("(採用された掟のうち、古い", z)
        self.assertIn("新しい仕組み (上の決まりを見て決める", z)
        self.assertIn('"tax": null, "rate": null', z)
        self.assertRegex(z, r"\n9\. 新しい仕組み[^\n]*\n(?:   [^\n]*\n)+10\. 今の気持ちを一言")

    def test_facts(self):
        bad = ("王", "お金", "国", "神", "銀", "青銅", "法", "税", "預言者", "奴隷", "都市")
        for k, t in era2.FACTS_G7.items():
            self.assertFalse([w for w in bad if w in t], k)
            if k != "cattle":  # 牛は、ほかの村のようすを書いた文
                self.assertIn("ない", t, f"{k}: しないことも同じ重さで")
        st, g7 = self.st(), self.g7
        on = [k for k in era2.FACTS_G7 if g7.FACTS_ON[k](st)]
        self.assertLessEqual({"tax", "write", "loan", "guard", "others"}, set(on))
        self.assertNotIn("leave", on)
        self.assertNotIn("try", on)
        add_law(st)["tax"] = {"what": "草の種", "share": 0.1}
        st["laws"][-1]["status"] = "採用"
        self.assertTrue(g7.FACTS_ON["leave"](st), "税の掟があれば、家ごとに村を出る")

    def test_offered(self):
        st, g7 = self.st(), self.g7
        G, D = st["era2"]["g7"], st["day"]
        self.assertEqual(set(G["offered"]), {k for k in era2.FACTS_G7 if g7.FACTS_ON[k](st)} | set(g7.fields_on(st)))
        self.assertEqual(set(G["offered"].values()), {D})
        st["day"] += 30
        G["region"]["demands"] = [{"id": "Q1", "from": "N1", "to": "V0", "end": None}]
        G["ask"] = None
        g7._offer(st)
        self.assertNotIn("answer_demand", G["offered"], "お題を書かない歩では数えない")
        G["ask"] = "寄る"
        g7._offer(st)
        self.assertEqual((G["offered"]["answer_demand"], G["offered"]["leave"], G["offered"]["tax"]), (D + 30, D + 30, D), "初めて出た日だけ")

    def test_meeting_event(self):
        self.assertTrue(era2._meeting_event({"type": "交換", "text": era2.POLICY + "、村は、村の物で 南の村 の申し出 [T1] を受け"}))
        self.assertTrue(era2._meeting_event({"type": "もめごと", "text": era2.POLICY + "、もめごと [M1] を収めようとしたが、まとまらなかった"}))
        self.assertFalse(era2._meeting_event({"type": "もめごと", "text": "もめごと [M1] (倉): A が、B のことで不満を言い出した"}))
        self.assertFalse(era2._meeting_event({"type": "交換", "text": "ソル が 南の村 で、土器 を ヤギ と取り替えた"}))

    def test_g6_unchanged_helpers(self):
        g6 = real_state()
        self.assertEqual(era2.answerers(g6), [p["name"] for p in era2.adults(g6) if p["name"] in era2._reps(g6) | {era2._leader(g6)}])
        self.assertNotIn("(採用された掟のうち", characters_laws(g6))

    def test_workflow_year(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node がない")
        harness = r"""
const fs = require('fs')
const src = fs.readFileSync(process.argv[2], 'utf8').replace(/^export const meta/m, 'const meta')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const run = async (args, start, mode) => {
  let day = start
  const labels = []
  const meetOf = (d) => ((d + 1) % 120 === 0 ? '年' : 'none')
  const agent = async (prompt, opts) => {
    labels.push(opts.label)
    if (prompt.includes('step.py who')) {
      const m = meetOf(day)
      return `DAY ${day} season False\nPHASE G7\nHOLD none\nMODE ${mode}\nMEET ${m}\nNAMES ${m === 'none' ? '' : 'ソル ミナ'}\nFEEL ${m === 'none' ? '' : 'カイ'}\nCOUNCIL \nASKLOG True`
    }
    if (prompt.includes('season_step.sh')) { day += 30; return `season exit=0\n${day} 日目まで進んだ / 人 10\ncommitted` }
    if (prompt.includes('echo FEELING:')) return 'FEELING:'
    if (prompt.includes('/feeling/`')) return 'カイ.json'
    if (prompt.includes('ls ')) return 'ソル.json ミナ.json'
    return 'done'
  }
  const fn = new AsyncFunction('args', 'agent', 'parallel', 'log', src)
  const res = await fn(args, agent, async (fs_) => Promise.all(fs_.map((f) => f())), () => {})
  return { res, labels }
}
;(async () => {
  const a = await run({ mode: 'year', years: 1 }, 5519, 'year')
  const b = await run({ mode: 'season', steps: 3 }, 5519, 'year')
  console.log(JSON.stringify({ a: { why: a.res.why, stopped: a.res.stopped, labels: a.labels }, b: { why: b.res.why } }))
})()
"""
        f = Path(tmpdir()) / "h.js"
        try:
            f.write_text(harness, encoding="utf-8")
            r = subprocess.run([node, str(f), str(SOC / "tools" / "society2_seasons_workflow.js")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
        finally:
            shutil.rmtree(f.parent, ignore_errors=True)
        a = out["a"]
        self.assertEqual((a["why"], a["stopped"]), ("end", 5639), "年の終わりを 1 回すぎたら止まる")
        roles = [x for x in a["labels"] if re.match(r"d\d+ (ソル|ミナ|カイ)", x)]
        self.assertEqual({x.split()[0] for x in roles}, {"d5519"}, "役を演じる体を起こすのは集まりの歩だけ")
        self.assertEqual(sum(1 for x in a["labels"] if x.endswith("season step")), 4)
        self.assertTrue(out["b"]["why"].startswith("mode"), "G7 なのに season の形なら進めずに止まる")

    def test_pythons(self):
        """年の集まりと答えのない季節の当てはめ方は、python3.13 と python3 (3.11) で同じ (世界は進めない)"""
        code = ("import sys, json, hashlib; sys.path[:0] = [sys.argv[1], sys.argv[1] + '/tools']; import test_g7 as t, g7, era2; "
                "st = t.to_year_end(t.g7_state()); g7.apply_year(st, {n: t.year_answer(list(g7.SEASONS), judge_rule='ゆるす', feast=['秋']) for n in era2.answerers(st)}); "
                "st['day'] += 30; st['era2']['g7']['ask'] = g7.ask_next(st); g7.apply_plan(st); "
                "print(hashlib.sha256(json.dumps(st, sort_keys=True, ensure_ascii=False).encode()).hexdigest())")
        outs = {}
        for py in pythons():
            r = subprocess.run([py, "-c", code, str(SOC)], capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8="1"))
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            outs[py] = r.stdout.strip()
        self.assertEqual(len(set(outs.values())), 1, outs)

    def test_same_as_g6(self):
        """全部の家を見本にし、毎季節寄るようにした G7 (直し・天気も止める) は、同じ答えの G6 と同じ世界になる (6.2 の「同じになる試し」)"""
        days = sorted(int(p.name[3:]) for p in (REAL / "answers").glob("day*") if p.name[3:].isdigit())
        if not days:
            self.skipTest("答えがない")
        tmp = tmpdir()
        try:
            (tmp / "runner.py").write_text(RUNNER_SAME, encoding="utf-8")
            env = dict(os.environ, PYTHONUTF8="1", PYTHONHASHSEED="0")
            ps = {m: subprocess.Popen([sys.executable, str(tmp / "runner.py"), str(SOC), str(REAL), str(REAL / "answers" / f"day{days[-1]}"), m,
                                       str(tmp / f"{m}.json")], env=env, stderr=subprocess.PIPE, text=True) for m in ("g6", "g7")}
            for m, p in ps.items():
                err = p.communicate()[1]
                self.assertEqual(p.returncode, 0, err[-3000:])
            a, b = (json.loads((tmp / f"{m}.json").read_text(encoding="utf-8")) for m in ("g6", "g7"))
            diff = [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
            diff += [f"era2.{k}" for k in sorted(set(a.get("era2", {})) | set(b.get("era2", {}))) if a["era2"].get(k) != b["era2"].get(k)]
            self.assertEqual(diff, [], "ちがう鍵")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def characters_laws(st):
    import characters
    return characters._laws(st, with_pending=True)


RUNNER_SAME = r'''
import json, sys
from pathlib import Path
soc, real, ans, mode, out_f = sys.argv[1:6]
sys.path[:0] = [soc, soc + "/tools"]
import era2, world, test_g7
st = json.loads(Path(real, "state.json").read_text(encoding="utf-8"))
test_g7.part_end(st)
if mode == "g7":  # 年 1 回の答え・直し・天気を止めた G7 (全部の家が見本で、毎季節寄る)
    world.G7_PARTS.update(fix=False, weather=False, year=False, region=False, hints=False, joints=False)
    import g7
    g7.enter(st, 0.0)
else:  # 出来事の番号をそろえる (G7 に入った日の出来事と同じ数)
    world.log(st, "フェーズ", None, "第 5 部「王と青銅」を始めた: フェーズ G7 (王と役所)")
def read(kind, who):
    d = Path(ans) / kind
    return {n: (d / f"{n}.json").read_text(encoding="utf-8") for n in who if (d / f"{n}.json").exists()}
feels = read("feeling", era2.feelers(st))
answers = read("season", era2.answerers(st))
if mode == "g7":
    assert st["era2"]["g7"]["ask"] == "寄る" and not st["era2"]["g7"]["donor"]
    g7.apply_year(st, answers)
else:
    era2.apply_answers(st, answers)
era2.apply_feelings(st, feels)
first = era2.simulate_season(st)
st["era2"]["last_first"] = first
era2.check(st)
for k in ("era", "era_info", "era_log", "hold", "next_event"):
    st.pop(k, None)
for k in ("g7", "ahead", "cattle", "walls"):
    st["era2"].pop(k, None)
for o in st["era2"]["g6"]["others"]:  # G6 の鍵だけくらべる
    for k in ("cell", "land", "parent", "org", "commit", "stance", "walls", "tech", "head_age", "cattle_f", "pots_f", "sickles_f"):
        o.pop(k, None)
st["events"] = [e for e in st["events"] if e["type"] not in ("年の集まり", "目盛り")]
Path(out_f).write_text(json.dumps(st, ensure_ascii=False, sort_keys=True), encoding="utf-8")
'''


# ---------------------------------------------------------------- G
@unittest.skipUnless(os.environ.get("SOC_SLOW") == "1", "SOC_SLOW=1 のときだけ (写しで step.py を 3 季節回す。10 分ほど)")
class G_Flow(unittest.TestCase):
    """写しで step.py を回す: G7 に入る (短い年の集まり) → 年の集まり → 答えのない季節。記録は 1 行 = 1 季節 (4.A.10)"""

    @classmethod
    def setUpClass(cls):
        st = real_state()
        if not is_g6(st) or st["phase"] != "season" or st.get("hold"):
            raise unittest.SkipTest("本物の state が、季節の答えを待っている G6 でない")
        cls.tmp = tmpdir()
        cls.data = cls.tmp / "data"
        cls.data.mkdir()
        for d in ("archive", "records"):
            if (REAL / d).exists():
                shutil.copytree(REAL / d, cls.data / d)
        part_end(st)
        (cls.data / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        cls.env = dict(os.environ, SOC_DATA=str(cls.data), SOC_RECORDS="1", SOC_ARCHIVE="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "tmp", None):
            shutil.rmtree(cls.tmp, ignore_errors=True)

    def step(self, *args):
        r = subprocess.run([sys.executable, str(SOC / "step.py"), *args], capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-3000:])
        return r.stdout

    def who(self):
        w = dict((l.split(" ", 1) + [""])[:2] for l in self.step("who").strip().splitlines())
        return int(w["DAY"].split()[0]), w["MEET"].strip(), w["NAMES"].split(), w["FEEL"].split()

    def answer(self, day, names, feel, seas):
        a = self.data / "answers" / f"day{day:03d}"
        for kind, who in (("season", names), ("feeling", feel)):
            (a / kind).mkdir(parents=True, exist_ok=True)
            for n in who:
                txt = (year_answer(seas, judge_rule="ゆるす", feast=["秋"], year_name="試しの年") if kind == "season"
                       else json.dumps({"feeling": "試し", "say": []}, ensure_ascii=False))
                (a / kind / f"{n}.json").write_text(txt, encoding="utf-8")

    def test_flow(self):
        self.step("next_part")
        d0, meet, names, feel = self.who()
        self.assertEqual(meet, "年")
        self.assertTrue(names and feel)
        seas = list(__import__("g7").SEASONS)
        self.answer(d0, names, feel, seas[seas.index(world.season(d0 + 1)):])
        self.step("season")
        d1, meet, names, feel = self.who()
        self.assertEqual((d1, meet), (d0 + 30, "年" if (d1 + 1) % era2.YEAR == 0 else meet))
        if meet != "年":
            self.skipTest("G7 に入った日の次が年の終わりでない (この試しは 5489 日目の state 向け)")
        y = (self.data / "prompts" / f"day{d1:03d}" / "season" / f"{names[0]}.md").read_text(encoding="utf-8")
        self.assertIn("1 年に 1 回の村の集まり", y)
        self.assertIn('"year_name": "..."', y)
        self.assertNotIn("見本", y)
        f = (self.data / "prompts" / f"day{d1:03d}" / "feeling" / f"{feel[0]}.md").read_text(encoding="utf-8")
        self.assertIn("1 年に 1 回の村の集まり。あなたが答えるのは", f)
        self.answer(d1, names, feel, seas)
        self.step("season")
        d2, meet, names2, feel2 = self.who()
        self.assertEqual((d2, meet, names2, feel2), (d1 + 30, "none", [], []))
        self.assertFalse((self.data / "prompts" / f"day{d2:03d}").exists(), "集まりのない季節は、お題のフォルダを作らない")
        out = self.step("season")
        self.assertIn("この季節は集まらない", out)
        st = json.loads((self.data / "state.json").read_text(encoding="utf-8"))
        G = st["era2"]["g7"]
        self.assertEqual((st["day"], G["step"]["how"], G["step"]["answer_day"]), (d2 + 30, "方針", d1))
        self.assertIn("見本から広げた", G["src"].values())
        self.assertTrue(any(e["type"] == "年の名前" and "試しの年" in e["text"] for e in st["events"]))
        # 記録: 1 行 = 1 季節。G7 の季節は decided_by・is_sample・plan_answer_day
        rows = [json.loads(x) for x in (self.data / "records" / "season_person.jsonl").read_text(encoding="utf-8").splitlines()]
        vil = {r["season_end_day"]: r for r in (json.loads(x) for x in (self.data / "records" / "season_village.jsonl").read_text(encoding="utf-8").splitlines())}
        for D, plan_day in ((d1, d0), (d2, d1), (d2 + 30, d1)):
            rs = [r for r in rows if r["season_end_day"] == D]
            self.assertTrue(rs, D)
            self.assertEqual(len({r["person_id"] for r in rs}), len(rs), "1 人 1 季節に 1 行")
            ad = [r for r in rs if not r["child"] and r["status_at_end"] == "生きている"]
            self.assertTrue(all(r["plan_answer_day"] == plan_day and "is_sample" in r for r in ad), D)
            self.assertLessEqual({r["decided_by"] for r in ad}, YEAR_SRC | {None})
            self.assertIn("見本から広げた", {r["decided_by"] for r in ad})
            self.assertEqual(vil[D]["answered"]["plan_answer_day"], plan_day)
            self.assertGreater(vil[D]["answered"]["sample_households"], 0)
        self.assertEqual(vil[d2 + 30]["answered"]["season"], 0, "答えのない季節")
        self.assertTrue(any(r["answered"] == "season" for r in rows if r["season_end_day"] == d2))
        self.assertTrue(any(r["decided_by"] == "年の答え (自分)" for r in rows if r["season_end_day"] == d2 + 30))


# ---------------------------------------------------------------- C2
class C2_ClosedByDecision(unittest.TestCase):
    """G6 を本人の決めで閉じて G7 に入る (2026-10-17。町の条件がそろわないまま。止まっていない state から。step.py を写しで動かす)"""

    @classmethod
    def setUpClass(cls):
        st = real_state()
        if not is_g6(st) or st["phase"] != "season" or st.get("hold") or (st["era2"].get("g6") or {}).get("end"):
            raise unittest.SkipTest("本物の state が、止まっていない G6 でない")
        cls.tmp = tmpdir()
        cls.data = cls.tmp / "data"
        cls.data.mkdir()
        cls.D = st["day"]
        if (REAL / "archive").exists():
            shutil.copytree(REAL / "archive", cls.data / "archive")
        (cls.data / "state.json").write_text(real_text(), encoding="utf-8")
        cls.env = dict(os.environ, SOC_DATA=str(cls.data), SOC_RECORDS="0", SOC_ARCHIVE="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "tmp", None):
            shutil.rmtree(cls.tmp, ignore_errors=True)

    def step(self, *args):
        return subprocess.run([sys.executable, str(SOC / "step.py"), *args], capture_output=True, text=True, env=self.env)

    def test_closed(self):
        before = sha((self.data / "state.json").read_bytes())
        for args, word in ((("next_part",), "一時停止していない"), (("next_part", "--closed-by-decision", " "), "本人の言葉がない"),
                           (("season", "--closed-by-decision", "x"), "next_part のときだけ")):
            r = self.step(*args)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn(word, r.stdout + r.stderr)
        a = self.data / "answers" / f"day{self.D:03d}" / "season"
        a.mkdir(parents=True)
        (a / "だれか.json").write_text("{}", encoding="utf-8")
        r = self.step("next_part", "--closed-by-decision", "町は生まれなかったとして G6 を閉じる")
        self.assertEqual(r.returncode, 3)
        self.assertIn("答えがもうある", r.stdout)
        shutil.rmtree(self.data / "answers")
        self.assertEqual(sha((self.data / "state.json").read_bytes()), before, "断ったときは何も変えない")
        r = self.step("next_part", "--closed-by-decision", "町は生まれなかったとして G6 を閉じる", "--fill", "0.1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("本人の決めで閉じた", r.stdout)
        st = json.loads((self.data / "state.json").read_text(encoding="utf-8"))
        c = st["era2"]["g6"]["closed"]
        self.assertEqual((c["day"], c["by"], c["note"], c["town"]), (self.D, "本人の決め", "町は生まれなかったとして G6 を閉じる", None))
        self.assertIsNone(st["era2"]["g6"]["end"], "町はそろっていないので、g6.end は書かない")
        ev = [e for e in st["events"] if e["day"] == self.D and e["type"] == "フェーズ"]
        self.assertEqual(len(ev), 2)
        self.assertTrue(ev[0]["text"].startswith("第 4 部の終わり (G6): 町の条件はそろわないまま、ここで閉じた"))
        self.assertNotIn("本人", ev[0]["text"], "村の人の年のまとめに出る文に、作る側のことばを入れない")
        self.assertEqual((ev[0]["data"]["closed_by"], ev[0]["data"]["note"]), ("本人の決め", "町は生まれなかったとして G6 を閉じる"))
        self.assertEqual(ev[1]["text"], "第 5 部「王と青銅」を始めた: フェーズ G7 (王と役所)")
        self.assertLess(ev[0]["id"], ev[1]["id"])
        e = st["era_log"][-1]
        self.assertEqual((e["era"], e["how"], e["g6_closed"]), ("G7", "next_part", self.D))
        self.assertEqual(st["era2"]["g7"]["region"]["fill"]["share"], 0.1)
        r = self.step("next_part", "--closed-by-decision", "もう一度")
        self.assertEqual(r.returncode, 3)
        self.assertIn("G6 から G7 だけ", r.stdout)


# ---------------------------------------------------------------- H
def sett(sid, people, cell, org=0, grain=None, **kw):
    s = {"id": sid, "name": sid, "people": people, "cell": list(cell), "land": region.land(cell), "org": org, "commit": {}, "stance": "ふつう",
         "walls": None, "tech": 1, "grain": people * 100 if grain is None else grain, "goats": 0, "bad": None, "known": 0}
    s.update(kw)
    return s


def tie(n, payer, payee, since=0, paid=(0,)):
    return {"id": f"K{n}", "payer": payer, "payee": payee, "goods": {"草の種": 100}, "since": since, "paid": list(paid), "missed": 0,
            "status": "続く", "end": None, "fixed": None}


class H_Region(unittest.TestCase):
    """まわりの集落の決まり (4.B.3) と決める段 (4.D.2)。region.py の関数だけ (state は使わない)"""

    def test_levels(self):
        lv = region.levels([sett("V0", 100, (5, 5)), sett("N1", 20, (5, 7)), sett("N2", 20, (5, 3))], [tie(1, "N1", "V0"), tie(2, "N2", "V0")], 0)
        self.assertEqual([(g["top"], g["D"], g["village"]) for g in lv], [("V0", 1, "中心")], "星形は D 1")
        lv = region.levels([sett(f"N{i}", 20, (i, 0)) for i in range(1, 5)], [tie(1, "N1", "N2"), tie(2, "N2", "N3"), tie(3, "N3", "N4")], 0)
        self.assertEqual([(g["top"], g["D"], g["T"], g["village"]) for g in lv], [("N4", 3, 4, "外")], "集落 4 段の列は D 3 (村は外)")
        lv = region.levels([sett("N1", 20, (1, 1)), sett("N2", 20, (2, 2))], [tie(1, "N1", "N2", 0), tie(2, "N2", "N1", 5)], 0)
        self.assertEqual([(g["top"], g["D"]) for g in lv], [("N2", 1)], "輪になる矢印は新しいほうを数えない")
        lv = region.levels([sett("N1", 70, (1, 1), org=2), sett("N2", 20, (2, 2)), sett("N3", 20, (3, 3))], [tie(1, "N2", "N1"), tie(2, "N3", "N1")], 0)
        self.assertEqual([(g["top"], g["D"], g["T"], g["office"]) for g in lv], [("N1", 2, 2, 1)], "段 2 の集落は、長の下に集める役が 1 つ")
        S = [sett("V0", 100, (5, 5)), sett("N1", 20, (5, 7)), sett("N2", 20, (5, 3)), sett("N4", 20, (5, 8)), sett("N5", 20, (4, 8))]
        T = [tie(1, "N4", "N1"), tie(2, "N5", "N1"), tie(3, "N1", "V0"), tie(4, "N2", "V0")]
        self.assertEqual(region.levels(S, T, 0)[0]["D"], 2)
        lv = region.levels(S, T, 0, officials={"ソル": ["N1", "N2"], "ミナ": ["V0"]})
        self.assertEqual([(g["top"], g["D"], g["T"], g["office"], g["village"]) for g in lv], [("V0", 3, 3, 1, "中心")], "設計 4.D.2 の D 3 の例")
        lv = region.levels(S, T, 0, officials={"ミナ": ["V0"]})
        self.assertEqual(lv[0]["D"], 2, "村の中の税だけの役は、段を足さない (下が村の葉 1 つ)")
        lv = region.levels([sett("V0", 100, (5, 5)), sett("N1", 20, (5, 7))], [], 0)
        self.assertTrue(all(g["D"] == 0 for g in lv), "この 1 年に払いがなければ数えない")

    def test_demand_pay_and_fixed(self):
        R = {"ties": [], "demands": [], "wars": [], "pending": [], "gone": [], "log": []}
        S = [sett("V0", 150, (5, 5), village=True, kcap=10 ** 6), sett("N1", 80, (5, 7), org=1), sett("N2", 10, (6, 8), grain=3000)]
        made = []
        out = region.year_end(R, S, random.Random(1), 49, 5879, out=[])
        qs = [q for q in R["demands"] if q["from"] == "N1"]
        self.assertTrue(qs and qs[0]["to"] == "N2", "強い N1 は、届く範囲のいちばん弱い N2 に求める")
        self.assertFalse(any(q["from"] == "V0" for q in R["demands"]), "本物の村の求めは、決まりでは出さない (答えから)")
        self.assertTrue(5880 + 9 <= qs[0]["war_day"] <= 5880 + 49)
        p = next(p for p in R["pending"] if p["kind"] == "求めへの答え")
        self.assertIn(p["rule"], ("払う", "逃げる", "助けを頼む", "戦う"))
        self.assertIn("N2", R["councils"]["ask"], "求められた集落は集まりで答える")
        R["councils"]["answers"] = {"N2": {qs[0]["id"]: "払う"}}
        region.decide(R, S, 5880, make=lambda *a: made.append(a), out=out)
        self.assertEqual(qs[0]["answer"], "払う")
        t = R["ties"][0]
        g0 = S[2]["grain"]
        region.pay_ties(R, S, 5880, out=out)
        self.assertEqual((t["paid"], S[2]["grain"]), ([5880], g0 - t["goods"]["草の種"]))
        self.assertIsNone(t["fixed"])
        region.pay_ties(R, S, 6000, out=out)
        self.assertEqual(t["fixed"], 6000, "期日に 2 回続けて払われたら「決まった」")
        self.assertNotIn("N2", {q["to"] for q in region.open_demands(R)})
        # 輪にならない: 貢いでいる N2 は、上の N1 に求めない
        self.assertIsNone(region._demand_target(R, S, S[2], "求める"))
        self.assertIn("N1", region.above(R, "N2"))

    def test_refuge_and_flee(self):
        a, t = sett("N1", 80, (5, 7)), sett("N2", 10, (5, 9))
        S = [sett("V0", 150, (5, 5), village=True), a, t]
        c = region.refuge(S, t, a)
        self.assertGreater(region.dist(c, (5, 7)), region.reach(a))
        full = S + [sett(f"N{i + 3}", 10, cc) for i, cc in enumerate(x for x in region.cells() if x not in {(5, 5), (5, 7), (5, 9)} and region.dist(x, (5, 7)) > 2)]
        self.assertIsNone(region.refuge(full, t, a), "届く範囲の外が埋まっていれば、逃げ場はない (囲まれている)")
        R = {"ties": [tie(1, "N2", "N1")], "demands": []}
        self.assertTrue(region.flee(R, S, t, a, 100, []))
        self.assertEqual(tuple(t["cell"]), c)
        self.assertEqual(R["ties"][0]["status"], "切れた")

    def test_war(self):
        S = [sett("V0", 150, (5, 5), village=True), sett("N1", 80, (5, 7)), sett("N2", 40, (5, 9), grain=4000, goats=10)]
        R = {"ties": [], "demands": [{"id": "Q1", "from": "N1", "to": "N2", "what": {"草の種": 100}, "end": None}], "wars": []}
        w = {"id": "W1", "att": "N1", "def": "N2", "day": 5890, "demand": "Q1", "done": None}
        R["wars"].append(w)
        p0 = (S[1]["people"], S[2]["people"])
        region.fight(R, S, w, region.war_rng(7, 1), 5890, out=[])
        w2 = dict(w, done=None)
        S2 = [dict(x, commit={}) for x in [sett("V0", 150, (5, 5), village=True), sett("N1", 80, (5, 7)), sett("N2", 40, (5, 9), grain=4000, goats=10)]]
        R2 = {"ties": [], "demands": [{"id": "Q1", "from": "N1", "to": "N2", "what": {"草の種": 100}, "end": None}], "wars": [w2]}
        region.fight(R2, S2, w2, region.war_rng(7, 1), 5890, out=[])
        self.assertEqual((w["att_win"], w["dead"], w["loot"]), (w2["att_win"], w2["dead"], w2["loot"]), "同じ戦の種なら同じ")
        win = w["att_win"]
        lo, hi = (region.WIN_DEATH, region.LOSE_DEATH) if win else (region.LOSE_DEATH, region.WIN_DEATH)
        self.assertTrue(round(20 * lo[0]) <= w["dead"]["N1"] <= round(20 * lo[1]) + 1)
        self.assertEqual(S[1]["people"], p0[0] - w["dead"]["N1"])
        self.assertEqual(bool(R["ties"]), win, "守る側が負ければ貢ぐ集落になる")
        self.assertEqual(R["demands"][0]["end"], 5890)
        # 川辺の村の人と物は、呼んだ側が当てる (own があるとき)
        S3 = [sett("V0", 150, (5, 5), village=True), sett("N1", 80, (5, 7))]
        w3 = {"id": "W2", "att": "N1", "def": "V0", "day": 1, "demand": None, "done": None}
        region.fight({"ties": [], "demands": [], "wars": [w3]}, S3, w3, region.war_rng(7, 2), 1, own={"S": 30.0, "n": 40})
        self.assertEqual((S3[0]["people"], S3[0]["grain"]), (150, 15000))
        self.assertEqual(w3["fighters"]["V0"], 40)
        self.assertGreater(region.p_win(3, 1), region.p_win(2, 1))
        self.assertAlmostEqual(region.p_win(1, 1), 0.5)

    def test_collapse_and_split(self):
        S = [sett("V0", 150, (5, 5), village=True), sett("N1", 30, (5, 7)), sett("N2", 4, (5, 9)), sett("N3", 130, (4, 3))]
        R = {"ties": [tie(1, "N2", "N1")], "demands": [], "gone": []}
        out = []
        region.collapse(R, S, 10, out)
        self.assertEqual((S[2].get("gone"), S[1]["people"], R["ties"][0]["status"]), (10, 34, "切れた"), "5 人未満は、貢ぐ相手に移ってなくなる")
        made = []

        def make(parent, c, n, kind):
            o = sett(f"N{9 + len(made)}", n, c)
            made.append(o)
            S.append(o)
            return o
        R["pending"] = [{"kind": "分かれる", "who": "N3", "u": 0.1, "share": 0.4}]
        region.decide(R, S, 20, make=make, out=out)
        self.assertEqual((S[3]["people"], made[0]["people"], made[0]["parent"]), (78, 52, "N3"))
        self.assertLessEqual(region.dist(tuple(made[0]["cell"]), (4, 3)), 2)
        self.assertEqual(made[0]["commit"]["N3"], 0.6)
        R["pending"] = [{"kind": "分かれる", "who": "N3", "u": 0.1, "share": 0.4}]
        R["councils"] = {"answers": {"N3": {"分かれるか": "とどめて役を作る"}}}
        region.decide(R, S, 30, make=make, out=out)
        self.assertEqual((S[3]["people"], S[3].get("org_boost")), (78, True), "集まりが「とどめて役を作る」と答えたら分かれない")

    def test_sick(self):
        s = sett("N1", 60, (5, 7))
        self.assertAlmostEqual(region.sick(random.Random(1), s, 0, False)[1], 0.005)
        self.assertAlmostEqual(region.sick(random.Random(1), dict(s, people=120), 1, False)[1], 0.02)
        self.assertAlmostEqual(region.sick(random.Random(1), dict(s, people=60000), 1, False)[1], 0.15)

    def test_sweep_same(self):
        """掃き出しは、同じ引数なら同じ (PYTHONHASHSEED によらない)"""
        sys.path.insert(0, str(HERE))
        import region_sweep
        base = {"day": 5849, "pop": 150, "grain": 20000, "goats": 30, "leader": False,
                "others": [{"id": "N1", "name": "南の村", "dir": "南", "days": 1, "people": 17, "goats": 17, "grain": 5100, "known": 1}]}
        args = (base, 0.3, False, region_sweep.POLICIES[4], 3, 12)
        a = json.dumps(region_sweep.run(args), sort_keys=True)
        self.assertEqual(a, json.dumps(region_sweep.run(args), sort_keys=True))
        code = f"import sys,json;sys.path[:0]=[{str(SOC)!r},{str(HERE)!r}];import region_sweep as r;print(json.dumps(r.run({args!r}),sort_keys=True))"
        for hs in ("1", "2"):
            o = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=hs)).stdout.strip()
            self.assertEqual(o, a)


class I_Debt(unittest.TestCase):
    """G6 の穴の直し (G7 からだけ): 期日の季節に返しに来た貸し借りが、その季節の終わりに「返されない」になって消えていた (D4・D6)"""

    def setup(self, st):
        g = st["era2"]["g6"]
        D = st["day"]
        o = next(x for x in g["others"] if x["id"] == "N2")
        d = {"id": "D99", "other": "N2", "lender": "村", "goods": {"草の種": 100}, "day": D - 2 * era2.YEAR, "due": D - era2.YEAR, "proof": None,
             "mem": {"village": 1.0, "other": 1.0}, "status": "まだ", "end": None}
        g["debts"].append(d)
        g["offers"].append({"kind": "返す", "debt": "D99", "give": {"草の種": 100}, "want": {}, "id": "T999", "other": "N2", "day": D, "goats_in": [], "mem": {}})
        return d, o

    def test_g6_unchanged(self):
        st = real_state()
        if not is_g6(st):
            self.skipTest("本物の state が G6 でない")
        d, _ = self.setup(st)
        era2._g6_season_end(st, 1.0)
        self.assertEqual(d["status"], "返されない", "G6 までは前のまま")

    def test_g7_repaid(self):
        if not is_g6(real_state()):
            self.skipTest("本物の state が G6 でない")
        st = g7_state()
        d, o = self.setup(st)
        era2._g6_season_end(st, 1.0)
        self.assertEqual(d["status"], "まだ", "返しに来た申し出がある貸し借りは、その季節の終わりには消さない")
        off = next(x for x in st["era2"]["g6"]["offers"] if x["id"] == "T999")
        before = era2._g6_have(st, "村", "草の種")
        era2._g6_repay(st, off, o)
        self.assertEqual(d["status"], "返した")
        self.assertGreater(era2._g6_have(st, "村", "草の種"), before)
        st["era2"]["g6"]["offers"] = [x for x in st["era2"]["g6"]["offers"] if x["id"] != "T999"]
        d2, _ = self.setup(st)
        st["era2"]["g6"]["offers"] = [x for x in st["era2"]["g6"]["offers"] if x["id"] != "T999"]
        st["day"] += 30
        d2["due"] = st["day"] - era2.YEAR
        era2._g6_season_end(st, 1.0)
        if not any(x.get("debt") == "D99" for x in st["era2"]["g6"]["offers"]):
            self.assertEqual(d2["status"], "返されない", "返しに来なければ、前のとおり 1 年で「返されない」")


class J_Village(unittest.TestCase):
    """川辺の村が地域にかかわる (4.B.5): 求めへの答え (広げた票)・村が求める・戦の日・家ごとに出ていく・まわりの集落の集まりの答え (メモリの中の写し)"""

    @classmethod
    def setUpClass(cls):
        if not is_g6(real_state()):
            raise unittest.SkipTest("本物の state が G6 でない")
        import g7
        cls.g7 = g7
        cls.base = g7_state(0.3)

    def st(self):
        return copy.deepcopy(self.base)

    def test_answers_tally(self):
        g7, st = self.g7, self.st()
        reg = st["era2"]["g7"]["region"]
        o = next(x for x in st["era2"]["g6"]["others"] if x["id"] == "N1")
        q = region.add_demand(reg, g7._v0(st), o, {"草の種": 100}, st["day"])
        q.update(**{"from": "N1", "to": "V0"})
        reps = g7.answerers(st)
        real = {n: {"answer_demand": {q["id"]: "戦う"}} for n in reps}
        v = g7.village_answers(st, real)
        self.assertEqual(v[q["id"]], "戦う", "見本の代表がみな同じ手なら、広げた票で大人の半分をこえる")
        self.assertEqual(sum(g7._vote_weights(st, {n: {} for n in reps}).values()), len(era2.adults(st)), "広げた票の合計は大人の数")
        real = {n: {"answer_demand": {q["id"]: "払う" if i == 0 else "わからない"}} for i, n in enumerate(reps)}
        self.assertEqual(g7.village_answers(st, real)[q["id"]], "払う", "半分に届かなくても、まとめ役がいなければいちばん多い手")
        self.assertEqual(g7.village_answers(st, {}), {})
        self.assertTrue(g7._zoom.__doc__)
        g7._yoru(st, (st["day"] + 1) // era2.YEAR)
        self.assertTrue(reg["yoru"]["Z1"], "村への求めが来ていれば、次の年は寄る年 (Z1)")

    def test_village_demand_and_war(self):
        g7, st = self.g7, self.st()
        reg = st["era2"]["g7"]["region"]
        known = [o for o in st["era2"]["g6"]["others"] if o.get("known") is not None]
        t = min(known, key=lambda o: o["people"])
        t["cell"], t["land"] = [5, 3], region.land((5, 3))
        reps = g7.answerers(st)
        real = {n: {"demand": {"to": t["id"], "what": {"草の種": 50000}, "then": "戦う"}} for n in reps}
        from unittest import mock
        with mock.patch.object(region, "refuge", lambda *a: None):  # 逃げ場がない (囲まれている) ことにして、払う損を大きくする
            q = g7.village_demand(st, real)
        self.assertIsNotNone(q)
        self.assertEqual((q["from"], q["to"], q["how"]), ("V0", t["id"], "決まりで選んだ"))
        self.assertTrue(any(e["type"] == "求め" and "村の集まりで" in e["text"] for e in st["events"]))
        w = next((w for w in reg["wars"] if w["demand"] == q["id"]), None)
        if q["answer"] != "戦う":
            self.skipTest(f"相手が戦わなかった ({q['answer']})")
        self.assertEqual(w["day"], st["day"] + 1 + 30 + 9, "次の季節の 10 日目 (乱数なし)")
        self.assertIn("戦に出る", g7.acts(st))
        st["day"] = w["day"]
        ads = era2.adults(st)
        for p in ads:
            p["today"] = {"activity": "採集"}
        for p in ads[:6]:
            p["today"] = {"activity": "戦に出る"}
        pop0, n0 = sum(p["alive"] for p in st["people"]), st["next_event"]
        g7.region_day(st)
        self.assertIsNotNone(w["done"])
        dead = w.get("dead_names") or []
        self.assertLessEqual(set(dead), {p["name"] for p in ads[:6]}, "死ぬのは戦った人だけ")
        self.assertEqual(sum(p["alive"] for p in st["people"]), pop0 - len(dead))
        self.assertTrue(all(p["today"].get("away") for p in ads[:6]))
        ev = [e for e in st["events"] if e["id"] >= n0]
        self.assertTrue(any(e["type"] == "戦" for e in ev))
        self.assertEqual(sum(1 for e in ev if e["type"] == "死"), len(dead))
        st2 = self.st()
        # 同じ戦の種なら同じ (戦ごとの文字の種)
        self.assertEqual(region.war_rng(st["seed"], 1).random(), region.war_rng(st2["seed"], 1).random())

    def test_no_fighters(self):
        g7, st = self.g7, self.st()
        reg = st["era2"]["g7"]["region"]
        o = next(x for x in st["era2"]["g6"]["others"] if x["id"] == "N2")
        q = region.add_demand(reg, g7._v0(st), o, {"草の種": 10}, st["day"])
        reg["wars"].append({"id": "W1", "att": "V0", "def": "N2", "day": st["day"], "demand": q["id"], "done": None})
        for p in era2.adults(st):
            p["today"] = {"activity": "採集"}
        g7.region_day(st)
        self.assertTrue(reg["wars"][0]["called_off"])
        self.assertTrue(any("戦に出る人がいなかった" in e["text"] for e in st["events"]))

    def test_defend(self):
        g7, st = self.g7, self.st()
        reg = st["era2"]["g7"]["region"]
        o = next(x for x in st["era2"]["g6"]["others"] if x["id"] == "N1")
        reg["wars"].append({"id": "W1", "att": "N1", "def": "V0", "day": st["day"], "demand": None, "done": None})
        for i, p in enumerate(era2.adults(st)):
            p["today"] = {"activity": "守る" if i < 3 else "採集"}
        p0 = o["people"]
        g7.region_day(st)
        w = reg["wars"][0]
        n = len(era2.adults(self.base))
        self.assertEqual(w["fighters"]["V0"], n, "守るときは、キャンプにいる大人みんな")
        self.assertAlmostEqual(w["Sd"], 3 + 0.5 * (n - 3), places=3)  # 「守る」の人は 1、ほかの大人は 0.5 (村は川ぞい。壁はまだない)
        self.assertEqual(o["people"], p0 - w["dead"]["N1"])

    def test_leave(self):
        g7, st = self.g7, self.st()
        reg = st["era2"]["g7"]["region"]
        o = next(x for x in st["era2"]["g6"]["others"] if x["id"] == "N1")
        q = region.add_demand(reg, o, g7._v0(st), {"草の種": 100}, st["day"])
        reps = g7._rep_of(st)
        h, n = sorted(reps.items())[0]
        ppl = [p["name"] for p in st["people"] if p["alive"] and p.get("household") == h]
        out = g7.leave_households(st, {n: {"leave": True}, "だれか": {"leave": True}})
        self.assertEqual(out, [h])
        self.assertTrue(all(not p["alive"] and p.get("left") for p in st["people"] if p["name"] in ppl))
        f = st["era2"]["g5"]["fissions"][-1]
        self.assertEqual((f["household"], f["dispute"], f["why"]), (h, None, "ほかの村の求め"))
        self.assertEqual(g7.leave_households(st, {reps[sorted(reps)[1]]: {"leave": False}}), [])
        q["end"] = st["day"]
        self.assertEqual(g7.leave_households(st, {reps[sorted(reps)[1]]: {"leave": True}}), [], "求めも貢ぎも税もなければ、出ていく欄はない")

    def test_councils(self):
        g7, st = self.g7, self.st()
        reg = st["era2"]["g7"]["region"]
        D = st["day"]
        st["day"] = (D + 1) // era2.YEAR * era2.YEAR + era2.YEAR - 1  # 次の年の終わりの日 (写しの中だけ)
        g7.region_year(st)
        c = reg["councils"]
        self.assertLessEqual(len(c["ask"]), region.COUNCIL_MAX)
        if not c["ask"]:
            self.skipTest("分かれ目がなかった")
        sid = c["ask"][0]
        txt = g7.council_prompt(st, sid)
        self.assertIn("## 答えの形 (JSON)", txt)
        for w in ("王", "国", "神", "銀", "お金", "見込み", "%"):
            self.assertNotIn(w, txt)
        pts = c["points"][sid]
        key = pts[0].get("demand") or pts[0].get("tie") or "分かれるか"
        choice = {"求められた": "戦う", "払い続けるか": "やめる", "分かれるか": "分かれる"}[pts[0]["kind"]]
        raw = {sid: json.dumps({"choice": {key: choice}, "stance": "守る", "say": "", "why": ""}, ensure_ascii=False)}
        g7.apply_councils(st, raw)
        self.assertEqual(c["answers"][sid][key], choice)
        self.assertEqual(next(o for o in st["era2"]["g6"]["others"] if o["id"] == sid)["stance"], "守る")
        for other in c["ask"][1:]:
            self.assertEqual(c["answers"][other], {}, "答えのない集落は決まりの手")
        st["day"] += 0
        out = g7.begin(st, {}, None)
        self.assertEqual(reg["pending"], [], "待ちは夏の集まりの日に決まる")
        if pts[0]["kind"] == "求められた":
            q = next(x for x in reg["demands"] if x["id"] == key)
            self.assertEqual((q["answer"], q["how"]), (choice, "集まり"))
        self.assertIsInstance(out, list)


# ---------------------------------------------------------------- K
class K_Joints(unittest.TestCase):
    """つなぎ目 (4.F): 税・板に書く掟・換算・利子・牛と犂・壁・病・戦に勝ったとき・貢ぎをやめる (メモリの中の写し)"""

    @classmethod
    def setUpClass(cls):
        if not is_g6(real_state()):
            raise unittest.SkipTest("本物の state が G6 でない")
        import g7
        cls.g7 = g7
        cls.base = g7_state()

    def st(self):
        return copy.deepcopy(self.base)

    def law(self, st, **kw):
        l = add_law(st)
        l["status"] = "採用"
        self.g7.law_extra(st, l, kw)
        return l

    def test_law_extra(self):
        st = self.st()
        l = self.law(st, tax={"what": "草の種", "share": 0.9}, rate={"ヤギ": 300})
        self.assertEqual(l["tax"], {"what": "草の種", "share": 0.5}, "割合は 5 割まで")
        self.assertEqual(l["rate"], {"ヤギ": 300})
        self.assertIn("取り立て: 家の倉の草の種の 5 割", l["text"])
        l2 = self.law(st, tax=None, rate=None)
        self.assertNotIn("tax", l2)
        self.assertNotIn("rate", l2)

    def test_tax(self):
        g7, st = self.g7, self.st()
        l = self.law(st, tax={"what": "草の種", "share": 0.1})
        homes = sorted(era2._homes(st))
        for h in homes:
            era2._house(st, h)["store"].append({"kind": "草の種", "kcal": 1000 * era2.GRAIN, "day": st["day"]})
        p = next(q for q in era2.adults(st) if q.get("household"))
        st["era2"]["g7"]["season_days"] = {p["name"]: {"取り立てる": 3}}
        v0 = era2._g6_have(st, "村", "草の種")
        g7.collect_tax(st, 1.0)
        e = st["events"][-1]
        self.assertEqual(e["type"], "取り立て")
        self.assertEqual(len(e["data"]["homes"]), 4, "1 日に 1 家 (3 日) と、自分の家")
        self.assertIn(p["household"], e["data"]["homes"])
        self.assertEqual(era2._g6_have(st, "村", "草の種") - v0, e["data"]["goods"]["草の種"])
        self.assertGreater(e["data"]["goods"]["草の種"], 0)
        self.assertEqual(st["era2"]["g7"]["coll"][-1]["kind"], "税")
        g7.collect_tax(st, 1.0)
        e2_ = st["events"][-1]
        self.assertFalse(set(e2_["data"]["homes"]) & set(e["data"]["homes"]), "同じ年に同じ家からは 2 度集めない")
        st["day"] += era2.YEAR  # 次の年はまた集める
        g7.collect_tax(st, 1.0)
        self.assertIn(p["household"], st["events"][-1]["data"]["homes"])
        self.assertIn("取り立てる", g7.acts(st))
        self.assertIn("取り立て", g7.whats(st))

    def test_write_laws(self):
        g7, st = self.g7, self.st()
        ls = [self.law(st) for _ in range(3)]
        g6 = era2._g6(st)
        n = era2.adults(st)[0]["name"]
        g6["open"]["板"] = True
        g6["jobs"][n] = {"activity": "記録をつける", "what": ["掟"], "how": "板"}
        st["era2"]["g7"]["jobs7"] = {n: {"laws": [ls[2]["id"], ls[0]["id"]]}}
        g7.write_laws(st, {n: 1})
        self.assertTrue(ls[2].get("written") and not ls[0].get("written"), "1 日に 1 本、laws の順")
        g6["jobs"][n]["how"] = "数え札"
        g7.write_laws(st, {n: 5})
        self.assertFalse(ls[0].get("written"), "数え札では書けない")

    def test_rate_and_judged(self):
        g7, st = self.g7, self.st()
        self.assertEqual(g7.goat_worth(st), (era2.GOAT_WORTH, None))
        l = self.law(st, rate={"ヤギ": 100})
        self.assertEqual(g7.goat_worth(st)[1], None, "板に書くまでは使わない")
        l["written"] = {"day": st["day"], "by": "x", "how": "板"}
        self.assertEqual(g7.goat_worth(st), (100 * era2.GRAIN, l))
        a, b = sorted(era2._homes(st))[:2]
        era2._house(st, a)["store"] = []
        for x in [x for x in st["era2"]["goats"] if x.get("owner") == a]:
            x["owner"] = None
        for i, x in enumerate(st["era2"]["goats"][:3]):
            x["owner"] = a
        got = {}
        paid, words = era2._pay(st, a, b, 250 * era2.GRAIN, 100 * era2.GRAIN, got)
        self.assertEqual(got["goats"], 3, "1 頭 = 100 つかみで 250 つかみなら 3 頭 (半頭分からは渡す)")
        d = {"id": "M1", "kind": "倉", "from": b, "against": a, "harm": 250, "what": "x", "status": era2.OPEN}
        era2._g5(st)["disputes"].append(d)
        for x in st["era2"]["goats"][3:6]:
            x["owner"] = a
        era2._verdict(st, d, "つぐなう", "集まり", None)
        self.assertEqual(d["law"], l["id"])
        self.assertEqual(st["era2"]["g7"]["judged"][-1]["law"], l["id"])
        self.assertEqual(st["era2"]["g7"]["judged"][-1]["kind"], "換算")

    def test_loan(self):
        g7 = self.g7
        d = {"goods": {"草の種": 1000}, "rate": 0.2}
        self.assertEqual(g7.owed(d), {"草の種": 1200})
        self.assertEqual(g7.owed({"goods": {"草の種": 7}, "rate": 0.25}), {"草の種": 9})
        self.assertTrue(g7.loan_refused({"bad": None}, 0.3))
        self.assertFalse(g7.loan_refused({"bad": 5}, 0.5))
        self.assertFalse(g7.loan_refused({"bad": None}, 0.2))
        c6 = {"rate": {"T1": {"a": (0.2, 3), "b": (0.1, 1)}}}
        self.assertEqual(g7.loan_rate({}, c6, {"id": "T1"}, None), 0.2)
        self.assertEqual(g7.loan_rate({}, c6, {"id": "T1"}, "b"), 0.1, "まとめ役が書いていればその数")

    def test_cattle_and_plough(self):
        g7, st = self.g7, self.st()
        st["era2"]["cattle"] = [{"id": 1, "sex": "メス", "born": st["day"] - 3 * era2.YEAR + 1, "owner": None},
                                {"id": 2, "sex": "メス", "born": st["day"] - 2 * era2.YEAR, "owner": None}]
        cap0 = era2.pasture_cap(self.base)
        self.assertEqual(era2.pasture_cap(st), max(0, cap0 - 10), "牛 1 頭はヤギ 5 頭分")
        n = len(st["era2"]["cattle"])
        st["day"] = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1  # 春の終わり
        st["era2"]["tended_run"] = 99
        g7.cattle_season(st, random.Random(1), 1.0, "夏")
        self.assertEqual(len(st["era2"]["cattle"]), n, "子牛は春のはじめだけ")
        g7.cattle_season(st, random.Random(1), 1.0, "春")
        born = len(st["era2"]["cattle"]) - n
        self.assertIn(born, (0, 1, 2))
        # 犂: H7-06 ができて、2 歳以上の牛が 2 頭
        st["era2"]["g7"]["hints"]["tech"]["H7-06"] = {"open": 1, "done": 2, "source": "ヒント", "first": 1, "progress": 999, "last": 1, "wait": None}
        p = era2.adults(st)[0]
        st["era2"]["g7"]["jobs7"] = {p["name"]: {"plough": True}}
        self.assertEqual(g7.plough_work(st, p, 4.0), 12.0)
        self.assertTrue(st["events"][-1]["data"]["plough"])
        q = era2.adults(st)[1]
        st["era2"]["g7"]["jobs7"][q["name"]] = {"plough": True}
        self.assertEqual(g7.plough_work(st, q, 4.0), 12.0 if sum(1 for c in st["era2"]["cattle"] if st["day"] - c["born"] >= 2 * era2.YEAR) >= 4 else 4.0,
                         "牛 2 頭で 1 人")

    def test_wall(self):
        g7, st = self.g7, self.st()
        p = era2.adults(st)[0]
        st["era2"]["g7"]["jobs7"] = {p["name"]: {"build": "壁"}}
        self.assertTrue(g7.wall_job(st, p))
        st["era2"]["g7"]["wall_work"] = g7.WALL_DAYS - 1
        g7.wall_day(st, p, {})
        self.assertEqual(st["era2"]["walls"], st["day"])
        self.assertFalse(g7.wall_job(st, p), "できたあとは住まいを建てる")
        self.assertEqual(g7._v0(st)["walls"], st["day"])

    def test_sick(self):
        g7, st = self.g7, self.st()
        sea = __import__("world").season(st["day"])
        st["era2"]["g7"]["sick"] = {"year": st["day"] // era2.YEAR, "season": sea}
        self.assertEqual(g7.sick_mult(st), 3)
        st["era2"]["g7"]["sick"]["season"] = "冬" if sea != "冬" else "夏"
        self.assertEqual(g7.sick_mult(st), 1)
        # 病の季節も、塩 7 の列から引く数は同じ
        counts = []
        for s in (sea, "x"):
            st2 = self.st()
            st2["era2"]["g7"]["sick"] = {"year": st2["day"] // era2.YEAR, "season": s}
            n = [0]
            old = era2._rng

            def spy(state, salt, n=n):
                r = old(state, salt)
                if salt == 7:
                    f = r.random

                    def rnd():
                        n[0] += 1
                        return f()
                    r.random = rnd
                return r
            era2._rng = spy
            try:
                era2._season_end(st2, 1.0)
            finally:
                era2._rng = old
            counts.append(n[0])
        self.assertEqual(counts[0], counts[1])

    def test_captives_and_tribute_answers(self):
        g7, st = self.g7, self.st()
        real = {n: {"captives": "連れて帰る", "tribute": {"K1": "やめる"}} for n in era2.answerers(st)}
        g7.captives_answer(st, real)
        self.assertEqual(st["era2"]["g7"]["captives"]["choice"], "連れて帰る")
        reg = st["era2"]["g7"]["region"]
        o = era2._g6(st)["others"][0]
        reg["ties"] = [{"id": "K1", "payer": "V0", "payee": o["id"], "goods": {"草の種": 100}, "since": 1, "paid": [1], "missed": 0, "status": "続く",
                        "end": None, "fixed": None}]
        self.assertIn("tribute", g7.fields_on(st))
        v = g7.tribute_answers(st, real)
        self.assertEqual(v, {"K1": "やめる"})
        __import__("region").decide(reg, g7._setts(st), st["day"] + 1, village=v, make=g7._maker(st), out=[])
        self.assertEqual(reg["ties"][0]["status"], "切れた")
        self.assertEqual(reg["ties"][0]["why"], "やめた")


# ---------------------------------------------------------------- L
class L_Yardstick(unittest.TestCase):
    """物差し (4.D): 決める段 (税だけなら 0)・取り立ての年・F6・条件ごとの止まり・marks・目安 (メモリの中の写し。乱数は引かない)"""

    @classmethod
    def setUpClass(cls):
        if not is_g6(real_state()):
            raise unittest.SkipTest("本物の state が G6 でない")
        import g7
        import yardstick
        cls.g7, cls.y = g7, yardstick
        cls.base = g7_state()

    def st(self):
        return copy.deepcopy(self.base)

    def test_tax_only_is_zero(self):
        y, st = self.y, self.st()
        a, b, c = sorted(era2._homes(st))[:3]
        p = next(q for q in era2.adults(st) if q.get("household") == c)
        world.log(st, "取り立て", p["name"], "試し", law="L1", homes=[a, b], goods={"草の種": 10}, moves=[["村", 1, {"草の種": 10}, []]])
        self.assertEqual(y.officials(st), {p["name"]: ["V0"]})
        vg = y.village_group(y.levels(st))
        self.assertEqual(vg["D"] if vg else 0, 0, "村の中の税だけなら D 0")

    def test_tribute_years(self):
        y, st = self.y, self.st()
        g = st["era2"]["g7"]
        D0 = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
        for k in (0, 1):
            st["day"] = D0 + k * era2.YEAR
            g["coll_seasons"] = g.get("coll_seasons", []) + [{"day": st["day"] - 10, "full": True, "how": "板", "n": 1}]
            y._tribute_year(st)
        self.assertEqual(g["tribute2_day"], st["day"])
        self.assertEqual(g["marks"][-1]["what"], "条件 2")
        st2 = self.st()
        g2 = st2["era2"]["g7"]
        for k, full in ((0, True), (1, False)):
            st2["day"] = D0 + k * era2.YEAR
            g2["coll_seasons"] = g2.get("coll_seasons", []) + [{"day": st2["day"] - 10, "full": full, "how": None, "n": 1}]
            y._tribute_year(st2)
        self.assertIsNone(g2.get("tribute2_day"), "全部残せなかった年があると数えない")

    def test_season_end_and_f6(self):
        y, st = self.y, self.st()
        g = st["era2"]["g7"]
        ads = era2.adults(st)
        k = max(1, math.ceil(0.1 * len(ads)))
        for _ in range(4):
            g["season_days"] = {p["name"]: {"記録をつける": 20} for p in ads[:k]}
            y.season_end(st, 1.0)
        self.assertEqual(g["f6_run"], 4)
        self.assertIn("F6", g["reached"])
        self.assertTrue(any(m["what"] == "F6" for m in g["marks"]))
        self.assertTrue(self.g7.reached(st, "F6"))
        ind = era2.indicators(st)
        for key in ("g7_levels", "g7_tiers", "g7_village", "g7_tribute2_day", "g7_written_laws", "g7_law_judged", "g7_interest", "g7_role_share"):
            self.assertIn(key, ind)
        r = era2.check_substeps(st) if hasattr(era2, "check_substeps") else None
        self.assertTrue(any(x["g"] == "G7" and x["f"] == "F6" for x in st["era2"].get("substeps", [])) or r is None)

    def test_stall(self):
        y, st = self.y, self.st()
        g = st["era2"]["g7"]
        D0 = (st["day"] // era2.YEAR + 1) * era2.YEAR - 1
        for k in range(9):
            st["day"] = D0 + k * era2.YEAR
            y._stall(st, [])
        self.assertEqual(g["stall"]["c1"]["ask"], g["stall"]["c1"]["since"] + 8, "8 年進まなければ報告で相談")
        st["day"] = D0 + 16 * era2.YEAR
        y._stall(st, [])
        self.assertEqual(self.g7.consult_why(st)["why"], "c1")


class M_Fixes1022(unittest.TestCase):
    """2026-10-22 の 3 つの直し: 集まり直しの歩の記録 (理由を g7.step.answer_day の答えから・作れなかったら終わりのコード 6)・
    飢饉で出ていく見込みを日数に合わせる (G7 から)・なくなった集落の申し出を外す (G7 から)。本物の data にはさわらない"""

    def g7st(self):
        st = real_state()
        if "g7" in (st.get("era2") or {}):
            return st
        if is_g6(st):
            return g7_state()
        self.skipTest("本物の state が G6 でも G7 でもない")

    # ---- 1. 記録: 集まり直し (kind が 年 でない歩) の「自分」の理由は、g7.step.answer_day の答えから
    def builder(self, answers, C, why_on=True):
        sys.path.insert(0, str(HERE))
        import build_records
        b = build_records.Builder.__new__(build_records.Builder)
        b.answers, b.snaps, b.state = answers, {}, {"laws": [], "knowledge_log": []}
        b.byname = {"X": {"household": "H1"}, "R": {"household": "H2"}, "Y": {"household": "H2"}}
        b.t_out, b.t_in = {k: None for k in b.byname}, {k: 0 for k in b.byname}
        b.reps_at = lambda a, P: {"R"}
        b.leader_at = lambda a, P: None
        b.alive_at = lambda n, d: True
        b.is_adult = lambda n, d, P: True
        b.age = lambda n, d: 30
        b.why_asked = lambda d: why_on
        b.P = b.H = lambda x: x
        c = {"D": 6479, "a": 6450, "P": None, "C": C, "demo": {"joined": []}, "present": ["X", "Y"], "rds": [], "act": {}, "out": {},
             "said": {}, "inj": {}, "rain_out": {}}
        return {r["person_id"]: r for r in b.person_rows(c)}

    def test_records_remeeting_why(self):
        w1 = "蓄えが空で食べ物が足りないから。林で木の実や芋を見つけるのが得意なので、二人以上でいっしょに行って見つけた量を夜に報告する。"
        w2 = "東の林には春でも芋が多いと聞いた。芋は一人 8 本で、いまは一番たしかな食べ物だから。"
        ans = {6450: {"season": {}},  # 季節の最初の集まり (X も R も答えていない。前はここを sea[n] で読んで KeyError)
               6477: {"season": {"X": {"job": {"activity": "採集", "place": "林", "why": w1}},
                                 "R": {"job": {"activity": "採集"}, "family": {"Y": {"activity": "採集", "why": w2}}}}}}
        C = {"g7": {"src": {"X": "自分", "Y": "代表が割り振った", "R": "自分"}, "step": {"answer_day": 6477, "sample": [], "donor": {}}}}
        rows = self.builder(ans, C)
        self.assertEqual((rows["X"]["decided_by"], rows["X"]["why"], rows["X"]["why_by"]), ("自分", w1, "自分"))
        self.assertEqual((rows["Y"]["decided_by"], rows["Y"]["why"], rows["Y"]["why_by"]), ("代表が割り振った", w2, "代表"))
        self.assertEqual(rows["X"]["plan_answer_day"], 6477)
        # 答えが見つからなくても止まらない (理由なし)
        rows = self.builder({6450: {"season": {}}}, C)
        self.assertIsNone(rows["X"]["why"])
        # G6 まで (g7 がない): 前と同じに、季節の最初の集まりの答えから
        rows = self.builder({6450: {"season": {"X": {"job": {"activity": "採集", "why": w1}}}}}, None)
        self.assertEqual((rows["X"]["decided_by"], rows["X"]["why"]), ("自分", w1))
        self.assertNotIn("plan_answer_day", rows["X"])

    def test_records_failure_exit(self):
        import step
        saved = (step.DATA, step.RECORDS_ON, list(step.RECORDS_FAILED))
        d = tmpdir()
        try:
            step.DATA, step.RECORDS_ON = d / "nothing", True  # state.json がない → build_records.py が 0 でないコードで終わる
            step.RECORDS_FAILED.clear()
            step._records(None)
            self.assertTrue(step.RECORDS_FAILED, "作れなかったことを覚える")
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
                step._records_exit()
            self.assertEqual(cm.exception.code, 6)
            self.assertRegex(buf.getvalue(), r"(?m)^RECORDS failed ")
            step.RECORDS_FAILED.clear()
            step._records_exit()  # 失敗がなければ何もしない
        finally:
            step.DATA, step.RECORDS_ON = saved[0], saved[1]
            step.RECORDS_FAILED[:] = saved[2]
            shutil.rmtree(d, ignore_errors=True)
        js = (HERE / "society2_seasons_workflow.js").read_text(encoding="utf-8")
        self.assertIn("'records failed'", js)
        self.assertIn("/^RECORDS failed/m", js)

    # ---- 2. 飢饉で出ていく: G7 からは 1 − 0.6^(日数/30)。G6 までは 4 割のまま (乱数を引く回数も同じ)
    def famine(self, st, days, r):
        st = copy.deepcopy(st)
        for p in era2.adults(st)[:5]:
            p["origin"], p["hunger"] = "よそから来た", 0.7
        draws = []

        class R:
            def random(self):
                draws.append(1)
                return r
        saved = era2._rng
        era2._rng = lambda state, salt: R()
        try:
            n0 = sum(1 for p in st["people"] if p["alive"])
            era2._famine_leave(st, days)
        finally:
            era2._rng = saved
        return n0 - sum(1 for p in st["people"] if p["alive"]), len(draws)

    def test_famine_scaled(self):
        st = self.g7st()
        self.assertAlmostEqual(1 - 0.6 ** (3 / 30), 0.0498, places=3)
        gone, k = self.famine(st, 3, 0.1)
        self.assertEqual((gone, k), (0, 5), "3 日の集まり直しでは 5% ほど (0.1 では出ていかない)")
        gone, k = self.famine(st, 3, 0.04)
        self.assertGreaterEqual(gone, 5)
        gone, k = self.famine(st, 30, 0.39)
        self.assertGreaterEqual(gone, 5, "30 日なら 4 割のまま")
        gone, k = self.famine(st, 30, 0.41)
        self.assertEqual(gone, 0)
        # 10 回の 3 日 ≒ 30 日 1 回 (季節あたり 4 割)
        self.assertAlmostEqual(1 - (0.6 ** (3 / 30)) ** 10, 0.4, places=9)
        g6 = copy.deepcopy(st)
        g6["era2"].pop("g7")
        gone, k = self.famine(g6, 3, 0.39)
        self.assertEqual(k, 5, "G6 まで: 引く回数は同じ")
        self.assertGreaterEqual(gone, 5, "G6 まで: 日数によらず 4 割")

    # ---- 3. なくなった集落の申し出を外す (お題の「ほかの村」の節が止まらない)
    def test_drop_gone_offers(self):
        import g7
        st = copy.deepcopy(self.g7st())
        g6 = st["era2"]["g6"]
        o1, o2 = g6["others"][0], g6["others"][1]
        g6["offers"] = [{"kind": "交換", "give": {"黒曜石": 5}, "want": {"土器": 1}, "id": "T900", "other": o1["id"], "day": st["day"]},
                        {"kind": "交換", "give": {"黒曜石": 5}, "want": {"土器": 1}, "id": "T901", "other": o2["id"], "day": st["day"]}]
        o1["gone"] = st["day"]
        g6["trips"] = {k: v for k, v in g6.get("trips", {}).items() if v.get("to") != o1["id"]}
        g7.drop_gone(st)
        self.assertNotIn(o1["id"], [o["id"] for o in g6["others"]])
        self.assertEqual([off["id"] for off in g6["offers"]], ["T901"], "なくなった集落の申し出だけ外す")
        txt = era2._g6_text(st)  # 前はここで TypeError ('NoneType' object is not subscriptable)
        self.assertIn("[T901]", txt)
        self.assertNotIn("[T900]", txt)
        # 交換に行く途中の人のために残した集落でも、なくなっていれば申し出はない
        st2 = copy.deepcopy(self.g7st())
        g6b = st2["era2"]["g6"]
        o = g6b["others"][0]
        o["gone"] = st2["day"]
        g6b["offers"] = [{"kind": "交換", "give": {"黒曜石": 5}, "want": {"土器": 1}, "id": "T902", "other": o["id"], "day": st2["day"]}]
        g6b["trips"] = {"X1": {"to": o["id"], "state": "行く"}}
        g7.drop_gone(st2)
        self.assertIn(o["id"], [x["id"] for x in g6b["others"]])
        self.assertEqual(g6b["offers"], [])
        era2._g6_text(st2)


class N_FieldText(unittest.TestCase):
    """2026-10-22: 年の集まりのお題の、畑の文。草の種は sow の量でまかれる (仕事の「種まき」は持ち物の「種」を埋める)。
    実りは秋・冬・春の畑仕事 (草取り) で増える (era2 の need = まいた種 × 0.15 + 10、min(1, 0.3 + 0.7 × work / need))。夏の畑仕事は刈り入れ"""

    def test_year_prompt(self):
        st = real_state()
        if "g7" not in (st.get("era2") or {}):
            if not is_g6(st):
                self.skipTest("本物の state が G6 でも G7 でもない")
            st = g7_state()
        import g7
        y = to_year_end(st)
        p = next(q for q in era2.adults(y) if q["name"] in era2.answerers(y))
        t = g7.year_prompt(y, p, g7.since(y))
        self.assertNotIn("蓄えの草の種を畑にまく季節", t)
        self.assertIn("- 秋: 秋のはじめに、sow に書いた量の蓄えの草の種が畑にまかれる (仕事の「種まき」はいらない。"
                      "「種まき」は持ち物の「種」を埋めて木を育てる仕事)", t)
        self.assertIn("- 実りと畑仕事: まいた畑の実りは、秋・冬・春の畑仕事 (草取り) で増える。"
                      "畑 1 つに要る草取りは (まいた種 つかみ × 0.15 + 10) 時間で、草取りがなければ実りは 3 割", t)
        self.assertIn("夏の畑仕事は刈り入れ", t)
        self.assertNotIn("実りと畑仕事", era2.season_prompt(y, p, g7.since(y)), "季節のお題 (G1〜G6 と同じ文) は変えない")


if __name__ == "__main__":
    unittest.main(verbosity=2)
