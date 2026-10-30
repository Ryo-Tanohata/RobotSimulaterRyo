"""論文 2・実験 3 (exp3.py・step.py exp3) の試し。本物の data にはさわらない (state はメモリの中か /tmp の写し)

  PYTHONUTF8=1 python3.13 sim/society/tools/test_exp3.py

- 組なし・A0: お題は 1 字も変わらない (本物の今のお題のファイルとも同じ)
- A1・A2・A3: 節の数と場所・strip で今のお題に戻る・禁じた言葉がない・数が state から数えたものと同じ
- 断る: 本物の村・知らない組・組の入れかえ・season でない段階。同じ組は何も変えない
- step.py exp3: 写し (/tmp) で組を残し、今の歩のお題を書き直す。A0 のお題は本物のお題と同じ。本物の村では断って何も変えない
- 実験 3 の数え方 (exp3_measure): 裁きの文の読み方・お題からの読み方
"""
import copy
import json
import os
import re
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
import exp3_measure as M  # noqa: E402
import g7  # noqa: E402

REAL = SOC / "data"
_S = {}


def real():
    if "s" not in _S:
        _S["s"] = json.loads((REAL / "state.json").read_text(encoding="utf-8"))
    return copy.deepcopy(_S["s"])


def old_state():
    """本物の 12599 日目 (G9 に入ったところ。実験 3 のはじめの state)。浅いクローンでコミットがなければ None"""
    if "o" not in _S:
        r = subprocess.run(["git", "-C", str(SOC.parent.parent), "show", "726c5340:sim/society/data/state.json"], capture_output=True)
        _S["o"] = json.loads(r.stdout) if r.returncode == 0 else None
    return copy.deepcopy(_S["o"]) if _S["o"] else None


def prompts(state):
    first = g7.since(state)
    out = {}
    for n in era2.answerers(state):
        p = next(q for q in state["people"] if q["name"] == n)
        t = g7.year_prompt(state, p, first) if state["era2"]["g7"].get("ask") == "年" else era2.season_prompt(state, p, first)
        out[n] = (p, t)
    return out


def states():
    out = [("今", real())]
    o = old_state()
    if o:
        out.append(("12599", o))
    return out


class A_Off(unittest.TestCase):
    def test_no_flag_same(self):
        for lab, s in states():
            for n, (p, t) in prompts(s).items():
                self.assertEqual(exp3.apply(s, p, t), t, f"{lab} {n}")

    def test_a0_same(self):
        for lab, s in states():
            exp3.set_arm(s, "A0", "試し")
            for n, (p, t) in prompts(s).items():
                self.assertEqual(exp3.apply(s, p, t), t, f"{lab} {n}")

    def test_real_prompt_files_same(self):
        """本物の今のお題 (コミットしたファイル) = 今のコード (組なし) で作り直したお題"""
        s = real()
        d = REAL / "prompts" / f"day{s['day']:03d}" / "season"
        ps = prompts(s)
        self.assertTrue(ps)
        for n, (p, t) in ps.items():
            f = d / f"{n}.md"
            if f.exists():
                self.assertEqual(exp3.apply(s, p, t), f.read_text(encoding="utf-8"), n)


