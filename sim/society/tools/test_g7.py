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
        self.assertEqual(era2.ORDER2[-3:], ["G7", "G8", "G9"])  # 2026-10-25: G8 (外からの押し) を足した。2026-10-29: G9 (遠くとの商い)
        self.assertEqual(era2.NAMES2["G7"], "王と役所")
        self.assertEqual(era2.NAMES2["G8"], "外からの押し")
        self.assertEqual(era2.NAMES2["G9"], "遠くとの商い")
        self.assertEqual(era2.PART_END["G9"], 5)
        self.assertEqual([x[0] for x in era2.SUBSTEPS["G9"]], ["F1", "F2", "F3", "F4"])
        self.assertLessEqual(set(era2.CRITERIA), set(era2.ORDER2))
        self.assertTrue(era2.era_at_least({"era": "G7"}, "G6") and era2.era_at_least({"era": "G7"}, "G3"))
        self.assertFalse(era2.era_at_least({"era": "G6"}, "G7"))
        self.assertEqual(era2.PART_END["G6"], 4)
        self.assertNotIn("G7", era2.PART_END)
        self.assertNotIn("G8", era2.PART_END)
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
        """2026-10-25: G8 (外からの押し) を足したので、G7 の条件がそろうと G8 に進む (G8 の世界になる)。G8 の条件がそろうと次の G (G9) を待つ"""
        import g7
        st = g7_state()
        g = st["era2"]["g7"]
        st["era2"].setdefault("substeps", []).extend({"g": "G7", "f": f, "name": f, "day": st["day"]} for f in ("F3", "F4"))
        g["tribute2_day"] = st["day"]
        g["reached"] = {"F3": st["day"], "F4": st["day"]}
        self.assertIs(era2.check(st), True)
        self.assertEqual(st["era"], "G8")
        st["hold"] = True
        self.assertEqual(era2.hold_why(st)[0], "phase")
        self.assertEqual((g["world"], g["count"]), (g7.G8_WORLD, "v2"))
        self.assertTrue(g.get("strong"))
        self.assertEqual(g["before"]["G7"]["tribute2_day"], st["day"], "G7 の物差しの数は g7.before に移す")
        self.assertNotIn("tribute2_day", g)
        st["hold"] = False
        self.assertFalse(era2.check(st), "G8 に入った日には、まだ届いていない (G8 の F で数え直す)")
        st["era2"]["substeps"].extend({"g": "G8", "f": f, "name": f, "day": st["day"]} for f in ("F3", "F4"))
        g["tribute2_day"] = st["day"]
        self.assertEqual(era2.check(st), "wait", "G9 のコードがまだない")
        st["hold"] = True
        self.assertEqual(era2.hold_why(st)[0], "wait")
        self.assertFalse(era2.check(st), "待ちは一度だけ")
        self.assertEqual((era2.PART_END, era2.ENTRANCE), ({"G6": 4, "G9": 5, "G12": 6, "G14": 7, "G15": 8}, "G15"))

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
                           accept_rule={"よその群れ": True}, feast=["春"], seal_store=["冬"])
        g7.apply_year(st, ans)
        st["day"] += 60  # 秋の終わり (冬のはじめは答えのない季節。秋は毎年集まる)
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
        self.assertEqual(e2["g6"]["store_sealed"], e2["step_day"], "封をする季節 (冬)")
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
        self.assertEqual(g7.ask_next(st), "秋", "寄らない年も、秋は集まる")
        st["day"] += 30
        self.assertIsNone(g7.ask_next(st), "冬は集まらない")
        st["day"] += 30
        self.assertIsNone(g7.ask_next(st), "春は集まらない")
        st["day"] -= 60
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

    def test_autumn(self):
        """秋の集まり (2026-10-22 本人の決め): 秋は毎年、季節のお題で大人 (答える人) みんなに聞く。答えはその秋だけ。冬と春は年の予定で進む"""
        st, g7 = to_year_end(self.st()), self.g7
        G = st["era2"]["g7"]
        G["zoom"] = None
        y = {s: {"job": {"activity": "採集", "place": "camp"}, "pick": 0, "plant": 0, "harvest": 0} for s in g7.SEASONS}
        y["秋"]["sow"] = 700
        y["冬"]["job"] = {"activity": "ヤギの世話", "place": "camp"}
        g7.apply_year(st, {n: json.dumps({"say": [], "year": y, "feeling": "試し"}, ensure_ascii=False) for n in era2.answerers(st)})
        D0 = st["day"]
        self.assertEqual(G["answer_day"], D0)
        st["day"] += 30  # 夏の終わり: 次は秋
        self.assertEqual(g7.ask_next(st), "秋")
        who = era2.answerers(st)
        self.assertEqual(set(who), set(g7.answerers(st)), "答える人は年の集まりと同じ (見本の家の代表とまとめ役)")
        self.assertTrue(who)
        p = next(q for q in era2.adults(st) if q["name"] == who[0])
        t = era2.season_prompt(st, p, g7.since(st))
        self.assertIn("秋は毎年、季節のはじめに集まって、畑と種を見てから、この秋の仕事とまく量を決め直す (冬と春は、年の集まりで決めた予定で進む)", t)
        self.assertIn("\n- 実りと畑仕事: まいた畑の実りは、秋・冬・春の畑仕事 (草取り) で増える。", t)
        self.assertIn("草取りがなければ実りは 3 割", t)
        self.assertIn("残りはまく人の家の倉の草の種からまかれる", t)
        self.assertIn("季節のはじめの集まり", g7.meeting_word(st))
        self.assertIn('"sow": 0, ', t, "秋のお題は sow を書ける")
        self.assertNotIn("今年は季節ごとに集まる", t)
        D1 = st["day"]
        sa = {"say": [], "job": {"activity": "畑仕事", "place": "camp"}, "sow": 100, "pick": 0, "plant": 0, "harvest": 0, "feeling": "秋の気持ち"}
        g7.apply_year(st, {n: json.dumps(sa, ensure_ascii=False) for n in who})
        self.assertEqual(set(G["plan"]), set(who), "秋の集まりは年の予定を消さない")
        self.assertEqual((G["step"]["ask"], G["step"]["answer_day"], G["answer_day"]), ("秋", D1, D1))
        self.assertEqual(G["src"][who[0]], "自分", "秋の仕事は秋の答えから")
        self.assertEqual(p["plan"]["activity"], "畑仕事")
        self.assertEqual(st["era2"]["jobs"][who[0]]["sow"], 100, "まく量は秋の答えから (年の予定の 700 ではない)")
        self.assertEqual(g7.plan_day(st), D0)
        st["day"] += 30  # 秋の終わり: 冬は集まらない (年の予定で進む)
        self.assertIsNone(g7.ask_next(st))
        G["ask"] = None
        g7.apply_plan(st)
        self.assertEqual((G["step"]["how"], G["step"]["answer_day"]), ("方針", D0), "冬の仕事を決めたのは夏の年の集まり")
        self.assertEqual(G["src"][who[0]], "年の答え (自分)")
        self.assertEqual(p["plan"]["activity"], "ヤギの世話")
        st["day"] += 30
        self.assertIsNone(g7.ask_next(st), "春も集まらない")
        self.assertEqual(g7.digest_head(st), f"この前の集まり ({D1 + 1} 日目) からのこと", "お題の「この前の集まり」は秋の集まり")
        st["day"] += 30
        self.assertEqual(g7.ask_next(st), "年", "夏は年の集まり (季節のお題ではない)")
        # 寄る年 (と、蓄えが尽きた年) の秋は、今までどおり寄る季節
        st["day"] = D1
        G["zoom"] = {"year": (D1 + 1) // era2.YEAR, "why": ["Z5"], "day": D1}
        self.assertEqual(g7.ask_next(st), "寄る")
        # 年の集まりのお題: 秋は秋のはじめにも集まると書く
        y2 = to_year_end(self.st())
        ty = g7.year_prompt(y2, next(q for q in era2.adults(y2) if q["name"] == p["name"]), g7.since(y2))
        self.assertIn("秋は、秋のはじめにも集まって、畑と種を見てから、秋の仕事とまく量 (sow) を決め直す (year の秋は、そのときの見込み)。ほかの季節は集まらない。", ty)

    def test_g6_autumn_unchanged(self):
        """G6 の秋のお題には、秋の集まりの文は出ない (G6 は毎季節集まる。お題は前のまま)"""
        st = real_state()
        st["day"] = st["day"] // era2.YEAR * era2.YEAR + era2.SEASON_DAYS - 1  # 夏の終わり (次は秋)。お題の文だけ見る
        p = next(q for q in era2.adults(st) if q["name"] in era2.answerers(st))
        t = era2.season_prompt(st, p, st["era2"].get("last_first", 0))
        self.assertIn(" 日目、秋。", t)
        self.assertIn('"sow": 0, ', t)
        self.assertNotIn("秋は毎年", t)
        self.assertNotIn("草取りがなければ実りは 3 割", t)

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
const run = async (args, start, mode, autumn) => {
  let day = start
  const labels = []
  const meetOf = (d) => ((d + 1) % 120 === 0 ? '年' : autumn && (d + 1) % 120 === 30 ? '秋' : 'none')
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
  const c = await run({ mode: 'year', years: 1 }, 5519, 'year', true)
  console.log(JSON.stringify({ a: { why: a.res.why, stopped: a.res.stopped, labels: a.labels }, b: { why: b.res.why },
                               c: { why: c.res.why, stopped: c.res.stopped, labels: c.labels } }))
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
        c = out["c"]  # 秋の集まり (MEET 秋) の歩も、役を演じる体を起こす
        self.assertEqual((c["why"], c["stopped"]), ("end", 5639))
        roles = [x for x in c["labels"] if re.match(r"d\d+ (ソル|ミナ|カイ)", x)]
        self.assertEqual({x.split()[0] for x in roles}, {"d5519", "d5549"}, "年の集まりと秋の集まり")
        self.assertEqual(sum(1 for x in c["labels"] if x.endswith("season step")), 4)

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
        # 秋の集まり (2026-10-22 本人の決め): 夏の終わりの歩は、季節のお題で答える (年の集まりと同じ人)
        d2, meet, names2, feel2 = self.who()
        self.assertEqual((d2, meet), (d1 + 30, "秋"))
        self.assertTrue(names2 and len(set(names2) & set(names)) >= len(names) // 2, "答える人は年の集まりとほぼ同じ (見本の家の代表とまとめ役。代表は季節のあいだに変わりうる)")
        z = (self.data / "prompts" / f"day{d2:03d}" / "season" / f"{names2[0]}.md").read_text(encoding="utf-8")
        self.assertIn("秋は毎年、季節のはじめに集まって", z)
        self.assertIn('"job": {"activity": "採集", "place": "camp"', z)
        self.assertNotIn('"year": {', z)
        a = self.data / "answers" / f"day{d2:03d}"
        for kind, who in (("season", names2), ("feeling", feel2)):
            (a / kind).mkdir(parents=True, exist_ok=True)
            for n in who:
                txt = ({"say": [], "job": {"activity": "畑仕事", "place": "camp"}, "sow": 10, "pick": 0, "plant": 0, "harvest": 0, "feeling": "秋"}
                       if kind == "season" else {"feeling": "試し", "say": []})
                (a / kind / f"{n}.json").write_text(json.dumps(txt, ensure_ascii=False), encoding="utf-8")
        self.step("season")
        st = json.loads((self.data / "state.json").read_text(encoding="utf-8"))
        self.assertEqual((st["era2"]["g7"]["step"]["ask"], st["era2"]["g7"]["step"]["answer_day"]), ("秋", d2))
        self.assertTrue(st["era2"]["g7"]["plan"], "秋の集まりのあとも年の予定は残る")
        d3, meet, names3, feel3 = self.who()
        self.assertEqual((d3, meet, names3, feel3), (d2 + 30, "none", [], []))
        self.assertFalse((self.data / "prompts" / f"day{d3:03d}").exists(), "集まりのない季節は、お題のフォルダを作らない")
        out = self.step("season")
        self.assertIn(f"この季節は集まらない (年の集まり {d1} 日目の予定と方針で進む)", out)
        st = json.loads((self.data / "state.json").read_text(encoding="utf-8"))
        G = st["era2"]["g7"]
        self.assertEqual((st["day"], G["step"]["how"], G["step"]["answer_day"]), (d3 + 30, "方針", d1))
        self.assertIn("見本から広げた", G["src"].values())
        self.assertTrue(any(e["type"] == "年の名前" and "試しの年" in e["text"] for e in st["events"]))
        # 記録: 1 行 = 1 季節。G7 の季節は decided_by・is_sample・plan_answer_day
        rows = [json.loads(x) for x in (self.data / "records" / "season_person.jsonl").read_text(encoding="utf-8").splitlines()]
        vil = {r["season_end_day"]: r for r in (json.loads(x) for x in (self.data / "records" / "season_village.jsonl").read_text(encoding="utf-8").splitlines())}
        for D, plan_day in ((d1, d0), (d2, d1), (d2 + 30, d2), (d3 + 30, d1)):
            rs = [r for r in rows if r["season_end_day"] == D]
            self.assertTrue(rs, D)
            self.assertEqual(len({r["person_id"] for r in rs}), len(rs), "1 人 1 季節に 1 行")
            ad = [r for r in rs if not r["child"] and r["status_at_end"] == "生きている"]
            self.assertTrue(all(r["plan_answer_day"] == plan_day and "is_sample" in r for r in ad), D)
            self.assertLessEqual({r["decided_by"] for r in ad}, YEAR_SRC | {None})
            self.assertIn("見本から広げた", {r["decided_by"] for r in ad})
            self.assertEqual(vil[D]["answered"]["plan_answer_day"], plan_day)
            self.assertGreater(vil[D]["answered"]["sample_households"], 0)
        self.assertEqual(vil[d3 + 30]["answered"]["season"], 0, "答えのない季節")
        self.assertTrue(any(r["answered"] == "season" for r in rows if r["season_end_day"] == d2))
        self.assertTrue(any(r["decided_by"] == "自分" for r in rows if r["season_end_day"] == d2 + 30), "秋は秋の集まりの答え")
        self.assertTrue(any(r["decided_by"] == "年の答え (自分)" for r in rows if r["season_end_day"] == d3 + 30), "冬は年の答え")


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
        # 2026-10-25: G7 も本人の決めで閉じて G8 (外からの押し) に入れる。2 回目は断る
        r = self.step("next_part", "--closed-by-decision", "もう一度")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("G7 (王と役所): 3 つの条件はそろわないまま、本人の決めで閉じた", r.stdout)
        self.assertIn("強い集落", r.stdout)
        st = json.loads((self.data / "state.json").read_text(encoding="utf-8"))
        self.assertEqual((st["era"], st["era_log"][-1]["g7_closed"], st["era2"]["g7"]["closed"]["note"]), ("G8", self.D, "もう一度"))
        r = self.step("next_part", "--closed-by-decision", "さらにもう一度")
        self.assertEqual(r.returncode, 3)
        self.assertIn("G6 から G7 と、G7 から G8 だけ", r.stdout)


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


class O_SowFromHouse(unittest.TestCase):
    """2026-10-22: 秋の種まき (era2._sow)。G7 では、村の蓄えの草の種が sow の量に足りなければ、残りをまく人の家の倉から出す
    (畑は今までどおりその家のもの)。帳簿 (build_records.ledger) は、家の倉から出た分を家の「まいた (畑)」に入れ、村の分から引く。G6 までは前のまま"""
    U = era2.UNITS["草の種"][1]

    def setup(self, g7_on):
        st = real_state()
        if "g7" not in (st.get("era2") or {}):
            if not is_g6(st):
                self.skipTest("本物の state が G6 でも G7 でもない")
            st = g7_state()
        if not g7_on:  # G6 のふるまい (_fix は "g7" があるかだけを見る)
            del st["era2"]["g7"]
        p = next(q for q in era2.adults(st) if q.get("household"))
        h = p["household"]
        st["store"] = [f for f in st["store"] if f["kind"] != "草の種"]  # 村の蓄えに草の種がない
        house = era2._house(st, h)
        house["store"] = [f for f in house["store"] if f["kind"] != "草の種"] + [{"kind": "草の種", "kcal": 50 * self.U, "day": st["day"]}]
        return st, p, h

    def sow(self, st, p, want):
        import records
        P = records.snapshot(st)
        n0, e0 = len(st["era2"]["fields"]), st["next_event"]
        era2._sow(st, p, want)
        return P, records.snapshot(st), st["era2"]["fields"][n0:], [e for e in st["events"] if e["id"] >= e0]

    def ledger(self, st, P, C, evs):
        sys.path.insert(0, str(HERE))
        import build_records
        b = build_records.Builder.__new__(build_records.Builder)
        b.H = lambda x: x
        b.hname = {}
        fv = {}
        sown = [e for e in evs if e["type"] == "畑" and (e.get("data") or {}).get("seed") is not None]
        for e in sown:  # build_records の出来事の読み方と同じ
            d = e["data"]
            build_records.add(fv.setdefault("まいた (畑)", {}), "草の種", d["seed"] * self.U - d.get("home_kcal", 0))
        c = {"D": st["day"], "a": st["day"], "P": P, "C": C, "flows_v": fv, "sown_ev": sown, "eaten": {},
             "harvest": {"to": {}, "by_household": {}}, "g5": {"feast": None, "payments": [], "fission": None},
             "pests": {"amount": 0, "events": []}, "inherit": [], "pots": {"made": 0, "broken": 0}, "sick": {"made": 0, "broken": 0}, "g6": {"moves": []}, "goats": {"flows": {}, "known": False}}
        return b.ledger(c)

    def test_g7_from_house(self):
        st, p, h = self.setup(True)
        house0 = sum(f["kcal"] for f in era2._house(st, h)["store"] if f["kind"] == "草の種")
        P, C, fields, evs = self.sow(st, p, 30)
        self.assertEqual(len(fields), 1)
        self.assertEqual((fields[0]["seed"], fields[0]["owner"], fields[0]["by"]), (30, h, p["name"]))
        self.assertAlmostEqual(house0 - sum(f["kcal"] for f in era2._house(st, h)["store"] if f["kind"] == "草の種"), 30 * self.U)
        e = next(e for e in evs if e["type"] == "畑")
        self.assertIn(f"草の種 30 つかみ をまいた (家の倉から 30 つかみ)", e["text"])
        self.assertEqual((e["data"]["seed"], e["data"]["household"], e["data"]["home_kcal"]), (30, h, 30 * self.U))
        rows = self.ledger(st, P, C, evs)
        diff = [r for r in rows if r["reason"] == "記録にない差" and r["item"] == "草の種" and r["holder"] in ("村", h)]
        self.assertEqual(diff, [], "村と家の草の種の帳簿が合う")
        sown = {r["holder"]: r["kcal"] for r in rows if r["reason"] == "まいた (畑)"}
        self.assertEqual(sown, {h: -30 * self.U}, "家の倉の分は家の帳簿に、村の帳簿には出ない")
        # 家の倉にも足りなければ、ある分だけ (50 つかみ のうち残り 20)
        P, C, fields, evs = self.sow(st, p, 40)
        self.assertEqual([f["seed"] for f in fields], [20])
        # 家の倉もからなら、畑はできない
        P, C, fields, evs = self.sow(st, p, 10)
        self.assertEqual(fields, [])

    def test_g7_village_then_house(self):
        st, p, h = self.setup(True)
        st["store"].append({"kind": "草の種", "kcal": 12 * self.U, "day": st["day"]})
        P, C, fields, evs = self.sow(st, p, 20)
        self.assertEqual([f["seed"] for f in fields], [20])
        e = next(e for e in evs if e["type"] == "畑")
        self.assertTrue(e["text"].endswith("草の種 20 つかみ をまいた (家の倉から 8 つかみ)"), e["text"])
        rows = self.ledger(st, P, C, evs)
        self.assertEqual([r for r in rows if r["reason"] == "記録にない差" and r["item"] == "草の種" and r["holder"] in ("村", h)], [])
        sown = {r["holder"]: r["kcal"] for r in rows if r["reason"] == "まいた (畑)"}
        self.assertEqual(sown, {"村": -12 * self.U, h: -8 * self.U})
        # 村の蓄えで足りれば、家の倉は使わない (文も data も前と同じ)
        st["store"].append({"kind": "草の種", "kcal": 5 * self.U, "day": st["day"]})
        house0 = copy.deepcopy(era2._house(st, h)["store"])
        P, C, fields, evs = self.sow(st, p, 5)
        e = next(e for e in evs if e["type"] == "畑")
        self.assertTrue(e["text"].endswith("草の種 5 つかみ をまいた"), e["text"])
        self.assertEqual(e["data"], {"seed": 5})
        self.assertEqual(era2._house(st, h)["store"], house0)

    def test_g6_unchanged(self):
        st, p, h = self.setup(False)
        house0 = copy.deepcopy(era2._house(st, h)["store"])
        P, C, fields, evs = self.sow(st, p, 30)
        self.assertEqual(fields, [], "G6 までは村の蓄えからだけ (家の倉にあっても、まかない)")
        self.assertEqual(era2._house(st, h)["store"], house0)
        self.assertFalse([e for e in evs if e["type"] == "畑"])
        st["store"].append({"kind": "草の種", "kcal": 12 * self.U, "day": st["day"]})
        P, C, fields, evs = self.sow(st, p, 20)
        self.assertEqual([f["seed"] for f in fields], [12])
        e = next(e for e in evs if e["type"] == "畑")
        self.assertTrue(e["text"].endswith("草の種 12 つかみ をまいた"), e["text"])
        self.assertEqual(e["data"], {"seed": 12})
        self.assertEqual(era2._house(st, h)["store"], house0)

    def test_prompt(self):
        import g7
        t = g7._season_notes(g7_state() if is_g6(real_state()) else real_state(), ["秋"])
        self.assertIn("村の蓄えの草の種が足りなければ、残りはまく人の家の倉の草の種からまかれる (家の倉にもなければ、ある分だけ)", t)


class P_Fixes1023(unittest.TestCase):
    """2026-10-23 の 3 つの直し (G7 から。メモリの中の写しだけ):
    1. 村を出た家の村は一度だけ作る (なくなっても、次の季節の終わりに新しい番号で作り直さない。g7.left_made)
    2. 村を出た家の村の名を、村 (川辺の村) と同じにしない
    3. 条件 1 の進み (止まり) は、村のいるまとまりの決める段 D で数える (地域のいちばん高い段ではない)。前の数え方の best は直す"""

    def st(self):
        st = real_state()
        if "g7" in (st.get("era2") or {}):
            return st
        if is_g6(st):
            return g7_state()
        self.skipTest("本物の state が G6 でも G7 でもない")

    @staticmethod
    def season_end(st):
        st["day"] += era2.SEASON_DAYS
        era2._g6_season_end(st, 1.0)

    @staticmethod
    def left(st, h):
        st["era2"]["g5"].setdefault("fissions", []).append({"day": st["day"] + era2.SEASON_DAYS, "household": h, "people": ["甲", "乙"],
                                                            "goats": 0, "store": 0, "fields": 0, "dispute": None})

    @staticmethod
    def split_others(st):
        return [o for o in st["era2"]["g6"]["others"] if o["kind"] == "分かれた家"]

    def gone(self, st, o):
        import g7
        o["people"], o["gone"] = 0, st["day"]
        g7.drop_gone(st)

    def test_left_made_once(self):
        import g7
        st = self.st()
        self.left(st, "テスト5の家")
        n0 = st["era2"]["g6"]["next_other"]
        self.season_end(st)
        mine = [o for o in self.split_others(st) if o["household"] == "テスト5の家"]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[0]["name"], "テスト5の村")
        self.assertIn("テスト5の家", g7.left_made(st))
        self.assertGreaterEqual(st["era2"]["g6"]["next_other"], n0 + 1)
        for o in self.split_others(st):  # 村を出た家の村がみな、5 人未満でなくなった (年の終わり)
            self.gone(st, o)
        self.assertEqual(self.split_others(st), [])
        for _ in range(2):
            self.season_end(st)
            self.assertEqual(self.split_others(st), [], "なくなった村を作り直さない")
        self.assertEqual(sorted(g7.left_made(st)), sorted({f["household"] for f in st["era2"]["g5"]["fissions"]}))

    def test_left_made_from_old_state(self):
        """直しの前に G7 に入った state (g7.left_made がない): 前の季節の終わりまでに出た家は作らない。いまの季節に出た家は作る"""
        import g7
        st = self.st()
        g6 = st["era2"]["g6"]
        last = g6["log"][-1]["day"]  # 前の季節の終わり (この日に出た家も、その季節の終わりの G6 の 1. で村にした)
        st["era2"]["g5"].setdefault("fissions", []).append({"day": last, "household": "テスト6の家", "people": ["甲"], "goats": 0, "store": 0})
        for o in self.split_others(st):
            self.gone(st, o)
        self.left(st, "テスト7の家")
        st["era2"]["g7"].pop("left_made", None)
        self.season_end(st)
        self.assertEqual([o["household"] for o in self.split_others(st)], ["テスト7の家"])
        made = g7.left_made(st)
        self.assertIn("テスト6の家", made)
        self.assertIn("テスト7の家", made)

    def test_name_not_village(self):
        import g7
        st = self.st()
        g5 = st["era2"]["g5"]
        g5["fissions"] = [f for f in g5.get("fissions", []) if f["household"] != "川辺の家"]  # 本物の state では、もう出た家 (この試しでは、いま出る)
        st["era2"]["g7"].pop("left_made", None)
        self.left(st, "川辺の家")
        self.season_end(st)
        o = next(o for o in self.split_others(st) if o["household"] == "川辺の家")
        self.assertNotEqual(o["name"], g7.V0_NAME)
        self.assertEqual(o["name"], f"{g7.V0_NAME}{o['id'][1:]}", "同じ名のときと同じに、番号をつける")
        self.assertEqual(g7._v0(st)["name"], "川辺の村")
        # G6 までは前のまま (村の名は見ない。乱数の引き方も同じ)
        st6 = self.st()
        del st6["era2"]["g7"]
        st6["era2"]["g6"]["others"] = [x for x in st6["era2"]["g6"]["others"] if x["name"] != "川辺の村"]
        o6 = era2._new_other(st6, random.Random(5), "分かれた家", household="川辺の家", people=3)
        self.assertEqual(o6["name"], "川辺の村")

    def test_stall_c1_village_level(self):
        import g7
        import yardstick as y
        st = self.st()
        g = st["era2"]["g7"]
        y0 = -(-(g["start"] + 1) // era2.YEAR)
        Y = y0 + 17
        st["day"] = Y * era2.YEAR - 1  # 年の終わりの日
        g.setdefault("level_seen", {"village": 0, "region3": None})["village"] = 0
        g.pop("reached", None)
        g.pop("tribute2_day", None)
        region_only = [{"D": 2, "T": 2, "office": 0, "top": "N1", "village": "外", "members": ["N1", "N2"]}]
        self.assertEqual(y._progress(st, region_only)["c1"], 0, "村が外なら、地域に段 2 のまとまりがあっても 0")
        g["stall"] = {"c1": {"best": 2, "since": y0 + 4, "done": False, "ask": y0 + 12}}  # 前の数え方で残った best
        y._stall(st, region_only)
        s = g["stall"]["c1"]
        self.assertEqual((s["best"], s["since"], s["ask"]), (0, y0, Y), "村の段で数え直す (村は一度も段に届いていない)")
        g["consulted"] = [{"why": "years", "part": g.get("part", 5)}]
        self.assertEqual((g7.consult_why(st) or {}).get("why"), "c1")
        # 村が段 1 のまとまりに入れば、進んだ
        st["day"] += era2.YEAR
        g["level_seen"]["village"] = 1
        y._stall(st, [{"D": 1, "T": 1, "office": 1, "top": "V0", "village": "中心", "members": ["V0"]}] + region_only)
        self.assertEqual((g["stall"]["c1"]["best"], g["stall"]["c1"]["since"], g["stall"]["c1"]["ask"]), (1, Y + 1, None))
        # 村が段に届いたことがあれば (level_seen.village)、best はその段に直し、since はそのまま
        g["stall"]["c1"] = {"best": 2, "since": y0 + 4, "done": False, "ask": None}
        st["day"] += era2.YEAR
        y._stall(st, [])
        self.assertEqual((g["stall"]["c1"]["best"], g["stall"]["c1"]["since"]), (1, y0 + 4))


class Q_KinShare(unittest.TestCase):
    """2026-10-23 の 2 つの直し (計画 docs/research/state_emergence_plan.md 6. の 1・2、9. の 2。G7 から。メモリの中の写しだけ):
    1. 子は、村の蓄えと自分の家の倉で足りなければ、母の家 → 近い親類の家の倉から食べる (g7.kin_houses。era2._feed)
    2. 家の代表の答え share: 家の倉から村の蓄え・ほかの家の倉へ出す (g7.apply_shares。出来事「倉を分ける」の moves を記録が読む)"""
    U = era2.UNITS["草の種"][1]

    def st(self):
        st = real_state()
        if "g7" in (st.get("era2") or {}):
            return st
        if is_g6(st):
            return g7_state()
        self.skipTest("本物の state が G6 でも G7 でもない")

    @staticmethod
    def grain(store):
        return sum(f["kcal"] for f in store if f["kind"] == "草の種")

    def kin_case(self, st, sib=False):
        """母を別の家 (大人のいる家) に移した子 (写しの中だけ)。sib: 同じ母の子がいる子。戻り値: 子・自分の家・母の家"""
        import g7
        homes = era2._homes(st)
        by = {p["name"]: p for p in st["people"]}
        c = next(c for c in era2.children(st) if by.get(c.get("mother")) and by[c["mother"]]["alive"] and not by[c["mother"]].get("child")
                 and (not sib or any(q is not c and q.get("mother") == c["mother"] for q in st["people"])))
        own = c["household"]
        h2 = next(h for h in homes if h != own)
        by[c["mother"]]["household"] = h2
        self.assertEqual(g7.kin_houses(st, c)[0], h2, "母の家が先")
        return c, own, h2

    def feed(self, st, c, own, h2, food_kcal):
        st["store"] = []
        for h in era2._homes(st) + [own]:
            era2._house(st, h)["store"] = []
        era2._house(st, h2)["store"] = [{"kind": "草の種", "kcal": food_kcal, "day": st["day"]}]
        for p in st["people"]:
            p["hunger"] = 0.0
            p["food"] = []  # 大人も手元にない (村の蓄えに入れない)
        before = self.grain(era2._house(st, h2)["store"])
        era2._feed(st, random.Random(1))
        return before - self.grain(era2._house(st, h2)["store"]), c["hunger"]

    def test_real_data_kin_is_own_house(self):
        """家は母から子へ受けつぐので、本物の state では、どの子も親類の家は自分の家と同じ (この直しで動く子はいない)"""
        import g7
        st = self.st()
        self.assertEqual([c["name"] for c in era2.children(st) if g7.kin_houses(st, c)], [])

    def test_kin_feeds_child(self):
        st = self.st()
        c, own, h2 = self.kin_case(st)
        took, hunger = self.feed(st, c, own, h2, 10 ** 6)
        self.assertGreater(took, 0)
        self.assertEqual(hunger, 0.0, "母の家の倉から食べた")
        # 母の家の倉もからなら空腹になる
        took, hunger = self.feed(st, c, own, h2, 0)
        self.assertEqual(hunger, 0.15)

    def test_g6_unchanged(self):
        st = self.st()
        c, own, h2 = self.kin_case(st)
        del st["era2"]["g7"]  # G6 のふるまい
        took, hunger = self.feed(st, c, own, h2, 10 ** 6)
        self.assertEqual(hunger, 0.15, "G6 までは、自分の家の倉がからなら空腹になる (母の家の倉からは食べない)")

    def test_kin_order(self):
        import g7
        st = self.st()
        c, own, h2 = self.kin_case(st, sib=True)
        by = {p["name"]: p for p in st["people"]}
        sib = next(q for q in st["people"] if q is not c and q.get("mother") == c["mother"])
        h3 = next(h for h in era2._homes(st) if h not in (own, h2))
        sib["household"] = h3
        self.assertEqual(g7.kin_houses(st, c), [h2, h3])
        by[c["mother"]]["household"] = own  # 母が自分の家なら、兄弟姉妹の家だけ
        self.assertEqual(g7.kin_houses(st, c), [h3])

    def rep(self, st):
        import g7
        reps = g7._rep_of(st)
        h = era2._homes(st)[0]
        return reps[h], h

    def test_share_to_village_and_house(self):
        import g7
        st = self.st()
        n, h = self.rep(st)
        other = next(x for x in era2._homes(st) if x != h)
        era2._house(st, h)["store"] = [{"kind": "草の種", "kcal": 100 * self.U, "day": st["day"]}]
        v0, o0 = self.grain(st["store"]), self.grain(era2._house(st, other)["store"])
        e0 = st["next_event"]
        g7.apply_shares(st, {n: {"share": {"村": {"草の種": 30}, other: {"草の種": 500}, "ない家": {"草の種": 5}}}})
        self.assertAlmostEqual(self.grain(st["store"]) - v0, 30 * self.U)
        self.assertAlmostEqual(self.grain(era2._house(st, other)["store"]) - o0, 70 * self.U, msg="家の倉にある分まで")
        self.assertEqual(self.grain(era2._house(st, h)["store"]), 0)
        evs = [e for e in st["events"] if e["id"] >= e0]
        self.assertEqual([e["type"] for e in evs], ["倉を分ける", "倉を分ける"])
        self.assertIn(f"{h}の代表の {n} が、家の倉から 草の種 30 つかみ を村の蓄えに出した", evs[0]["text"])
        self.assertEqual(evs[1]["data"]["moves"], [[h, -1, {"草の種": 70}, []], [other, 1, {"草の種": 70}, []]])
        self.assertEqual([x["to"] for x in st["era2"]["g7"]["shares"]], ["村", other])
        # 代表でない人の share は読まない・数だけなら草の種のつかみ
        era2._house(st, h)["store"] = [{"kind": "草の種", "kcal": 100 * self.U, "day": st["day"]}]
        not_rep = next((p["name"] for p in era2.adults(st) if p.get("household") == h and p["name"] != n), None)
        if not_rep:
            g7.apply_shares(st, {not_rep: {"share": {"村": 10}}})
            self.assertEqual(self.grain(era2._house(st, h)["store"]), 100 * self.U)
        g7.apply_shares(st, {n: {"share": {"村": 10}}})
        self.assertEqual(self.grain(era2._house(st, h)["store"]), 90 * self.U)
        g7.apply_shares(st, {n: {"share": None}})
        g7.apply_shares(st, {n: {"share": {"村": {"ヤギ": 2, "土器": 3}}}})  # 食べ物だけ
        self.assertEqual(self.grain(era2._house(st, h)["store"]), 90 * self.U)

    def test_share_ledger(self):
        """記録の帳簿 (build_records.ledger): 村の蓄えと家の倉の草の種に「記録にない差」が出ない"""
        import g7
        import records
        sys.path.insert(0, str(HERE))
        import build_records
        st = self.st()
        n, h = self.rep(st)
        era2._house(st, h)["store"] = [{"kind": "草の種", "kcal": 100 * self.U, "day": st["day"]}]
        P = records.snapshot(st)
        e0 = st["next_event"]
        g7.apply_shares(st, {n: {"share": {"村": {"草の種": 40}}}})
        C = records.snapshot(st)
        moves7 = [(side, sg, goods, build_records.MOVE7[e["type"]][0 if sg < 0 else 1])
                  for e in st["events"] if e["id"] >= e0 for side, sg, goods, ids in e["data"]["moves"]]
        b = build_records.Builder.__new__(build_records.Builder)
        b.H = lambda x: x
        b.hname = {}
        c = {"D": st["day"], "a": st["day"], "P": P, "C": C, "flows_v": {}, "sown_ev": [], "eaten": {},
             "harvest": {"to": {}, "by_household": {}}, "g5": {"feast": None, "payments": [], "fission": None},
             "pests": {"amount": 0, "events": []}, "inherit": [], "pots": {"made": 0, "broken": 0}, "sick": {"made": 0, "broken": 0},
             "g6": {"moves": [], "moves7": moves7}, "goats": {"flows": {}, "known": False}}
        rows = b.ledger(c)
        self.assertEqual([r for r in rows if r["reason"] == "記録にない差" and r["item"] == "草の種" and r["holder"] in ("村", h)], [])
        got = {(r["holder"], r["reason"]): r["kcal"] for r in rows if r["reason"] in ("分けて出した", "分けて受けた")}
        self.assertEqual(got, {(h, "分けて出した"): -40 * self.U, ("村", "分けて受けた"): 40 * self.U})
        import accounts
        self.assertEqual((accounts.KIND["分けて出した"], accounts.KIND["分けて受けた"]), ("transfers", "transfers"))

    def test_share_in_apply_year_and_prompt(self):
        import g7
        st = self.st()
        if is_g6(real_state()):
            st = to_year_end(st)
        else:
            st["era2"]["g7"]["ask"] = "年"
        reps = set(g7._rep_of(st).values())
        n = next(x for x in era2.answerers(st) if x in reps)
        h = next(p for p in era2.adults(st) if p["name"] == n)["household"]
        era2._house(st, h)["store"] = [{"kind": "草の種", "kcal": 50 * self.U, "day": st["day"]}]
        ans = {x: year_answer(list(g7.SEASONS)) for x in era2.answerers(st)}
        ans[n] = year_answer(list(g7.SEASONS), share={"村": {"草の種": 20}})
        v0 = self.grain(st["store"])
        g7.apply_year(st, ans)
        e = next(e for e in reversed(st["events"]) if e["type"] == "倉を分ける")
        self.assertEqual((e["who"], e["data"]["to"], e["data"]["goods"]), (n, "村", {"草の種": 20}))
        self.assertGreaterEqual(self.grain(st["store"]) - v0, 20 * self.U - 1e-6)
        rows = g7._field_rows(st, False, True)
        self.assertIn("分ける: 家の倉の食べ物を、村の蓄えやほかの家の倉へ出すなら share", rows)
        self.assertNotIn("分ける:", g7._field_rows(st, True, True), "代表でない人には出さない")
        self.assertIn('"share": null,', g7.fields_json(st, None, False))


class R_CountV2World(unittest.TestCase):
    """2026-10-24 (実験 C の準備): 決める段の数え方 "v2" (村もまわりの集落と同じに数える) と、世界の選び (砂地・逃げ場なし)。どちらも選ばなければ前のまま"""

    @staticmethod
    def vD(setts, ties, officials=None, rules=False):
        lv = region.levels(setts, ties, 0, officials=officials, **({"village_rules": True} if rules else {}))
        return next((x["D"] for x in lv if x["village"] != "外"), 0)

    def graph(self, org, deep=False):
        setts = [sett("V0", 100, (5, 5), org=org), sett("N1", 10, (3, 3)), sett("N2", 10, (7, 7))]
        ties = [tie(1, "N1", "V0"), tie(2, "N2", "V0")]
        if deep:
            setts += [sett("N3", 5, (1, 1)), sett("N4", 5, (1, 3))]
            ties += [tie(3, "N3", "N1"), tie(4, "N4", "N1")]
        return setts, ties

    def test_levels_v2(self):
        off = {"甲": ["V0"], "乙": ["V0"]}  # 村の役の人 (下は村の葉だけ)
        s, t = self.graph(2)
        self.assertEqual(self.vD(s, t, off, rules=True), 2, "org 2 + 貢ぐ集落 2 → 段 2")
        self.assertEqual(self.vD(s, t, off), 1, "前の数え方では 1")
        s, t = self.graph(2, deep=True)
        self.assertEqual(self.vD(s, t, off, rules=True), 3, "貢ぐ集落の 1 つが 2 つに貢がれていれば段 3")
        self.assertEqual(self.vD(s, t, off), 2)
        s, t = self.graph(1, deep=True)
        self.assertEqual(self.vD(s, t, off, rules=True), self.vD(s, t, off), "org 1 は前のまま")
        s = [sett("V0", 100, (5, 5), org=2)]
        self.assertEqual(self.vD(s, [], off, rules=True), self.vD(s, [], off), "貢ぐ集落がなければ前のまま (役の人の数え方)")
        for org in (0, 1, 2):
            for deep in (False, True):
                s, t = self.graph(org, deep)
                a = region.levels(s, t, 0, officials=off)
                self.assertEqual(region.levels(s, t, 0, officials=off, village_rules=False), a)

    def test_yardstick_uses_v2(self):
        import g7
        import yardstick
        st = real_state()
        if not (is_g6(st) or "g7" in st["era2"]):
            self.skipTest("G6 でも G7 でもない")
        st = g7_state() if is_g6(st) else st
        calls = []
        orig = region.levels

        def spy(*a, **kw):
            calls.append(kw.get("village_rules", False))
            return orig(*a, **kw)
        region.levels = spy
        try:
            yardstick.levels(st)
            st["era2"]["g7"]["count"] = "v2"
            yardstick.levels(st)
        finally:
            region.levels = orig
        self.assertEqual(calls, [False, True])

    def test_world_flags(self):
        import g7
        st = real_state()
        if not is_g6(st):
            self.skipTest("本物の state が G6 でない")
        a = g7_state(0.1)
        self.assertNotIn("world", a["era2"]["g7"])
        self.assertNotIn("count", a["era2"]["g7"])
        self.assertFalse(region.DESERT or region.NO_FLEE)
        b = part_end(real_state())
        g7.enter(b, 0.1, {"desert": True, "no_flee": True}, "v2")
        g = b["era2"]["g7"]
        self.assertEqual((g["world"], g["count"]), ({"desert": True, "no_flee": True}, "v2"))
        self.assertTrue(region.DESERT and region.NO_FLEE)
        placed = [o for o in g7._others(b) if o["id"] in g["region"]["fill"]["placed"]]
        self.assertTrue(placed and all(region.land(tuple(o["cell"])) != "s" for o in placed), "砂地には置かない")
        pa = sum(o["people"] for o in g7._others(a) if o["id"] in a["era2"]["g7"]["region"]["fill"]["placed"])
        self.assertAlmostEqual(g["region"]["fill"]["people"] / pa, 1, delta=0.2, msg="置く人数は今の地図の K の割合 (砂地でも)")
        setts = g7._setts(b)
        self.assertIsNone(region.refuge(setts, setts[1], setts[0]), "逃げ場がない")
        self.assertEqual(region.cap((0, 0)) if region.land((0, 0)) == "s" else 0, 0)
        b["era2"]["g7"]["region"]["demands"].append({"id": "Q99", "from": "N1", "to": "V0", "end": None})
        self.assertFalse(g7._leave_on(b), "逃げ場のない世界では、家ごとに出ていく欄を出さない")
        self.assertEqual(g7.leave_households(b, {}), [])
        self.assertNotIn("家ごとに村を出る", g7._field_rows(b, False, True))
        self.assertNotIn('"逃げる"', g7._field_rows(b, False, True))
        self.assertIn("逃げる道はない", g7.facts(b))
        rep = g7._rep_of(b)[era2._homes(b)[0]]
        self.assertEqual(g7.village_answers(b, {rep: {"answer_demand": {"Q99": "逃げる"}}}), {}, "逃げるは選べない")
        g7.sync_world(a)  # 選びのない state を回すと、region はいつもに戻る
        self.assertFalse(region.DESERT or region.NO_FLEE)
        a["era2"]["g7"]["region"]["demands"].append({"id": "Q99", "from": "N1", "to": "V0", "end": None})
        self.assertTrue(g7._leave_on(a))
        self.assertIn('"逃げる"', g7._field_rows(a, False, True))
        self.assertNotIn("逃げる道はない", g7.facts(a))


class S_G8(unittest.TestCase):
    """2026-10-25 G8「外からの押し」(docs/society_phase/G8_design.md): 強い集落の決まり・G8 に入る日・札の段"""

    def R(self):
        return {"ties": [], "demands": [], "wars": [], "pending": [], "gone": [], "log": [], "next_war": 1}

    def test_strong_target(self):
        R = self.R()
        v0 = sett("V0", 100, (5, 5), village=True, kcap=10 ** 6, known=0)
        big = sett("N9", 200, (5, 3), org=2, strong=True, kcap=10 ** 6)
        small = sett("N1", 10, (6, 3))
        q = region._demand_target(R, [v0, big, small], big, "ふつう")
        self.assertEqual(q["to"], "V0", "余り (求める量) のいちばん多い村に求める (ふつうの集落なら、いちばん弱い N1)")
        self.assertEqual(q["amount"], region.amount_of(v0))
        self.assertEqual(region._demand_target(R, [v0, dict(big, strong=False), small], dict(big, strong=False), "ふつう")["to"], "N1")
        v0w = dict(v0, people=150)  # 村が強すぎる (200 < 1.5 × 150): ほかの相手に
        self.assertEqual(region._demand_target(R, [v0w, big, small], big, "ふつう")["to"], "N1")
        v0w["walls"] = 1
        self.assertIsNone(region._demand_target(R, [v0w, big], big, "ふつう"), "1.5 倍強い相手がいなければ求めない")

    def test_strong_year(self):
        R = self.R()
        v0 = sett("V0", 100, (5, 5), village=True, kcap=10 ** 6, known=0)
        big = sett("N9", 400, (5, 3), org=2, strong=True, kcap=10 ** 6)
        others = [sett(f"N{i}", 30, (i, 9)) for i in range(1, 8)]
        setts = [v0, big] + others
        for y in range(3):
            region.year_end(R, setts, random.Random(y), 70 + y, (70 + y) * 120 - 1, out=[])
            self.assertEqual(big["org"], 2)
            self.assertFalse([p for p in R["pending"] if p["who"] == "N9" and p["kind"] in ("分かれる", "出ていく")], "分かれない・出ていかない")
            self.assertTrue(any(q["from"] == "N9" for q in R["demands"]), "毎年動く (求める相手がいれば)")

    def real_g7(self):
        st = real_state()
        if st.get("era") != "G7":
            self.skipTest("本物の state が G7 でない")
        return st

    def test_start_g8(self):
        import g7
        st = self.real_g7()
        pop = g7._pop(st)
        n0 = len(g7._others(st))
        g7.close_g7(st, "試し")
        self.assertEqual(g7.enter_next(st), "G8")
        g = st["era2"]["g7"]
        o = next(x for x in g7._others(st) if x["id"] == g["strong"])
        self.assertEqual(len(g7._others(st)), n0 + 1)
        self.assertEqual(o["people"], round(g7.STRONG_MUL * pop))
        self.assertTrue(2 <= region.dist(tuple(o["cell"]), region.VILLAGE) <= 4 and region.land(tuple(o["cell"])) != "s")
        self.assertEqual((o["org"], o["kcap"], o["known"], o["strong"]), (2, g7.STRONG_KCAP, st["day"], True))
        self.assertEqual((g["world"], g["count"]), (g7.G8_WORLD, "v2"))
        self.assertEqual(region.WEATHER_BAD, 0.35)
        self.assertTrue(region.DESERT and region.NO_FLEE)
        self.assertIn("G7", g["before"])
        self.assertEqual(st["era_info"]["era"], "G8")
        self.assertEqual(st["events"][-1]["text"], "フェーズ G8 (外からの押し) を始めた")
        self.assertIn("ここで閉じた", next(e for e in reversed(st["events"]) if e["type"] == "フェーズ" and "G7" in e["text"])["text"])
        self.assertIn("逃げる道はない", g7.facts(st))
        g7.sync_world(self.real_g7())  # G7 の state では、もとに戻る
        self.assertEqual((region.WEATHER_BAD, region.DESERT, region.NO_FLEE), (0.2, False, False))

    def test_hint_stage(self):
        import hints
        self.assertEqual([hints._stage_now({"era": e}) for e in ("G6", "G7", "G8", "G9", "G15")], [0, 0, 0, 1, 7])


class T_G8Heavy(unittest.TestCase):
    """2026-10-25 G8 の続き「重い押し」(docs/society_phase/G8_heavy_design.md): 去年の刈り入れの 2 割・「増やせ」の求め・毎年の数え直し。入れなければ前のまま"""

    def world(self, paying=True):
        R = {"ties": [], "demands": [], "wars": [], "pending": [], "gone": [], "log": [], "next_war": 1, "next_tie": 2, "next_demand": 5}
        v0 = sett("V0", 100, (5, 5), village=True, kcap=10 ** 6, known=0, grain=10 ** 6)
        big = sett("N9", 400, (5, 3), org=2, strong=True, kcap=10 ** 6)
        others = [sett(f"N{i}", 30, (i, 9)) for i in range(1, 5)]
        if paying:
            R["ties"].append(dict(tie(1, "V0", "N9"), goods={"草の種": 2000}))
        return R, [v0, big] + others

    HV = {"from": "N9", "to": "V0", "amount": 90000}

    def test_raise_year_end(self):
        R, setts = self.world()
        region.year_end(R, setts, random.Random(1), 91, 91 * 120 - 1, out=[], heavy=self.HV)
        q = next(q for q in R["demands"] if q["to"] == "V0")
        self.assertEqual((q["from"], q["what"], q["raise"], q["old"], q["heavy"]), ("N9", {"草の種": 90000}, "K1", {"草の種": 2000}, True))
        self.assertEqual(q["war_day"], 91 * 120 + region.RAISE_WAR_DAY, "断られたら年の 30 日目に戦 (乱数なし)")
        self.assertTrue(any(p["kind"] == "求めへの答え" and p["demand"] == q["id"] for p in R["pending"]))
        R2, setts2 = self.world()
        region.year_end(R2, setts2, random.Random(1), 91, 91 * 120 - 1, out=[])
        self.assertFalse([q for q in R2["demands"] if q["to"] == "V0"], "重い押しがなければ、もう払っている村には求めない (前のまま)")
        R3, setts3 = self.world()
        R3["ties"][0]["heavy"] = True
        region.year_end(R3, setts3, random.Random(1), 91, 91 * 120 - 1, out=[], heavy=self.HV)
        self.assertFalse([q for q in R3["demands"] if q["to"] == "V0"], "もう重い量で払っていれば、増やせとは求めない (数え直しは g7.heavy_year)")

    def test_same_without_heavy(self):
        R1, s1 = self.world(False)
        R2, s2 = self.world(False)
        o1 = region.year_end(R1, s1, random.Random(3), 91, 91 * 120 - 1, out=[])
        o2 = region.year_end(R2, s2, random.Random(3), 91, 91 * 120 - 1, out=[], heavy=None)
        self.assertEqual((R1, s1, o1), (R2, s2, o2))

    def test_not_paying_demand_heavy_amount(self):
        R, setts = self.world(False)
        q = region._demand_target(R, setts, setts[1], "ふつう", heavy=self.HV)
        self.assertEqual((q["to"], q["amount"], q.get("heavy")), ("V0", 90000, True))
        q0 = region._demand_target(R, setts, setts[1], "ふつう")
        self.assertEqual((q0["amount"], q0.get("heavy")), (region.amount_of(setts[0]), None))
        region.year_end(R, setts, random.Random(1), 91, 91 * 120 - 1, out=[], heavy=self.HV)
        q = next(q for q in R["demands"] if q["to"] == "V0")
        self.assertEqual((q["what"], q.get("heavy"), q.get("raise")), ({"草の種": 90000}, True, None))
        region.answer(R, setts, q, "払う", None, 91 * 120, "決まり", [])
        t = R["ties"][-1]
        self.assertEqual((t["payer"], t["goods"], t.get("heavy")), ("V0", {"草の種": 90000}, True))

    def test_answer_pay_raises_tie(self):
        R, setts = self.world()
        out = []
        q = region.raise_demand(R, setts, self.HV, 91 * 120 - 1, out, pending=True)
        self.assertIn("増やし", out[-1]["text"])
        self.assertIn(q["id"], out[-1]["text"])
        region.answer(R, setts, q, "払う", None, 91 * 120, "村の答え", out)
        self.assertEqual(len(R["ties"]), 1, "新しいつながりは作らない")
        t = R["ties"][0]
        self.assertEqual((t["goods"], t["heavy"], t["status"], q["end"]), ({"草の種": 90000}, True, "続く", 91 * 120))
        self.assertIsNone(region.raise_demand(R, setts, self.HV, 92 * 120 - 1, []), "もう重い量なら求めない")

    def test_refuse_war(self):
        for win in (True, False):
            R, setts = self.world()
            q = region.raise_demand(R, setts, self.HV, 91 * 120 - 1, [], pending=True)
            region.answer(R, setts, q, "戦う", None, 91 * 120, "村の答え", [])
            w = R["wars"][-1]

            class Rng:
                def random(self):
                    return 0.0 if win else 0.999999

                def uniform(self, a, b):
                    return a
            region.fight(R, setts, w, Rng(), w["day"], out=[])
            t = R["ties"][0]
            if win:
                self.assertEqual((len(R["ties"]), t["goods"], t["heavy"], t["status"]), (1, {"草の種": 90000}, True, "続く"), "負けた: 今の貢ぎが重い量に")
            else:
                self.assertEqual((len(R["ties"]), t["status"], t["why"]), (1, "切れた", "戦に勝った"), "勝った: 今の貢ぎもやめる")

    def real_g8(self):
        st = real_state()
        g = (st.get("era2") or {}).get("g7") or {}
        if st.get("era") != "G8" or g.get("heavy") or g.get("ask") != "年" or (st["day"] + 1) % era2.YEAR:
            self.skipTest("本物の state が、重い押しのない G8 の年の集まりの歩でない")
        return st

    def test_harvest_year(self):
        import g7
        st = real_state()
        if "g7" not in (st.get("era2") or {}):
            self.skipTest("G7 より前")
        y = st["day"] // era2.YEAR
        ev = sum(e["data"].get("amount", 0) for e in st["events"] if e["type"] == "収穫" and e["day"] // era2.YEAR == y)
        if ev:
            self.assertEqual(g7.harvest_year(st), ev, "前の年の秋にまいた畑の刈った量 = その年の出来事「収穫」の合わせ")

    def test_heavy_on_real(self):
        import g7
        st = self.real_g8()
        self.assertIsNone(g7.heavy_now(st))
        self.assertIsNone(g7.heavy_refusal(st))
        n_ev = st["next_event"]
        q = g7.heavy_on(st)
        g = st["era2"]["g7"]
        self.assertEqual(g["heavy"], {"day": st["day"], "share": g7.HEAVY_SHARE})
        h = g7.harvest_year(st)
        self.assertEqual((q["what"]["草の種"], q["harvest"], q["raise"], q["from"]), (round(g7.HEAVY_SHARE * h), h, g7.region.heavy_tie(g["region"], g7.heavy_now(st))["id"], g["strong"]))
        types = [e["type"] for e in st["events"] if e["id"] >= n_ev]
        self.assertEqual(types, ["集落", "求め"])
        self.assertTrue(any(p.get("demand") == q["id"] for p in g["region"]["pending"]))
        txt = g7.region_text(st)
        self.assertIn(f"毎年 草の種 {q['what']['草の種']} つかみ を出すように村に求めている (いま出している", txt)
        self.assertEqual(g7.HEAVY_SHARE, 1.0, "本人の決め (2026-10-26): 10 割")
        self.assertIn(f"刈り入れ 草の種 {h} つかみ の {round(g7.HEAVY_SHARE * 10)} 割) (answer_demand で答える)", txt)
        self.assertIn(q["id"], g7._field_rows(st, False, True))
        t = next(t for t in g["region"]["ties"] if t["id"] == q["raise"])
        t["heavy"] = True
        old = t["goods"]["草の種"]
        g7.heavy_year(st)
        self.assertEqual(t["goods"]["草の種"], round(g7.HEAVY_SHARE * h))
        self.assertEqual(t["recount"][-1], [st["day"], old, round(g7.HEAVY_SHARE * h), h])
        self.assertIn("割。年の終わりごとに数え直す", g7.region_text(st))
        st["era"] = "G7"
        self.assertIn("G8 のときだけ", g7.heavy_refusal(st))


class T_G9(unittest.TestCase):
    """2026-10-29 G9「遠くとの商い」(docs/society_phase/G9_design.md): G8 を閉じて入る・重い押しを切る・遠くの運ぶ人・約束を板に書く・赤い金属の道具・
    商人の家・条件と F・止まり・札の表 (G9 の札は G9 から)。G8 までは前のまま"""

    NOTE = "本人の決め 2026-10-28: 外からの押しを 104年120日目で閉じた"

    def g9_state(self):
        import g7
        st = real_state()
        g = (st.get("era2") or {}).get("g7") or {}
        if st.get("era") == "G9" and "g9" in g:
            return st
        if st.get("era") != "G8" or g.get("closed8"):
            self.skipTest("本物の state が G8 (閉じる前) でも G9 でもない")
        g7.close_g8(st, self.NOTE)
        g7.enter_next(st)
        st["era_log"][-1]["g8_closed"] = st["day"]
        return st

    def real_g8(self):
        st = real_state()
        if st.get("era") != "G8" or "g9" in ((st.get("era2") or {}).get("g7") or {}):
            self.skipTest("本物の state が G8 でない")
        return st

    def answers(self, st, **a):
        return {n: dict(a) for n in era2.answerers(st)}

    def test_enter_from_g8(self):
        import g7
        import g9
        import hints
        import step
        st = self.real_g8()
        self.assertIsNone(step._next_part_refusal(st, None, self.NOTE))
        n_ev = st["next_event"]
        g = st["era2"]["g7"]
        tools0 = [t for t in (g.get("hints") or {}).get("things", []) if t["thing"] in g9.BRONZE_THINGS]
        g7.close_g8(st, self.NOTE)
        self.assertEqual(step._next_part_refusal(st, None, self.NOTE), "G8 はもう閉じている")
        g7.enter_next(st)
        g = st["era2"]["g7"]
        self.assertEqual((st["era"], st["era_info"]["name"], g["closed8"]["note"], g["closed8"]["day"]), ("G9", "遠くとの商い", self.NOTE, st["day"]))
        self.assertIn("closed", g, "G7 を閉じた記録 (g7.closed) はそのまま")
        self.assertEqual(g["heavy"]["end"], st["day"], "重い押しは G9 に入る日に切る (消さない)")
        self.assertIsNone(g7.heavy_now(st))
        self.assertEqual(sorted(g["before"]), ["G7", "G8"])
        self.assertNotIn("reached", g, "G8 の物差しの数は before.G8 に移して数え直す")
        self.assertEqual(g["world"], g7.G8_WORLD, "世界の旗は G8 のまま")
        self.assertEqual(g["count"], "v2")
        self.assertEqual(len(g["g9"]["tools"]), len(tools0), "67年の赤い金属の刃も道具の一覧に入る (新しく手に入れたものではない)")
        self.assertFalse(g["g9"]["reached"])
        self.assertEqual(g["hints"]["cards_sha"], hints.cards_sha(st))
        self.assertNotEqual(hints.cards_sha(st), hints.cards_sha(), "G9 からは G9 の札もハッシュに入る")
        self.assertIsNone(hints.cards_changed(st))
        types = [e["type"] for e in st["events"] if e["id"] >= n_ev]
        self.assertEqual(types, ["フェーズ", "集落", "区切り", "フェーズ"])
        ind = era2.indicators(st)
        self.assertEqual((ind["g9_c1_day"], ind["g9_c2_day"], ind["g9_c3_day"]), (None, None, None))
        self.assertFalse(era2.CRITERIA["G9"][1](ind))
        self.assertEqual(era2.PART_END["G9"], 5)
        txt = g7.facts(st) + g7.text(st, era2.adults(st)[0]) + g7._field_rows(st, False, True)
        self.assertIn("遠くの町の運ぶ人", txt)
        self.assertIn("(metal)", txt)
        self.assertNotIn("青銅", txt, "村の人に見せる文に「青銅」は書かない")

    def test_g9_cards_only_from_g9(self):
        import hints
        st = self.real_g8()
        self.assertEqual(hints.cards_sha(st), hints.cards_sha(), "G8 までは前のハッシュ (hint_cards.json だけ)")
        self.assertIsNone(hints.cards_changed(st))
        now = hints._stage_now(st)
        self.assertNotIn("H8-04", hints._cand(st, 1, now and 1, "商人"), "G8 では G9 の札を引かない")
        self.assertNotIn("H8-05", hints._cand(st, 1, 1, "旅人"))
        self.assertFalse(any(t[2] == hints.FAR for t in hints.terms(st, "V0")), "遠くの商人は G9 から")
        st9 = self.g9_state()
        self.assertIn("H8-04", hints._cand(st9, 1, 1, "商人"))
        self.assertIn("H8-05", hints._cand(st9, 1, 1, "旅人"))
        self.assertEqual(hints.check_cards(), [])

    def test_far_term_without_trade(self):
        """2026-10-29 本人の決め「交換しなくても来る」: 前の年に交換をしなくても、遠くの運ぶ人の項がある (重みは 0.1 のまま)"""
        import g9
        import hints
        st = self.g9_state()
        lo, hi = hints._window(st)
        self.assertFalse(g9.traded(st, lo, hi), "本物の村は 12599 日目の前の年に交換をしていない")
        self.assertIn(("商人", hints.LAM_FAR, hints.FAR), hints.terms(st, "V0"))
        self.assertEqual(hints.LAM_FAR, 0.1)
        self.assertEqual(sum(1 for t in hints.terms(st, "V0") if t[2] == hints.FAR), 1)
        self.assertIn("交換をしていなくても来る", g9.facts(st))

    def test_one_flow_only(self):
        """2026-10-29 本人の決め: 約束の流れは 1 つだけ。流れが続くあいだの別の運ぶ人とは、その場で替えるだけ (once)"""
        import g9
        st = self.g9_state()
        g = st["era2"]["g7"]["g9"]
        if era2._g6_have(st, "村", "草の種") < 6 * g9.FAR_TOOLS * g9.FAR_PRICE:
            self.skipTest("村の蓄えの草の種が少ない")
        a, b = g9.far_arrive(st), g9.far_arrive(st)
        self.assertFalse(a.get("once") or b.get("once"), "流れがないときは、どちらも約束できる申し出")
        g9.apply_answers(st, self.answers(st, far={a["id"]: "約束する", b["id"]: "約束する"}, far_write="書く"))
        self.assertEqual(len(g["promises"]), 1, "同じ集まりで 2 人と約束しない")
        pid = g["promises"][0]["id"]
        self.assertEqual(g9.flow(st), pid)
        self.assertEqual([o["end"][1] for o in g["offer_log"][-2:]], ["約束する", "受ける"])
        self.assertIn("約束しなかった", next(e for e in reversed(st["events"]) if e["type"] == "交換")["text"])
        self.assertEqual(len(g9.tools(st)), 1 + 2 * g9.FAR_TOOLS, "2 人目とも、その場で替えた")
        c = g9.far_arrive(st)
        self.assertEqual(c["once"], pid, "流れが続くあいだに来た運ぶ人は once")
        self.assertIn("約束できない", g9.text(st, era2.adults(st)[0]))
        self.assertIn("約束をしているので", st["events"][-1]["text"])
        g9.apply_answers(st, self.answers(st, far={c["id"]: "受けない"}))
        self.assertEqual(g["offer_log"][-1]["end"][1], "受けない")
        pr = g["promises"][0]
        st["day"] = pr["due"]
        g9._due(st)
        self.assertEqual(pr["status"], "守られた")
        nxt = g["offers"][-1]
        self.assertEqual((nxt["after"], nxt.get("once")), (pid, None), "守り合ったあとの次の申し出は、同じ流れ (約束できる)")
        self.assertEqual(g9.flow(st), pid)
        d = g9.far_arrive(st)
        self.assertEqual(d["once"], pid)
        g9.apply_answers(st, self.answers(st, far={nxt["id"]: "約束する", d["id"]: "約束する"}, far_write="書く"))
        self.assertEqual([p["status"] for p in g["promises"]], ["守られた", "待つ"])
        self.assertEqual(g["promises"][1]["offer"], nxt["id"], "流れを続けるのは、前の運ぶ人")
        self.assertEqual(g["offer_log"][-1]["end"][1], "受ける")
        g["promises"][1]["status"] = "守られた"
        self.assertIsNone(g9.flow(st), "流れが終われば、次の運ぶ人とまた約束できる")
        self.assertIsNone(g9.far_arrive(st).get("once"))

    def test_far_promise_written_and_kept_twice(self):
        import g9
        st = self.g9_state()
        g = st["era2"]["g7"]["g9"]
        grain0 = era2._g6_have(st, "村", "草の種")
        if grain0 < 4 * g9.FAR_TOOLS * g9.FAR_PRICE:
            self.skipTest("村の蓄えの草の種が少ない")
        off = g9.far_arrive(st)
        self.assertTrue(any("(far" in r for r in g9.field_rows(st)))
        self.assertIn(off["id"], g9.fields_json(st))
        g9.apply_answers(st, self.answers(st, far={off["id"]: "約束する"}, far_write="書く", metal="使う"))
        self.assertEqual(g["offers"], [])
        self.assertEqual(era2._g6_have(st, "村", "草の種"), grain0 - g9.FAR_TOOLS * g9.FAR_PRICE)
        self.assertEqual(len(g9.tools(st)), 1 + g9.FAR_TOOLS)
        pr = g["promises"][-1]
        self.assertEqual((pr["written"], pr["status"], pr["due"]), (True, "待つ", st["day"] + era2.YEAR))
        self.assertEqual(sorted(g["reached"]), ["F1", "F3"])
        self.assertEqual(g["c"].get("c3"), st["day"])
        self.assertEqual(g["use"]["choice"], "使う")
        e = next(e for e in reversed(st["events"]) if e["type"] == "交換")
        self.assertIn("粘土の板に書いて残した", e["text"])
        self.assertTrue(e["text"].startswith("季節の集まりで"), "集まりの出来事")
        st["day"] = pr["due"]
        g9._due(st)
        self.assertEqual((pr["status"], g["kept"]), ("守られた", 1))
        self.assertEqual(len(g["offers"]), 1, "守り合ったら、また申し出る")
        off2 = g["offers"][0]
        g9.apply_answers(st, self.answers(st, far={off2["id"]: "約束する"}, far_write="書かない"))
        pr2 = g["promises"][-1]
        self.assertFalse(pr2["written"])
        pr2["mem"] = {"village": 1.0, "merchant": 1.0}
        st["day"] = pr2["due"]
        g9._due(st)
        self.assertEqual((pr2["status"], g["kept"]), ("守られた", 2))
        self.assertEqual(g["reached"].get("F4"), st["day"])

    def test_unwritten_memory_differs(self):
        import g9
        st = self.g9_state()
        g = st["era2"]["g7"]["g9"]
        off = g9.far_arrive(st)
        g9.apply_answers(st, self.answers(st, far={off["id"]: "約束する"}))
        if not g["promises"]:
            self.skipTest("村の蓄えが足りない")
        pr = g["promises"][-1]
        self.assertFalse(pr["written"], "far_write がなければ書かない")
        self.assertNotIn("c3", g["c"])
        pr["mem"] = {"village": 0.7, "merchant": 1.3}
        st["day"] = pr["due"]
        g9._due(st)
        self.assertEqual((pr["status"], g["kept"], g["offers"]), ("ちがっていた", 0, []))
        self.assertEqual(st["events"][-1]["type"], "覚え")

    def test_refuse_and_no_answer(self):
        import g9
        st = self.g9_state()
        g = st["era2"]["g7"]["g9"]
        a, b = g9.far_arrive(st), g9.far_arrive(st)
        n0 = len(g9.tools(st))
        g9.apply_answers(st, self.answers(st, far={a["id"]: "受けない"}))
        self.assertEqual((g["offers"], len(g9.tools(st)), [o["end"][1] for o in g["offer_log"][-2:]]), ([], n0, ["受けない", "答えなし"]))
        self.assertEqual(g["deals"], [])

    def test_bronze_use_and_c1(self):
        import g7
        import g9
        st = self.g9_state()
        g = st["era2"]["g7"]["g9"]
        self.assertEqual(g7.g9_tools(st), [], "しまっているあいだは使わない")
        g9.apply_answers(st, self.answers(st, metal="使う"))
        ts = g7.g9_tools(st)
        self.assertEqual(len(ts), len(g9.tools(st)))
        p = era2.adults(st)[0]
        self.assertEqual(g7.g9_reap(st, p, ts[0], 60), 150, "刈る量は 2.5 倍")
        y = str(st["day"] // era2.YEAR)
        g["used"][y] = g9.C1_DAYS
        g9.season_end(st)
        self.assertEqual(g["c"].get("c1"), st["day"])
        ts[0]["uses"] = g9.BRONZE_LIFE
        g9._wear(st)
        self.assertIsNotNone(ts[0]["gone"])

    def test_merchant_household_c2(self):
        import g9
        st = self.g9_state()
        g6 = st["era2"]["g6"]
        h = era2.adults(st)[0]
        D = st["day"]
        for i in range(9):
            g6["trip_log"].append({"id": f"RX{i}", "who": h["name"], "to": "N1", "start": D - 100 + i * 10, "end": D - 100 + i * 10 + 6})
        g9.season_end(st)
        g = st["era2"]["g7"]["g9"]
        self.assertGreater(g["merchant"]["max"], g9.MERCHANT_DAYS)
        self.assertEqual((g["reached"].get("F2"), g["c"].get("c2")), (D, D))
        import yardstick
        yardstick._ahead(st)
        self.assertFalse(any(x["g"] == "G8" for x in st["era2"].get("ahead", []) if x["day"] == D), "G9 では先の目盛り (G8 の F2) を書かない")

    def test_criteria_and_part_end(self):
        import g7
        st = self.g9_state()
        g = st["era2"]["g7"]
        g["g9"]["c"] = {"c1": st["day"], "c2": st["day"], "c3": st["day"]}
        ind = era2.indicators(st)
        self.assertTrue(era2.CRITERIA["G9"][1](ind))
        self.assertEqual(g7.check(st, True, ind), "end")
        self.assertEqual(g["hold"]["why"], "part_end")
        self.assertEqual(era2.hold_why(dict(st, hold=True))[0], "part_end")

    def test_g7_measures_side_by_side(self):
        import yardstick
        st = self.g9_state()
        g = st["era2"]["g7"]
        D0 = g["g9"]["start"]
        yardstick._reach(st, "F2", yardstick._f2_day(st), "試し")
        yardstick._reach(st, "F5", yardstick._f5_day(st), "試し")
        self.assertTrue(all(d >= D0 for d in (g.get("reached") or {}).values()), "G9 に入る前の取り立て・貸し借りでは、ならべて測る F に入れない")
        yardstick._reach(st, "F1", st["day"], "試し")
        self.assertEqual(g["reached"]["F1"], st["day"])
        self.assertEqual(era2.indicators(st)["g7_f3_day"], None)

    def test_stall_counts_g9(self):
        import yardstick
        st = self.g9_state()
        g = st["era2"]["g7"]
        self.assertNotIn("stall", g)
        yardstick._stall(st, [])
        self.assertEqual(sorted(g["stall"]), ["c1", "c2", "c3"])
        self.assertEqual(g["stall"]["c1"]["best"], 1, "道具はある (67年の刃)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
