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


G11_ENTRY = "c2566124"  # G11 に入った日 (18119 日目。印はまだ決まっていない。N52 が生きている) の state のコミット
G13_ENTRY = "f5561de4"  # G13 に入る日 (172年120日目 = 20759 日目。G12 の 3 つの条件がそろって HOLD part_end・答えなし) の state のコミット (2026-11-12)
G12_ENTRY = "c9fc7a96"  # G12 に入る日 (164年120日目 = 19799 日目。G11・HOLD consult・答えなし) の state のコミット (2026-11-10)
_GIT_TEXT = {}


def git_state(commit):
    """git にある、決まった日の state.json の中身 (読むだけ。コミットごとに 1 回だけ読む)。
    本物の state は日が進むと形が変わる (印が決まる・村がなくなる・直しの印がつく) ので、その日の場面が要る試しはこれを使う (2026-11-06)。
    git にないときは試しをとばす"""
    if commit not in _GIT_TEXT:
        r = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:sim/society/data/state.json"], capture_output=True)
        _GIT_TEXT[commit] = r.stdout.decode("utf-8") if r.returncode == 0 else None
    if _GIT_TEXT[commit] is None:
        raise unittest.SkipTest(f"{commit} の state が git にない")
    return json.loads(_GIT_TEXT[commit])


def as_g10(st):
    """本物の state が G11 なら、写しの中で G11 に入る前の G10 にもどす (G10 の仕組みだけの確かめのため。2026-11-06)。
    g11 を外し、G11 に入る日に g7.before.G10 に移した G7 の物差し (g7.start_g11) をもどす"""
    g = st["era2"]["g7"]
    if st.get("era") == "G11":
        g.pop("g11", None)
        g.pop("closed10", None)
        g.pop("part_start11", None)
        import g7
        b = (g.get("before") or {}).get("G10") or {}
        g.update({k: b[k] for k in g7.MEASURE_KEYS if k in b})
        g["before"] = {k: v for k, v in g["before"].items() if k != "G10"}
        st["era"] = "G10"
    return st


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
        self.assertEqual(era2.ORDER2[-5:], ["G7", "G8", "G9", "G10", "G11"])  # 2026-10-25: G8 (外からの押し) を足した。2026-10-29: G9 (遠くとの商い)。2026-11-04: G10 (鉄と広い国)。2026-11-05: G11 (お金と市場)
        self.assertEqual(era2.NAMES2["G11"], "お金と市場")
        self.assertNotIn("G11", era2.PART_END)
        self.assertEqual([x[0] for x in era2.SUBSTEPS["G11"]], ["F1", "F2", "F3", "F4"])
        self.assertEqual(era2.NAMES2["G10"], "鉄と広い国")
        self.assertNotIn("G10", era2.PART_END)
        self.assertEqual(era2.PART_START["G10"], 6)
        self.assertEqual([x[0] for x in era2.SUBSTEPS["G10"]], ["F1", "F2", "F3", "F4"])
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
        import records  # noqa: E402
        rows = records.person_rows(self.data)  # 年ごとのファイル records/season_person/ (2026-11-05)
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

    def test_far_rate_switch(self):
        """本人の決め 2026-10-29「来る見込みを 5 割に」(step.py far_rate): state に残す切り替え。はじめは 0.1・切り替えた日から新しい重み・
        同じ重みなら何も変えない・出来事「目盛り」(村は見ない)・年の終わりの日に、もう引いた次の年の分には差だけ引き足す (3 通まで)"""
        import copy
        import g9
        import hints
        st = self.g9_state()
        g = st["era2"]["g7"]["g9"]
        self.assertNotIn("far_rate", g, "切り替える前の state には鍵がない (前と 1 バイトも同じ)")
        self.assertEqual(hints.far_weight(st), hints.LAM_FAR)
        self.assertEqual(hints.LAM_FAR, 0.1, "決めのはじめの重みは 0.1 のまま (定数は変えない)")
        if (st["day"] + 1) % era2.YEAR or st["phase"] != "season":
            self.skipTest("本物の state が年の終わりの season でない")
        st0 = copy.deepcopy(st)
        self.assertIsNone(g9.far_rate_refusal(st, 0.5))
        self.assertIn("0 より大きく", g9.far_rate_refusal(st, 0))
        self.assertIn("0 より大きく", g9.far_rate_refusal(st, 1.5))
        n_ev, h = st["next_event"], st["era2"]["g7"]["hints"]
        n_led = len(h["ledger"])
        row = g9.set_far_rate(st, 0.5, "本人の決め 2026-10-29: 来る見込みを 5 割に")
        self.assertEqual((row["day"], row["rate"], row["was"]), (st["day"], 0.5, 0.1))
        self.assertEqual(g["far_rate"], [row])
        self.assertEqual(hints.far_weight(st), 0.5)
        self.assertIn(("商人", 0.5, hints.FAR), hints.terms(st, "V0"))
        self.assertEqual(row["topup"]["lam"], 0.4, "今日もう引いた次の年の分 (0.1) との差")
        new = h["ledger"][n_led:]
        self.assertEqual(len(new), row["topup"]["n"])
        self.assertTrue(all(r["from"] == hints.FAR and r["carrier"] == "商人" and r.get("far_rate") for r in new))
        self.assertLessEqual(sum(x["n"] for x in h["lam"] if x["day"] == st["day"] and x["to"] == "V0"), hints.HINT_CAP)
        ev = [e for e in st["events"] if e["id"] >= n_ev]
        self.assertEqual([e["type"] for e in ev], ["目盛り"])
        self.assertNotIn("目盛り", era2.YEAR_EVENTS + era2.MEETING_EVENTS + era2.G7_EVENTS, "村の人には見せない")
        self.assertIsNone(g9.set_far_rate(st, 0.5, "x"), "同じ重みなら何も変えない")
        self.assertEqual(len(g["far_rate"]), 1)
        self.assertNotIn("0.5", g9.facts(st), "お題の文は変わらない")
        self.assertEqual(g9.facts(st), g9.facts(st0))
        st1 = copy.deepcopy(st0)  # 同じ state から同じ引き足し (乱数は日と種から。世界の塩の列にはさわらない)
        g9.set_far_rate(st1, 0.5, "本人の決め 2026-10-29: 来る見込みを 5 割に")
        self.assertEqual(st1["era2"]["g7"]["hints"], h)
        g9.set_far_rate(st, 0.7, "x")  # 同じ日にもう一度上げても、足すのは引いた重みとの差 (0.2) だけ
        self.assertEqual(g["far_rate"][-1]["topup"]["lam"], 0.2)
        g9.set_far_rate(st, 0.3, "x")  # 下げるときは引き足さない
        self.assertNotIn("topup", g["far_rate"][-1])
        self.assertEqual(hints.far_weight(st), 0.3)

    def test_far_rate_topup_rows_and_mid_year(self):
        """引き足した行は、ふつうの遠くの商人の行と同じに届く (g9.far_arrive の申し出)。年の終わりの日でなければ引き足さない (次の年の終わりから)"""
        import copy
        import g9
        import hints
        st = self.g9_state()
        if (st["day"] + 1) % era2.YEAR or st["phase"] != "season":
            self.skipTest("本物の state が年の終わりの season でない")
        mid = copy.deepcopy(st)
        h = mid["era2"]["g7"]["hints"]
        h["lam"] = [x for x in h["lam"] if x["day"] != mid["day"]]  # 年の途中の日 (今日はまだ引いていない) のかわり
        row = g9.set_far_rate(mid, 0.5, "x")
        self.assertNotIn("topup", row)
        self.assertEqual(hints.far_weight(mid), 0.5)
        orig = hints.poisson
        hints.poisson = lambda rng, lam: 5
        try:
            have = sum(x["n"] for x in st["era2"]["g7"]["hints"]["lam"] if x["day"] == st["day"] and x["to"] == "V0")
            row = g9.set_far_rate(st, 0.5, "x")
        finally:
            hints.poisson = orig
        h = st["era2"]["g7"]["hints"]
        self.assertEqual(row["topup"]["n"], hints.HINT_CAP - have, "村の便りは 1 年に 3 通まで")
        rows = [r for r in h["ledger"] if r.get("far_rate")]
        self.assertEqual([r["y"] for r in rows], row["topup"]["rows"])
        self.assertTrue(all(st["day"] < r["due"] <= st["day"] + era2.YEAR for r in rows))
        got = [r for r in rows if r["status"] == "待つ"]
        if not got:
            self.skipTest("商人の札が引けなかった")
        self.assertTrue(all(r["y"] in h["plan"] for r in got))
        n_off = len(st["era2"]["g7"]["g9"]["offers"])
        st["day"] = got[0]["due"]
        hints._deliver_v0(st, era2._rng(st, era2.HINT_SALT), got[0])
        if got[0]["status"] == "空振り":
            self.skipTest("聞く人がいない")
        self.assertEqual(len(st["era2"]["g7"]["g9"]["offers"]), n_off + 1, "遠くの町の運ぶ人の申し出")

    def test_far_rate_refused_outside_g9(self):
        import g9
        st = real_state()
        if st.get("era") != "G9":
            self.skipTest("本物の state が G9 でない")
        st["phase"] = "night"
        self.assertIn("season", g9.far_rate_refusal(st, 0.5))
        st["phase"] = "season"
        st["era"] = "G8"
        self.assertIn("G9 のときだけ", g9.far_rate_refusal(st, 0.5))
        del st["era2"]["g7"]["g9"]
        self.assertIn("G9 のときだけ", g9.far_rate_refusal(st, 0.5))