class B_On(unittest.TestCase):
    def test_sections(self):
        for lab, s0 in states():
            for arm in ("A1", "A2", "A3"):
                s = copy.deepcopy(s0)
                exp3.set_arm(s, arm, "試し")
                for n, (p, t) in prompts(s).items():
                    x = exp3.apply(s, p, t)
                    self.assertEqual(exp3.strip(x), t, f"{lab} {arm} {n}")
                    self.assertEqual(x.count(exp3.LIFE_HEAD), int("life" in exp3.ARMS[arm]))
                    self.assertEqual(x.count(exp3.AROUND_HEAD), int("around" in exp3.ARMS[arm]))
                    a = x.index(exp3.ANCHOR)
                    for h in (exp3.LIFE_HEAD, exp3.AROUND_HEAD):
                        if h in x:
                            self.assertLess(x.index(h), a)
                    if "life" in exp3.ARMS[arm] and "around" in exp3.ARMS[arm]:
                        self.assertLess(x.index(exp3.LIFE_HEAD), x.index(exp3.AROUND_HEAD))
                    add = x[t.index(exp3.ANCHOR):x.index(exp3.ANCHOR)]
                    for w in exp3.FORBIDDEN:
                        self.assertNotIn(w, add, f"{lab} {arm} {n}: {w}")
                    self.assertNotIn("\n\n\n", x[t.index(exp3.ANCHOR) - 5:x.index(exp3.ANCHOR) + 5])

    def test_numbers(self):
        for lab, s in states():
            exp3.set_arm(s, "A2", "試し")
            n, (p, t) = next(iter(prompts(s).items()))
            life, around = exp3.life_text(s, p), exp3.around_text(s, p)
            self.assertIn(f"約 {era2.store_days(s)} 日分", life)
            h = p["household"]
            ads = [q for q in era2.adults(s) if q.get("household") == h]
            self.assertIn(f"大人 {len(ads)} 人", life)
            w = exp3._wealth(s)
            self.assertEqual(w, g7._wealth(s))
            self.assertIn(f"何も持たない家は {sum(1 for v in w.values() if v <= 0)} 家", life)
            since = s["day"] + 1 - exp3.WINDOW_YEARS * era2.YEAR
            ds = [d for d in s["era2"]["g5"]["disputes"] if d["day"] >= since]
            self.assertIn(f"もめごと: {len(ds)} 件", around)
            paid = [d for d in s["era2"]["g5"]["disputes"] if d.get("verdict") == "つぐなう" and (d.get("paid") or 0) > 0]
            if paid:
                ld = max(d.get("end", d["day"]) for d in paid)
                self.assertIn(f"({ld} 日目)", around)
            homes = era2._homes(s)
            how, shown = exp3._shown_rows(s)
            if shown:
                more = sum(1 for x in homes if x in shown and shown[x][1][0] > shown[x][0][1])
                self.assertIn(f"のうち {more} の家は、村の蓄えに入れた量より多く取った", around)

    def test_12599_facts(self):
        """はじめの state (12599 日目) の事実 (prereg 4. の表と同じ)"""
        s = old_state()
        if not s:
            self.skipTest("12599 日目のコミットがない")
        p = next(q for q in s["people"] if q["name"] == era2.answerers(s)[0])
        a = exp3.around_text(s, p)
        self.assertIn("村の家 24 のうち 21 の家は", a)
        self.assertIn("「つぐなう」で払うことになったのは 0 件", a)
        self.assertIn("49年 (5999 日目)。それから 55 年", a)
        self.assertIn("罰のある掟: 0 本", a)
        self.assertIn("48年 (5820 日目) が最後", a)
        self.assertIn("約 23 日分", exp3.life_text(s, p))

    def test_world_untouched(self):
        """apply・life_text・around_text は state を変えない"""
        s = real()
        exp3.set_arm(s, "A2", "試し")
        ps = prompts(s)  # お題を作る今のコード (era2._house など) は、家の空の行を足すことがある。それは組によらないので、作ったあとからくらべる
        before = json.dumps(s, ensure_ascii=False, sort_keys=True)
        for n, (p, t) in ps.items():
            exp3.apply(s, p, t)
        self.assertEqual(json.dumps(s, ensure_ascii=False, sort_keys=True), before)


class C_Refuse(unittest.TestCase):
    def test_refusals(self):
        s = real()
        self.assertIn("本物の村", exp3.refusal(s, "A2", REAL, REAL))
        tmp = Path(tempfile.gettempdir()) / "exp3_x"
        self.assertIn("組は", exp3.refusal(s, "A9", tmp, REAL))
        self.assertIsNone(exp3.refusal(s, "A2", tmp, REAL))
        exp3.set_arm(s, "A2", "試し")
        self.assertIn("もう組 A2", exp3.refusal(s, "A1", tmp, REAL))
        self.assertIsNone(exp3.refusal(s, "A2", tmp, REAL))
        self.assertIsNone(exp3.set_arm(s, "A2", "試し"))
        s2 = real()
        s2["phase"] = "evening"
        self.assertIn("season でない", exp3.refusal(s2, "A2", tmp, REAL))


class D_Step(unittest.TestCase):
    def _copy(self):
        d = Path(tempfile.mkdtemp(prefix="exp3_test_"))
        shutil.copy(REAL / "state.json", d / "state.json")
        return d

    def _run(self, d, *args):
        env = dict(os.environ, SOC_DATA=str(d), SOC_RECORDS="0", PYTHONUTF8="1")
        return subprocess.run([sys.executable, str(SOC / "step.py"), *args], capture_output=True, text=True, env=env, cwd=str(SOC))

    def test_step_a0_a2(self):
        s = real()
        if s.get("phase") != "season" or not (s.get("era2") or {}).get("g7", {}).get("ask"):
            self.skipTest("本物の村が集まりの歩でない")
        day = s["day"]
        for arm in ("A0", "A2"):
            d = self._copy()
            try:
                r = self._run(d, "exp3", arm, "--note", "試し")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                st = json.loads((d / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(st["era2"]["g7"]["exp3"]["arm"], arm)
                self.assertEqual(st["era2"]["g7"]["exp3"]["note"], "試し")
                st["era2"]["g7"].pop("exp3")
                self.assertEqual(json.dumps(st, ensure_ascii=False, separators=(",", ":")), (REAL / "state.json").read_text(encoding="utf-8"))
                pd = d / "prompts" / f"day{day:03d}"
                for kind in ("season", "feeling", "council"):
                    for f in sorted((REAL / "prompts" / f"day{day:03d}" / kind).glob("*.md")):
                        t = (pd / kind / f.name).read_text(encoding="utf-8")
                        if arm == "A2" and kind == "season":
                            self.assertIn(exp3.AROUND_HEAD, t)
                            t = exp3.strip(t)
                        self.assertEqual(t, f.read_text(encoding="utf-8"), f"{arm} {kind} {f.name}")
                r = self._run(d, "exp3", "A1" if arm == "A2" else "A2")
                self.assertEqual(r.returncode, 3)
                r = self._run(d, "status")
                self.assertIn(f"実験 3 の組: {arm}", r.stdout)
            finally:
                shutil.rmtree(d)

    def test_step_real_refused(self):
        before = (REAL / "state.json").stat().st_mtime_ns
        env = dict(os.environ, PYTHONUTF8="1")
        env.pop("SOC_DATA", None)
        r = subprocess.run([sys.executable, str(SOC / "step.py"), "exp3", "A2"], capture_output=True, text=True, env=env, cwd=str(SOC))
        self.assertEqual(r.returncode, 3)
        self.assertIn("本物の村", r.stdout)
        self.assertEqual((REAL / "state.json").stat().st_mtime_ns, before)

    def test_note_only_exp3(self):
        d = self._copy()
        try:
            r = self._run(d, "status", "--note", "x")
            self.assertNotEqual(r.returncode, 0)
        finally:
            shutil.rmtree(d)


class E_Measure(unittest.TestCase):
    def test_verdict(self):
        self.assertEqual(M._verdict("ゆるす"), "ゆるす")
        self.assertEqual(M._verdict("つぐなう"), "つぐなう")
        self.assertEqual(M._verdict("ゆるす。払わせても収まらない (つぐなうより)"), "ゆるす")
        self.assertEqual(M._verdict("つぐなう。ゆるすと続くから"), "つぐなう")
        self.assertIsNone(M._verdict(None))
        self.assertIsNone(M._verdict("..."))

    def test_prompt_facts(self):
        d = REAL / "prompts" / "day12599" / "season"
        fs = sorted(d.glob("*.md")) if d.exists() else []
        if not fs:
            self.skipTest("12599 日目のお題がない")
        h, disp, wealth, days, kids, added = M._prompt_facts(fs[0].read_text(encoding="utf-8"))
        self.assertTrue(h and h.endswith("の家"))
        self.assertEqual(days, 23)
        self.assertEqual(wealth.get("シエ20の家"), 14788)
        self.assertTrue(all(not re.match("、", k) for k in wealth))
        self.assertEqual(added, (False, False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