class T_G10(unittest.TestCase):
    """2026-11-04 G10「鉄と広い国」(docs/society_phase/G10_design.md): G9 を閉じて入る (第 5 部の終わり)・札を入る日に開く・黒い金属を作る・刈る人日 (c1・F4)・
    音の字と読み書き (F2・c2・字で比べる)・広いまとまりの物差し (c3・F3)・道の見張り・止まり・札の表 (G10 の札は G10 から)・言葉の表。G9 までは前のまま"""

    NOTE = "本人の決め 2026-11-04 (お任せ): 遠くとの商いを閉じた (試し)"

    def real_g9(self):
        st = real_state()
        g = (st.get("era2") or {}).get("g7") or {}
        if st.get("era") != "G9" or "g9" not in g or "g10" in g or g.get("closed9"):
            self.skipTest("本物の state が G9 (閉じる前) でない")
        return st

    def g10_state(self):
        import g7
        st = self.real_g9()
        g7.close_g9(st, self.NOTE)
        g7.enter_next(st)
        st["era_log"][-1]["g9_closed"] = st["day"]
        return st

    def done_tech(self, st, card, names):
        """札の「試す」を終わったことにする (試した人の腕を 0.3 に)"""
        t = st["era2"]["g7"]["hints"]["tech"][card]
        t.update(open=t.get("open") or st["day"], first=st["day"], progress=1000.0, done=st["day"])
        for p in era2.adults(st):
            if p["name"] in names:
                p["skills"][f"試す:{card}"] = 0.3

    def test_enter_from_g9(self):
        import g7
        import g10
        import hints
        import step
        st = self.real_g9()
        self.assertIsNone(step._next_part_refusal(st, None, self.NOTE))
        self.assertEqual(step._next_part_refusal(st, None, " "), "--closed-by-decision に本人の言葉がない")
        n_ev = st["next_event"]
        g9_reached = dict(st["era2"]["g7"]["g9"]["reached"])
        c = g7.close_g9(st, self.NOTE)
        self.assertEqual((c["day"], c["note"], c["part_end"], c["visits"]), (st["day"], self.NOTE, 5, len(st["era2"]["g7"]["g9"]["visits"])))
        self.assertIn("G9 はもう閉じている", step._next_part_refusal(st, None, self.NOTE))
        g7.enter_next(st)
        g = st["era2"]["g7"]
        self.assertEqual((st["era"], st["era_info"]["name"], g["part"], g["part_start"], g["part_start10"]), ("G10", "鉄と広い国", 6, st["day"], st["day"]))
        self.assertIn("closed", g)
        self.assertIn("closed8", g, "G7・G8 を閉じた記録はそのまま")
        self.assertEqual(g["closed9"]["note"], self.NOTE)
        self.assertEqual(sorted(g["before"]), ["G7", "G8", "G9"])
        self.assertEqual(g["before"]["G9"]["g9"]["reached"], g9_reached, "G9 の物差しは before.G9 に写して数え直す")
        self.assertEqual((g["g9"]["reached"], g["g9"]["c"], g["g9"]["kept"]), ({}, {}, 0))
        self.assertNotIn("reached", g, "G9 のときの G7 の物差しの数は before.G9 に移す")
        self.assertEqual(g["world"], g7.G8_WORLD, "世界の旗はそのまま")
        self.assertEqual(hints.far_weight(st), 0.5, "遠くの町の運ぶ人の重みはそのまま")
        self.assertEqual(g7.PART_YEARS[6], 50)
        self.assertEqual(g["hints"]["cards_sha"], hints.cards_sha(st))
        self.assertIsNone(hints.cards_changed(st))
        types = [e["type"] for e in st["events"] if e["id"] >= n_ev]
        self.assertEqual(types[0], "フェーズ")
        self.assertIn("第 5 部「王と青銅」も、ここで終わった", st["events"][-len(types)]["text"])
        self.assertEqual(types[1], "区切り")
        self.assertEqual(types[-1], "フェーズ")
        self.assertIn("第 6 部「鉄とお金の帝国」を始めた", st["events"][-1]["text"])
        opened = g["g10"]["opened"]
        self.assertEqual(types[2:-1], ["試す"] * len(opened))
        for card in ("H9-01", "H9-02"):
            if card in g["hints"]["tech"] and g["hints"]["tech"][card].get("wait") is not None:
                self.assertIn(card, opened, "待っている札は、入る日に開く")
                self.assertIn(card, hints.open_techs(st))
        ind = era2.indicators(st)
        self.assertEqual((ind["g10_c1_day"], ind["g10_c2_day"], ind["g10_c3_day"]), (None, None, None))
        self.assertFalse(era2.CRITERIA["G10"][1](ind))
        self.assertNotIn("G10", era2.PART_END)
        txt = g7.facts(st) + g7.text(st, era2.adults(st)[0]) + g7._field_rows(st, False, True)
        self.assertIn("黒い金属", txt)
        self.assertIn("音の字", txt)
        self.assertEqual(g10.bad_words(g10.facts(st) + g10.text(st, None) + "".join(g10.field_rows(st))), [], "G10 の文に鉄・国・帝国などを書かない")
        if opened:
            self.assertIn("試す", g7.acts(st))

    def test_g9_unchanged(self):
        """G9 の state (g7.g10 がない) では、新しい前提・札・仕事・文は何も働かない"""
        import g7
        import hints
        st = self.real_g9()
        self.assertFalse(hints.needs_ok(st, {"鉄の鉱石": 1, "強い火": 1}))
        self.assertFalse(hints.needs_ok(st, {"粘土の板": 1, "音で書く": 1}))
        self.assertEqual(hints.cards_sha(st), hashlib.sha256(hints.CARDS.read_bytes() + b"\n" + hints.CARDS_G9.read_bytes()).hexdigest())
        self.assertIsNone(hints.cards_changed(st), "G9 の札の表のハッシュは前のまま")
        self.assertNotIn("H9-03", hints._cand(st, "V0", hints.STAGES.index("G9"), "旅人"))
        self.assertFalse(set(g7.acts(st)) & set(g7.ACTS10))
        self.assertNotIn("黒い金属", g7.facts(st) + g7.text(st, era2.adults(st)[0]) + g7._field_rows(st, False, True))
        self.assertNotIn("g10_c1_day", era2.indicators(st))
        q = era2.adults(st)[0]
        q["plan"] = {"activity": "黒い金属を作る", "place": "camp", "with": []}
        g7.job(st, q, {})
        self.assertEqual(q["plan"]["activity"], "休む", "G9 までは選べない")

    def test_g10_cards_only_from_g10(self):
        import hints
        st = self.g10_state()
        self.assertIn("H9-03", hints._cand(st, "V0", hints.STAGES.index("G9"), "旅人"))
        self.assertEqual(hints._stage_now(st), hints.STAGES.index("G9"), "G10 はもとの G9 の札の段を読む")
        self.assertEqual(hints.check_cards(), [])
        import g10
        c = hints.cards()["H9-03"]
        self.assertEqual(g10.bad_words(c["text"] + c["name"]), [])
        self.assertTrue(hints.needs_ok(st, {"鉄の鉱石": 1, "強い火": 1}))
        self.assertTrue(hints.needs_ok(st, {"粘土の板": 1, "音で書く": 1}))
        self.assertFalse(hints.needs_ok(st, {"牛": 10 ** 6}))

    def test_make_iron_and_c1(self):
        import g7
        import g9
        import g10
        st = self.g10_state()
        g = st["era2"]["g7"]["g10"]
        ads = era2.adults(st)
        a, b, c = ads[0], ads[1], ads[2]
        self.assertFalse(g10.can_make(st, a["name"]))
        self.done_tech(st, "H9-01", [a["name"]])
        self.assertTrue(g10.can_make(st, a["name"]))
        self.assertFalse(g10.can_make(st, b["name"]))
        self.assertTrue(g10.can_make(st, b["name"], [a["name"]]), "作り方を知る人と一緒なら作れる")
        self.assertIn("黒い金属を作る", g7.acts(st))
        c["plan"] = {"activity": "黒い金属を作る", "place": "camp", "with": []}
        g7.job(st, c, {})
        self.assertEqual(c["plan"]["activity"], "休む", "作り方を知らない人は休む")
        n0 = len(g9.tools(st))
        a["today"] = {"activity": "黒い金属を作る"}
        b["today"], b["plan"] = {"activity": "黒い金属を作る"}, {"activity": "黒い金属を作る", "place": "camp", "with": [a["name"]]}
        for _ in range(g10.IRON_DAYS // 2):
            g10.make_day(st, a, {})
            g10.make_day(st, b, {})
        self.assertEqual(len(g["made"]), 1)
        self.assertEqual(len(g9.tools(st)), n0 + 1)
        t = g9.tools(st)[-1]
        self.assertEqual((t["name"], t["iron"], t["from"]), (g10.IRON, True, "村"))
        self.assertEqual(g["reached"].get("F1"), st["day"])
        self.assertEqual(g["pending_smiths"], [b["name"]])
        g10.season_end(st)
        self.assertTrue(g10.smith(st, b["name"]), "一緒に作った人は、次の季節から作れる")
        self.assertEqual(st["era2"]["g7"]["g9"]["reached"], {}, "村で作った黒い金属は、G9 の F1 (新しく手に入れる) に数えない")
        y = str(st["day"] // era2.YEAR)
        used0 = st["era2"]["g7"]["g9"]["used"].get(y, 0)
        self.assertEqual(g9.reap(st, a, t, 60), 150, "刈る量は赤い金属と同じ")
        self.assertEqual(st["era2"]["g7"]["g9"]["used"].get(y, 0), used0, "黒い金属は G9 の c1 (赤い金属) に数えない")
        self.assertEqual(g["reap"][y]["iron"], 1)
        bronze = next(x for x in g9.tools(st) if not x.get("iron"))
        g9.reap(st, a, bronze, 60)
        self.assertEqual((g["reap"][y]["bronze"], st["era2"]["g7"]["g9"]["used"].get(y, 0)), (1, used0 + 1))
        g["reap"][y] = {"all": 250, "bronze": 100, "iron": 99}
        g10.season_end(st)
        self.assertIsNone(g["c"].get("c1"), "100 人日に届かない")
        self.assertEqual(g["reached"].get("F4"), st["day"], "30 人日で F4")
        g["reap"][y] = {"all": 250, "bronze": 100, "iron": 124}
        g10.season_end(st)
        self.assertIsNone(g["c"].get("c1"), "半分に届かない")
        g["reap"][y] = {"all": 250, "bronze": 100, "iron": 125}
        g10.season_end(st)
        self.assertEqual(g["c"].get("c1"), st["day"])
        self.assertEqual(g10.bad_words(g10.text(st, None)), [])
        self.assertIn("黒い金属の鎌", g10.text(st, None))

    def test_reap_count_in_day(self):
        """era2._day の夕方の刈り入れ: G10 では、実った畑があるとき、刈る人日をすべて数える (道具を使った人日は g9.reap で分けて数える)"""
        import g7
        st = self.g10_state()
        e2 = st["era2"]
        if not any(f["state"] == "実った" for f in e2["fields"]):
            for f in e2["fields"][:1]:
                f["state"] = "実った"
        if not e2["fields"]:
            self.skipTest("畑がない")
        st["era2"]["g7"]["g9"]["use"]["choice"] = "使う"
        for p in era2.adults(st):
            e2["jobs"].setdefault(p["name"], {})["harvest"] = 60
        rows = st["era2"]["g7"]["g10"]["reap"]
        era2._day(st)
        y = str(st["day"] // era2.YEAR)
        row = rows.get(y) or rows.get(str((st["day"] - 1) // era2.YEAR)) or {}
        self.assertGreater(row.get("all", 0), 0)
        self.assertLessEqual(row.get("bronze", 0) + row.get("iron", 0), row.get("all", 0))
        self.assertGreater(row.get("bronze", 0), 0, "赤い金属の道具を使った人日")
        self.assertIsNotNone(g7)

    def test_alphabet_readers_and_c2(self):
        import g10
        st = self.g10_state()
        g = st["era2"]["g7"]["g10"]
        sh = set(g10.scribe_houses(st))
        out = [p for p in era2.adults(st) if p.get("household") not in sh]
        ins = [p for p in era2.adults(st) if p.get("household") in sh]
        if len(out) < 3:
            self.skipTest("記録をつける家の外の大人が少ない")
        self.done_tech(st, "H9-02", [out[0]["name"]] + [p["name"] for p in ins[:1]])
        g10.season_end(st)
        self.assertEqual(g["reached"].get("F2"), st["day"])
        self.assertIn(out[0]["name"], g10.readers(st))
        self.assertIsNone(g["c"].get("c2"), "記録をつける家の外は 1 人だけ")
        self.assertTrue(g10.can_learn(st, out[1]["name"]))
        self.assertFalse(g10.can_learn(st, out[0]["name"]), "もう読める人は習わない")
        self.assertIn("字を習う", g10.acts(st))
        out[0]["today"] = {"activity": "休む"}
        for _ in range(g10.LEARN_DAYS):
            g10.learn_day(st, out[1], {})
        self.assertIn(out[1]["name"], g10.readers(st))
        g10.season_end(st)
        self.assertEqual(g["c"].get("c2"), st["day"])
        for p in era2.adults(st):
            p["today"] = {"activity": "交換に行く", "away": True} if p["name"] in g["readers"] else {"activity": "休む"}
        n0 = g["learn"].get(out[2]["name"], 0)
        g10.learn_day(st, out[2], {})
        self.assertEqual(g["learn"].get(out[2]["name"], 0), n0, "読める人がみな出かけている日は習えない")

    def test_letters(self):
        """読み書きできる大人のいる家・村は、量を字で書いて比べる (遠くとの約束・もめごと)"""
        import g9
        import g10
        st = self.g10_state()
        g = st["era2"]["g7"]["g10"]
        self.assertFalse(g10.letters(st, "村"))
        p = era2.adults(st)[0]
        g["readers"][p["name"]] = st["day"]
        self.assertTrue(g10.letters(st, "村"))
        self.assertTrue(g10.letters(st, p.get("household")))
        g9s = st["era2"]["g7"]["g9"]
        if era2._g6_have(st, "村", "草の種") < 4 * g9.FAR_TOOLS * g9.FAR_PRICE:
            self.skipTest("村の蓄えの草の種が少ない")
        off = g9.far_arrive(st)
        g9.apply_answers(st, {n: {"far": {off["id"]: "約束する"}, "far_write": "書かない"} for n in era2.answerers(st)})
        pr = g9s["promises"][-1]
        self.assertEqual((pr["written"], pr.get("letters")), (False, True))
        pr["mem"] = {"village": 0.7, "merchant": 1.3}
        st["day"] = pr["due"]
        g9._due(st)
        self.assertEqual(pr["status"], "守られた", "字で書いておいた約束は、覚えのずれで言い争わない")
        self.assertGreaterEqual(g["letters"], 1)
        self.assertNotIn("c3", g9s["c"], "字で書いた約束は、G9 の c3 (粘土の板に書く) ではない")

    def test_c3_measure(self):
        import g10
        import yardstick
        st = self.g10_state()
        g = st["era2"]["g7"]["g10"]
        lv, n, best, hit = g10.region_now(st)
        self.assertGreater(n, 0)
        self.assertIsNone(hit, "入る日 (13799 日目) には、段 4 のまとまりはない")
        orig = yardstick.levels
        fake = [{"top": best["top"], "D": 4, "T": 3, "office": 1, "members": ["N%d" % i for i in range(n)], "village": "外", "B": 2}]
        yardstick.levels = lambda s: fake
        try:
            g10.season_end(st)
        finally:
            yardstick.levels = orig
        self.assertEqual((g["reached"].get("F3"), g["c"].get("c3")), (st["day"], st["day"]))
        self.assertEqual(g["c3_log"][0]["top"], best["top"])
        self.assertEqual(g["c3_log"][0]["village"], "外", "中心が村でなくても届く")
        e = [x for x in st["events"] if x["type"] == "目盛り"][-1]
        self.assertIn("G10 の条件 3", e["text"])

    def test_path_watch_and_stall(self):
        import g7
        import g10
        import yardstick
        st = self.g10_state()
        g = st["era2"]["g7"]
        G = g["g10"]
        y0 = (G["start"] + 1) // era2.YEAR
        g10.count_paths(st)
        self.assertEqual(G["path"][str(y0)]["meetings"], 1)
        self.assertEqual(G["path"][str(y0)]["c1"], int(g10.paths(st)["c1"]))
        st["day"] = (y0 + 1) * era2.YEAR - 1
        G["path"] = {str(y0): {"meetings": 3, "c1": 0, "c2": 3}}
        self.assertIsNone(g10.path_consult(st, []), "1 年だけなら止めない")
        st["day"] = (y0 + 2) * era2.YEAR - 1
        G["path"][str(y0 + 1)] = {"meetings": 3, "c1": 0, "c2": 2}
        c = g10.path_consult(st, [])
        self.assertEqual((c["why"], c["year"]), ("path_c1", y0 + 1))
        self.assertIsNone(g10.path_consult(st, [c]), "一度ずつ")
        c2 = g7.consult_why(st)
        self.assertIsNotNone(c2)
        G["c"]["c1"] = st["day"]
        self.assertIsNone(g10.path_consult(st, []), "届いた条件は見張らない")
        self.assertNotIn("stall", g)
        yardstick._stall(st, [])
        self.assertEqual(sorted(g["stall"]), ["c1", "c2", "c3"])
        self.assertEqual(g["stall"]["c1"]["best"], g10.progress(st)["c1"])
        self.assertTrue(g["stall"]["c1"]["done"])

    def test_criteria_and_wait(self):
        import g7
        st = self.g10_state()
        g = st["era2"]["g7"]
        g["g10"]["c"] = {"c1": st["day"], "c2": st["day"], "c3": st["day"]}
        ind = era2.indicators(st)
        self.assertTrue(era2.CRITERIA["G10"][1](ind))
        self.assertEqual(g7.check(st, True, ind), "wait", "G10 の終わりは部の終わりではない (次の G のコードを待つ)")

    def test_g7_measures_since_g10(self):
        import yardstick
        st = self.g10_state()
        g = st["era2"]["g7"]
        self.assertEqual(yardstick._g9_since(st), g["g10"]["start"])
        yardstick._reach(st, "F2", st["day"] - 1, "試し")
        self.assertNotIn("F2", g.get("reached") or {}, "G10 に入る前のことは、ならべて測る数に入れない")


class T_G10FIX(unittest.TestCase):
    """2026-11-05 本人の決め「直して 5 年続ける」(docs/society_phase/G10_stall.md 7.): g10.G10_FIX_FROM の日からの直し 4 つ。
    ① 便りを知る人・作れる人にお題で知らせる ② 休んだわけを出来事に残す ③ 作れる人・試している人の家を答える家に足す ④ 道の見張りは答える人で数える。
    本物の state (G10) の写しに、作る側で場面を組んで確かめる (本物の data は読むだけ。refresh_prompts は写しのフォルダで動かす)"""

    _st = None

    @classmethod
    def base(cls):
        if cls._st is None:
            st = real_state()
            cls._st = as_g10(st) if "g10" in ((st.get("era2") or {}).get("g7") or {}) else False
        if cls._st is False:
            raise unittest.SkipTest("本物の state が G10 でない")
        return copy.deepcopy(cls._st)

    def scene(self, day=None, mark=True):
        """場面: 札 H9-01 はでき、H9-02 は試せる (だれも試していない)。3 つの家の代表 A (作れる人)・B (H9-02 を知っている)・C (どちらでもない)。
        ほかに作れる人・知っている人はいない。見本の家は A・B・C の家のどれでもない (答える家は、ほかの家)"""
        import g7
        import g10
        st = self.base()
        st["day"] = g10.G10_FIX_FROM if day is None else day
        g = st["era2"]["g7"]
        h = g["hints"]
        ti, ta = h["tech"]["H9-01"], h["tech"]["H9-02"]
        ti.update(open=ti.get("open") or 14279, done=ti.get("done") or 15209)
        ta.update(open=14279, first=None, progress=0.0, done=None, last=None)
        for p in st["people"]:
            p["skills"] = {k: v for k, v in p["skills"].items() if not k.startswith("試す:H9-0")}
        g["g10"].update(smiths=[], pending_smiths=[], readers={}, learn={})
        g["g10"].pop("fix", None)
        if mark:
            g10.mark_fix(st, "試し")  # 直しの日なら refresh_prompts と同じ印 (前の日なら何もしない)
        era2._sync_households(st)
        reps = g7._rep_of(st)
        hs = sorted(h_ for h_ in reps if sum(1 for q in era2.adults(st) if q.get("household") == h_) >= 2)
        self.assertGreaterEqual(len(hs), 4)
        ha, hb, hc = hs[0], hs[1], hs[2]
        A, B, C = (next(q for q in st["people"] if q["name"] == reps[x]) for x in (ha, hb, hc))
        A["skills"]["試す:H9-01"] = 1.0
        h["knowers"]["H9-01"] = [A["name"]]
        h["knowers"]["H9-02"] = [B["name"]]
        h.setdefault("pending_knowers", {}).pop("H9-02", None)
        sample = {x: v for x, v in g["sample"].items() if x not in (ha, hb, hc)}
        if hc not in g["sample"]:
            sample[hc] = {"since": st["day"], "cell": g["cells"].get(hc), "must": False}
        g["sample"] = dict(sorted(sample.items()))
        return st, A, B, C

    def test_prompt_knower(self):
        """① 知っている本人に「あなたは試せる (try に番号)」、節に知っている人・作れる人の名前と一緒に覚える道。直しの日より前は前の文のまま"""
        import g10
        import hints
        st, A, B, C = self.scene()
        for r in hints._h(st)["ledger"]:
            if r.get("card") == "H9-02" and r.get("to") == "V0":
                r["status"] = "忘れられた"  # 便りは「忘れられた」(3 年の枠の外) でも、知っている人のまま
        self.assertNotIn('try に "H9-02"', hints.text(st, B))
        tb, tc, ta = g10.text(st, B), g10.text(st, C), g10.text(st, A)
        self.assertIn(f'あなた ({B["name"]}) は、便り「音 1 つに字 1 つ」[H9-02] を知っている。あなたは、主な仕事を「試す」にして、job の try に "H9-02" と書けば試せる', tb)
        self.assertIn(f"この便りを知っている人 ({B['name']}) と、その人と同じ季節に「試す」をして with にその人の名前を書く人", tc)
        self.assertNotIn(f"あなた ({C['name']})", tc)
        self.assertIn(f"作れる人: {A['name']}", tc)
        self.assertIn(f"作り方を知らない人も、作れる人 ({A['name']}) と同じ季節に「黒い金属を作る」をして、with にその人の名前を書けば", tc)
        self.assertIn(f"あなた ({A['name']}) は、黒い金属の作り方を知っている。あなたは、主な仕事を「黒い金属を作る」にできる", ta)
        for t in (ta, tb, tc, g10.feel_note(st, B), g10.feel_note(st, A)):
            self.assertEqual(g10.bad_words(t), [], t)
            self.assertNotIn("【", t)
        self.assertIn('[H9-02] を知っている。家の代表が、あなたの仕事を「試す」(try に "H9-02") にすれば', g10.feel_note(st, B))
        self.assertEqual(g10.feel_note(st, C), "")
        fam = next(q for q in era2.adults(st) if q.get("household") == B.get("household") and q is not B)
        self.assertIn(f"あなたの家で、便り [H9-02] を知っている人: {B['name']}", g10.text(st, fam))
        st0, A0, B0, C0 = self.scene(mark=False)
        self.assertFalse(g10.fixed(st0), "直しの日でも、refresh_prompts の印がなければ前のまま (その日までの歩のやり直しは同じ)")
        self.assertIn("試せる (まだだれも試していない。試せるのは、この便りを知っている人と、その人と一緒に試す人)", g10.text(st0, B0))
        self.assertTrue(g10.fixed(self.scene(day=g10.G10_FIX_FROM + 1, mark=False)[0]), "直しの日より後は、印がなくても直す")
        st2, A2, B2, C2 = self.scene(day=g10.G10_FIX_FROM - 30)
        t2 = g10.text(st2, B2)
        self.assertIn("試せる (まだだれも試していない。試せるのは、この便りを知っている人と、その人と一緒に試す人)", t2, "直しの日より前は前の文")
        self.assertNotIn("あなた (", t2)
        self.assertNotIn("作り方を知らない人も", t2)
        self.assertEqual(g10.feel_note(st2, B2), "")

    def test_rest_reason(self):
        """② 試す・黒い金属を作る・字を習うを「休む」に変えたら、わけをその季節のはじめの日の出来事「休む」に残し、お題の自分のことに出す"""
        import g7
        import g10
        st, A, B, C = self.scene()
        n0 = st["next_event"]
        g7.new_season(st)
        cases = [({"activity": "試す", "try": "H9-02"}, "試す", f"{C['name']} は、「音 1 つに字 1 つ」[H9-02] の便りを知らないので、試せず、休んだ"),
                 ({"activity": "黒い金属を作る"}, "黒い金属を作る", f"{C['name']} は、黒い金属の作り方を知らないので、休んだ"),
                 ({"activity": "字を習う"}, "休む", f"{C['name']} は、村に字を教えられる人がいないので、字を習えず、休んだ")]  # 字を習うは仕事の並びにない (era2 が先に休むにする)
        for j, act, want in cases:
            g7.new_season(st)
            C["plan"] = {"activity": act, "place": "camp", "with": []}
            g7.job(st, C, j)
            self.assertEqual(C["plan"]["activity"], "休む")
            self.assertTrue(st["era2"]["g7"]["rest_why"][C["name"]]["text"].startswith(want), st["era2"]["g7"]["rest_why"][C["name"]]["text"])
            self.assertEqual(st["next_event"], n0, "答えのときは出来事を書かない (季節のはじめの日に書く)")
        first = st["next_event"]
        for _ in range(6):
            world.log(st, "休む", C["name"], f"{C['name']} はキャンプで休んだ")
            g7.count_day(st, C["name"], "休む")
        ev = [e for e in st["events"] if e["id"] >= first and (e.get("data") or {}).get("rest_why")]
        self.assertEqual(len(ev), 1, "1 回だけ")
        self.assertEqual((ev[0]["type"], ev[0]["who"], ev[0]["text"][:len(cases[-1][2])]), ("休む", C["name"], cases[-1][2]))
        self.assertNotIn("rest_why", st["era2"]["g7"])
        self.assertIn(cases[-1][2], era2._season_digest(st, C, first), "休んだ日が 3 日より多くても、わけはお題に出る")
        g7.new_season(st)  # 知っている人・作れる人・一緒にする人は、休まない
        B["plan"] = {"activity": "試す", "place": "camp", "with": []}
        g7.job(st, B, {"activity": "試す", "try": "H9-02"})
        C["plan"] = {"activity": "黒い金属を作る", "place": "camp", "with": [A["name"]]}
        g7.job(st, C, {"activity": "黒い金属を作る"})
        self.assertEqual((B["plan"]["activity"], C["plan"]["activity"]), ("試す", "黒い金属を作る"))
        self.assertNotIn("rest_why", st["era2"]["g7"])
        st2, A2, B2, C2 = self.scene(day=g10.G10_FIX_FROM - 30)  # 直しの日より前: 休むにするだけ (わけは残さない)
        g7.new_season(st2)
        C2["plan"] = {"activity": "試す", "place": "camp", "with": []}
        g7.job(st2, C2, {"activity": "試す", "try": "H9-02"})
        self.assertEqual(C2["plan"]["activity"], "休む")
        self.assertNotIn("rest_why", st2["era2"]["g7"])

    def test_sample_add(self):
        """③ 作れる人・試している人の家を、ふつうの見本の家に足す (ふつうの選びは変えない)。直しの日の年の選びより前は、何も足さない"""
        import g7
        import g10
        import random
        st, A, B, C = self.scene()
        ha, hb = A["household"], B["household"]
        self.assertEqual(g10.key_houses(st), [ha])
        self.assertNotIn(A["name"], era2.answerers(st))
        added = g7.g10_sample_add(st)
        self.assertEqual(added, [ha])
        self.assertEqual({k: v for k, v in st["era2"]["g7"]["sample"][ha].items() if k != "cell"}, {"since": st["day"], "must": True, "g10": True})
        self.assertIn(A["name"], era2.answerers(st))
        self.assertEqual(g7.g10_sample_add(st), [], "2 度は足さない")
        st["era2"]["g7"]["hints"]["tech"]["H9-02"]["first"] = st["day"]  # 試している人 (腕が 0 より大きい) の家も
        B["skills"]["試す:H9-02"] = 0.2
        self.assertEqual(g10.key_houses(st), sorted([ha, hb]))

        def pick(day, keys):
            s2, *_ = self.scene(day=day)
            s2["people"] = st["people"]  # 同じ人 (A を作れる人に)
            real = g10.key_houses
            g10.key_houses = (lambda s: keys) if keys is not None else real
            import g11
            import g12  # 2026-11-12: 本物の state が G11・G12 からは、作れる人の家 (g11.key_houses)・読める人の家 (g12.key_houses) も足すので、この試しでは止める (G10 の足し方だけを見る)
            real11, real12 = g11.key_houses, g12.key_houses
            g11.key_houses = g12.key_houses = lambda s: []
            try:
                return g7.choose(s2, random.Random(7))
            finally:
                g10.key_houses = real
                g11.key_houses, g12.key_houses = real11, real12

        y = g10.G10_FIX_FROM + era2.YEAR  # 次の年の終わり
        plain, more = pick(y, []), pick(y, [ha])
        self.assertEqual({h: v for h, v in more.items() if not v.get("g10")}, plain, "ふつうの選びは同じ (足すだけ)")
        self.assertTrue(ha in plain or more[ha].get("g10"))
        before, before2 = pick(g10.G10_FIX_FROM, []), pick(g10.G10_FIX_FROM, [ha])
        self.assertEqual(before, before2, "直しの日 (と前) の年の選びは前のまま (その日は refresh_prompts が足す)")

    def test_paths_answerers(self):
        """④ 道の見張りは、お題に答える人 (代表) がその道を選べるときだけ数える。2 年つづけて 0 なら止めて相談 (前のまま)"""
        import g7
        import g10
        st, A, B, C = self.scene()
        self.assertEqual(g10.paths(st), {"c1": False, "c2": False}, "作れる人も知っている人も答えない")
        old, *_ = self.scene(day=g10.G10_FIX_FROM - 30)
        self.assertEqual(g10.paths(old), {"c1": True, "c2": True}, "直しの日より前は、前の数え方 (札と作れる人があれば出ていた)")
        g = st["era2"]["g7"]
        g["sample"][B["household"]] = {"since": st["day"], "cell": g["cells"].get(B["household"]), "must": False}
        self.assertEqual(g10.paths(st), {"c1": False, "c2": True})
        g7.g10_sample_add(st)
        self.assertEqual(g10.paths(st), {"c1": True, "c2": True})
        G = g["g10"]
        y = (st["day"] + 1) // era2.YEAR
        G["path"].pop(str(y), None)
        g10.count_paths(st)
        self.assertEqual({k: G["path"][str(y)][k] for k in ("c1", "c2")}, {"c1": 1, "c2": 1})
        st["day"] = st["day"] + 2 * era2.YEAR  # 2 年あと (y・y+1 が終わった) の年の終わり
        G["c"].pop("c1", None)
        G["path"][str(y)] = {"meetings": 2, "c1": 0, "c2": 1}
        G["path"][str(y + 1)] = {"meetings": 2, "c1": 0, "c2": 2}
        c = g10.path_consult(st, [])
        self.assertEqual((c["why"], c["year"]), ("path_c1", y + 1), "2 年つづけて 0 なら止めて相談")
        G["path"][str(y)]["c1"] = 1
        self.assertIsNone(g10.path_consult(st, []), "1 年だけ 0 なら止めない")

    def test_refresh_prompts(self):
        """refresh_prompts: 答えのない集まりの歩のお題を書き直す (日は進めない・区切り (村の人には見せない)・作れる人の家を答える家に)。答えがあれば断る"""
        import g10
        import step
        st, A, B, C = self.scene(mark=False)
        st["day"] = self.base()["day"]
        st["hold"] = None  # 2026-11-06: 本物の state が止まっている (HOLD consult) 日でも試せるように、写しでは止まりを外す
        st["era2"]["g7"]["hold"] = None
        d = tmpdir()
        try:
            self.assertIn("--why", step._refresh_refusal(st, " "))
            if not st["era2"]["g7"].get("ask"):
                self.assertEqual(step._refresh_refusal(st, "試し"), "この歩は集まらない (お題がない)")
                return
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")  # 読むだけ (export)
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
            r = run("refresh_prompts")
            self.assertNotEqual(r.returncode, 0)
            r = run("refresh_prompts", "--why", "試しのわけ")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            new = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual((new["day"], new["phase"]), (st["day"], st["phase"]), "日は進めない")
            ev = new["events"][-1]
            self.assertEqual((ev["type"], ev["text"], ev["data"]["refresh"]), ("区切り", "お題を書き直した (試しのわけ)", True))
            fx = g10.fixed(new)
            self.assertEqual(fx, st["day"] >= g10.G10_FIX_FROM)
            if st["day"] == g10.G10_FIX_FROM:
                self.assertEqual(new["era2"]["g7"]["g10"]["fix"], {"day": st["day"], "why": "試しのわけ"})
            if fx:
                self.assertEqual(ev["data"]["added"], [A["household"]])
            pd = d / "prompts" / f"day{st['day']:03d}"
            names = {f.stem for f in (pd / "season").glob("*.md")}
            self.assertEqual(names, set(era2.answerers(new)))
            if fx:
                self.assertIn(A["name"], names)
                self.assertIn(f"あなた ({A['name']}) は、黒い金属の作り方を知っている", (pd / "season" / f"{A['name']}.md").read_text(encoding="utf-8"))
            for f in pd.rglob("*.md"):
                t = f.read_text(encoding="utf-8")
                self.assertNotIn("試しのわけ", t, f"{f.name}: 区切りのわけは村の人に見せない")
                self.assertNotIn("お題を書き直した", t)
            ad = d / "answers" / f"day{st['day']:03d}" / "season"
            ad.mkdir(parents=True, exist_ok=True)
            (ad / f"{A['name']}.json").write_text("{}", encoding="utf-8")
            r = run("refresh_prompts", "--why", "もう一度")
            self.assertEqual(r.returncode, 3)
            self.assertIn("答えがもうある", r.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class T_G11(unittest.TestCase):
    """2026-11-05 G11「お金と市場」(docs/society_phase/G11_design.md): G10 を閉じて入る (部は終わらない)・印のかたまりを作る (腕・一緒に作る・印の前と後)・
    印で払う (受けとる決まり・引きかえ・断ったあと 2 年・返しを印で)・市の日 (来る・替える・方針がないとき)・c1〜c3・F・進み・道の見張り (答える人のうち選べる人)・
    名前で知らせる行・わけのない休むが 0・作れる人の家が答える家に・言葉の表。G10 の state では何も働かない。
    G11 に入った日の state (git の G11_ENTRY。印はまだ決まっていない) の写しから、メモリの中で確かめる (G10 なら close_g10 → enter_next。G11 ならそのまま)。
    本物の state は日が進むと印が決まり、試した人が亡くなるので使わない (2026-11-06)。本物の data は読むだけ"""

    NOTE = "本人の決め 2026-11-05 (お任せ): 鉄と広い国を閉じた (試し)"
    _st = None

    @classmethod
    def real(cls):
        if cls._st is None:
            st = git_state(G11_ENTRY)
            g = (st.get("era2") or {}).get("g7") or {}
            cls._st = st if ("g10" in g and st.get("era") in ("G10", "G11")) else False
        if cls._st is False:
            raise unittest.SkipTest("G11_ENTRY の state が G10 か G11 でない")
        return copy.deepcopy(cls._st)

    def g10_state(self):
        """G10 の state (本物が G11 なら、写しの中で g11 を外して G10 にもどす。G10 の仕組みだけの確かめのため)"""
        st = as_g10(self.real())
        g = st["era2"]["g7"]
        st["hold"] = False
        g["hold"] = None
        return st

    def g11_state(self):
        import g7
        st = self.real()
        if st["era"] == "G10":
            st["hold"] = False
            st["era2"]["g7"]["hold"] = None
            g7.close_g10(st, self.NOTE)
            g7.enter_next(st)
            st["era_log"][-1]["g10_closed"] = st["day"]
        return st

    def people3(self, st):
        """作れる人 A と、作れない答える人 B (A と別の家)"""
        import g10
        sm = g10.smiths_now(st)
        self.assertTrue(sm, "作れる人がいる")
        ans = era2.answerers(st)
        A = next(p for p in era2.adults(st) if p["name"] in sm)
        B = next(p for p in era2.adults(st) if p["name"] in ans and not g10.smith(st, p["name"]) and p.get("household") != A.get("household"))
        return A, B

    def test_enter_from_g10(self):
        import g10
        import g11
        import g7
        import hints
        import step
        st = self.g10_state()
        if not list((REAL / "answers" / f"day{st['day']:03d}").glob("*/*.json")):
            self.assertIsNone(step._next_part_refusal(st, None, self.NOTE))
        n_ev = st["next_event"]
        t10 = st["era2"]["g7"]["g10"]
        reached10, c10, reap10 = dict(t10["reached"]), dict(t10["c"]), {k: dict(v) for k, v in t10["reap"].items()}
        sha0 = hints.cards_sha(st)
        c = g7.close_g10(st, self.NOTE)
        self.assertEqual((c["day"], c["note"], c["made"], c["reached"]), (st["day"], self.NOTE, len(t10["made"]), reached10))
        self.assertEqual(c["iron_share_best"], max((round(r["iron"] / r["all"], 3) for r in reap10.values() if r["all"]), default=0.0))
        self.assertIn("G10 はもう閉じている", step._next_part_refusal(st, None, self.NOTE))
        part0, ps0 = st["era2"]["g7"]["part"], st["era2"]["g7"]["part_start"]
        g7.enter_next(st)
        g = st["era2"]["g7"]
        self.assertEqual((st["era"], st["era_info"]["name"], g["part"], g["part_start"], g["part_start11"]), ("G11", "お金と市場", part0, ps0, st["day"]),
                         "部は終わらない (第 6 部のまま)")
        self.assertNotIn("G11", era2.PART_END)
        self.assertEqual(g["before"]["G10"]["g10"]["reached"], reached10)
        self.assertEqual(g["before"]["G10"]["g10"]["c"], c10)
        self.assertEqual((g["g10"]["c"], g["g10"]["path"]), ({}, {}), "G10 の条件と道の見張りは数え直す")
        self.assertEqual(g["g10"]["reached"], reached10, "G10 の F は村に起きたことなので消さない (字を習う道は F2 を見る)")
        self.assertNotIn("stall", g, "G10 のときの止まりは before.G10 に移す")
        self.assertIn("stall", g["before"]["G10"])
        self.assertEqual(hints.cards_sha(st), sha0, "札は足さない")
        self.assertIsNone(hints.cards_changed(st))
        types = [e["type"] for e in st["events"] if e["id"] >= n_ev]
        self.assertEqual(types, ["フェーズ", "試す", "フェーズ"])
        self.assertIn("フェーズ G11 (お金と市場) を始めた", st["events"][-1]["text"])
        ind = era2.indicators(st)
        self.assertEqual((ind["g11_c1_day"], ind["g11_c2_day"], ind["g11_c3_day"]), (None, None, None))
        self.assertFalse(era2.CRITERIA["G11"][1](ind))
        self.assertIn(g11.ACT_COIN, g7.acts(st))
        for h in g11.key_houses(st):
            self.assertIn(h, g["sample"], "作れる人の家は、入る日から答える家")
        self.assertTrue(set(g10.smiths_now(st)) & set(era2.answerers(st)))
        txt = g7.facts(st) + g7._field_rows(st, False, True) + g7.fields_json(st, era2.adults(st)[0], False) + g7.fields_prop(st)
        for p in era2.adults(st)[:40]:
            txt += g11.text(st, p) + g11.feel_note(st, p)
        self.assertIn("印のかたまり", txt)
        self.assertIn('"market_day": null', txt)
        self.assertEqual(g11.bad_words(txt), [], "お金・硬貨・市場・鉄・国などを書かない")
        self.assertNotIn("【", g11.text(st, era2.adults(st)[0]))

    def test_g10_unchanged(self):
        """G10 の state (g7.g11 がない) では、新しい仕事・文・欄・目安・掟の欄は何も働かない"""
        import g7
        import g11
        st = self.g10_state()
        self.assertNotIn(g11.ACT_COIN, g7.acts(st))
        self.assertNotIn("印のかたまり", g7.facts(st) + g7.text(st, era2.adults(st)[0]) + g7._field_rows(st, False, True))
        self.assertEqual(g7.fields_prop(st), ', "tax": null, "rate": null')
        self.assertNotIn('"pay"', g7.fields_json(st, era2.adults(st)[0], False))
        self.assertNotIn("g11_c1_day", era2.indicators(st))
        q = era2.adults(st)[0]
        g7.new_season(st)
        q["plan"] = {"activity": "休む", "place": "camp", "with": []}
        g7.job(st, q, {"activity": g11.ACT_COIN})
        self.assertNotIn("rest_why", st["era2"]["g7"], "G10 では、印のかたまりのわけは残さない (仕事の並びにないので前のまま)")
        self.assertEqual(era2.ORDER2[era2.ORDER2.index("G10"):era2.ORDER2.index("G10") + 2], ["G10", "G11"])

    def test_make_coins(self):
        """作る: 作れる人は 1 日 10 個 / 作れない人は休む (わけ) / 作れる人と同じ日に with で作れば作れ、次の季節から作れる人 / 印の前は印のないかたまり、印が決まると村のもの (F1)"""
        import g10
        import g11
        import g7
        st = self.g11_state()
        A, B = self.people3(st)
        g = st["era2"]["g7"]["g11"]
        for p in era2.adults(st):
            p["today"] = {"activity": "休む"}
        A["today"] = {"activity": g11.ACT_COIN}
        A["plan"] = {"activity": g11.ACT_COIN, "place": "camp", "with": []}
        B["today"] = {"activity": g11.ACT_COIN}
        B["plan"] = {"activity": g11.ACT_COIN, "place": "camp", "with": []}
        t = {}
        g11.make_day(st, A, t)
        self.assertEqual((g["coins"]["unmarked"], g["coins"]["village"]), (10, 0), "印の前は印のないかたまり")
        g11.make_day(st, B, t)
        self.assertEqual(g["coins"]["unmarked"], 10, "with のない作れない人は作れない")
        ev = st["events"][-1]
        self.assertEqual((ev["type"], ev["who"]), ("休む", B["name"]))
        self.assertIn("休んだ", ev["text"])
        self.assertTrue(any(f["who"] == B["name"] for f in g["fails"]), "できなかったことの帳簿")
        B["plan"]["with"] = [A["name"]]
        g11.make_day(st, B, t)
        self.assertEqual(g["coins"]["unmarked"], 20)
        self.assertIn(B["name"], st["era2"]["g7"]["g10"]["pending_smiths"])
        g10.season_end(st)
        self.assertTrue(g10.smith(st, B["name"]), "一緒に作った人は次の季節から作れる人")
        self.assertNotIn("F1", g["reached"])
        g11.apply_answers(st, {A["name"]: {"mark": "川と麦の穂"}})
        self.assertEqual((g["mark"]["text"], g["coins"]["village"], g["coins"]["unmarked"]), ("川と麦の穂", 20, 0))
        self.assertIn("F1", g["reached"])
        g11.make_day(st, A, t)
        self.assertEqual(g["coins"]["village"], 30)
        self.assertTrue(g7._g11_ok(st, B["name"], g11.ACT_COIN, ()))

    def ready(self, st, coins=500):
        """印が決まり、村に印のかたまりがあり、払い方は「印」"""
        g = st["era2"]["g7"]["g11"]
        g["mark"] = {"text": "川と麦の穂", "day": st["day"], "votes": ""}
        g["coins"]["village"] = coins
        g["pay"] = {"choice": "印", "day": st["day"], "votes": ""}
        return g

    def offer(self, st, o, kind="貸して", want=None, give=None):
        g6 = era2._g6(st)
        off = {"id": f"T{g6['next_offer']}", "other": o["id"], "day": st["day"], "kind": kind, "give": give or {}, "want": want or {"草の種": 3000},
               "goats_in": [{"sex": "メス", "age": 2}] * (give or {}).get("ヤギ", 0), "mem": {"village": 1.0, "other": 1.0}}
        g6["next_offer"] += 1
        return off

    def decide(self, st, off, o):
        n = len(era2.adults(st))
        c = {"trade": {off["id"]: {"村": {p["name"] for p in era2.adults(st)}}}, "trade_by": {}, "house": {}}
        era2._g6_decide(st, c, off, o, n, None)

    def test_pay_and_accept(self):
        """印で貸す (字で書く → F3・F4)・受けとらないわけ (蓄えが足りない・断ったあと 2 年・印が決まっていない) で物で払う (わけを残す)"""
        import g10
        import g11
        st = self.g11_state()
        g = self.ready(st)
        others = era2._g6(st)["others"]
        o = others[0]
        o["bad"] = st["day"]
        g6 = era2._g6(st)
        nd = len(g6["debts"])
        self.decide(st, self.offer(st, o, "貸して", {"草の種": 3000}), o)
        self.assertEqual(len(g6["debts"]), nd + 1)
        d = g6["debts"][-1]
        self.assertEqual((d["coin"], d["goods"], d["lender"]), (300, {"草の種": 3000}, "村"))
        self.assertEqual((g["coins"]["village"], g["coins"]["others"][o["id"]]), (200, 300))
        row = g["flows"][str(st["day"] // era2.YEAR)]
        self.assertEqual((row["all"], row["coin"]), (1, 1))
        self.assertIn("F3", g["reached"])
        if g10.readers(st):
            self.assertIn("F4", g["reached"])
            self.assertEqual(g["credit"][str(st["day"] // era2.YEAR)]["written"], 1)
        grain = era2._g6_have(st, "村", "草の種")
        g["coins"]["others"]["N0"] = grain // g11.value(st) + 1
        self.assertIn("引きかえられるほどない", g11.accept_why(st, 1))
        nf = len(g["fails"])
        o2 = others[1]
        o2["bad"] = None
        self.decide(st, self.offer(st, o2, "交換", {"鎌": 1}, {"ヤギ": 1}), o2)
        self.assertEqual(len(g["fails"]), nf + 1, "物で払ったわけを残す")
        self.assertIn("物で払う", g["fails"][-1]["why"])
        self.assertEqual(st["events"][-2]["type"], "印のかたまり", "わけの出来事")
        self.assertEqual(st["events"][-1]["type"], "交換", "物で受けた (今までどおり)")
        g["coins"]["others"].pop("N0")
        g["refused"] = [st["day"] - 10]
        self.assertIn("引きかえを断った", g11.accept_why(st, 1))
        g["refused"] = [st["day"] - 2 * era2.YEAR]
        self.assertIsNone(g11.accept_why(st, 1), "2 年たてば受けとる")
        g["mark"] = None
        self.assertIn("印がまだ決まっていない", g11.accept_why(st, 1))

    def test_redeem_and_repay(self):
        """引きかえ (苦しい村は季節の終わりに草の種と引きかえる)・断る (redeem 引きかえない → 2 年受けとらない)・返しを印で先に"""
        import g11
        st = self.g11_state()
        g = self.ready(st)
        o = era2._g6(st)["others"][0]
        o["bad"] = st["day"]
        g["coins"]["others"][o["id"]] = 50
        v0, og = era2._g6_have(st, "村", "草の種"), o["grain"]
        g11._redeem(st)
        self.assertEqual(g["coins"]["others"][o["id"]], 0)
        self.assertEqual(g["coins"]["village"], 550)
        self.assertEqual(era2._g6_have(st, "村", "草の種"), v0 - 500)
        self.assertEqual(o["grain"], og + 500)
        g["coins"]["others"][o["id"]] = 20
        g["redeem"] = {"choice": "引きかえない", "day": st["day"], "votes": ""}
        g11._redeem(st)
        self.assertEqual(g["refused"], [st["day"]])
        self.assertIn("断った", g["fails"][-1]["why"])
        self.assertIn("引きかえを断った", g11.accept_why(st, 1))
        g["refused"], g["redeem"]["choice"] = [], "引きかえる"
        g6 = era2._g6(st)
        d = {"id": f"D{g6['next_debt']}", "other": o["id"], "lender": "村", "goods": {"草の種": 1000}, "day": st["day"] - 100, "due": st["day"],
             "proof": "板", "mem": {"village": 1.0, "other": 1.0}, "status": "まだ", "end": None}
        g6["next_debt"] += 1
        g6["debts"].append(d)
        o["grain"] = 5000
        off = {"id": "T0", "other": o["id"], "kind": "返す", "debt": d["id"], "give": {"草の種": 1000}, "want": {}}
        c0 = g["coins"]["village"]
        era2._g6_repay(st, off, o)
        self.assertEqual(d["status"], "返した", "印で返した分も数えて、足りている")
        self.assertEqual(g["coins"]["village"], c0 + 20)
        self.assertEqual(o["grain"], 5000 - 800)
        self.assertIn("印のかたまり", st["events"][-1]["text"])

    def test_market(self):
        """市の日: 掟の market_day の日に、行き来のある近くの村の人が来る。方針がなければ見て帰る。方針のとおりに印か物で替える (F2)。c2 は 2 年つづけて 2 回"""
        import g11
        st = self.g11_state()
        g = self.ready(st, 2000)
        vis = g11.visitors(st)
        if not vis:
            self.skipTest("行き来のある近くの村がない")
        st["laws"].append({"id": "L9999", "text": "市の日を決める", "status": "採用", "votes": {}, "day": st["day"], "market_day": 10})
        self.assertEqual(g11.market_day(st), 10)
        st["day"] = (st["day"] // era2.SEASON_DAYS + 1) * era2.SEASON_DAYS + 9  # 次の季節の 10 日目
        for o in vis:
            o["goats"] = max(o["goats"], 10)
        n0 = st["next_event"]
        g11.market(st)
        ev = [e for e in st["events"] if e["id"] >= n0]
        self.assertEqual(len(ev), 1)
        self.assertIn("市の方針 (market) を決めていない", ev[0]["text"])
        g["market"] = {"give": {"草の種": 3000, "鎌": 2}, "take": ["ヤギ", "土器"], "pay": True}
        st["day"] += era2.SEASON_DAYS
        g11.market(st)
        y = st["day"] // era2.YEAR
        self.assertGreaterEqual(g11.markets_with_deals(st, y), 1)
        self.assertIn("F2", g["reached"])
        self.assertTrue(any(f["coin"] for f in g["flow_log"]), "印で払った")
        st["day"] += 1
        n1 = st["next_event"]
        g11.market(st)
        self.assertEqual(st["next_event"], n1, "市の日でない日は何もしない")
        g["markets"][str(y - 1)] = [{"day": 0, "came": ["N1"], "deals": 1}] * 2
        g["markets"][str(y)] = [{"day": 0, "came": ["N1"], "deals": 1}] * 2
        g11.season_end(st)
        self.assertIn("c2", g["c"])

    def test_conditions_progress(self):
        """c1 (半分以上・4 回)・c3 (字で書いた年が 2 年)・進みは段と数をつなげる (割合が上がれば上がる)"""
        import g11
        st = self.g11_state()
        g = self.ready(st)
        y = st["day"] // era2.YEAR
        g["flows"][str(y)] = {"all": 8, "coin": 3}
        p1 = g11.progress(st)["c1"]
        g["flows"][str(y)] = {"all": 8, "coin": 4}
        self.assertGreater(g11.progress(st)["c1"], p1, "割合が上がれば進みが上がる")
        g["flows"][str(y)] = {"all": 9, "coin": 4}
        g11.season_end(st)
        self.assertNotIn("c1", g["c"], "半分に届かない")
        g["flows"][str(y)] = {"all": 8, "coin": 4}
        g11.season_end(st)
        self.assertIn("c1", g["c"])
        g["credit"][str(y)] = {"coin": 1, "written": 1}
        g11.season_end(st)
        self.assertNotIn("c3", g["c"], "1 年だけでは届かない")
        g["credit"][str(y - 1)] = {"coin": 2, "written": 1}
        self.assertGreaterEqual(g11.progress(st)["c3"] % 1000, 200)
        g11.season_end(st)
        self.assertIn("c3", g["c"])

    def test_paths_and_named_lines(self):
        """G10 から学んだこと: 道を選べる答える人のお題には、みな名前で「あなたは〜できる」の 1 行がある。道の見張りは選べる人で数え、選べる人がいない場面で 0 になり、
        2 年つづけて 0 なら止めて相談。読める人が 0 なら条件 3 の道は 0"""
        import g10
        import g11
        st = self.g11_state()
        g = st["era2"]["g7"]["g11"]
        ans = era2.answerers(st)
        pt = g11.paths(st)
        self.assertEqual(set(pt["c1"]), set(ans), "印が決まっていなければ、答える人はみな mark を選べる")
        sm = set(g10.smiths_now(st))
        for n in ans:
            p = next(q for q in era2.adults(st) if q["name"] == n)
            t = g11.text(st, p)
            self.assertTrue("mark に" in t, n)
            if n in sm:
                self.assertIn(f"あなた ({n}) は黒い金属を作れるので、主な仕事を「印のかたまりを作る」にできる", t)
            elif g11._house_smiths(st, n):
                self.assertIn("は印のかたまりを作れる (家族の仕事 family", t)
        g["mark"] = {"text": "川", "day": st["day"], "votes": ""}
        for n in [n for n in ans if n in sm or g11._house_smiths(st, n)]:
            p = next(q for q in era2.adults(st) if q["name"] == n)
            self.assertIn("印のかたまりを作", "".join(g11._mine(st, p)), "印が決まったあとも、作れる人と家の代表には名前で出る")
        sm_h = set(g11.key_houses(st))
        g7s = st["era2"]["g7"]
        g7s["sample"] = {h: v for h, v in g7s["sample"].items() if h not in sm_h}
        if era2._leader(st) in sm:
            st["era2"]["g5"]["leader"] = None
        pt = g11.paths(st)
        self.assertEqual(pt["c1"], [], "作れる人も印のかたまりもない答える人は、条件 1 の道を選べない")
        self.assertEqual(pt["c3"], [])
        y = (st["day"] + 1) // era2.YEAR
        g["path"].pop(str(y), None)
        g11.count_paths(st, {})
        self.assertEqual(g["path"][str(y)]["c1"], 0)
        g["start"] = st["day"] - 3 * era2.YEAR
        st["day"] = (y + 2) * era2.YEAR - 1
        g["path"][str(y)] = {"meetings": 2, "c1": 0, "c2": 3, "c3": 0, "chose": 0, "who": {}}
        g["path"][str(y + 1)] = {"meetings": 2, "c1": 0, "c2": 3, "c3": 1, "chose": 0, "who": {}}
        c = g11.path_consult(st, [])
        self.assertEqual((c["why"], c["year"]), ("g11_path_c1", y + 1))
        g["path"][str(y)]["c1"] = 1
        self.assertIsNone(g11.path_consult(st, []), "1 年だけ 0 なら止めない")
        st2 = self.g11_state()
        st2["era2"]["g7"]["g10"]["readers"] = {}
        self.assertEqual(g11.paths(st2).get("c3"), [], "読める人がいなければ、条件 3 の道は 0")
        self.assertTrue(any("読み書きできる大人が 0 人" in t for t in g11.report_lines(st2)))

    def test_rest_reason(self):
        """わけのない「休む」が 0: 印のかたまりを作るを選べず休むにしたら、わけを出来事に残す (答えのときは季節のはじめの日に)"""
        import g11
        import g7
        st = self.g11_state()
        A, B = self.people3(st)
        g7.new_season(st)
        B["plan"] = {"activity": g11.ACT_COIN, "place": "camp", "with": []}
        g7.job(st, B, {"activity": g11.ACT_COIN})
        self.assertEqual(B["plan"]["activity"], "休む")
        w = st["era2"]["g7"]["rest_why"][B["name"]]["text"]
        self.assertTrue(w.startswith(f"{B['name']} は、印のかたまりの作り方を知らないので、休んだ"), w)
        first = st["next_event"]
        g7.count_day(st, B["name"], "休む")
        ev = [e for e in st["events"] if e["id"] >= first]
        self.assertEqual((ev[0]["type"], (ev[0].get("data") or {}).get("rest_why")), ("休む", g11.ACT_COIN))
        self.assertIn(w, era2._season_digest(st, B, first))
        g7.new_season(st)  # 作れる人がいない (仕事の並びにない) ときも
        st["era2"]["g7"]["g10"]["smiths"] = []
        for p in era2.adults(st):
            p["skills"] = {k: v for k, v in p["skills"].items() if not k.startswith("試す:H9-01")}
        self.assertNotIn(g11.ACT_COIN, g7.acts(st))
        B["plan"] = {"activity": "休む", "place": "camp", "with": []}
        g7.job(st, B, {"activity": g11.ACT_COIN})
        self.assertIn("黒い金属を作れる人がいない", st["era2"]["g7"]["rest_why"][B["name"]]["text"])
        st2 = self.g11_state()
        A2, B2 = self.people3(st2)
        g7.new_season(st2)
        B2["plan"] = {"activity": g11.ACT_COIN, "place": "camp", "with": [A2["name"]]}
        g7.job(st2, B2, {"activity": g11.ACT_COIN})
        self.assertEqual(B2["plan"]["activity"], g11.ACT_COIN, "作れる人と一緒なら休まない")
        self.assertNotIn("rest_why", st2["era2"]["g7"])

    def test_key_houses_sample(self):
        """作れる人の家は、ふつうの見本の家に足す (年の選び直しでも外れない)。G10 の直し ③ と同じ形 (g10: true)"""
        import g11
        import g7
        import random
        st = self.g11_state()
        kh = g11.key_houses(st)
        self.assertTrue(kh)
        g7s = st["era2"]["g7"]
        for h in kh:
            g7s["sample"].pop(h, None)
        self.assertEqual(sorted(g7.g10_sample_add(st)), kh)
        for h in kh:
            self.assertTrue(g7s["sample"][h]["must"])
        st["day"] = (st["day"] // era2.YEAR + 4) * era2.YEAR - 1  # 4 年あと (3 年をこえても) の年の終わりの選び
        for h in kh:
            g7s["sample"][h]["since"] = st["day"] - 4 * era2.YEAR
        new = g7.choose(st, random.Random(7))
        for h in kh:
            self.assertIn(h, new, "3 年をこえても、作れる人の家は外れない")

    def test_iron_kept_by_learned(self):
        """札を試した人 (試すの腕のある人) がみな亡くなっても、一緒に作って覚えた人が生きていれば、G11 では黒い金属は作れたまま
        (2026-11-05 の決まりの村 G11B0 の種 1 で、ケセ19 が 4 年目に亡くなり、タユ25 がいるのに作れる人が 0 人になった)。G10 では前のまま (できなくなる)"""
        import g10
        import g11
        import hints
        key = f"試す:{g10.CARD_IRON}"
        for st, kept in ((self.g11_state(), True), (self.g10_state(), False)):
            tried = [p for p in era2.adults(st) if p["skills"].get(key, 0) > 0]
            learned = [n for n in st["era2"]["g7"]["g10"]["smiths"] if n not in {p["name"] for p in tried}]
            self.assertTrue(tried and learned, "試した人と、一緒に作って覚えた人がいる")
            for p in tried:
                p["alive"] = False
            self.assertTrue(g10.iron_ready(st))
            hints._tech_season(st)
            self.assertEqual(g10.iron_ready(st), kept)
            if kept:
                self.assertEqual(g11.smiths(st), sorted(n for n in learned if n in {p["name"] for p in era2.adults(st)}))
                self.assertTrue(g11.key_houses(st))
                self.assertFalse(any("できなくなった" in e["text"] for e in st["events"][-3:]))
            else:
                self.assertIn("できなくなった", st["events"][-1]["text"])

    def test_next_part_cli(self):
        """step.py next_part --closed-by-decision (写しのフォルダ): G10 → G11。形 A・B の文をそのまま残す。G11 のお題に節と欄。2 回目は断る"""
        import g11
        st = self.g10_state()
        if not st["era2"]["g7"].get("ask"):
            self.skipTest("集まりの歩でない")
        y = (st["day"] + 1) // era2.YEAR - 1
        notes = {"A": f"本人の決め 2026-11-05 (お任せ): 鉄と広い国を {y}年120日目で閉じた。c1・c2 は届き、c3 は 23 年届かなかった",
                 "B": f"本人の決め 2026-11-05 (お任せ): 鉄と広い国を {y}年120日目で閉じた。c2 は届き、c1・c3 は 23 年届かなかった (c1 はいちばん多い年で 4.4 割)"}
        for form, note in notes.items():
            d = tmpdir()
            try:
                (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                (d / "archive").symlink_to(REAL / "archive")
                env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
                run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
                r = run("next_part", "--closed-by-decision", note)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("* G10 (鉄と広い国): 3 つの条件はそろわないまま、本人の決めで閉じた", r.stdout)
                self.assertIn("* フェーズ G11 (お金と市場) に入った", r.stdout)
                new = json.loads((d / "state.json").read_text(encoding="utf-8"))
                self.assertEqual((new["era"], new["day"], new["era2"]["g7"]["closed10"]["note"], new["era_log"][-1]["g10_closed"]), ("G11", st["day"], note, st["day"]))
                ph = [e for e in new["events"] if e["type"] == "フェーズ" and (e.get("data") or {}).get("note") == note]
                self.assertEqual(len(ph), 1, f"形 {form}: 本人の言葉は出来事「フェーズ」の data に残る")
                if form == "B":
                    pd = d / "prompts" / f"day{st['day']:03d}"
                    names = {f.stem for f in (pd / "season").glob("*.md")}
                    self.assertEqual(names, set(era2.answerers(new)))
                    for f in (pd / "season").glob("*.md"):
                        t = f.read_text(encoding="utf-8")
                        i = t.index("## 印のかたまりと市")
                        j = t.find("\n## ", i + 5)
                        self.assertEqual(g11.bad_words(t[i:j if j > 0 else None]), [], "節に書かない言葉 (年の出来事の「フェーズ」の文は G10 と同じく前からの形)")
                    r = run("next_part", "--closed-by-decision", note)
                    # 2026-11-10: G11 から G12 に閉じて入れるようになったので、2 回目は G10 をもう一度閉じず、G11 を閉じて G12 に入る (G10 は閉じたまま)
                    self.assertNotIn("* G10 (鉄と広い国)", r.stdout, "G10 は 2 回閉じない")
                    if r.returncode == 0:
                        self.assertIn("* G11 (お金と市場)", r.stdout)
                        self.assertEqual(json.loads((d / "state.json").read_text(encoding="utf-8"))["era2"]["g7"]["closed10"]["note"], note)
                    else:
                        self.assertEqual(r.returncode, 3)
            finally:
                shutil.rmtree(d, ignore_errors=True)


class T_G11FIX(unittest.TestCase):
    """2026-11-06 本人の決め「②③を直して続ける」(docs/society_phase/G11_stall_diag.md 7. の 1〜3 と「した直し」): g11.G11_FIX_FROM (158年の年の集まり) からの直し 3 つ。
    ① 市の日 (market_day) とねうち (coin_rate) を年の集まりの村の欄に (g7._tally。掟の道も残す) ② 道の見張り: 前の 1 年に出し入れ 0 回なら条件 1・3 は 0、報告に 1 行
    ③ お題だけの行 (印のかたまりでできること・申し出に来なくなった村・null だと受けない・市の日に来る村)。
    直しの日より前と、直しの日で refresh_prompts の印がないときは、前のコード (OLD) と同じ文・同じ state。直しの前の state (git の OLD。18839 日目・G11・印のまま・直しの印なし) の写しで確かめる。
    本物の state はもう直しの日をこえ、印と市の日がついているので使わない (2026-11-06。本物の data は読むだけ)"""

    OLD = "78d16211"  # 直しの前のコミット (g11.py)
    _st = None
    _old = None

    @classmethod
    def base(cls):
        if cls._st is None:
            st = git_state(cls.OLD)
            cls._st = st if "g11" in ((st.get("era2") or {}).get("g7") or {}) else False
        if cls._st is False:
            raise unittest.SkipTest("OLD の state が G11 でない")
        return copy.deepcopy(cls._st)

    @classmethod
    def old(cls):
        """直しの前の g11.py (git から読む。別の名の模様として。中で呼ぶ g7・era2 は今のもの)"""
        if cls._old is None:
            import importlib.util
            r = subprocess.run(["git", "-C", str(ROOT), "show", f"{cls.OLD}:sim/society/g11.py"], capture_output=True, text=True)
            if r.returncode:
                raise unittest.SkipTest("前のコードが git にない")
            spec = importlib.util.spec_from_loader("g11_old", loader=None)
            m = importlib.util.module_from_spec(spec)
            exec(compile(r.stdout, "g11_old.py", "exec"), m.__dict__)
            cls._old = m
        return cls._old

    def scene(self, day=None, mark=True, year=True):
        import g11
        st = self.base()
        st["day"] = g11.G11_FIX_FROM if day is None else day
        g7s = st["era2"]["g7"]
        if year:
            g7s["ask"] = "年"
        g7s["g11"].pop("fix", None)
        if mark:
            g11.mark_fix(st, "試し")
        return st

    def texts(self, mod, st):
        out = [mod.facts(st), "\n".join(mod.field_rows(st, True)), "\n".join(mod.field_rows(st, False)), mod.fields_json(st), json.dumps(mod.paths(st), ensure_ascii=False),
               "\n".join(mod.report_lines(st)), str(mod.market_day(st)), str(mod.value(st))]
        for p in era2.adults(st)[:60]:
            out += [mod.text(st, p), mod.feel_note(st, p)]
        return out

    def test_gate_identical(self):
        """直しの日より前 (本物の日・直しの日の 1 年前) と、直しの日で印がないときは、お題の文・道の見張り・報告・欄が前のコードと 1 文字も同じ。
        答えに market_day・coin_rate があっても state は前と同じ (読まない)"""
        import g11
        old = self.old()
        for day, mark in ((self.base()["day"], True), (g11.G11_FIX_FROM - era2.YEAR, True), (g11.G11_FIX_FROM - 1, True), (g11.G11_FIX_FROM, False)):
            st = self.scene(day, mark)
            self.assertFalse(g11.fixed(st), (day, mark))
            self.assertNotIn("fix", st["era2"]["g7"]["g11"])
            self.assertEqual(self.texts(g11, st), self.texts(old, st), (day, mark))
            ans = {n: {"market_day": 7, "coin_rate": 20, "pay": "物"} for n in era2.answerers(st)[:5]}
            a, b = copy.deepcopy(st), copy.deepcopy(st)
            g11.apply_answers(a, copy.deepcopy(ans))
            g11.count_paths(a, copy.deepcopy(ans))
            old.apply_answers(b, copy.deepcopy(ans))
            old.count_paths(b, copy.deepcopy(ans))
            self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True), json.dumps(b, ensure_ascii=False, sort_keys=True), (day, mark))
            self.assertIsNone(a["era2"]["g7"]["g11"]["value"])
            self.assertNotIn("market_day", a["era2"]["g7"]["g11"])
        self.assertTrue(g11.fixed(self.scene(g11.G11_FIX_FROM + 1, mark=False)), "直しの日より後は、印がなくても直す")
        st = self.scene(g11.G11_FIX_FROM - era2.YEAR)
        self.assertNotIn("fix", st["era2"]["g7"]["g11"], "直しの日より前は、mark_fix も何もしない")

    def test_fields_tally(self):
        """① 直しの日から、年の集まりの答えの market_day・coin_rate を、いちばん多い手で決める (決めない人は数えない)。出来事「印」。掟の道も残り、新しいほうを使う。
        ほかの集まりでは読まない。欄はお題の形と答えの欄の説明に出る"""
        import g11
        st = self.scene()
        g = st["era2"]["g7"]["g11"]
        self.assertTrue(g11.fixed(st))
        self.assertEqual(g["fix"], {"day": st["day"], "why": "試し"})
        fj = g11.fields_json(st)
        self.assertIn('"market_day": null, "coin_rate": null', fj)
        rows = "\n".join(g11.field_rows(st, True))
        self.assertIn("(market_day。決めないなら null)", rows)
        self.assertIn("(coin_rate。決めないなら null)", rows)
        self.assertNotIn("掟の提案に market_day (季節の何日目か。1 から 30) をつけると", rows)
        self.assertIsNone(g11.market_day(st))
        self.assertEqual(g11.value(st), g11.COIN_VALUE)
        ans = era2.answerers(st)
        self.assertGreaterEqual(len(ans), 4)
        real = {ans[0]: {"market_day": 7, "coin_rate": 20}, ans[1]: {"market_day": "7", "coin_rate": {"印のかたまり": 20}},
                ans[2]: {"market_day": 12, "coin_rate": None}, ans[3]: {"market_day": 99, "coin_rate": 0}}
        n0 = st["next_event"]
        g11.apply_answers(st, real)
        self.assertEqual((g11.market_day(st), g11.value(st)), (7, 20))
        self.assertEqual((g["market_day"]["n"], g["market_day"]["day"], g["value"]["n"]), (7, st["day"], 20))
        self.assertIn("いちばん多い手", g["market_day"]["votes"])
        ev = [e["text"] for e in st["events"] if e["id"] >= n0]
        self.assertTrue(any("市の日を、季節ごとの 7 日目に決めた" in t for t in ev), ev)
        self.assertTrue(any("印のかたまり 1 個のねうちを、草の種 20 つかみに決めた" in t for t in ev), ev)
        n1 = st["next_event"]
        g11.apply_answers(st, {ans[0]: {"market_day": 7}})
        self.assertFalse(any(e["id"] >= n1 and e["type"] == "印" for e in st["events"]), "同じなら出来事は書かない")
        self.assertIn("- 市の日: 季節ごとの 7 日目。", g11.text(st, era2.adults(st)[0]))
        st["laws"].append({"id": "L99999", "text": "市の日", "status": "採用", "votes": {}, "day": st["day"], "changed": st["day"] + 1, "market_day": 15, "coin_rate": 30})
        self.assertEqual((g11.market_day(st), g11.value(st)), (15, 30), "掟のほうが新しければ掟")
        st["day"] += 2
        g11.apply_answers(st, {ans[0]: {"market_day": 3}})
        self.assertEqual(g11.market_day(st), 3, "年の集まりで決め直したほうが新しい")
        st2 = self.scene()
        st2["era2"]["g7"]["ask"] = "秋"
        g11.apply_answers(st2, {ans[0]: {"market_day": 7, "coin_rate": 20}})
        self.assertIsNone(g11.market_day(st2), "年の集まりでないときは読まない")
        self.assertNotIn("market_day", g11.fields_json(st2))
        self.assertIn("年の集まりの答え (market_day・coin_rate)", "\n".join(g11.field_rows(st2, False)))
        st3 = self.scene()
        self.assertEqual(g11._chose(st3, {ans[0]: {"market_day": 5}}), 1, "道を選んだ人に数える")
        st3["era2"]["g7"]["g11"]["market_day"] = {"n": 10, "day": st3["day"], "votes": ""}
        st3["day"] = (st3["day"] // era2.SEASON_DAYS + 1) * era2.SEASON_DAYS + 9
        n2 = st3["next_event"]
        g11.market(st3)
        self.assertTrue(any(e["id"] >= n2 and e["type"] == "市" for e in st3["events"]), "村の欄で決めた市の日にも市が立つ")

    def test_path_watch(self):
        """② 直しの日から: 前の 1 年によその集落との出し入れが 0 回なら、条件 1・3 の道は 0 (報告に 1 行)。出し入れがあれば前のとおり。
        条件 2 は、年の集まりなら答える人みな (market_day を書ける)。2 年つづけて 0 なら止めて相談 (前の決まりのまま)"""
        import g11
        st = self.scene()
        g = st["era2"]["g7"]["g11"]
        ans = era2.answerers(st)
        g["flow_log"] = [f for f in g["flow_log"] if f["day"] <= st["day"] - era2.YEAR]
        self.assertEqual(g11.flows_recent(st), 0)
        pt = g11.paths(st)
        self.assertEqual((pt.get("c1"), pt.get("c3", [])), ([], []))
        self.assertEqual(set(pt["c2"]), set(ans), "年の集まりは、だれでも market_day を書ける")
        y = st["day"] // era2.YEAR
        g["flows"].pop(str(y), None)
        self.assertTrue(any("よその集落との出し入れが 0 回" in t for t in g11.report_lines(st)))
        old = self.old()
        pre = self.scene(mark=False)
        self.assertEqual(g11.paths(pre), old.paths(pre), "印がなければ前のまま")
        g["flow_log"].append({"day": st["day"] - 10, "other": "N89", "kind": "交換", "coin": 0})
        g["flows"][str(y)] = {"all": 1, "coin": 0}
        self.assertEqual(g11.paths(st)["c1"], old.paths(st)["c1"], "出し入れがあれば前の数え方")
        self.assertFalse(any("出し入れが 0 回" in t for t in g11.report_lines(st)))
        g["flow_log"][-1]["day"] = st["day"] - era2.YEAR
        self.assertEqual(g11.flows_recent(st), 0, "1 年より前の出し入れは数えない")
        yy = (st["day"] + 1) // era2.YEAR
        g["path"].pop(str(yy), None)
        g11.count_paths(st, {})
        self.assertEqual(g["path"][str(yy)]["c1"], 0)
        self.assertEqual(g["path"][str(yy)]["c2"], len(ans))
        g["path"][str(yy + 1)] = dict(g["path"][str(yy)])
        st["day"] = (yy + 2) * era2.YEAR - 1
        c = g11.path_consult(st, [])
        self.assertEqual((c["why"], c["year"]), ("g11_path_c1", yy + 1), "2 年つづけて 0 なら止めて相談")

    def test_prompt_lines(self):
        """③ お題だけの行: 直しの日 (印のあと) から、決まりの文に「印のかたまりでできること」、節に市の日に来る村・申し出に来なくなった村 (信頼 0)・
        決めないと受けない、気持ちのお題にも 1 行。前は出ない。state は変えない。書かない言葉・【】は出ない"""
        import g11
        import g7
        st = self.scene()
        before = json.dumps(st, ensure_ascii=False, sort_keys=True)
        p = era2.adults(st)[0]
        f, t, fn = g11.facts(st), g11.text(st, p), g11.feel_note(st, p)
        self.assertEqual(json.dumps(st, ensure_ascii=False, sort_keys=True), before, "お題を書いても state は変わらない")
        self.assertIn(g11.GAIN_TEXT, f)
        self.assertIn("市の日に、村の物を運び出さずに", f)
        self.assertIn("年の集まりの答えの market_day か掟で", f)
        self.assertIn("- 市の日を決めると来る村: ", t)
        vis = g11.visitors(st)
        for o in vis:
            self.assertIn(f"[{o['id']}] {o['name']}", t.split("- 市の日を決めると来る村: ")[1].split("\n")[0])
        zero = [o for o in g7._others(st) if o.get("known") is not None and not o.get("gone") and o.get("people", 0) > 0 and o["trust"] <= 0]
        self.assertTrue(zero)
        for o in zero:
            self.assertIn(f"- [{o['id']}] {o['name']}: 村に申し出や、ここで暮らしたい人を何度も受けてもらえなかったので、もう申し出に来ない", t)
        for o in g7._others(st):
            if o["trust"] > 0:
                self.assertNotIn(f"- [{o['id']}] {o['name']}: 村に申し出や", t)
        self.assertIn("を決めない (null) 人が多いと", t)
        self.assertIn("その申し出は受けないことになる", t)
        self.assertIn("市の日をどうするか、家の代表に伝えられる", fn)
        allt = "".join(self.texts(g11, st))
        self.assertEqual(g11.bad_words(allt), [])
        self.assertNotIn("【", allt)
        self.assertNotIn("信頼", allt, "信頼の数・字は出さない")
        pre = self.scene(mark=False)
        q = era2.adults(pre)[0]
        for s_ in (g11.facts(pre), g11.text(pre, q), g11.feel_note(pre, q)):
            self.assertNotIn("市の日を決めると来る村", s_)
            self.assertNotIn("もう申し出に来ない", s_)
            self.assertNotIn(g11.GAIN_TEXT, s_)
        yp = g7.year_prompt(st, p, g7.since(st))
        self.assertIn(g11.GAIN_TEXT, yp)
        self.assertIn('"market_day": null, "coin_rate": null', yp)

    def test_refresh_prompts(self):
        """step.py refresh_prompts (写しのフォルダ。直しの日の年の集まり): g7.g11.fix を書き、季節・気持ちのお題を新しい行で書き直す"""
        import g11
        st = self.scene(mark=False)
        st["hold"] = None
        st["era2"]["g7"]["hold"] = None
        d = tmpdir()
        try:
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")  # 読むだけ (export)
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            r = subprocess.run([sys.executable, str(SOC / "step.py"), "refresh_prompts", "--why", "試しのわけ"], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            new = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(new["era2"]["g7"]["g11"]["fix"], {"day": g11.G11_FIX_FROM, "why": "試しのわけ"})
            self.assertTrue(g11.fixed(new))
            pd = d / "prompts" / f"day{st['day']:03d}"
            ss = list((pd / "season").glob("*.md"))
            self.assertEqual({f.stem for f in ss}, set(era2.answerers(new)))
            for f in ss:
                t = f.read_text(encoding="utf-8")
                self.assertIn(g11.GAIN_TEXT.strip(), t)
                self.assertIn("市の日を決めると来る村", t)
                self.assertIn('"market_day": null, "coin_rate": null', t)
                self.assertNotIn("試しのわけ", t)
            fs = list((pd / "feeling").glob("*.md"))
            self.assertTrue(fs)
            for f in fs:
                self.assertIn("市の日をどうするか、家の代表に伝えられる", f.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(d, ignore_errors=True)


class T_AppSlim(unittest.TestCase):
    """2026-11-05 (docs/society_phase/data_size_plan.md 案 A): step.APP_SLIM_FROM から app_data.json の信頼の表の 0 を外す。
    その日は step.py slim_app の印 (state["app_slim"]) があるときだけ (だから、その日を作った歩のやり直しは前と 1 バイトも同じ)。
    本物の state の写しで、写しのフォルダに export する (本物の data は読むだけ)"""

    def test_gate(self):
        import step
        st = real_state()
        st.pop("app_slim", None)
        D = step.APP_SLIM_FROM
        for day, mark, want in ((D - 30, False, False), (D, False, False), (D, True, True), (D + 30, False, True)):
            x = dict(st, day=day) | ({"app_slim": {"day": D, "why": "試し"}} if mark else {})
            self.assertEqual(step.app_slim(x), want, (day, mark))
        self.assertIn("--why", step._slim_refusal(dict(st, day=D), " "))
        self.assertIn("APP_SLIM_FROM", step._slim_refusal(dict(st, day=D - 30), "試し"))
        self.assertIn("APP_SLIM_FROM", step._slim_refusal(dict(st, day=D + 30), "試し"))

    def test_slim_app(self):
        """印のない APP_SLIM_FROM の日は前の形。slim_app のあとは people[] に trust がなく、resumes[].trust は 0 でないものだけ。ほかは同じ。
        答えがあれば断る。日・お題は変えない"""
        import step
        st = real_state()
        st.pop("app_slim", None)
        st["day"], st["hold"] = step.APP_SLIM_FROM, None
        d = tmpdir()
        try:
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")  # 読むだけ (export)
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
            r = run("export")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            old = json.loads((d / "app_data.json").read_text(encoding="utf-8"))
            self.assertTrue(all("trust" in p for p in old["people"]), "印がなければ前の形")
            self.assertNotEqual(run("slim_app").returncode, 0, "わけがなければ断る")
            r = run("slim_app", "--why", "試しのわけ")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            new_st = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(new_st.pop("app_slim"), {"day": step.APP_SLIM_FROM, "why": "試しのわけ"})
            self.assertEqual(new_st, st, "印のほかは state を変えない")
            self.assertFalse((d / "prompts").exists(), "お題は書かない")
            new = json.loads((d / "app_data.json").read_text(encoding="utf-8"))
            self.assertEqual({k: v for k, v in new.items() if k not in ("people", "resumes")},
                             {k: v for k, v in old.items() if k not in ("people", "resumes")})
            self.assertEqual(new["people"], [{k: v for k, v in p.items() if k != "trust"} for p in old["people"]])
            self.assertEqual(new["resumes"], [r_ | {"trust": {k: v for k, v in r_["trust"].items() if v}} for r_ in old["resumes"]])
            self.assertFalse(any(0 in r_["trust"].values() for r_ in new["resumes"]))
            self.assertEqual(run("slim_app", "--why", "もう一度").returncode, 0, "印がもうあれば何もしない")
            ad = d / "answers" / f"day{st['day']:03d}" / "season"
            ad.mkdir(parents=True, exist_ok=True)
            (ad / "だれか.json").write_text("{}", encoding="utf-8")
            r = run("slim_app", "--why", "答えのあと")
            self.assertEqual(r.returncode, 3)
            self.assertIn("答えがもうある", r.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)

class T_TrustSparse(unittest.TestCase):
    """2026-11-06 (docs/society_phase/state_size_plan.md 案 A): step.py slim_trust が TRUST_SPARSE_FROM の日に state.json の信頼の表から 0 を外し、
    印 state["trust_sparse"] を書く。印があれば、新しい人に 0 を足さない (ない名前 = 0.0)。お題の「仲間への信頼」の行は前と 1 文字も同じ。
    本物の state の写しで (本物の data は読むだけ)"""

    @staticmethod
    def old_line(st, p):  # 前の書き方 (2026-11-06 より前の characters._me)
        return "、".join(f"{n} {v:+.1f}" for n, v in p["trust"].items() if any(q["name"] == n and q["alive"] and not q.get("child") for q in st["people"]))

    def test_me_same(self):
        """印のない state でも、0 を外した state でも、生きている人みなの _me が前の書き方の行をふくみ、外す前と後で 1 文字も同じ"""
        import characters
        import step
        st = real_state()
        if st.pop("trust_sparse", None):  # 本物がもう 0 を外したあと (17639 日目から): 外す前の形 (people の順に自分を除くみな。ない名前は 0.0) にもどしてから
            for p in st["people"]:
                if p.get("trust") is not None:
                    p["trust"] = {**{q["name"]: p["trust"].get(q["name"], 0.0) for q in st["people"] if q is not p}, **p["trust"]}
        alive = [i for i, p in enumerate(st["people"]) if p["alive"]]
        before = {i: characters._me(st, st["people"][i]) for i in alive}
        for i in alive:
            self.assertIn(f"仲間への信頼 (-1〜+1): {self.old_line(st, st['people'][i])}\n", before[i])
        nz = {p["name"]: {k: v for k, v in p["trust"].items() if v} for p in st["people"]}
        n = step.slim_trust(st, "試し")
        self.assertGreater(n, 0)
        self.assertEqual(st["trust_sparse"], {"day": st["day"], "why": "試し"})
        self.assertEqual({p["name"]: p["trust"] for p in st["people"]}, nz, "0 でないものは残る")
        self.assertFalse(any(0 in p["trust"].values() for p in st["people"]))
        for i in alive:
            self.assertEqual(characters._me(st, st["people"][i]), before[i])

    def test_new_person(self):
        """印があれば _new_person は 0 を足さない。印がなければ前のまま (新しい人にみなの 0、みなに新しい人の 0)"""
        import step
        st = real_state()
        st.pop("trust_sparse", None)
        n0 = len(st["people"])
        p = era2._new_person(st, random.Random(1), "女", 20)
        self.assertEqual(list(p["trust"]), [q["name"] for q in st["people"][:n0]])
        self.assertTrue(all(q["trust"][p["name"]] == 0.0 for q in st["people"][:n0]))
        st = real_state()
        st.pop("trust_sparse", None)
        step.slim_trust(st, "試し")
        before = [dict(q["trust"]) for q in st["people"]]
        p = era2._new_person(st, random.Random(1), "女", 20)
        self.assertEqual(p["trust"], {})
        self.assertEqual([q["trust"] for q in st["people"][:n0]], before)

    def test_refusal(self):
        import step
        st = real_state()
        D = step.TRUST_SPARSE_FROM
        self.assertEqual((D + 1) % era2.YEAR, 0, "年の集まりの日")
        self.assertIn("--why", step._trust_refusal(dict(st, day=D), " "))
        self.assertIn("TRUST_SPARSE_FROM", step._trust_refusal(dict(st, day=D - 120), "試し"))
        self.assertIn("TRUST_SPARSE_FROM", step._trust_refusal(dict(st, day=D + 120), "試し"))
        self.assertIn("一時停止", step._trust_refusal(dict(st, day=D, hold=True), "試し"))

    def test_slim_trust(self):
        """slim_trust: わけがなければ断る。印と 0 を外した trust のほかは state を変えない。お題は書かない。
        2 回目は何もしない。答えがあれば断る"""
        import step
        st = real_state()
        st.pop("trust_sparse", None)
        st["day"], st["hold"] = step.TRUST_SPARSE_FROM, None
        d = tmpdir()
        try:
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")  # 読むだけ (export)
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
            ad = d / "answers" / f"day{st['day']:03d}" / "feeling"
            ad.mkdir(parents=True)
            (ad / "だれか.json").write_text("{}", encoding="utf-8")
            r = run("slim_trust", "--why", "答えのあと")
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertIn("答えがもうある", r.stdout)
            shutil.rmtree(d / "answers")
            self.assertEqual(run("slim_trust").returncode, 3, "わけがなければ断る")
            r = run("slim_trust", "--why", "試しのわけ")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            new = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(new.pop("trust_sparse"), {"day": step.TRUST_SPARSE_FROM, "why": "試しのわけ"})
            for p in st["people"]:
                p["trust"] = {k: v for k, v in p["trust"].items() if v}
            self.assertEqual(new, st, "印と 0 を外した trust のほかは state を変えない")
            self.assertFalse((d / "prompts").exists(), "お題は書かない")
            text = (d / "state.json").read_text(encoding="utf-8")
            r = run("slim_trust", "--why", "もう一度")
            self.assertEqual(r.returncode, 0, "印がもうあれば何もしない")
            self.assertEqual((d / "state.json").read_text(encoding="utf-8"), text)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class T_AllyCheck(unittest.TestCase):
    """2026-11-06 (docs/society_phase/G10_c3_diag.md 6. の 1・9.): region.ALLY_CHECK_FROM から、集まりの「助けを頼む」は、ally が設計の条件
    (region.allies_for。決まりの答えと同じ) に合うときだけ通す。合わなければ決まりと同じく払うか戦うか。逃げ場がないのに「逃げる」も同じ。
    集まりのお題には頼める村を書き、逃げ場のない世界では逃げるを出さない。その日より前は前のまま"""

    G = region.ALLY_CHECK_FROM

    def world(self, ally_commit):
        R = {"ties": [], "demands": [], "wars": [], "pending": [], "gone": [], "log": []}
        S = [sett("V0", 150, (5, 5), village=True), sett("N1", 90, (5, 7), org=1), sett("N2", 20, (5, 9)),
             sett("N3", 30, (6, 8), commit=dict(ally_commit))]
        q = {"id": "Q1", "from": "N1", "to": "N2", "what": {"草の種": 100}, "war_day": None}
        R["demands"].append(q)
        return R, S, q

    def ans(self, ally_commit, day, ch="助けを頼む", ally="N3", how="集まり"):
        R, S, q = self.world(ally_commit)
        out = []
        region.answer(R, S, q, ch, ally, day, how, out)
        return R, S, q, out

    def test_rule_and_council_same_condition(self):
        R, S, q = self.world({"N2": 1.0, "N1": 1.0})
        by = region._by(S)
        self.assertEqual(region.allies_for(S, by["N2"], by["N1"]), [], "同じ結びつきでは頼めない")
        self.assertIsNone(region.costs(R, S, by["N2"], by["N1"], 100)[1], "決まりの答えも頼めない")
        R, S, q = self.world({"N2": 1.0, "N1": 0.5})
        by = region._by(S)
        self.assertEqual([c["id"] for c in region.allies_for(S, by["N2"], by["N1"])], ["N3"])
        self.assertEqual(region.costs(R, S, by["N2"], by["N1"], 100)[1], "N3")

    def test_invalid_ally_refused_after_gate(self):
        R, S, q, out = self.ans({"N2": 1.0, "N1": 1.0}, self.G + 1)
        self.assertIn(q["answer"], ("払う", "戦う"), "決まりと同じく払うか戦うか")
        self.assertFalse(any(e["kind"] == "同盟" for e in out), "求めは取り下げられない")
        e = next(e for e in out if e["data"].get("refused") == "助けを頼む")
        self.assertIn("助けに来なかった", e["text"])
        self.assertIn("結びつきが強くない", e["text"])
        self.assertEqual(e["data"]["ally"], "N3")
        self.assertEqual(S[3]["commit"], {"N2": 1.0, "N1": 1.0}, "結びつきは足さない")
        self.assertTrue(q.get("end") or R["wars"], "払うならつながり、戦うなら戦")
        # 求めた村に貢いでいる村 (N2 とも 0 の村) も、地域にない村も
        R, S, q, out = self.ans({"N1": 1.0}, self.G + 1)
        self.assertIn(q["answer"], ("払う", "戦う"))
        R, S, q, out = self.ans({"N2": 1.0}, self.G + 1, ally="N1")
        self.assertIn(q["answer"], ("払う", "戦う"), "求めた村そのものには頼めない")

    def test_invalid_ally_accepted_before_gate(self):
        for day in (self.G, self.G - 120):
            R, S, q, out = self.ans({"N2": 1.0, "N1": 1.0}, day)
            self.assertEqual((q["answer"], q["end"]), ("助けを頼む", day), "前のまま (ただで取り下げる)")
            self.assertTrue(any(e["kind"] == "同盟" for e in out))
            self.assertFalse(any("refused" in e["data"] for e in out))

    def test_valid_ally_after_gate(self):
        R, S, q, out = self.ans({"N2": 1.0, "N1": 0.5}, self.G + 1)
        self.assertEqual((q["answer"], q["end"]), ("助けを頼む", self.G + 1))
        e = next(e for e in out if e["kind"] == "同盟")
        self.assertIn("取り下げた", e["text"])
        self.assertGreater(S[3]["commit"]["N2"], 1.0 - 1e-9)

    def test_rule_how_not_checked(self):
        """決まりで選んだ・村の答えは、前のまま (決まりの手はもともと条件どおり)"""
        R, S, q, out = self.ans({"N2": 1.0, "N1": 1.0}, self.G + 1, how="決まりで選んだ")
        self.assertEqual(q["answer"], "助けを頼む")

    def test_flee_without_refuge(self):
        saved = region.NO_FLEE
        try:
            region.NO_FLEE = True
            R, S, q, out = self.ans({}, self.G + 1, ch="逃げる", ally=None)
            self.assertIn(q["answer"], ("払う", "戦う"))
            self.assertTrue(any("逃げられる空いた土地がなかった" in e["text"] for e in out))
            R, S, q, out = self.ans({}, self.G, ch="逃げる", ally=None)
            self.assertEqual((q["answer"], q["end"]), ("逃げる", self.G), "前のまま")
        finally:
            region.NO_FLEE = saved

    def test_decide_uses_check(self):
        R, S, q = self.world({"N2": 1.0, "N1": 1.0})
        R["pending"] = [{"kind": "求めへの答え", "who": "N2", "demand": "Q1", "rule": "払う", "ally": None}]
        R["councils"] = {"answers": {"N2": {"Q1": "助けを頼む", "ally": "N3"}}}
        out = region.decide(R, S, self.G + 1, out=[])
        self.assertIn(q["answer"], ("払う", "戦う"))
        self.assertEqual(q["how"], "集まり")
        self.assertTrue(any(e["data"].get("refused") for e in out))

    def prompt_state(self, day):
        """G11 に入った日の state (git の G11_ENTRY。N52 が生きている。本物では 18839 日目に N52 がなくなった) の写し"""
        import g7
        st = git_state(G11_ENTRY)
        st["day"] = day
        reg = g7._reg(st)
        oth = {o["id"]: o for o in g7._others(st)}
        oth["N14"]["commit"].update(N13=1.0, N83=1.0)
        oth["N52"]["commit"].update(N13=0.9, N83=0.2)
        reg["demands"].append({"id": "Q9999", "from": "N83", "to": "N13", "what": {"草の種": 560}})
        reg["councils"] = {"day": day, "ask": ["N13"], "points": {"N13": [{"kind": "求められた", "demand": "Q9999"}]}, "answers": {}}
        return g7, st

    def test_prompt(self):
        g7, st = self.prompt_state(self.G - 120)
        old = g7.council_prompt(st, "N13")
        self.assertIn("払う / 戦う / 逃げる (村ごと、遠くの空いた土地へ移る) / 助けを頼む (ほかの村に。頼む村を ally に) のどれか\n", old)
        self.assertNotIn("結びつき", old, "前の日のお題は前のまま")
        self.assertIn('"Q9999": "払う か 戦う か 逃げる か 助けを頼む"', old)
        g7, st = self.prompt_state(self.G)
        self.assertTrue(g7.no_flee(st), "本物の世界は逃げ場がない")
        new = g7.council_prompt(st, "N13")
        line = next(x for x in new.splitlines() if "[Q9999]" in x)
        self.assertNotIn("逃げる (", line)
        self.assertIn("逃げる道はない", line)
        self.assertIn('"Q9999": "払う か 戦う か 助けを頼む"', new)
        setts = g7._setts(st)
        by = region._by(setts)
        ok = [f"{region._name(c)} ({c['id']})" for c in region.allies_for(setts, by["N13"], by["N83"])]
        self.assertIn(f"{region._name(by['N52'])} (N52)", ok)
        self.assertNotIn(f"{region._name(by['N14'])} (N14)", ok)
        self.assertIn("結びつきが強い村だけ: " + "・".join(ok) + " (頼むなら、ally にその番号を書く)", line)
        self.assertNotIn(region._name(by["N14"]), line)
        oth = {o["id"]: o for o in g7._others(st)}
        for o in oth.values():
            o.get("commit", {}).pop("N13", None)
        self.assertIn("助けを頼んでも来てくれる村はない", g7.council_prompt(st, "N13"))


class T_TrustFix(unittest.TestCase):
    """2026-11-06 本人の決め「信頼の決まりも直して 5 年見る」(docs/society_phase/G11_stall_diag.md 7. の 4 と「した直し 2」): era2.TRUST_FIX_FROM (160年の年の集まり)
    の日に始まる歩から (step_day > TRUST_FIX_FROM)。(a) 決める人が足りずに受けなかった申し出・よそから来た人では信頼を下げない (本当に断ったときだけ −0.1)
    (b) 知っている村の信頼は、その年に村と争いがなければ 1 年に TRUST_RECOVER ずつ TRUST_FLOOR までもどる。お題の「もう申し出に来ない」の行は、
    その日は refresh_prompts の印 (g7.g11.trust_fix) のあとだけ新しい文。決まった git の state (OLD。19199 日目・G11・前のコード) の写しで確かめる。本物の data は読まない"""

    OLD = "0cef573f"  # 直しの前のコミット (159年の年報。state は 19199 日目、前のコードで書いたお題がある)
    G = era2.TRUST_FIX_FROM
    _st = None
    _old = {}

    @classmethod
    def base(cls):
        if cls._st is None:
            st = git_state(cls.OLD)
            cls._st = st if st["day"] == cls.G and "g11" in ((st.get("era2") or {}).get("g7") or {}) else False
        if cls._st is False:
            raise unittest.SkipTest("OLD の state が 19199 日目の G11 でない")
        return copy.deepcopy(cls._st)

    @classmethod
    def old(cls, name):
        """直しの前の era2.py・g11.py (git から読む。別の名の模様として。中で呼ぶほかの模様は今のもの)"""
        if name not in cls._old:
            import importlib.util
            r = subprocess.run(["git", "-C", str(ROOT), "show", f"{cls.OLD}:sim/society/{name}.py"], capture_output=True, text=True)
            if r.returncode:
                raise unittest.SkipTest("前のコードが git にない")
            spec = importlib.util.spec_from_loader(f"{name}_old", loader=None)
            m = importlib.util.module_from_spec(spec)
            m.__file__ = str(SOC / f"{name}.py")
            exec(compile(r.stdout, f"{name}_old.py", "exec"), m.__dict__)
            cls._old[name] = m
        return cls._old[name]

    def scene(self, start):
        """start の日に始まる歩の中 (step_day = start + 1)"""
        st = self.base()
        st["era2"]["step_day"] = start + 1
        return st

    @staticmethod
    def js(st):
        return json.dumps(st, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def oth(st, oid):
        return next(o for o in st["era2"]["g6"]["others"] if o["id"] == oid)

    def offer(self, st, votes, lead=None, lead_vote=None, oid="N1", trust=0.3):
        """申し出 1 つを決める (家の物で受ける家はない)。votes: {"村": 人数, False: 人数}。戻り値: その村の信頼"""
        mod = era2
        o = self.oth(st, oid)
        o["trust"] = trust
        names = [p["name"] for p in era2.adults(st)]
        n, i, c = len(names), 0, {"trade": {"T9999": {}}, "trade_by": {"T9999": {}}, "house": {}}
        for side, k in votes.items():
            c["trade"]["T9999"][side] = set(names[i:i + k])
            for x in names[i:i + k]:
                c["trade_by"]["T9999"][x] = side
            i += k
        if lead:
            c["trade_by"]["T9999"][lead] = lead_vote
        off = {"id": "T9999", "other": oid, "kind": "交換", "want": {"草の種": 10 ** 9}, "give": {"ヤギ": 1}}
        mod._g6_decide(st, c, off, o, n, lead)
        return o["trust"], n

    def test_gate_identical(self):
        """この日を作った歩 (19169 日目から) と、その日より前に始まる歩: 申し出・よそから来た人・季節の終わりは、前のコード (OLD の era2.py) と state が 1 バイトも同じ"""
        old = self.old("era2")
        for start in (self.G - 30, self.G - 1, self.G - era2.YEAR):
            self.assertFalse(era2.trust_fixed(self.scene(start)))
            for votes in ({"村": 3}, {"村": 3, False: 2}, {}):
                a, b = self.scene(start), self.scene(start)
                n = len(era2.adults(a))
                for st, mod in ((a, era2), (b, old)):
                    o = self.oth(st, "N1")
                    o["trust"] = 0.3
                    c = {"trade": {"T9999": {k: {p["name"] for p in era2.adults(st)[:v]} for k, v in votes.items()}}, "trade_by": {"T9999": {}}, "house": {}}
                    mod._g6_decide(st, c, {"id": "T9999", "other": "N1", "kind": "交換", "want": {"草の種": 10 ** 9}, "give": {}}, o, n, None)
                    v = {"name": "テス1", "from": "N2", "members": [{"name": "テス1", "sex": "女", "age": 20}], "seed": 1}
                    st["era2"]["visitors"] = [v]
                    acc = {"テス1": [(era2.adults(st)[0]["name"], False)]}
                    if mod is era2:
                        mod._settle_visitors(st, acc, n, "集まり", {"テス1": {era2.adults(st)[0]["name"]}})
                    else:
                        mod._settle_visitors(st, acc, n, "集まり")
                self.assertEqual(self.oth(a, "N1")["trust"], 0.2, "前は、決めないだけでも −0.1")
                self.assertEqual(self.js(a), self.js(b), (start, votes))
            a, b = self.scene(start), self.scene(start)
            a["day"] = b["day"] = start + 30
            era2._g6_season_end(a, 1.0)
            old._g6_season_end(b, 1.0)
            self.assertNotIn("trust_up", a["era2"]["g6"])
            self.assertEqual(self.js(a), self.js(b), start)

    def test_offer_after_gate(self):
        """(a) この日に始まる歩から: 決める人が足りずに受けなかった申し出 (「村」が半分に届かず、「受けない」も半分をこえない) では信頼を下げない。
        大人の半分をこえる「受けない」(年の方針の false も同じ票) か、まとめ役の「受けない」なら、前のとおり −0.1"""
        st = self.scene(self.G)
        self.assertTrue(era2.trust_fixed(st))
        for votes in ({}, {"村": 3}, {"村": 30, False: 20}):
            t, n = self.offer(self.scene(self.G), votes)
            self.assertEqual(t, 0.3, votes)
        st = self.scene(self.G)
        n = len(era2.adults(st))
        t, _ = self.offer(st, {False: n // 2 + 1})
        self.assertEqual(t, 0.2, "本当に断った")
        t, _ = self.offer(self.scene(self.G), {False: n // 2})
        self.assertEqual(t, 0.3, "ちょうど半分は、半分をこえない")
        ad = [p["name"] for p in era2.adults(st)]
        t, _ = self.offer(self.scene(self.G), {}, lead=ad[-1], lead_vote=False)
        self.assertEqual(t, 0.2, "まとめ役が受けないと答えた")
        t, _ = self.offer(self.scene(self.G), {False: n // 2 + 1}, trust=0.0)
        self.assertEqual(t, 0.0, "0 より下にはならない")
        ev = [e for e in st["events"] if e.get("data", {}).get("offer") == "T9999"]
        self.assertTrue(ev and "は受けなかった (" in ev[-1]["text"], "出来事の文は前のまま")

    def test_newcomers_after_gate(self):
        """(a) よそから来た人: 賛成が半分に届かず、はっきり「受け入れない」も半分をこえないなら下げない。半分をこえる「受け入れない」(年の方針の false も) なら −0.1。
        答えの accept の false・「受け入れない」だけを数え、null は数えない (era2._no)"""
        for ok, want in ((False, True), ("受け入れない", True), ("いいえ", True), (None, False), ("わからない", False), (True, False)):
            self.assertEqual(era2._no(ok), want, ok)
        for n_no, want in ((0, 0.3), (2, 0.3), (3, 0.2)):
            st = self.scene(self.G)
            o = self.oth(st, "N2")
            o["trust"] = 0.3
            ad = [p["name"] for p in era2.adults(st)][:5]
            st["era2"]["visitors"] = [{"name": "テス1", "from": "N2", "members": [{"name": "テス1", "sex": "女", "age": 20}, {"name": "テス2", "sex": "男", "age": 22}], "seed": 1}]
            acc = {"テス1": [(x, False) for x in ad[:n_no]]}
            era2._settle_visitors(st, acc, 5, "集まり", {"テス2": set(ad[:n_no])})  # 群れのだれの名前で書いても同じ群れ
            self.assertEqual(o["trust"], want, n_no)
        st = self.scene(self.G)
        o = self.oth(st, "N2")
        o["trust"] = 0.3
        ad = [p["name"] for p in era2.adults(st)][:5]
        st["era2"]["visitors"] = [{"name": "テス1", "from": "N2", "members": [{"name": "テス1", "sex": "女", "age": 20}], "seed": 1}]
        era2._settle_visitors(st, {"テス1": [(x, x != ad[0]) for x in ad[:3]] + [(ad[0], False)]}, 9, "集まり", {"テス1": {ad[0], ad[1], ad[2]}})
        self.assertEqual(o["trust"], 0.3, "賛成と書いた人は、受け入れないに数えない")
        st = self.scene(self.G - 30)
        era2._g6_settled(st, {"from": "N2", "members": []}, False, False)
        self.assertEqual(self.oth(st, "N2")["trust"], max(0.0, round(self.oth(self.base(), "N2")["trust"] - 0.1, 2)), "前の歩は前のまま")

    def test_recover(self):
        """(b) 年が変わって最初の季節の終わりに 1 度、知っている村の信頼が TRUST_RECOVER ずつ TRUST_FLOOR までもどる。上より高い村・知らない村・なくなった村はそのまま。
        その 1 年に村と戦 (起きた日・終わった日)・求め (どちらからでも)・返されないままの貸し借りがあった村はもどらない。0 の村も 4 年で 0.2 (申し出に来る見込みが 0 でなくなる)"""
        st = self.scene(self.G)
        st["day"] = self.G + 30
        oth = {o["id"]: o for o in st["era2"]["g6"]["others"]}
        for k, t in (("N1", 0.0), ("N2", 0.17), ("N4", 0.3), ("N5", 0.0), ("N7", 0.0), ("N8", 0.0), ("N10", 0.0), ("N12", 0.0), ("N86", 0.0)):
            oth[k]["trust"] = t
        self.assertIsNone(oth["N86"]["known"])
        reg = st["era2"]["g7"]["region"]
        reg["wars"].append({"id": "W9999", "att": "N5", "def": "V0", "day": st["day"] - 100, "done": None})
        reg["wars"].append({"id": "W9998", "att": "V0", "def": "N10", "day": st["day"] - 400, "done": st["day"] - 5})
        reg["wars"].append({"id": "W9997", "att": "V0", "def": "N12", "day": st["day"] - 400, "done": st["day"] - 300})  # 前の年の戦は数えない
        reg["demands"].append({"id": "Q9999", "from": "V0", "to": "N7", "what": {"草の種": 1}, "day": st["day"] - 50})
        st["era2"]["g6"]["debts"].append({"id": "D9999", "other": "N8", "lender": "村", "goods": {"草の種": 1}, "day": 0, "due": 1, "status": "返されない", "end": st["day"] - 2})
        era2._trust_recover(st)
        got = {k: oth[k]["trust"] for k in ("N1", "N2", "N4", "N5", "N7", "N8", "N10", "N12", "N86")}
        self.assertEqual(got, {"N1": 0.05, "N2": 0.2, "N4": 0.3, "N5": 0.0, "N7": 0.0, "N8": 0.0, "N10": 0.0, "N12": 0.05, "N86": 0.0})
        self.assertEqual(st["era2"]["g6"]["trust_up"], st["day"] // era2.YEAR)
        st["day"] += 60
        era2._trust_recover(st)
        self.assertEqual(oth["N1"]["trust"], 0.05, "1 年に 1 度だけ")
        for y in range(1, 6):
            st["day"] += era2.YEAR
            era2._trust_recover(st)
        self.assertEqual(oth["N1"]["trust"], era2.TRUST_FLOOR, "上 (0.2) まで、そこで止まる")
        self.assertEqual(oth["N5"]["trust"], era2.TRUST_FLOOR, "争いのない年がつづけば、もどる")
        self.assertEqual(oth["N4"]["trust"], 0.3)
        st2 = self.scene(self.G)
        o = self.oth(st2, "N1")
        o["trust"] = 0.0
        days = []
        for y in range(4):
            st2["day"] = self.G + 30 + y * era2.YEAR
            era2._trust_recover(st2)
            days.append(o["trust"])
        self.assertEqual(days, [0.05, 0.1, 0.15, 0.2])
        p = era2.CONTACT_P["よその村"] * o["trust"] / 0.5
        self.assertAlmostEqual(p, 0.06, msg="4 年で 1 季節に 6% (1 年に約 2 割) の見込みで申し出に来る")

    def test_season_end_after_gate(self):
        """季節の終わり (_g6_season_end) の中で、この日に始まる歩から、1 年に 1 度もどす (乱数は使わない)"""
        st = self.scene(self.G)
        st["day"] = self.G + 30
        before = {o["id"]: o["trust"] for o in st["era2"]["g6"]["others"]}
        era2._g6_season_end(st, 1.0)
        self.assertEqual(st["era2"]["g6"]["trust_up"], st["day"] // era2.YEAR)
        after = {o["id"]: o["trust"] for o in st["era2"]["g6"]["others"]}
        self.assertEqual(after["N1"], 0.05, (before["N1"], after["N1"]))
        self.assertEqual(after["N86"], before["N86"], "知らない村はそのまま")
        n0 = st["next_event"]
        era2._g6_season_end(st, 1.0)
        self.assertEqual(self.oth(st, "N1")["trust"], 0.05, "同じ年の 2 度目の季節の終わりは、もどさない")
        self.assertFalse(any(e["id"] >= n0 and "信頼" in e["text"] for e in st["events"]), "もどすときは出来事を書かない")

    def test_prompt_line(self):
        """お題の行: 19199 日目は印 (g7.g11.trust_fix) がなければ前のコード (OLD の g11.py) と 1 文字も同じ。印のあと (と、その日より後) は、信頼の低い村
        (TRUST_FLOOR より下) に「申し出にはあまり来ない。…また来るようになり、…もっと来る」。書かない言葉・信頼の字は出ない"""
        import g11
        old = self.old("g11")
        st = self.base()
        self.assertNotIn("trust_fix", st["era2"]["g7"]["g11"])
        self.assertFalse(g11.trust_fixed(st))
        for p in era2.adults(st)[:40]:
            self.assertEqual(g11.text(st, p), old.text(st, p))
        self.assertEqual(g11._others_rows(st), old._others_rows(st))
        t0 = "\n".join(g11._others_rows(st))
        self.assertIn("もう申し出に来ない", t0)
        pre = self.base()
        pre["day"] = self.G - era2.YEAR
        g11.mark_trust_fix(pre, "試し")
        self.assertNotIn("trust_fix", pre["era2"]["g7"]["g11"], "その日より前は何もしない")
        g11.mark_trust_fix(st, "試し")
        self.assertEqual(st["era2"]["g7"]["g11"]["trust_fix"], {"day": self.G, "why": "試し"})
        self.assertTrue(g11.trust_fixed(st))
        for o in st["era2"]["g6"]["others"]:
            if o["id"] == "N89":
                o["trust"] = 0.15
        rows = g11._others_rows(st)
        t1 = "\n".join(rows)
        self.assertNotIn("もう申し出に来ない", t1)
        low = [o for o in st["era2"]["g6"]["others"] if o.get("known") is not None and not o.get("gone") and o.get("people", 0) > 0 and o["trust"] < era2.TRUST_FLOOR]
        self.assertIn("N89", [o["id"] for o in low])
        for o in low:
            self.assertIn(f"- [{o['id']}] {o['name']}: 村に申し出や、ここで暮らしたい人を何度も受けてもらえなかったので、申し出にはあまり来ない。"
                          "村と争わない年がつづけば少しずつまた来るようになり、来た申し出を村が受ければもっと来る", t1)
        for o in st["era2"]["g6"]["others"]:
            if o["trust"] >= era2.TRUST_FLOOR:
                self.assertNotIn(f"[{o['id']}] {o['name']}: 村に申し出や", t1)
        self.assertEqual(g11.bad_words(t1), [])
        self.assertNotIn("信頼", t1)
        nxt = self.base()
        nxt["day"] = self.G + era2.YEAR
        self.assertTrue(g11.trust_fixed(nxt), "その日より後は、印がなくても新しい文")

    def test_refresh_prompts(self):
        """step.py refresh_prompts (写しのフォルダ。19199 日目の年の集まり): 止まっている (HOLD consult) あいだは断る (何も変えない)。resume のあとなら
        g7.g11.trust_fix を書き、季節のお題を新しい行で書き直す (g7.g11.fix はもうあるので、そのまま)"""
        import g11
        st = self.base()
        d = tmpdir()
        try:
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")  # 読むだけ (export)
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
            if st.get("hold"):
                r = run("refresh_prompts", "--why", "試しのわけ")
                self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
                self.assertIn("一時停止している", r.stdout)
                r = run("resume")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            r = run("refresh_prompts", "--why", "試しのわけ")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            new = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(new["era2"]["g7"]["g11"]["trust_fix"], {"day": self.G, "why": "試しのわけ"})
            self.assertEqual(new["era2"]["g7"]["g11"]["fix"], st["era2"]["g7"]["g11"]["fix"])
            pd = d / "prompts" / f"day{st['day']:03d}"
            ss = list((pd / "season").glob("*.md"))
            self.assertEqual({f.stem for f in ss}, set(era2.answerers(new)))
            for f in ss:
                t = f.read_text(encoding="utf-8")
                self.assertIn("申し出にはあまり来ない。村と争わない年がつづけば", t)
                self.assertNotIn("もう申し出に来ない", t)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class T_FeelCap(unittest.TestCase):
    """2026-11-07 本人の決め「心持ちだけの役を減らして続ける」(docs/society_phase/token_plan.md): g7.FEEL_CAP_FROM (163年の年の集まり = 19559 日目) から、
    1 回の集まりで答える人は代表と気持ちの人を合わせて g7.FEEL_SEATS 人まで。その日は refresh_prompts の印 (g7.feel_cap) のあとだけ。
    決まった git の state (OLD。19559 日目・HOLD consult・前のコードで書いた気持ちのお題 82 通) と、その前の集まりの state (EARLY。19469 日目の秋の集まり) で確かめる"""

    OLD = "8b121c95"  # 19529 日目からの歩 (state は 19559 日目。年の集まりのお題は前のコード)
    EARLY = "bc4bff13"  # 19439 日目からの歩 (state は 19469 日目。秋の集まり。気持ち 80 人が答えた)
    CODE = "cb9e892c"  # 前のコード (162年の年報)
    G = 19559
    _old = None

    @classmethod
    def old_g7(cls):
        if cls._old is None:
            import importlib.util
            r = subprocess.run(["git", "-C", str(ROOT), "show", f"{cls.CODE}:sim/society/g7.py"], capture_output=True, text=True)
            if r.returncode:
                raise unittest.SkipTest("前のコードが git にない")
            spec = importlib.util.spec_from_loader("g7_old_feel", loader=None)
            m = importlib.util.module_from_spec(spec)
            m.__file__ = str(SOC / "g7.py")
            exec(compile(r.stdout, "g7_old_feel.py", "exec"), m.__dict__)
            cls._old = m
        return cls._old

    def st(self, commit=None):
        st = git_state(commit or self.OLD)
        if commit is None and (st["day"] != self.G or "g7" not in st["era2"]):
            self.skipTest("OLD の state が 19559 日目の G7 からでない")
        return st

    def test_gate_identical(self):
        """印のない 19559 日目と、その前の集まり: 気持ちの人は前のコードと同じ (みな)。印はその日より前には書かない"""
        import g7
        self.assertEqual(g7.FEEL_CAP_FROM, self.G)
        old = self.old_g7()
        for c in (self.OLD, self.EARLY):
            st = self.st(c)
            self.assertFalse(g7.feel_capped(st), c)
            self.assertEqual(era2.feelers(st), old.feelers(st), c)
            self.assertGreater(len(era2.feelers(st)), 70, c)
        early = self.st(self.EARLY)
        js = json.dumps(early, sort_keys=True, ensure_ascii=False)
        g7.mark_feel_cap(early, "試し")
        self.assertEqual(json.dumps(early, sort_keys=True, ensure_ascii=False), js, "その日より前は何もしない")
        st = self.st()
        # 2026-11-12: いまの data の day19559/feeling は、feel-cap の書き直し (f6438c8b) で 53 通になった。くらべるのは、OLD のコミットのときの (前のコードで書いた) お題
        r = subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotePath=false", "ls-tree", "--name-only", f"{self.OLD}:sim/society/data/prompts/day19559/feeling"], capture_output=True, text=True)
        if r.returncode == 0:
            on = [x[:-3] for x in r.stdout.split() if x.endswith(".md")]
            self.assertEqual(sorted(on), sorted(era2.feelers(st)))

    def test_after_gate(self):
        """印のあと (と、その日より後): 気持ちの人は FEEL_SEATS − 答える人 (並びは前のまま)。答えたのがいちばん前の人から。代表はみな答える"""
        import g7
        st = self.st()
        full, names = era2.feelers(st), era2.answerers(st)
        g7.mark_feel_cap(st, "試し")
        self.assertEqual(st["era2"]["g7"]["feel_cap"], {"day": self.G, "why": "試し"})
        self.assertTrue(g7.feel_capped(st))
        self.assertEqual(era2.answerers(st), names, "代表は変えない")
        sub = era2.feelers(st)
        self.assertEqual(len(sub), g7.FEEL_SEATS - len(names))
        self.assertEqual(sub, [n for n in full if n in set(sub)], "並びは前のまま")
        self.assertEqual(sub, era2.feelers(st), "何度呼んでも同じ")
        fd = {p["name"]: p.get("feeling_day") for p in era2.adults(st)}
        key = lambda n: -1 if fd[n] is None else fd[n]
        self.assertLessEqual(max(key(n) for n in sub), min(key(n) for n in full if n not in sub), "答えたのが前の人から")
        nxt = self.st()
        nxt["day"] = self.G + 1
        self.assertTrue(g7.feel_capped(nxt), "その日より後は印がなくても")
        x4 = self.st()
        x4["day"] = self.G + 30
        x4["era2"]["g7"]["exp4"] = {"arm": "B0"}
        self.assertFalse(g7.feel_capped(x4), "実験 4 の写しの村では減らさない")
        few = self.st()
        g7.mark_feel_cap(few, "試し")
        self.assertEqual(g7.feel_pick(few, full[:5], 53), full[:5], "席より少なければみな")
        self.assertEqual(g7.feel_pick(few, full, 0), [])

    def test_rotation(self):
        """答えた人の feeling_day が新しくなると、次の集まりでは、前に選ばれなかった人がみな先に選ばれる (2 回の集まりで全員)。同じ日の人は年で並びが変わる"""
        import g7
        st = self.st()
        full = era2.feelers(st)
        g7.mark_feel_cap(st, "試し")
        a = era2.feelers(st)
        for p in era2.adults(st):
            if p["name"] in a:
                p["feeling_day"] = st["day"]
        st["day"] += 30  # 次の集まり (秋)。見本の家は変えない
        b = era2.feelers(st)
        self.assertEqual(len(b), len(a))
        self.assertTrue(set(full) - set(a) <= set(b), "前に選ばれなかった人が先")
        self.assertEqual(set(a) | set(b), set(full))
        y1 = g7.feel_pick(dict(st, day=self.G), full, 20)
        y2 = g7.feel_pick(dict(st, day=self.G + era2.YEAR), full, 20)
        self.assertNotEqual(set(y1), set(y2), "同じ日の人の並びは年で変わる")

    def test_no_prompt(self):
        """お題のない人: 気持ち・気持ちの日・予定・家は変わらない (答えのない人と同じ)。read_feelings は、お題のない人を「答えがない人」に数えない"""
        import g7
        import io
        import contextlib
        import step
        st = self.st()
        full = era2.feelers(st)
        g7.mark_feel_cap(st, "試し")
        sub = era2.feelers(st)
        off = [n for n in full if n not in sub]
        self.assertTrue(off)
        before = {p["name"]: json.dumps(p, sort_keys=True, ensure_ascii=False) for p in st["people"] if p["name"] in off}
        era2.apply_feelings(st, {n: json.dumps({"feeling": "うれしい", "say": [{"to": "みんな", "text": "やあ"}]}, ensure_ascii=False) for n in sub})
        for n in sub:
            self.assertEqual(next(p for p in st["people"] if p["name"] == n)["feeling"], "うれしい")
        for p in st["people"]:
            if p["name"] in off:
                q = json.loads(before[p["name"]])
                self.assertEqual({k: p.get(k) for k in ("feeling", "feeling_day", "plan", "household", "trust")},
                                 {k: q.get(k) for k in ("feeling", "feeling_day", "plan", "household", "trust")}, p["name"])
        d = tmpdir()
        saved = step.DATA
        try:
            step.DATA = d
            st3 = self.st()
            g7.mark_feel_cap(st3, "試し")
            fa = step.pdir(st3, "feeling", "answers")
            fa.mkdir(parents=True)
            for n in era2.feelers(st3)[:-2]:
                (fa / f"{n}.json").write_text('{"feeling": "x"}', encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                got = step.read_feelings(st3)
            self.assertEqual(set(got), set(era2.feelers(st3)[:-2]))
            self.assertIn("気持ちの答えがない人: " + "、".join(era2.feelers(st3)[-2:]), buf.getvalue())
            self.assertFalse(any(n in buf.getvalue() for n in off), "お題のない人は数えない")
        finally:
            step.DATA = saved
            shutil.rmtree(d, ignore_errors=True)

    def test_refresh_prompts(self):
        """写しのフォルダ (OLD の state と 19559 日目のお題): HOLD のあいだは断る。resume → refresh_prompts で g7.feel_cap を書き、前のコードの気持ちのお題
        (82 通) を消して席の数だけ書く。who の FEEL の行とお題のファイルが同じ。季節・まわりの集落のお題は 1 バイトも同じ"""
        st = self.st()
        d = tmpdir()
        try:
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")  # 読むだけ (export)
            r = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", self.OLD, "sim/society/data/prompts/day19559"], capture_output=True)
            if r.returncode:
                self.skipTest("19559 日目のお題が git にない")
            import tarfile
            import io
            with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
                for m in t.getmembers():
                    m.name = m.name[len("sim/society/data/"):]
                    t.extract(m, d, filter="data")
            pd = d / "prompts" / "day19559"
            old = {f"{k}/{f.name}": f.read_bytes() for k in ("season", "feeling", "council") for f in sorted((pd / k).glob("*.md"))}
            self.assertEqual(len([k for k in old if k.startswith("feeling/")]), len(era2.feelers(st)))
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
            if st.get("hold"):
                r = run("refresh_prompts", "--why", "試しのわけ")
                self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
                r = run("resume")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            r = run("refresh_prompts", "--why", "試しのわけ")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            new = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(new["era2"]["g7"]["feel_cap"], {"day": self.G, "why": "試しのわけ"})
            import g7
            sub = era2.feelers(new)
            self.assertEqual(len(sub), g7.FEEL_SEATS - len(era2.answerers(new)))
            self.assertIn(f"気持ち {len(sub)}", r.stdout)
            got = {f"{k}/{f.name}": f.read_bytes() for k in ("season", "feeling", "council") for f in sorted((pd / k).glob("*.md"))}
            self.assertEqual({k[8:-3] for k in got if k.startswith("feeling/")}, set(sub), "前のお題は消えた")
            for k, v in got.items():
                self.assertEqual(v, old[k], f"{k} は前のコードのお題と同じ")
            w = run("who")
            self.assertEqual(re.search(r"^FEEL (.*)$", w.stdout, re.M).group(1).split(), sub)
            self.assertIn("HOLD none", w.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_workflow_calls(self):
        """ワークフロー: 集まりの歩の読む役は、答えの有無を 1 回の ls で読み (check (気持ち) はない)、models.json は季節を進めるコマンドの頭で書く。
        気持ちの答えのない人は 1 回だけやり直す"""
        node = shutil.which("node")
        if not node:
            self.skipTest("node がない")
        harness = r"""
const fs = require('fs')
const src = fs.readFileSync(process.argv[2], 'utf8').replace(/^export const meta/m, 'const meta')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
;(async () => {
  let day = 5519, n = 0
  const labels = [], cmds = []
  const agent = async (prompt, opts) => {
    labels.push(opts.label)
    if (prompt.includes('step.py who')) return `DAY ${day} season False\nPHASE G7\nHOLD none\nMODE year\nMEET ${(day + 1) % 120 === 0 ? '年' : 'none'}\nNAMES ソル ミナ\nFEEL カイ ルナ\nCOUNCIL \nASKLOG True`
    if (prompt.includes('season_step.sh')) { cmds.push(prompt); day += 30; return `season exit=0\n${day} 日目まで進んだ\ncommitted` }
    if (prompt.includes('mkdir -p')) return 'FEELING:'
    if (prompt.includes('echo CHECKED')) return n++ ? 'CHECKED' : 'MISS_F ルナ\nCHECKED'  // 2026-11-12: 25974fb3 から、読む役はない名前だけを書く (前の ls の一覧は読まない)
    return 'done'
  }
  const fn = new AsyncFunction('args', 'agent', 'parallel', 'log', src)
  const res = await fn({ mode: 'year', years: 1 }, agent, async (fs_) => Promise.all(fs_.map((f) => f())), () => {})
  console.log(JSON.stringify({ res: res.why, labels, cmds }))
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
        self.assertEqual(out["res"], "end")
        lab = out["labels"]
        self.assertFalse([x for x in lab if "models" in x or "check (気持ち)" in x], lab)
        self.assertEqual([x for x in lab if "retry" in x], ["d5519 ルナ (気持ち) retry"], "気持ちのない人だけ 1 回")
        self.assertIn("models.json", out["cmds"][0])
        self.assertTrue(all("models.json" not in c for c in out["cmds"][1:]), "集まらない歩では書かない")


class T_G12(unittest.TestCase):
    """2026-11-10 G12「大きな都と帝国」(docs/society_phase/G12_design.md): G11 を閉じて入る (部は終わらない)・倉の約束 (受ける決まり 1〜5 とわけ・いちばん多い手・
    1 人で決まる・出し入れ・苦しい年に助ける・2 年で切れる・村が破るとすぐ切れる)・倉から助ける (苦しくない村は受けない・上限 1 割・300 日分・減らしたわけ・貸す)・
    刈り手 (刈られていない畑だけ)・帳 (読めない人は休む + わけ・2 家 / 日・そろった年)・c1〜c3・F・進み・道の見張り (名前の行・0 の場面・苦しい村のない年・5 年ごと)・
    わけのない休むが 0・step.py next_part (写し)。G11 の state では何も働かない。
    164年120日目 (19799 日目。G11・HOLD consult・答えなし) の git の state (G12_ENTRY) の写しから、メモリの中で確かめる。本物の data は読むだけ"""

    NOTE = "本人の決め 2026-11-10: お金と市場を 164年120日目で閉じた。c1・c2・c3 は 14 年届かなかった"
    _st = None

    @classmethod
    def real(cls):
        if cls._st is None:
            st = git_state(G12_ENTRY)
            cls._st = st if (st.get("era") in ("G11", "G12") and "g11" in st["era2"]["g7"]) else False
        if cls._st is False:
            raise unittest.SkipTest("G12_ENTRY の state が G11 か G12 でない")
        return copy.deepcopy(cls._st)

    def g11_state(self):
        st = self.real()
        if st["era"] != "G11":
            self.skipTest("G12_ENTRY の state が G11 でない")
        return st

    def g12_state(self):
        import g7
        st = self.real()
        if st["era"] == "G11":
            st["hold"] = False
            st["era2"]["g7"]["hold"] = None
            g7.close_g11(st, self.NOTE)
            g7.enter_next(st)
            st["era_log"][-1]["g11_closed"] = st["day"]
        return st

    def o(self, st, oid):
        import g7
        return next(x for x in g7._others(st) if x["id"] == oid)

    def calm(self, st, oid):
        """oid の村を苦しくない村にする (天気も蓄えも)"""
        o = self.o(st, oid)
        o["bad"] = None
        o["grain"] = max(o["grain"], o["people"] * 200 + 5000)
        return o

    def test_enter_from_g11(self):
        import g11
        import g12
        import g7
        import hints
        import step
        st = self.g11_state()
        self.assertEqual(st["day"], 19799)
        self.assertIn("一時停止している", step._next_part_refusal(st, None, self.NOTE), "止まっている (HOLD consult) と断る")
        st["hold"] = False
        st["era2"]["g7"]["hold"] = None  # step.py resume と同じ
        if not list((REAL / "answers" / f"day{st['day']:03d}").glob("*/*.json")):
            self.assertIsNone(step._next_part_refusal(st, None, self.NOTE))
        n_ev = st["next_event"]
        t11 = st["era2"]["g7"]["g11"]
        reached11, path11 = dict(t11["reached"]), {k: dict(v) for k, v in t11["path"].items()}
        sha0 = hints.cards_sha(st)
        c = g7.close_g11(st, self.NOTE)
        self.assertEqual((c["day"], c["note"], c["made"], c["c"]), (19799, self.NOTE, 0, {"c1": None, "c2": None, "c3": None}))
        self.assertEqual(sum(r["all"] for r in c["flows"].values()), 0)
        self.assertIn("G11 はもう閉じている", step._next_part_refusal(st, None, self.NOTE))
        part0, ps0 = st["era2"]["g7"]["part"], st["era2"]["g7"]["part_start"]
        g7.enter_next(st)
        g = st["era2"]["g7"]
        self.assertEqual((st["era"], st["era_info"]["name"], g["part"], g["part_start"], g["part_start12"]), ("G12", "大きな都と帝国", part0, ps0, 19799),
                         "部は終わらない (第 6 部のまま)")
        self.assertEqual(era2.PART_END["G12"], 6)
        self.assertEqual(g["before"]["G11"]["g11"]["reached"], reached11)
        self.assertEqual(g["before"]["G11"]["g11"]["path"], path11)
        self.assertEqual((g["g11"]["c"], g["g11"]["path"]), ({}, {}), "G11 の条件と道の見張りは数え直す")
        self.assertEqual(g["g11"]["reached"], reached11, "G11 の F は消さない")
        self.assertNotIn("stall", g)
        self.assertIn("stall", g["before"]["G11"])
        self.assertEqual(hints.cards_sha(st), sha0, "札は足さない")
        types = [e["type"] for e in st["events"] if e["id"] >= n_ev]
        self.assertEqual(types, ["フェーズ", "フェーズ"])
        self.assertIn("フェーズ G12 (大きな都と帝国) を始めた", st["events"][-1]["text"])
        ind = era2.indicators(st)
        self.assertEqual((ind["g12_c1_day"], ind["g12_c2_day"], ind["g12_c3_day"]), (None, None, None))
        self.assertFalse(era2.CRITERIA["G12"][1](ind))
        self.assertIn(g12.ACT_CENSUS, g7.acts(st))
        self.assertTrue(g12.key_houses(st))
        for h in g12.key_houses(st):
            self.assertIn(h, g["sample"], "読める人の家は、入る日から答える家")
        self.assertEqual(len(g12.candidates(st)), 17)
        self.assertEqual(g12.cap_left(st)[0], int(g["g12"]["year_store"]["164"] * 0.1))
        txt = g7.facts(st) + g7._field_rows(st, False, True) + g7.fields_json(st, era2.adults(st)[0], False)
        for p in era2.adults(st)[:60]:
            txt += g12.text(st, p) + g12.feel_note(st, p)
        self.assertIn('"pact": [], "help": []', txt)
        self.assertIn("## 倉と約束と帳", txt)
        self.assertEqual(g12.bad_words(txt), [], "都・帝国・国・税・お金・市場・鉄などを書かない")
        self.assertNotIn("【", g12.text(st, era2.adults(st)[0]))
        self.assertEqual(g11.bad_words(g12.facts(st)), [])
        consult = g7.consult_why(st)
        self.assertIsNone(consult, "入る日には止めない")

    def test_g11_unchanged(self):
        """G11 の state (g7.g12 がない) では、新しい仕事・文・欄・目安は何も働かない"""
        import g7
        import g12
        st = self.g11_state()
        self.assertNotIn(g12.ACT_CENSUS, g7.acts(st))
        p = era2.adults(st)[0]
        self.assertNotIn("倉の約束", g7.facts(st) + g7.text(st, p) + g7._field_rows(st, False, True))
        self.assertNotIn('"pact"', g7.fields_json(st, p, False))
        self.assertNotIn("g12_c1_day", era2.indicators(st))
        g7.new_season(st)
        p["plan"] = {"activity": "休む", "place": "camp", "with": []}
        g7.job(st, p, {"activity": g12.ACT_CENSUS})
        self.assertNotIn("rest_why", st["era2"]["g7"], "G11 では、帳をつけるの休みのわけは残さない (仕事の並びにないので前のまま)")
        self.assertEqual(era2.ORDER2[era2.ORDER2.index("G11"):era2.ORDER2.index("G11") + 2], ["G11", "G12"])  # 2026-11-12: G13 を足したので、G11 の次が G12 かを見る

    def test_pact_rules(self):
        """受ける決まり 1〜5 とわけ・いちばん多い手 (1 人でも決まる)・やめる"""
        import g12
        st = self.g12_state()
        g = st["era2"]["g7"]["g12"]
        ans = era2.answerers(st)
        A, B = ans[0], ans[1]
        n13 = self.o(st, "N13")
        cases = [({"to": "N19", "give": {"草の種": 3000}, "take": {"草の種": 100}}, "信じきれていない"),
                 ({"to": "N13", "give": {"草の種": 3000}, "take": {"草の種": n13["people"] * 10 + 1}}, f"{n13['people'] * 10} つかみより多くは出せない"),
                 ({"to": "N13", "give": {"草の種": 3000}, "take": {"刈り手": [9, 20]}}, "刈り手は"),
                 ({"to": "N13", "give": {"草の種": 3000}, "take": {"黒曜石": 3}}, "黒曜石"),
                 ({"to": "N13", "give": {"草の種": 500}, "take": {"草の種": 200}}, "得がない"),
                 ({"to": "N13", "give": {}, "take": {"草の種": 200}}, "give")]
        for row, word in cases:
            n0 = len(g["fails"])
            g12.apply_answers(st, {A: {"pact": [row]}})
            self.assertNotIn(row["to"], g["pacts"], word)
            self.assertEqual(len(g["fails"]), n0 + 1, word)
            self.assertIn(word, g["fails"][-1]["why"])
            self.assertEqual(st["events"][-1]["type"], "倉", "受けなかったわけは出来事「倉」に")
        far = next((o for o in era2._g6(st)["others"] if o.get("days", 0) > 3 and o.get("known") is not None), None)
        if far:
            self.assertIn("遠い", g12.accept_why(st, far, {"give": {"草の種": 3000}, "take": {"草の種": 10}}))
        self.assertIsNone(g12.accept_why(st, n13, {"give": {"草の種": 3000}, "take": {"草の種": 200}}))
        # 1 人で決まる
        g12.apply_answers(st, {A: {"pact": [{"to": "N13", "give": {"草の種": 3000}, "take": {"草の種": 200}}]}, B: {"pact": None}})
        p = g["pacts"]["N13"]
        self.assertEqual((p["status"], p["give"], p["take"], p["by"]), ("続く", {"草の種": 3000}, {"草の種": 200}, [A]))
        self.assertIn("F1", g["reached"])
        self.assertTrue(any(x["type"] == "区切り" or x["type"] == "目盛り" for x in st["events"][-3:]))
        # いちばん多い手 (重みの多いほう)
        w = __import__("g7")._vote_weights(st, {A: {}, B: {}})
        big, small = (A, B) if w[A] >= w[B] else (B, A)
        g12.apply_answers(st, {big: {"pact": [{"to": "N14", "give": {"草の種": 4000}, "take": {"草の種": 300}}]},
                               small: {"pact": [{"to": "N14", "give": {"草の種": 3000}, "take": {"草の種": 200}}]}})
        self.assertEqual(g["pacts"]["N14"]["give"], {"草の種": 4000})
        # やめる
        g12.apply_answers(st, {A: {"pact": [{"to": "N14", "end": True}]}})
        self.assertEqual(g["pacts"]["N14"]["status"], "切れた")
        self.assertEqual(g12.candidates(st)[0]["id"], "N1")

    def test_settle(self):
        """年の終わりの出し入れ: 苦しくない相手は take を出す (c1・F4・信頼 +0.1) / 出せない年が 2 年で切れる / 苦しい相手には村が give を出す / 出せなければすぐ切れる (信頼 −0.2)。
        c1 は 5 つ以上の年が 2 回"""
        import g12
        st = self.g12_state()
        g = st["era2"]["g7"]["g12"]
        A = era2.answerers(st)[0]
        ids = ["N1", "N2", "N4", "N5", "N7", "N10"]
        for oid in ids:
            self.calm(st, oid)
        g12.apply_answers(st, {A: {"pact": [{"to": oid, "give": {"草の種": 3000}, "take": {"草の種": 50}} for oid in ids]}})
        self.assertEqual(sum(1 for p in g["pacts"].values() if g12._active(p)), 6)
        t0 = self.o(st, "N1")["trust"]
        v0 = era2._g6_have(st, "村", "草の種")
        st["day"] = 19919
        g12._settle(st)
        self.assertEqual(g["paid"]["165"], {oid: "出した" for oid in ids})
        self.assertEqual(era2._g6_have(st, "村", "草の種"), v0 + 300)
        self.assertAlmostEqual(self.o(st, "N1")["trust"], round(t0 + 0.1, 2))
        self.assertIn("F4", g["reached"])
        self.assertEqual(g["c1_years"], [165])
        self.assertNotIn("c1", g["c"])
        st["day"] = 20039
        g12._settle(st)
        self.assertIn("c1", g["c"], "5 つ以上の年が 2 回")
        # 出せない年が 2 年で切れる
        n2 = self.o(st, "N2")
        n2["grain"] = n2["people"] * 100
        for d in (20159, 20279):
            st["day"] = d
            g12._settle(st)
        self.assertEqual(g["pacts"]["N2"]["status"], "切れた")
        self.assertIn("2 年つづけて", g["pacts"]["N2"]["why"])
        # 苦しい相手には村が出す
        n4 = self.o(st, "N4")
        n4["bad"] = 20399
        st["day"] = 20399
        n0 = era2._g6_have(st, "村", "草の種")
        g12._settle(st)
        self.assertEqual(g["paid"]["169"]["N4"], "苦しいので村が出した")
        self.assertIn("N4", g["relief"]["169"])
        self.assertIn("F2", g["reached"])
        # 村が出せなければすぐ切れる (上限)
        g["given"]["170"] = 10 ** 9
        st["day"] = 20519
        t5 = self.o(st, "N4")["trust"]
        g12._settle(st)
        self.assertEqual(g["pacts"]["N4"]["status"], "切れた")
        self.assertIn("村が約束を破った", g["pacts"]["N4"]["why"])
        self.assertAlmostEqual(self.o(st, "N4")["trust"], round(max(0, t5 - 0.2), 2))
        self.assertTrue(any("1 割" in f["why"] for f in g["fails"]), "減らしたわけ")

    def test_help_cap_lend(self):
        """苦しくない村は受けない / 苦しい村は受ける (F2・信頼) / 1 割の上限で減らしたわけ / 300 日分 / 貸す (貸し借りの帳簿) / c2 (3 集落・3 万)"""
        import g12
        st = self.g12_state()
        g = st["era2"]["g7"]["g12"]
        A = era2.answerers(st)[0]
        self.calm(st, "N2")
        g12.apply_answers(st, {A: {"help": [{"to": "N2", "草の種": 1000}]}})
        self.assertIn("いまは足りている", g["fails"][-1]["why"])
        self.assertNotIn("F2", g["reached"])
        nd = [o["id"] for o in g12.needy(st)]
        self.assertGreaterEqual(len(nd), 3)
        g6 = era2._g6(st)
        k0 = len(g6["debts"])
        g12.apply_answers(st, {A: {"help": [{"to": nd[0], "草の種": 12000}, {"to": nd[1], "草の種": 9000, "lend": 0.1}]}})
        self.assertIn("F2", g["reached"])
        self.assertEqual(len(g6["debts"]), k0 + 1)
        self.assertEqual((g6["debts"][-1]["other"], g6["debts"][-1]["rate"], g6["debts"][-1]["goods"]), (nd[1], 0.1, {"草の種": 9000}))
        self.assertNotIn("c2", g["c"])
        g12.apply_answers(st, {A: {"help": [{"to": nd[2], "草の種": 9000}]}})
        self.assertIn("c2", g["c"], "3 集落・3 万")
        left, _ = g12.cap_left(st)
        g12.apply_answers(st, {A: {"help": [{"to": nd[3], "草の種": left + 500}]}})
        self.assertIn(f"{left} つかみだけ出した", g["fails"][-1]["why"])
        self.assertEqual(g12.cap_left(st)[0], 0)
        # 300 日分
        st2 = self.g12_state()
        need = era2._need(st2)
        kc = sum(f["kcal"] for f in st2["store"])
        keep = int((kc - 301 * need) // era2.FOOD_KCAL["草の種"])
        era2._g6_take(st2, "村", {"草の種": keep})
        left2, why2 = g12.cap_left(st2)
        self.assertIn("300 日分", why2)
        self.assertLessEqual(left2, need // era2.FOOD_KCAL["草の種"] + 1, "300 日分を切る分は出さない")

    def test_hands(self):
        """刈り手は、実ったまま刈られていない畑だけを刈る (1 人 1 日 150 つかみまで)。村の蓄えから食べる。F4"""
        import g12
        st = self.g12_state()
        g = st["era2"]["g7"]["g12"]
        f = {"id": 99999, "state": "実った", "yield": 1000, "harvested": 900, "seed": 100, "day": 0, "work": 0, "owner": None}
        done = {"id": 99998, "state": "刈った", "yield": 1000, "harvested": 1000, "seed": 100, "day": 0, "work": 0, "owner": None}
        st["era2"]["fields"] = [f, done]
        g["hands_due"] = {"N1": {"n": 2, "left": 20, "days": 20, "day": st["day"], "came": 0}}
        g12.hands_day(st)
        self.assertEqual((f["harvested"], f["state"], done["harvested"]), (1000, "刈った", 1000))
        self.assertEqual(g["hands"][str(st["day"] // era2.YEAR)]["grain"], 100)
        self.assertIn("F4", g["reached"])
        g12.hands_day(st)
        self.assertEqual(g["hands_due"]["N1"]["came"], 1, "刈る畑がない日は来ない")

    def test_census(self):
        """読めない人は休む (わけ) / 読める人は 1 日 2 家 / 倉・約束のあとにそろう / c3 は 2 年 / 進みが上がる / 答えのときも休むのわけ"""
        import g10
        import g12
        import g7
        st = self.g12_state()
        g = st["era2"]["g7"]["g12"]
        rd = g10.readers(st)
        R = next(p for p in era2.adults(st) if p["name"] == rd[0])
        N = next(p for p in era2.adults(st) if p["name"] not in rd)
        t = {}
        st["day"] = 19800
        g12.census_day(st, N, t)
        ev = st["events"][-1]
        self.assertEqual((ev["type"], ev["who"]), ("休む", N["name"]))
        self.assertIn("字を読み書きできない", ev["text"])
        self.assertTrue(any(f["who"] == N["name"] and f["what"] == g12.ACT_CENSUS for f in g["fails"]))
        p0 = g12.progress(st)["c3"]
        g12.census_day(st, R, t)
        row = g["census"]["165"]
        self.assertEqual(len(row["houses"]), 2)
        self.assertIn("F3", g["reached"])
        self.assertGreater(g12.progress(st)["c3"], p0)
        n = len(era2._homes(st))
        for _ in range(n):
            g12.census_day(st, R, t)
        self.assertIsNotNone(row["done"])
        self.assertIsNotNone(row["store"])
        st["day"] = 19919
        g12.season_end(st)
        self.assertNotIn("c3", g["c"])
        st["day"] = 19920
        for _ in range(n):
            g12.census_day(st, R, t)
        st["day"] = 20039
        g12.season_end(st)
        self.assertIn("c3", g["c"])
        # 答えのとき: 読めない人の「帳をつける」は休む + わけ (G10 の直し ② と同じ道)
        g7.new_season(st)
        N["plan"] = {"activity": "休む", "place": "camp", "with": []}
        g7.job(st, N, {"activity": g12.ACT_CENSUS})
        self.assertIn(N["name"], st["era2"]["g7"]["rest_why"])
        N["plan"] = {"activity": g12.ACT_CENSUS, "place": "camp", "with": []}
        g7.job(st, N, {"activity": g12.ACT_CENSUS})
        self.assertEqual(N["plan"]["activity"], "休む")
        # 読める人がいない村でも、わけを残す
        st["era2"]["g7"]["g10"]["readers"] = {}
        self.assertNotIn(g12.ACT_CENSUS, g7.acts(st))
        self.assertIn("いない", g12.rest_why(st, N["name"], g12.ACT_CENSUS))

    def test_paths(self):
        """道の見張り: 名前の行 / 受けてくれそうな村が 0 なら c1 は 0 / 読める人が 0 なら c3 は 0 と報告 / 苦しい村のない年は 2 年 0 に数えない / 2 年 0 で相談 / 5 年ごと"""
        import g10
        import g12
        import g7
        st = self.g12_state()
        g = st["era2"]["g7"]["g12"]
        ans = era2.answerers(st)
        ps, need = g12.paths(st)
        self.assertEqual((len(ps["c1"]), len(ps["c2"]), need), (len(ans), len(ans), True))
        self.assertTrue(ps["c3"])
        for n in ps["c3"]:
            p = next(q for q in era2.adults(st) if q["name"] == n)
            self.assertTrue(any("帳をつけ" in x for x in g12._mine(st, p)), n)
        for n in ans:
            p = next(q for q in era2.adults(st) if q["name"] == n)
            self.assertTrue(any("pact と help" in x for x in g12._mine(st, p)), n)
        for o in g7._others(st):
            o["trust"] = 0.0
            o["bad"] = None
            o["grain"] = o["people"] * 500
        st["era2"]["g7"]["g10"]["readers"] = {}
        ps, need = g12.paths(st)
        self.assertEqual((ps["c1"], ps["c2"], ps["c3"], need), ([], [], [], False))
        self.assertTrue(any("0 人" in x for x in g12.report_lines(st)))
        for y in (165, 166):
            st["day"] = y * era2.YEAR - 1
            g12.count_paths(st, {})
        st["day"] = 166 * era2.YEAR + era2.YEAR - 1
        c = g12.path_consult(st, [])
        self.assertEqual(c["why"], "g12_path_c1")
        done = [c, {"why": "g12_path_c3", "year": c["year"]}]
        self.assertIsNone(g12.path_consult(st, done), "苦しい村のない年は、c2 の 2 年 0 に数えない")
        st["day"] = 20879
        g["c"] = {"c1": 1, "c2": 1, "c3": 1}
        self.assertEqual(g12.path_consult(st, [])["why"], "g12_years_20879")
        st["day"] = 20999
        self.assertIsNone(g12.path_consult(st, []))

    def test_next_part_cli(self):
        """step.py (写しのフォルダ): 止まっていると断る → resume → next_part で G11 → G12。G12 のお題に節と欄。2 回目は断る"""
        import g12
        st = self.g11_state()
        d = tmpdir()
        try:
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
            r = run("next_part", "--closed-by-decision", self.NOTE)
            self.assertEqual(r.returncode, 3, "止まっていると断る")
            r = run("resume")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            r = run("next_part", "--closed-by-decision", self.NOTE)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("* G11 (お金と市場): 3 つの条件はそろわないまま、本人の決めで閉じた (164年120日目 (19799 日目)", r.stdout)
            self.assertIn("* フェーズ G12 (大きな都と帝国) に入った", r.stdout)
            self.assertIn("* G12 の世界", r.stdout)
            new = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual((new["era"], new["day"], new["era2"]["g7"]["closed11"]["note"], new["era_log"][-1]["g11_closed"]), ("G12", 19799, self.NOTE, 19799))
            pd = d / "prompts" / "day19799"
            names = {f.stem for f in (pd / "season").glob("*.md")}
            self.assertEqual(names, set(era2.answerers(new)))
            for f in (pd / "season").glob("*.md"):
                t = f.read_text(encoding="utf-8")
                i = t.index("## 倉と約束と帳")
                j = t.find("\n## ", i + 5)
                self.assertEqual(g12.bad_words(t[i:j if j > 0 else None]), [], f.name)
                self.assertIn('"pact": [], "help": []', t)
            r = run("status")
            self.assertIn("G12 / 条件", r.stdout)
            r = run("next_part", "--closed-by-decision", self.NOTE)
            self.assertEqual(r.returncode, 3, "2 回目は断る")
        finally:
            shutil.rmtree(d, ignore_errors=True)


class T_G12Prompt(unittest.TestCase):
    """2026-11-11 本人の決め「お題を直して 5 年見る」(G12_design.md 12.): g12.G12_PROMPT_FROM (168年120日目 = 20279 日目) から、「## いま」の答えの並びのすぐ前に
    短い節 (g12.prompt_block。その人ができる pact・help・帳と 3 つの進み) を置く。その日は refresh_prompts の印 (g7.g12.prompt_fix) のあとだけ。
    20279 日目 (G12・HOLD consult・答えなし) の git の state (AT) と、そのとき前のコードで書いたお題から、メモリの中で確かめる"""

    AT = "1572f94a"  # 20249 日目からの歩 (state は 20279 日目。年の集まりのお題は前のコード)
    G = 20279
    READER = "ヒセ42"  # 自分が読める代表
    FAMILY = "ムイ25"  # 家の ヒセ35 が読める代表
    PLAIN = "キオ31"  # 家に読める人のいない代表

    def st(self):
        st = git_state(self.AT)
        if st["day"] != self.G or "g12" not in st["era2"]["g7"]:
            self.skipTest("AT の state が 20279 日目の G12 でない")
        return st

    def prompt(self, st, name, season=False):
        import g7
        p = next(q for q in st["people"] if q["name"] == name)
        return era2.season_prompt(st, p, g7.since(st)) if season else g7.year_prompt(st, p, g7.since(st))

    def old_file(self, name):
        r = subprocess.run(["git", "-C", str(ROOT), "show", f"{self.AT}:sim/society/data/prompts/day{self.G}/season/{name}.md"], capture_output=True)
        if r.returncode:
            self.skipTest("前のお題が git にない")
        return r.stdout.decode("utf-8")

    def test_gate_identical(self):
        """印のない 20279 日目: お題は前のコードで書いたものと 1 バイトも同じ (節はない)。印はその日より前には書かない"""
        import g12
        self.assertEqual(g12.G12_PROMPT_FROM, self.G)
        st = self.st()
        self.assertFalse(g12.prompt_fixed(st))
        for n in (self.READER, self.FAMILY, self.PLAIN):
            self.assertIn(n, era2.answerers(st))
            t = self.prompt(st, n)
            self.assertNotIn(g12.BLOCK_HEAD[:8], t)
            self.assertEqual(t, self.old_file(n), n)
        early = self.st()
        early["day"] = self.G - 30
        js = json.dumps(early, sort_keys=True, ensure_ascii=False)
        g12.mark_prompt_fix(early, "試し")
        self.assertEqual(json.dumps(early, sort_keys=True, ensure_ascii=False), js, "その日より前は何もしない")
        self.assertFalse(g12.prompt_fixed(early))
        self.assertEqual(g12.prompt_block(early, early["people"][0]), "")

    def test_block(self):
        """印のあと: 「## いま」の答えの並び (1.) のすぐ前に節。読める人の家の代表には、その家の読める人の名前。pact の例は相手が受ける形。書かない言葉は 0"""
        import g10
        import g12
        st = self.st()
        g12.mark_prompt_fix(st, "試し")
        self.assertEqual(st["era2"]["g7"]["g12"]["prompt_fix"], {"day": self.G, "why": "試し"})
        self.assertTrue(g12.prompt_fixed(st))
        nxt = self.st()
        nxt["day"] = self.G + 30
        self.assertTrue(g12.prompt_fixed(nxt), "その日より後は印がなくても")
        rd = set(g10.readers(st))
        for n, want in ((self.READER, f"- 帳: あなた ({self.READER}) は字を読み書きできる"), (self.FAMILY, "は family に書く"),
                        (self.PLAIN, "- 帳: あなたの家には字を読み書きできる人がいない")):
            t = self.prompt(st, n)
            head = g12.BLOCK_HEAD.replace("あなたが", f"あなた ({n}) が", 1)
            i, k, j = t.index("\n## いま\n"), t.index(head), t.index("\n1. 話したいこと")
            self.assertTrue(i < k < j, n)
            blk = t[k:j]
            self.assertEqual(t.count(head), 1)
            self.assertIn(want, blk, n)
            self.assertEqual(g12.bad_words(blk), [], n)
            for key in ('"pact": [{"to": "', '"help": [{"to": "', "倉の約束の輪:", "倉から地域を養う:", "人と倉の帳:", "しなくてもよい"):
                self.assertIn(key, blk, (n, key))
            self.assertIn("## 倉と約束と帳", t, "長い節も残す")
            self.assertNotIn(f"- あなた ({n}) は字を読み書きできるので、主な仕事を", t, "その人だけの行は短い節へ移した")
            self.assertEqual(len(re.findall(r"^- (倉の約束の輪|倉から地域を養う|人と倉の帳): ", blk, re.M)), 3)
            self.assertNotIn("しなければならない", blk)
            self.assertIn('"take": {"草の種": 100}}] のように書く', t, "欄の説明の例も、受ける形に")
        fam =g12._house_readers(st, self.FAMILY)
        self.assertTrue(fam and set(fam) <= rd)
        self.assertIn(f"あなたの家の {'・'.join(fam)} は", self.prompt(st, self.FAMILY))
        cand = g12.candidates(st)
        self.assertTrue(cand)
        for o in cand:
            self.assertIsNone(g12.accept_why(st, o, g12._pact_example(o)), f"例の約束は、相手が受ける形 ({o['id']})")

    def test_season_prompt(self):
        """秋の集まり・季節の形のお題 (era2.season_prompt) でも、「## いま」の答えの並びのすぐ前に出る (印の前は出ない)"""
        import g12
        st = self.st()
        self.assertNotIn(g12.BLOCK_HEAD[:8], self.prompt(st, self.READER, season=True))
        g12.mark_prompt_fix(st, "試し")
        t = self.prompt(st, self.READER, season=True)
        i, k, j = t.index("\n## いま\n"), t.index(g12.BLOCK_HEAD[:8]), t.index("\n1. 話したいこと")
        self.assertTrue(i < k < j)

    def test_progress(self):
        """進みの行: 届いた条件は「届いた」、帳のそろった年がつづけば数える"""
        import g12
        st = self.st()
        g = st["era2"]["g7"]["g12"]
        g["c"]["c2"] = 20000
        y = g12._y(st)
        for k, d in ((y, 20200), (y - 1, 20100)):
            g["census"][str(k)] = {"houses": [], "people": {}, "store": None, "pacts": None, "days": 3, "by": {}, "done": d}
        ls = g12.progress_lines(st)
        self.assertEqual(ls[1], "- 倉から地域を養う: 届いた (20000 日目)")
        self.assertIn("いま 2 年つづいている", ls[2])


class T_G13(unittest.TestCase):
    """2026-11-12 G13「帝国のあとの農業社会」(水と畑と務め。docs/society_phase/G13_design.md): G12 の部の終わり (HOLD part_end) から next_part で入る・
    粉ひきの手間 (家ごと・水の輪の分は引かない)・水の道 (cap・手入れ・まいた順・悪い年に半分にしない)・水の輪 (札が開く・試す・建てる・回る・止まる・
    知っている人が亡くなっても回る)・約束の働き手 (受ける決まり・刈る / 掘る)・c1〜c3・F・進み・道の見張り・step.py next_part (写し)。G12 の state では何も働かない。
    172年120日目 (20759 日目) の git の state (G13_ENTRY) の写しから、メモリの中で確かめる。本物の data は読むだけ"""

    _st = None

    @classmethod
    def real(cls):
        if cls._st is None:
            st = git_state(G13_ENTRY)
            cls._st = st if (st.get("era") == "G12" and (st["era2"]["g7"].get("hold") or {}).get("why") == "part_end") else False
        if cls._st is False:
            raise unittest.SkipTest("G13_ENTRY の state が G12 の部の終わりでない")
        return copy.deepcopy(cls._st)

    def g13_state(self):
        import g7
        st = self.real()
        g7.close_g12(st)
        g7.enter_next(st)
        return st

    def o(self, st, oid):
        import g7
        return next(x for x in g7._others(st) if x["id"] == oid)

    def test_enter_from_g12(self):
        import g12
        import g13
        import g7
        import hints
        import step
        st = self.real()
        self.assertEqual((st["day"], st["hold"]), (20759, True))
        self.assertIn("本人の決めで閉じて入れるのは", step._next_part_refusal(st, None, "閉じる"), "G12 は本人の決めでは閉じない (部の終わりから入る)")
        if not list((REAL / "answers" / f"day{st['day']:03d}").glob("*/*.json")):
            self.assertIsNone(step._next_part_refusal(st, None, None), "部の終わりで止まっているので入れる")
        n_ev = st["next_event"]
        t12 = st["era2"]["g7"]["g12"]
        reached12, c12 = dict(t12["reached"]), dict(t12["c"])
        sha0 = hints.cards_sha(st)
        c = g7.close_g12(st)
        self.assertEqual((c["day"], c["end"]["why"], c["c"]), (20759, "part_end", c12))
        self.assertEqual(set(c["c"]), {"c1", "c2", "c3"})
        g7.enter_next(st)
        g = st["era2"]["g7"]
        self.assertEqual((st["era"], st["hold"], g["hold"], st["era_info"]["name"], g["part"], g["part_start"], g["part_start13"]),
                         ("G13", False, None, "帝国のあとの農業社会", 7, 20759, 20759))
        self.assertEqual(g["closed12"]["c"], c12)
        self.assertEqual(g["before"]["G12"]["g12"]["reached"], reached12)
        self.assertEqual((g["g12"]["c"], g["g12"]["path"]), ({}, {}), "G12 の条件と道の見張りは数え直す")
        self.assertEqual(g["g12"]["reached"], reached12, "G12 の F は消さない")
        self.assertIn("stall", g["before"]["G12"])
        self.assertNotIn("stall", g)
        self.assertEqual(hints.cards_sha(st), sha0, "札は足さない")
        tc = g["hints"]["tech"][g13.CARD]
        self.assertEqual((tc["open"], g["g13"]["opened"]), (20759, 20759), "水の輪の札は入る日に開く")
        self.assertIn(g13.CARD, hints.open_techs(st))
        types = [e["type"] for e in st["events"] if e["id"] >= n_ev]
        self.assertEqual(types, ["フェーズ", "試す", "水", "フェーズ"])
        self.assertIn("第 7 部「帝国のあとと町」を始めた: フェーズ G13", st["events"][-1]["text"])
        ind = era2.indicators(st)
        self.assertEqual((ind["g13_c1_day"], ind["g13_c2_day"], ind["g13_c3_day"]), (None, None, None))
        self.assertFalse(era2.CRITERIA["G13"][1](ind))
        acts = g7.acts(st)
        self.assertIn(g13.ACT_CANAL, acts)
        self.assertNotIn(g13.ACT_MILL, acts, "水の輪は、できるようになるまで建てられない")
        self.assertIn("試す", acts)
        kn = g13.knowers_alive(st)
        self.assertEqual(kn, ["ヌオ29", "リセ32"])
        for h in g13.key_houses(st):
            self.assertIn(h, g["sample"], "札を知っている人の家は、入る日から答える家")
        for n in kn:
            self.assertIn(n, era2.answerers(st))
        self.assertIsNone(g7.consult_why(st), "入る日には止めない")
        self.assertEqual(g7.PART_YEARS[7], 30)
        txt = g7.facts(st) + g7._field_rows(st, False, True)
        for p in era2.adults(st)[:80]:
            txt += g13.text(st, p) + g13.feel_note(st, p) + g13.prompt_block(st, p)
        self.assertEqual(g13.bad_words(txt), [], "領主・荘園・国・税・帝国・都などを書かない")
        self.assertEqual(g13.bad_words(g13.facts(st)), [])
        self.assertIn("## 水と畑と務め", txt)
        self.assertEqual(g7.facts(st).count("粉ひき: G13 から"), 1)

    def test_g12_unchanged(self):
        """G12 の state (g7.g13 がない) では、新しい仕事・文・前提・働き手・悪い年の守りは何も働かない"""
        import g12
        import g13
        import g7
        import hints
        st = self.real()
        self.assertNotIn(g13.ACT_CANAL, g7.acts(st))
        p = era2.adults(st)[0]
        txt = g7.facts(st) + g7.text(st, p) + g7._field_rows(st, False, True)
        self.assertNotIn("水の道", txt)
        self.assertNotIn("水と畑と務め", g7.year_prompt(st, next(q for q in st["people"] if q["name"] == era2.answerers(st)[0]), g7.since(st)))
        self.assertNotIn("g13_c1_day", era2.indicators(st))
        self.assertFalse(hints.needs_ok(st, hints.cards()[g13.CARD]["needs"]), "G12 では札の前提はそろっていない")
        self.assertEqual(g12._pact_votes(st, {"pact": [{"to": "N1", "give": {"草の種": 3000}, "take": {"働き手": [1, 20]}}]}),
                         {"N1": '{"give": {"草の種": 3000}, "take": {}}'}, "G12 では働き手は読まない (前と同じ。take が空になる)")
        self.assertEqual(g12.take_goods(st), g12.TAKE_GOODS)
        self.assertEqual(era2.ORDER2[-2:], ["G12", "G13"])
        self.assertNotIn("G13", era2.PART_END)
        g7.new_season(st)
        p["plan"] = {"activity": "休む", "place": "camp", "with": []}
        g7.job(st, p, {"activity": g13.ACT_CANAL})
        self.assertNotIn("rest_why", st["era2"]["g7"], "G12 では、水の道の休みのわけは残さない (仕事の並びにないので前のまま)")

    def test_grind(self):
        """粉ひき: 家ごとに、その家の人数 × 0.25 時間を、家の大人の次の日の働く時間 (eve_h) から引く。水の輪がひいた分は引かない。B1G (GRIND_ON False) は引かない"""
        import g13
        st = self.g13_state()
        g = st["era2"]["g7"]["g13"]
        alive = [p for p in st["people"] if p["alive"]]
        for p in alive:
            p.pop("eve_h", None)
        g13.evening(st)
        h = alive[0].get("household")
        n = sum(1 for p in alive if p.get("household") == h)
        ads = [p for p in alive if p.get("household") == h and not p.get("child")]
        if ads:
            self.assertAlmostEqual(ads[0]["eve_h"], round(0.25 * n / len(ads), 2), places=2)
        gr = g["grind"][str(st["day"] // era2.YEAR)]
        self.assertEqual((gr["people"], gr["milled"]), (len(alive), 0))
        self.assertAlmostEqual(gr["hours"], 0.25 * (len(alive) - gr["no_adult"]), delta=2)
        self.assertEqual(g13.grind_people(st), round(len(alive) * 0.25 / 6))
        # 水の輪 1 つ: 250 人分は引かない
        for p in alive:
            p.pop("eve_h", None)
        g["mill"]["mills"].append({"id": "M1", "day": st["day"], "by": [], "houses": [], "stopped": None, "fix": 0})
        g13.evening(st)
        frac = 1 - 250 / len(alive)
        if ads:
            self.assertAlmostEqual(ads[0]["eve_h"], round(0.25 * n * frac / len(ads), 2), places=2)
        self.assertIn("F3", g["reached"])
        self.assertEqual(g["mill"]["year"][str(st["day"] // era2.YEAR)]["days"], 1)
        try:
            g13.GRIND_ON = False
            for p in alive:
                p.pop("eve_h", None)
            g13.evening(st)
            self.assertFalse(any("eve_h" in p for p in alive))
        finally:
            g13.GRIND_ON = True

    def test_canal_water(self):
        """水の道: 1 人日で 60 つかみ分・F1 / 秋の終わりに、この秋にまいた畑をまいた順に cap まで (割合) / c2 は半分以上が 2 年 / 手入れが足りなければ 2 割へる (わけ) /
        悪い年は水の来る分だけ半分にしない (守った量を数える)"""
        import g13
        import g7
        st = self.g13_state()
        g = st["era2"]["g7"]["g13"]
        p = era2.adults(st)[0]
        st["day"] = 20760
        g13.work_day(st, p, {}, g13.ACT_CANAL)
        self.assertEqual((g["canal"]["cap"], g["canal"]["dug"]["173"]), (60, 1))
        self.assertIn("F1", g["reached"])
        self.assertEqual(st["events"][-1]["type"], g13.ACT_CANAL)
        g["canal"]["cap"] = 150
        Y = era2.YEAR
        aut = 173 * Y + 30
        fs = [{"id": 900001, "day": aut, "seed": 100, "work": 0.0, "state": "育つ", "by": p["name"], "harvested": 0, "owner": None},
              {"id": 900002, "day": aut, "seed": 100, "work": 0.0, "state": "育つ", "by": p["name"], "harvested": 0, "owner": None},
              {"id": 900003, "day": aut, "seed": 100, "work": 0.0, "state": "育つ", "by": p["name"], "harvested": 0, "owner": None}]
        st["era2"]["fields"] = [f for f in st["era2"]["fields"] if f["state"] != "育つ"] + fs
        st["day"] = 173 * Y + 59
        g13.season_end(st)
        self.assertEqual([f.get("water") for f in fs], [1.0, 0.5, None])
        self.assertEqual(g["water"]["173"], {"sown": 300, "water": 150, "cap": 150})
        self.assertEqual(g["c2_years"], [173])
        self.assertNotIn("c2", g["c"])
        g["c2_years"].append(174)
        g["water"]["174"] = {"sown": 0, "water": 0, "cap": 150}
        st["day"] = 174 * Y + 59
        for f in fs:
            f["day"] = 174 * Y + 30
        g13.season_end(st)
        self.assertIn("c2", g["c"], "2 年つづく")
        self.assertAlmostEqual(g13.bad_factor({"water": 1.0}), 1.0)
        self.assertAlmostEqual(g13.bad_factor({"water": 0.5}), 0.5 + 0.5 * g7.FIELD_BAD)
        f = {"yield": 1000, "water": 1.0}
        st["day"] = 174 * Y + Y - 1
        g13.protected(st, f)
        self.assertEqual(g["protected"]["175"], 1000 - int(1000 * g7.FIELD_BAD))
        # 手入れ: cap 6000 (100 人日分) に、この年 5 人日 (要るのは 10) → 2 割へる
        g["canal"]["cap"] = 6000
        g["canal"]["dug"]["174"] = 5
        n0 = len(g["fails"])
        g13._year_end(st)
        self.assertEqual(g["canal"]["cap"], 4800)
        self.assertEqual(len(g["fails"]), n0 + 1)
        self.assertIn("泥でうまって", g["fails"][-1]["why"])
        self.assertEqual(st["events"][-1]["type"] if st["events"][-1]["type"] != "目盛り" else "水", "水")

    def test_field_season_bad(self):
        """era2._field_season: 村の悪い年に、水の来る畑は半分にしない (水の来ない畑は今のまま)"""
        import g7
        st = self.g13_state()
        Y = era2.YEAR
        d0 = 173 * Y + 30
        st["era2"]["fields"] = [{"id": 1, "day": d0, "seed": 1000, "work": 1000.0, "state": "育つ", "by": "x", "harvested": 0, "owner": None, "water": 1.0},
                                {"id": 2, "day": d0, "seed": 1000, "work": 1000.0, "state": "育つ", "by": "x", "harvested": 0, "owner": None}]
        st["day"] = 174 * Y - 1
        orig = g7.weather_day
        try:
            g7.weather_day = lambda s: True
            era2._field_season(st, None)
        finally:
            g7.weather_day = orig
        a, b = st["era2"]["fields"]
        self.assertEqual((a["state"], b["state"]), ("実った", "実った"))
        self.assertAlmostEqual(b["yield"] / a["yield"], g7.FIELD_BAD, delta=0.01)
        self.assertGreater(st["era2"]["g7"]["g13"]["protected"]["174"], 0)

    def test_mill(self):
        """水の輪: できる前は「建てる」で休む + わけ / 試す (F2) / できたら 80 人日で 1 つ (知っている人は 1.5 倍) / c1 (90 日・半分) / 直さないと止まる (わけ) /
        10 人日で動き直す / 知っている人がみな亡くなっても回りつづける"""
        import g13
        import g7
        import hints
        st = self.g13_state()
        g = st["era2"]["g7"]["g13"]
        kn = next(p for p in era2.adults(st) if p["name"] == "リセ32")
        other = next(p for p in era2.adults(st) if not g13.knower(st, p["name"]))
        t = {}
        g13.work_day(st, other, t, g13.ACT_MILL)
        self.assertEqual(st["events"][-1]["type"], "休む")
        self.assertIn("まだ水の輪を建てられない", st["events"][-1]["text"])
        self.assertEqual(g["fails"][-1]["what"], g13.ACT_MILL)
        # 試す (hints の決まりのまま)
        st["era2"]["g7"]["jobs7"] = {kn["name"]: {"try": g13.CARD}}
        kn["today"] = {"activity": "試す", "work_h": 6}
        st["day"] = 20760
        hints.try_day(st, kn, kn["today"])
        g13.season_end(st)
        self.assertEqual(g["reached"].get("F2"), 20760)
        # できた: 建てる
        g7._g(st)["hints"]["tech"][g13.CARD]["done"] = 20800
        self.assertTrue(g13.can_do(st, g13.ACT_MILL))
        self.assertIn(g13.ACT_MILL, g7.acts(st))
        for _ in range(53):
            g13.work_day(st, kn, t, g13.ACT_MILL)
        self.assertEqual(len(g["mill"]["mills"]), 0)
        g13.work_day(st, kn, t, g13.ACT_MILL)
        self.assertEqual(len(g["mill"]["mills"]), 1, "知っている人は 1.5 倍 (54 日で 81 人日分)")
        self.assertEqual(g["mill"]["mills"][0]["by"], [kn["name"]])
        # c1: 1 年に 90 日以上・半分以上
        Y = era2.YEAR
        for d in range(174 * Y, 174 * Y + 95):
            st["day"] = d
            g13.evening(st)
        st["day"] = 174 * Y + Y - 1
        g13._year_end(st)
        pop = len([q for q in st["people"] if q["alive"]])
        if 250 / pop >= 0.5:
            self.assertIn("c1", g["c"])
        # 直す人日がない年 (輪は 174年に建てた扱いで 175年に直さない) → 止まる
        g["mill"]["mills"][0]["day"] = 174 * Y
        st["day"] = 175 * Y + Y - 1
        g13._year_end(st)
        self.assertIsNotNone(g["mill"]["mills"][0]["stopped"])
        self.assertIn("止まった", g["fails"][-1]["why"])
        self.assertEqual(g13.mills_running(st), [])
        st["day"] = 176 * Y
        for _ in range(7):
            g13.work_day(st, kn, t, g13.ACT_MILL)
        self.assertIsNone(g["mill"]["mills"][0]["stopped"], "10 人日で動き直す")
        # 知っている人がみな亡くなる → 札は「できない」にもどるが、建った輪は回る・直せる
        for p in st["people"]:
            p["skills"].pop(f"試す:{g13.CARD}", None)
        g7._g(st)["hints"]["tech"][g13.CARD]["done"] = None
        self.assertFalse(g13.mill_ready(st))
        self.assertTrue(g13.can_do(st, g13.ACT_MILL), "建った輪は直せる")
        self.assertEqual(len(g13.mills_running(st)), 1)

    def test_workers(self):
        """約束の働き手: take に書ける (2 割 × 20 日まで。こえると受けないわけ) / 年の終わりに出す → 次の年に来る / 実った畑があれば刈り、なければ水の道を掘る (F4・F1) / c3"""
        import g12
        import g13
        st = self.g13_state()
        g, s12 = st["era2"]["g7"]["g13"], st["era2"]["g7"]["g12"]
        A = era2.answerers(st)[0]
        ex = g13.worker_example(st)
        self.assertIsNotNone(ex)
        self.assertIn(g12.WORKERS, ex["take"])
        o = self.o(st, ex["to"])
        self.assertIsNone(g12.accept_why(st, o, {"give": ex["give"], "take": ex["take"]}), "例の約束は受ける形")
        bad = dict(ex, take=dict(ex["take"], **{g12.WORKERS: [50, 20]}))
        n0 = len(s12["fails"])
        g12.apply_answers(st, {A: {"pact": [bad]}})
        self.assertIn("働き手は", s12["fails"][-1]["why"])
        self.assertEqual(len(s12["fails"]), n0 + 1)
        g12.apply_answers(st, {A: {"pact": [ex]}})
        p = s12["pacts"][ex["to"]]
        self.assertEqual(p["take"][g12.WORKERS], ex["take"][g12.WORKERS])
        o["bad"] = None
        o["grain"] = max(o["grain"], o["people"] * 300 + 5000)
        o["obsidian"] = max(o.get("obsidian", 0), 100)
        Y = era2.YEAR
        st["day"] = 173 * Y + Y - 1
        g12._settle(st)
        self.assertEqual(s12["paid"]["173"][ex["to"]], "出した")
        wd = s12["workers_due"][ex["to"]]
        self.assertEqual((wd["n"], wd["left"]), tuple(ex["take"][g12.WORKERS]))
        # 次の年: 実った畑があれば刈る
        st["day"] = 174 * Y
        f = {"id": 99999, "state": "実った", "yield": 1000, "harvested": 900, "seed": 100, "day": 0, "work": 0, "owner": None}
        st["era2"]["fields"] = [f]
        g12.hands_day(st)
        self.assertEqual(f["harvested"], 1000)
        self.assertIn("F4", g["reached"])
        self.assertEqual(g["workers"]["174"]["reap"], wd["n"])
        cap0 = g["canal"]["cap"]
        g12.hands_day(st)
        self.assertEqual(g["canal"]["cap"], cap0 + wd["n"] * g13.CANAL_PER_DAY, "刈る畑がない日は水の道を掘る")
        self.assertEqual(g["workers"]["174"]["dig"], wd["n"])
        self.assertIn("F1", g["reached"])
        self.assertEqual(st["events"][-1]["type"], "水")
        # 夏の終わりに刈り手は帰るが、働き手は残る
        st["day"] = 174 * Y + 29
        g12.season_end(st)
        self.assertIn(ex["to"], s12["workers_due"])
        # c3: 地域の集落の半分以上が出した年が 2 回 (G13 に入ってからの年だけ)
        tot = len(g13.settlements(st))
        s12["paid"]["172"] = {f"N{i}": "出した" for i in range(tot)}
        s12["paid"]["174"] = {f"N{i}": "出した" for i in range((tot + 1) // 2)}
        s12["paid"]["175"] = {f"N{i}": "出した" for i in range((tot + 1) // 2)}
        g["c3_years"] = []
        for y in (172, 174, 175):
            st["day"] = y * Y + Y - 1
            g13._year_end(st)
        self.assertEqual(g["c3_years"], [174, 175], "入った年 (172年) は数えない")
        self.assertIn("c3", g["c"])

    def test_paths_report(self):
        """道の見張り: c1 は札を知っている人とその家の代表 (知っている人 0 なら 0 と報告) / c2 は答える人みな / c3 は約束か候補があれば答える人みな /
        2 年 0 で相談 / 5 年ごと / 選んだ人の数"""
        import g12
        import g13
        import g7
        st = self.g13_state()
        g = st["era2"]["g7"]["g13"]
        ans = era2.answerers(st)
        ps = g13.paths(st)
        self.assertEqual(len(ps["c2"]), len(ans))
        self.assertEqual(len(ps["c3"]), len(ans))
        self.assertTrue({"ヌオ29", "リセ32"} & set(ps["c1"]))
        for n in ps["c1"]:
            self.assertTrue(g13.house_knowers(st, n), n)
        real = {ans[0]: {"job": {"activity": g13.ACT_CANAL}}, ans[1]: {"pact": [{"to": "N1", "take": {"働き手": [1, 20]}}]}, ans[2]: {"job": {"activity": "採集"}}}
        g13.count_paths(st, real)
        row = g["path"]["173"]
        self.assertEqual((row["meetings"], row["chose"], row["c2"]), (1, 2, len(ans)))
        # 知っている人 0
        st["era2"]["g7"]["hints"]["knowers"][g13.CARD] = []
        self.assertEqual(g13.paths(st)["c1"], [])
        self.assertTrue(any("0 人" in x for x in g13.report_lines(st)))
        # 約束も候補もない → c3 は 0
        for oid, p in st["era2"]["g7"]["g12"]["pacts"].items():
            p["status"] = "切れた"
        for o in g7._others(st):
            o["trust"] = 0.0
        self.assertEqual(g13.paths(st)["c3"], [])
        Y = era2.YEAR
        for y in (174, 175):
            st["day"] = y * Y - 1
            g13.count_paths(st, {})
        st["day"] = 175 * Y + Y - 1
        c = g13.path_consult(st, [])
        self.assertEqual(c["why"], "g13_path_c1")
        c2 = g13.path_consult(st, [c])
        self.assertEqual(c2["why"], "g13_path_c3")
        self.assertIsNone(g13.path_consult(st, [c, c2]))
        st["day"] = 20759 + 5 * Y
        g["c"] = {"c1": 1, "c2": 1, "c3": 1}
        self.assertEqual(g13.path_consult(st, [])["why"], f"g13_years_{20759 + 5 * Y}")
        self.assertEqual(g7.consult_why(st)["why"], f"g13_years_{20759 + 5 * Y}")
        # 3 年だれも選ばない
        for y in (178, 179, 180):
            g["path"][str(y)] = {"meetings": 1, "c1": 1, "c2": 5, "c3": 5, "chose": 0, "failed": 0, "who": {}}
        st["day"] = 180 * Y - 1
        self.assertTrue(any("だれも選ばなかった" in x for x in g13.report_lines(st)))

    def test_progress_stall(self):
        """進み: c1 は札が開いた・F2・できる・F3 の段 / c2・c3 は数。yardstick._stall は G13 の条件で数える"""
        import g13
        import g7
        import yardstick
        st = self.g13_state()
        g = st["era2"]["g7"]["g13"]
        p0 = g13.progress(st)
        self.assertEqual(p0["c1"] // 1000, 1)
        g7._g(st)["hints"]["tech"][g13.CARD]["done"] = 20800
        self.assertEqual(g13.progress(st)["c1"] // 1000, 3)
        st["day"] = 173 * era2.YEAR + era2.YEAR - 1
        yardstick._stall(st, None)
        self.assertEqual(set(st["era2"]["g7"]["stall"]), {"c1", "c2", "c3"})

    def test_next_part_cli(self):
        """step.py (写しのフォルダ): --closed-by-decision は断る → resume は進めない → next_part で G12 → G13。お題に短い節と長い節。status に G13 の行。2 回目は断る"""
        import g13
        st = self.real()
        d = tmpdir()
        try:
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            (d / "archive").symlink_to(REAL / "archive")
            env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
            run = lambda *a: subprocess.run([sys.executable, str(SOC / "step.py"), *a], env=env, capture_output=True, text=True)
            r = run("next_part", "--closed-by-decision", "閉じる")
            self.assertEqual(r.returncode, 3, "G12 は本人の決めでは閉じない")
            r = run("resume")
            self.assertIn("resume では進めない", r.stdout)
            r = run("next_part")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("* G12 (大きな都と帝国): 3 つの条件がそろって終わった (第 6 部の終わり。172年120日目 (20759 日目)", r.stdout)
            self.assertIn("* フェーズ G13 (帝国のあとの農業社会) に入った", r.stdout)
            self.assertIn("* G13 の世界", r.stdout)
            self.assertIn("を開いた・知っている大人 ヌオ29・リセ32", r.stdout)
            new = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertEqual((new["era"], new["day"], new["hold"], new["era2"]["g7"]["part"]), ("G13", 20759, False, 7))
            pd = d / "prompts" / "day20759"
            names = {f.stem for f in (pd / "season").glob("*.md")}
            self.assertEqual(names, set(era2.answerers(new)))
            self.assertTrue({"ヌオ29", "リセ32"} <= names)
            for f in (pd / "season").glob("*.md"):
                t = f.read_text(encoding="utf-8")
                head = g13.BLOCK_HEAD.replace("あなたが", f"あなた ({f.stem}) が", 1)
                i, k, j = t.index("\n## いま\n"), t.index(head), t.index("\n1. ", t.index(head))
                self.assertTrue(i < k < j, f.name)
                self.assertEqual(g13.bad_words(t[k:j]), [], f.name)
                self.assertIn("## 水と畑と務め", t)
            t = (pd / "season" / "リセ32.md").read_text(encoding="utf-8")
            self.assertIn("- 水の輪: あなたは「川の力で粉をひく輪」の話を知っている", t)
            r = run("status")
            self.assertIn("G13 / 条件", r.stdout)
            self.assertIn("G12 / 条件", r.stdout)
            r = run("next_part")
            self.assertEqual(r.returncode, 3, "2 回目は断る")
        finally:
            shutil.rmtree(d, ignore_errors=True)


class T_G13Prompt(unittest.TestCase):
    """2026-11-12 G13 のお題 (G13_design.md 5.・4. の確かめ): 短い節が「## いま」の答えの並び (1.) のすぐ前 (年の集まり・季節の形のお題) /
    知っている人とその家の代表に名前の行 / ほかの人に with の行 / G12 の短い節は 3 行にまとめる / 例の働き手の約束は相手が受ける形 / 1 通 +2.5 KB まで / 書かない言葉 0"""

    def st(self):
        import g7
        st = T_G13.real()
        g7.close_g12(st)
        g7.enter_next(st)
        return st

    def prompt(self, st, name, season=False):
        import g7
        p = next(q for q in st["people"] if q["name"] == name)
        return era2.season_prompt(st, p, g7.since(st)) if season else g7.year_prompt(st, p, g7.since(st))

    def test_block(self):
        import g12
        import g13
        st = self.st()
        ans = era2.answerers(st)
        plain = next(n for n in ans if not g13.house_knowers(st, n))
        for n, want in (("リセ32", "- 水の輪: あなたは「川の力で粉をひく輪」の話を知っている"), ("ヌオ29", "(ほかに知っている人: リセ32)"),
                        (plain, "あなたも、その人と同じ季節に「試す」(try に \"H12-01\") をして with にその人の名前を書けば")):
            for season in (False, True):
                t = self.prompt(st, n, season)
                head = g13.BLOCK_HEAD.replace("あなたが", f"あなた ({n}) が", 1)
                i, k, j = t.index("\n## いま\n"), t.index(head), t.index("\n1. 話したいこと")
                self.assertTrue(i < k < j, (n, season))
                blk = t[k:j]
                self.assertEqual(t.count(head), 1)
                self.assertIn(want, blk, n)
                self.assertNotIn(g12.BLOCK_HEAD, t, "G12 の見出しは 1 つにまとめた")
                for key in ("- 水の道: 主な仕事を「水の道を掘る」にできる", "- 約束の働き手:", "- 倉の約束 (pact): 続いている", "- 倉から助ける (help):", "- 帳:",
                            "いまの進み (水と畑と務め):", "- 水の輪: 札が開いた", "- 水の来る畑:", "- 約束の分:", "しなくてもよい"):
                    self.assertIn(key, blk, (n, key))
                self.assertEqual(g13.bad_words(blk), [], n)
                self.assertNotIn("しなければならない", blk)
                self.assertIn("## 水と畑と務め", t)
                self.assertIn("## 倉と約束と帳", t, "G12 の長い節も残す")

    def test_size(self):
        """1 通の大きさ: G12 のまま (入る前) とくらべて、平均 +2.5 KB まで (問い 11)"""
        import g7
        st0 = T_G13.real()
        st = self.st()
        ds = []
        for n in era2.answerers(st0):
            if n not in era2.answerers(st):
                continue
            ds.append(len(self.prompt(st, n).encode()) - len(self.prompt(st0, n).encode()))
        self.assertTrue(ds)
        self.assertLessEqual(sum(ds) / len(ds), 2500, ds)

    def test_examples_accepted(self):
        """例の働き手の約束は相手が受ける形 / 欄の説明に働き手と水の仕事"""
        import g12
        import g13
        import g7
        st = self.st()
        ex = g13.worker_example(st)
        o = next(x for x in g7._others(st) if x["id"] == ex["to"])
        self.assertIsNone(g12.accept_why(st, o, {"give": ex["give"], "take": ex["take"]}))
        rows = g7._field_rows(st, False, True)
        self.assertIn('"働き手": [人, 日]', rows)
        self.assertIn("水の道を掘る", rows)
        self.assertIn('try に "H12-01"', rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
