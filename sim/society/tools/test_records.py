"""ダッシュボードの内側の記録の試し (docs/dashboard_records_spec.md 8.)

  python3 sim/society/tools/test_records.py            速い試し (本物のデータは読むだけ。書くのは /tmp の写しだけ)
  python3 sim/society/tools/test_records.py --step     step.py の試しも (写しで季節を 4 回進める。1 分ほど)

本物の sim/society/data には何も書かない。step.py season を本物のデータで動かさない
"""
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
sys.path.insert(0, str(SOC))
sys.path.insert(0, str(HERE))
import build_records  # noqa: E402
import era2  # noqa: E402
import records  # noqa: E402

REAL = Path(os.environ.get("SOC_REAL_DATA") or (SOC / "data"))
STEP = "--step" in sys.argv
if STEP:
    sys.argv.remove("--step")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def scratch(snapshots=True):
    """本物のデータの写し (state.json は写し、答えとお題は読むだけのリンク)。控えは本物の records/ から写すか、git から作る"""
    d = Path(tempfile.mkdtemp(prefix="rec_test_"))  # 写しはふつうの一時フォルダに (Linux は /tmp。Windows でも動くように)
    shutil.copy(REAL / "state.json", d / "state.json")
    for sub in ("answers", "prompts"):
        if (REAL / sub).exists():
            try:
                os.symlink(REAL / sub, d / sub, target_is_directory=True)
            except OSError:  # Windows はリンクに特別な権限が要るので、写す (2026-10-09)
                shutil.copytree(REAL / sub, d / sub)
    if snapshots:
        global _SNAPS
        src = REAL / "records" / "snapshots.jsonl"
        (d / "records").mkdir()
        if src.exists():
            shutil.copy(src, d / "records" / "snapshots.jsonl")
        elif _SNAPS:
            (d / "records" / "snapshots.jsonl").write_text(_SNAPS, encoding="utf-8")
        else:  # 本物にまだ控えがなければ、git から作る (1 回だけ)
            subprocess.run([sys.executable, str(HERE / "backfill_snapshots.py"), "--data", str(d), "--quiet"], check=True,
                           stdout=subprocess.DEVNULL)
            _SNAPS = (d / "records" / "snapshots.jsonl").read_text(encoding="utf-8")
    return d


_SNAPS = None


def jl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(Base, "_d"):
            Base._before = {p: sha(REAL / p) for p in ("state.json",)}
            Base._d = scratch()
            t = time.time()
            Base._sum = build_records.build(Base._d, quiet=True)
            Base._secs = time.time() - t
        cls.d, cls.sum, cls.secs = Base._d, Base._sum, Base._secs
        r = cls.d / "records"
        cls.V = {x["season_end_day"]: x for x in jl(r / "season_village.jsonl")}
        cls.H = {(x["season_end_day"], x["household_id"]): x for x in jl(r / "season_household.jsonl")}
        cls.P = {(x["season_end_day"], x["person_id"]): x for x in jl(r / "season_person.jsonl")}
        cls.L = jl(r / "ledger.jsonl")
        cls.people = json.loads((r / "people.json").read_text(encoding="utf-8"))
        cls.mem = json.loads((r / "membership.json").read_text(encoding="utf-8"))
        cls.meta = json.loads((r / "meta.json").read_text(encoding="utf-8"))
        cls.state = cls.sum["builder"].state

    def flow(self, D, h, item, reason):
        return sum(x["amount"] for x in self.L if x["season_end_day"] == D and x["holder"] == h and x["item"] == item and x["reason"] == reason)


class B_KnownValues(Base):
    """B. 知っている値と合うか"""

    def test_snapshots(self):
        # 16年90日目 (2009 日目) までの 52 は git から作った控え。そのあとは季節ごとに足される (2026-10-09: 決め打ちから「それより多い」に)
        self.assertEqual(self.meta["snapshots"]["git"], 52)
        self.assertGreaterEqual(self.meta["snapshots"]["valid"], 52)
        self.assertEqual(self.meta["snapshots"]["invalid"], 0)
        self.assertGreaterEqual(len(self.V), 51)
        self.assertEqual(self.V[509]["days"], 20)

    def test_1709(self):
        v = self.V[1709]
        self.assertEqual((v["population"], v["adults"], v["children"], v["households_with_adults"]), (22, 15, 7, 8))
        self.assertEqual((v["goats"]["count"], v["goats"]["female"]), (10, 6))
        self.assertEqual((v["pots"], v["sickles"], v["store_days"]), (340, 34, 323))
        self.assertEqual({k: round(x) for k, x in v["store"].items()}, {"草の種": 168396, "木の実": 6465, "芋": 18})
        f = v["fields"]
        self.assertEqual((f["ripe"], f["harvested"], f["fallen"]), (12, 50400, 30518))
        self.assertEqual((v["pests"], v["wealth_gini"], v["house_gini"], v["homes_built"]), (62, 0.843, 0.375, 5))
        self.assertEqual(self.H[(1709, "H02")]["store"], {"草の種": 7795.26})
        self.assertEqual(self.H[(1709, "H02")]["wealth_kcal"], 623621)
        self.assertEqual((self.H[(1709, "H01")]["goats"]["count"], self.H[(1709, "H01")]["wealth_kcal"]), (3, 90000))
        self.assertEqual((v["era"], v["era_end"], v["advanced"]), ("G4", "G5", True))
        y = self.P[(1709, "P023")]
        self.assertEqual(y["jobs"][0]["activity"], "土器づくり")
        self.assertEqual(y["days_by_activity"].get("土器づくり"), 30)
        self.assertEqual((y["outputs"]["pots"], y["outputs"]["tree_pick_evenings"], y["skills"]["土器"]), (72, 30, 1))

    def test_1859(self):
        v = self.V[1859]
        self.assertEqual((v["population"], v["adults"], v["children"], v["households_with_adults"]), (25, 16, 9, 9))
        self.assertEqual((v["goats"]["count"], v["goats"]["female"], v["pots"], v["sickles"], v["store_days"]), (17, 9, 614, 24, 339))
        self.assertEqual(self.H[(1859, "H02")]["store"], {"草の種": 12137.26})
        self.assertEqual(self.H[(1859, "H04")]["store"], {"草の種": 8670.0})
        self.assertEqual(self.H[(1859, "H03")]["store"], {"草の種": 14.0})
        self.assertEqual(v["g5"]["feast"], {"held": True, "cost": {"木の実": 1236}})
        self.assertEqual(v["joined"], ["P028", "P029", "P030"])
        self.assertEqual(v["g5"]["stage"], 2)
        self.assertEqual(self.V[1829]["g5"]["stage"], 1)

    def test_2009(self):
        v = self.V[2009]
        self.assertEqual((v["population"], v["adults"], v["children"]), (27, 16, 11))
        self.assertEqual((v["households_with_adults"], v["households_with_members"]), (9, 10))
        self.assertEqual(self.H[(2009, "H05")]["status"], "大人がいない")
        self.assertEqual((v["goats"]["count"], v["goats"]["female"], v["pots"], v["sickles"]), (32, 22, 554, 22))
        st = {h: self.H[(2009, h)]["store"].get("草の種") for h in ("H01", "H02", "H03", "H04", "H05")}
        self.assertEqual(st, {"H01": 6551.0, "H02": 12137.26, "H03": 14.0, "H04": 14609.0, "H05": 4094.0})

    def test_people(self):
        self.assertGreaterEqual(len(self.people), 35)  # 16年90日目までの 35 人 (そのあとも人は増える)
        self.assertEqual([p["id"] for p in self.people], [f"P{i:03d}" for i in range(1, len(self.people) + 1)])
        self.assertEqual(self.people[22]["name"], "ヨナ")
        causes = {p["name"]: (p["death_cause"], p["died_day"]) for p in self.people if p["died_day"] is not None}
        known = {"イサ": ("飢え", 32), "ルオ": ("ザガ", 84), "リオ": ("子", 1019), "テオ": ("子", 1649),
                 "ナギ": ("病", 1679), "ユノ": ("病", 1829), "カイ": ("病", 1949), "フウ": ("病", 1979)}  # 16年90日目までに亡くなった人
        self.assertEqual({n: c for n, c in causes.items() if c[1] <= 2009}, known)
        ev = self.state["events"]
        for p in self.people:  # 年齢が文に書かれていれば、それと同じ
            if p["death_event"] is not None:
                m = __import__("re").search(r"\((\d+) 歳\)", ev[p["death_event"]]["text"])
                if m:
                    self.assertEqual(p["age_at_death"], int(m.group(1)), p["name"])
        self.assertGreaterEqual(len(self.mem), len(self.people))  # 1 人 1 行以上 (家が分かれると行が増える)
        hs = json.loads((self.d / "records" / "households.json").read_text(encoding="utf-8"))
        self.assertEqual([h["name"] for h in hs][:10], ["川辺の家", "ナギの家", "ケトの家", "トワの家", "ユノの家", "フウの家", "アルの家", "クラの家", "セキの家", "スイの家"])  # 16年90日目までの 10

    def test_meetings_and_rules(self):
        """答えのファイル名 = 代表 (と、代表でないまとめ役)。条件の中身 = CRITERIA。大人の区分 = 子でない。控えの生き死に = membership"""
        b = self.sum["builder"]
        for rds in b.seasons.values():
            a = rds[0]["start"]
            P = b.snaps.get(a)
            files = set((b.answers.get(a) or {}).get("season") or {})
            if not files:
                continue
            ads = {p["name"] for p in b.people if b.alive_at(p["name"], a) and b.is_adult(p["name"], a, P)}
            want = (b.reps_at(a, P) | ({b.leader_at(a, P)} - {None})) if P["season"]["rep_mode"] else ads
            self.assertEqual(files, want, f"集まり {a}")
        for day, s in b.snaps.items():
            ind = (s.get("era_info") or {}).get("indicators")
            era = b.era_on(day - 1) if day > b.start else None
            if not ind or era not in era2.CRITERIA:
                continue
            self.assertEqual(records.criteria_progress(era, ind)["all_met"], bool(era2.CRITERIA[era][1](ind)), f"条件 {day} {era}")
            for n, sp in s["people"].items():
                if sp.get("alive"):
                    self.assertEqual(b.alive_at(n, day), True, f"{n} {day}")
                    a_ = records.age_on(b.byname[n], day)
                    self.assertEqual(a_ >= era2.ADULT, not sp.get("child"), f"{n} {day}")
                    self.assertEqual(records.age_class(a_) in ("大人", "年寄り"), not sp.get("child"))
                elif n in b.t_in:
                    self.assertFalse(b.alive_at(n, day), f"{n} {day}")


class B_Prompts(Base):
    """B. お題に書かれた値 (G4 から) と記録が合うか: 村の蓄え・ヤギ・土器・鎌・家ごとの倉"""

    def test_prompts(self):
        import re
        b = self.sum["builder"]
        hid = b.hid
        seen = 0
        for D, v in sorted(self.V.items()):
            if D < 1589:
                continue
            pdir = REAL / "prompts" / f"day{D}" / "season"
            files = sorted(pdir.glob("*.md")) if pdir.is_dir() else []
            if not files:
                continue
            t = files[0].read_text(encoding="utf-8")
            m = re.search(r"^村の蓄え: (.+?) \(今の人数で 約 (\d+) 日分\)", t, re.M)
            self.assertIsNotNone(m, D)
            w = build_records.words(m.group(1))
            r = {k: x for k, x in v["store"].items() if round(x) > 0 or w.get(k)}
            self.assertEqual(set(w), set(r), D)
            for k, x in r.items():  # 記録は小数 2 桁まで。ちょうど .5 は丸め方で 1 ちがうことがある (2939 日目の木の実 15902.5)
                self.assertLessEqual(abs(w[k] - x), 0.51, (D, k))
            self.assertEqual(int(m.group(2)), v["store_days"], D)
            m = re.search(r"^飼っているヤギ: (\d+) 頭 \(メス (\d+)・オス (\d+)\)", t, re.M)
            if m:
                self.assertEqual(tuple(int(x) for x in m.groups()), (v["goats"]["count"], v["goats"]["female"], v["goats"]["male"]), D)
            m = re.search(r"^村の土器: (\d+) 個.*村の石の鎌: (\d+) 本", t, re.M)
            if m:
                self.assertEqual((int(m.group(1)), int(m.group(2))), (v["pots"], v["sickles"]), D)
            m = re.search(r"^家ごとの持ち物: (.+)$", t, re.M)
            if m:
                for h, keep, food, goats in re.findall(r"([^、 ]+?の家) \(倉: (持つ|持たない)、(.+?)、ヤギ (\d+) 頭\)", m.group(1)):
                    row = self.H.get((D, hid[h]))
                    self.assertIsNotNone(row, (D, h))
                    self.assertEqual(build_records.words(food), {k: round(x) for k, x in row["store"].items() if round(x) > 0}, (D, h))
                    self.assertEqual(row["keep"], keep == "持つ", (D, h))
                    self.assertEqual(row["goats"]["count"], int(goats), (D, h))
            seen += 1
        self.assertGreater(seen, 10)


class C_Ledger(Base):
    """C. 帳簿が合うか"""

    def test_exact_accounts(self):
        bad = [x for x in self.L if x["reason"] == build_records.DIFF and not (x["holder"] == "村" and x["item"] in build_records.FOODS)]
        self.assertEqual(bad, [])
        tot = [x["detail"]["total_kcal"] for x in self.L if x["reason"] == build_records.DIFF and x["holder"] == "村"]
        self.assertLessEqual(max(abs(t) for t in tot), 100 + 1e-6)
        # 1 品ごとの差は、採集の出来事が品ごとに丸めるので品のあいだで行き来する (合わせた kcal は上で 100 以内)。人が増えると幅が広がる (29年: 草の種 38.48)
        self.assertLessEqual(max(self.meta["ledger"]["village_food_max_residual"].values()), 60)
        self.assertEqual(self.meta["harvest_replay_unverified"], [])

    def test_rows(self):
        self.assertEqual(self.flow(1709, "H02", "草の種", "刈った (自分の家の畑)"), 7798)
        self.assertEqual(self.flow(1709, "H02", "草の種", "虫やネズミ"), -2.74)
        self.assertEqual(self.flow(1829, "H02", "草の種", "刈った (自分の家の畑)"), 4342)
        self.assertEqual(self.flow(1829, "H04", "草の種", "刈った (自分の家の畑)"), 8684)
        self.assertEqual(self.flow(1859, "H04", "草の種", "罰・つぐないで払った"), -14)
        self.assertEqual(self.flow(1859, "H03", "草の種", "罰・つぐないで受け取った"), 14)
        for h, n in (("H04", 5692), ("H01", 6798), ("H05", 4094)):
            self.assertEqual(self.flow(1949, h, "草の種", "刈った (自分の家の畑)"), n)
        self.assertEqual(self.flow(1979, "H01", "草の種", "罰・つぐないで払った"), -247)
        self.assertEqual(self.flow(1979, "H04", "草の種", "罰・つぐないで受け取った"), 247)
        for D, born, lost in ((2009, 15, 6), (1889, 9, 3)):
            g = [x for x in self.L if x["season_end_day"] == D and x["item"] == "ヤギ"]
            self.assertEqual(sum(x["amount"] for x in g if x["reason"] == "生まれた"), born)
            self.assertEqual(sum(x["amount"] for x in g if x["reason"] == "いなくなった (世話が足りない)"), -lost)

    def test_balance(self):
        """どの帳簿も、はじめ + 動き = 終わり (丸めた値で 0.02 単位まで)"""
        acc = {}
        for x in self.L:
            if x["kind"] == "メモ":
                continue
            k = (x["season_end_day"], x["holder"], x["item"])
            a = acc.setdefault(k, {"s": None, "e": None, "f": 0})
            if x["reason"] == build_records.START:
                a["s"] = x["amount"]
            elif x["reason"] == build_records.END:
                a["e"] = x["amount"]
            else:
                a["f"] += x["amount"]
        for k, a in acc.items():
            if a["s"] is not None and a["e"] is not None:
                self.assertAlmostEqual(a["s"] + a["f"], a["e"], delta=0.05, msg=str(k))


class D_Determinism(Base):
    """D. 何度作っても同じ"""

    def files(self, d):
        r = Path(d) / "records"
        return {p.name: p.read_bytes() for p in sorted(r.iterdir()) if p.name != "snapshots.jsonl"}

    def test_rebuild_same(self):
        a = self.files(self.d)
        build_records.build(self.d, quiet=True)
        self.assertEqual(a, self.files(self.d))

    def test_shuffled_and_invalid(self):
        d2 = scratch(snapshots=False)
        try:
            lines = (self.d / "records" / "snapshots.jsonl").read_text(encoding="utf-8").splitlines()
            random.Random(1).shuffle(lines)
            bad = json.loads(lines[0])
            bad["sig"] = "0" * 16  # 取りやめた回の控えのつもり
            (d2 / "records").mkdir()
            (d2 / "records" / "snapshots.jsonl").write_text("\n".join(lines + [json.dumps(bad, ensure_ascii=False), "{こわれた行"]) + "\n", encoding="utf-8")
            build_records.build(d2, quiet=True)
            a, b = self.files(self.d), self.files(d2)
            ma, mb = json.loads(a.pop("meta.json")), json.loads(b.pop("meta.json"))
            self.assertEqual(a, b)
            self.assertEqual((mb["snapshots"]["invalid"], mb["snapshots"]["malformed"]), (1, 1))
            ma["snapshots"], mb["snapshots"] = None, None
            self.assertEqual(ma, mb)
        finally:
            shutil.rmtree(d2)


class E_Boundaries(Base):
    """E. 集まりの区切りと、控えがないとき"""

    def test_meeting_first(self):
        b = self.sum["builder"]
        days = sorted(b.snaps)
        for a, r in zip(days, days[1:]):
            self.assertEqual(records.meeting_first(self.state, a), b.snaps[r]["meeting_first"], f"集まり {a}")
        self.assertTrue(self.meta["event_ids_are_indexes"])

    def test_without_snapshots(self):
        d2 = scratch(snapshots=False)
        try:
            build_records.build(d2, quiet=True)
            V2 = {x["season_end_day"]: x for x in jl(d2 / "records" / "season_village.jsonl")}
            self.assertEqual(sorted(V2), sorted(self.V))
            for D, v in self.V.items():
                w = V2[D]
                self.assertFalse(w["snapshot"])
                self.assertIsNone(w["store"])
                for k in ("population", "adults", "children", "births", "deaths", "joined", "came_of_age", "pots_made", "pests",
                          "rounds", "era", "era_end", "eaten", "laws"):
                    if k == "rounds":
                        self.assertEqual([dict(x, snapshot=None) for x in v[k]], [dict(x, snapshot=None) for x in w[k]], f"{D} {k}")
                    elif k == "laws":
                        self.assertEqual({x: v[k][x] for x in ("adopted", "abolished", "proposed")}, {x: w[k][x] for x in ("adopted", "abolished", "proposed")})
                    else:
                        self.assertEqual(v[k], w[k], f"{D} {k}")
                self.assertEqual(v["fields"]["harvested"], w["fields"]["harvested"], D)
        finally:
            shutil.rmtree(d2)


class A4_Purity(Base):
    """A4. 控えは state を変えない。本物のデータは変わらない"""

    def test_snapshot_pure(self):
        st = json.loads((REAL / "state.json").read_text(encoding="utf-8"))
        before = json.dumps(st, sort_keys=True, ensure_ascii=False)
        t = time.time()
        records.snapshot(st, meeting_first=1, event_first=2)
        self.assertLess(time.time() - t, 0.5)
        self.assertEqual(before, json.dumps(st, sort_keys=True, ensure_ascii=False))

    def test_real_data_untouched(self):
        self.assertEqual(self._before, {p: sha(REAL / p) for p in ("state.json",)})


class H_Performance(Base):
    def test_build_time(self):
        self.assertLess(self.secs, 15)


class B_Rows(Base):
    """B. 行どうしが合うか: 人の行は季節の中の日だけ・家の行の合計 = 村の行"""

    def test_present_in_season(self):
        for (D, _), r in self.P.items():
            self.assertGreaterEqual(r["present_from"], self.V[D]["season_start_day"], (D, r["person_id"]))
            self.assertLessEqual(r["present_from"], r["present_to"], (D, r["person_id"]))

    def test_household_sums(self):
        for D, v in self.V.items():
            hs = [h for (d, _), h in self.H.items() if d == D]
            self.assertEqual(sum(len(h["members"]) for h in hs), v["population"], D)
            self.assertEqual(sum(h["adults"] for h in hs), v["adults"], D)


class F_YearNames(unittest.TestCase):
    """F. 年の名前 (state の写しで、メモリの中だけ。本物のデータには書かない)"""

    @classmethod
    def setUpClass(cls):
        cls.base = (REAL / "state.json").read_text(encoding="utf-8")

    def state(self, day):
        st = json.loads(self.base)
        st["day"] = day
        st["era2"]["year_names"] = []  # 本物の state にもう年の名前があっても、まだない形で試す (2026-10-09)
        return st

    def test_text(self):
        f = era2._year_name_text
        self.assertEqual(f("「 豊かな年 」"), "豊かな年")
        self.assertEqual(f("ＡＢＣの年"), "ABCの年")  # NFKC
        for x in ("...", "…", "なし", "null", None, 3, "", "二行の\n名前", "フェーズが G6 に進んだ年", "あ" * 0):
            self.assertEqual(f(x), "", repr(x))
        self.assertEqual(len(f("あ" * 40)), era2.YEAR_NAME_MAX)

    def test_decide(self):
        st = self.state(2039)
        self.assertTrue(era2.year_end(st))
        self.assertFalse(era2.year_end(self.state(2009)))
        ads = sorted(era2.adults(st), key=lambda q: -q["age"])
        old, mid, young = ads[0], ads[1], ads[-1]
        n0 = st["next_event"]
        era2._year_name(st, [(young, "雨の年", 3), (mid, "祭りの年", 2), (old, "祭りの年", 1)], 16)  # 3 対 3 → 書いた人でいちばん年上
        x = st["era2"]["year_names"][0]
        self.assertEqual((x["year"], x["name"], x["weight"], x["adults"], x["event"]), (16, "祭りの年", 3, 16, n0))
        e = st["events"][-1]
        self.assertEqual((e["type"], e["who"], e["data"]), ("年の名前", None, {"year": 16, "name": "祭りの年"}))
        era2._year_name(st, [(young, "ちがう名前", 9)], 16)  # 同じ年は 1 回だけ
        self.assertEqual(len(st["era2"]["year_names"]), 1)
        self.assertEqual(st["next_event"], n0 + 1)
        era2._year_name(self.state(2039), [], 16)  # だれも書かなければ、何も変わらない

    def test_prompts(self):
        st = self.state(2039)
        p = next(q for q in era2.adults(st) if q["name"] in era2.answerers(st))
        t = era2.season_prompt(st, p, st["era2"].get("last_first", 0))
        self.assertIn("## 年の名前 (1 年に 1 回)", t)
        self.assertIn('"year_name": "..."', t)
        self.assertNotIn("## 村で覚えている年の名前", t)
        dg = era2._year_digest(st)
        self.assertIn(dg, t)
        self.assertLessEqual(dg.count("- [出来事 "), era2.YEAR_DIGEST_MAX)
        self.assertIn("畑で刈った草の種: 合わせて", dg)
        st2 = self.state(2009)
        t2 = era2.season_prompt(st2, p, st2["era2"].get("last_first", 0))
        self.assertNotIn("年の名前", t2)
        st2["era2"]["year_names"] = [{"year": 15, "name": "大きな祭りの年"}, {"year": 16, "name": "雨の年"}]
        st2["day"] = 2069
        t3 = era2.season_prompt(st2, p, st2["era2"].get("last_first", 0))
        self.assertIn("「雨の年」 (去年)", t3)
        self.assertNotIn("「大きな祭りの年」 (去年)", t3)


class I_Pasture(unittest.TestCase):
    """I. 草の量でヤギの数に上限 (2026-10-10。state の写しで、メモリの中だけ)"""

    @classmethod
    def setUpClass(cls):
        cls.base = (REAL / "state.json").read_text(encoding="utf-8")

    def state(self, owners):
        st = json.loads(self.base)
        st["era2"]["goats"] = [{"id": i, "sex": "メス" if i % 2 else "オス", "born": 0, "owner": h}
                               for i, h in enumerate(h for h, n in owners for _ in range(n))]
        return st

    def test_cap_and_text(self):
        st = self.state([(None, 100)])
        cap = era2.pasture_cap(st)
        self.assertEqual(cap, 140)  # この地図の草原と丘 276 ha × 0.5 頭
        self.assertEqual(era2._pasture_text(st), "")  # K の 8 割より少なければ、お題は前と同じ
        self.assertIn("約 140 頭 (今は 120 頭)", era2._pasture_text(self.state([(None, 120)])))
        self.assertIn("今は 141 頭で、草が足りない", era2._pasture_text(self.state([(None, 141)])))

    def test_loss(self):
        st = self.state([(None, 140)])
        n0 = st["next_event"]
        era2._pasture_loss(st, 140, 1.0, random.Random(1))  # K 頭以下: 何も変えない
        self.assertEqual((len(st["era2"]["goats"]), st["next_event"]), (140, n0))
        runs = []
        for _ in range(2):
            st = self.state([(None, 150), ("ルオの家", 40), ("セナの家", 10)])
            era2._pasture_loss(st, 140, 1.0, random.Random(1))  # 多すぎる 60 頭の 3 分の 1 = 20 頭を、持ち主の頭数に比べて分ける
            left = {}
            for g in st["era2"]["goats"]:
                left[g.get("owner")] = left.get(g.get("owner"), 0) + 1
            self.assertEqual(left, {None: 135, "ルオの家": 36, "セナの家": 9})
            e = st["events"][-1]
            self.assertEqual((e["type"], e["who"], e["data"]["cap"], e["data"]["herd"], len(e["data"]["goat_ids"])), ("ヤギ", None, 140, 200, 20))
            self.assertIn("ヤギ 20 頭がやせていなくなった (村 15 頭・セナの家 1 頭・ルオの家 4 頭)", e["text"])
            self.assertEqual(build_records.GOATS_RE.search(e["text"]).group(1), "20")  # 記録は「ヤギ n 頭」と「いなくなった」で数える
            runs.append(e["data"]["goat_ids"])
        self.assertEqual(runs[0], runs[1])  # 同じ乱数なら同じヤギ

    def spring(self, owners):
        """春のはじめの季節の終わり (子ヤギが生まれる) にした state"""
        st = self.state(owners)
        st["day"] = next(d for d in range(st["day"], st["day"] + era2.YEAR) if era2.season(d + 1) == "春" and era2.season(d) != "春")
        st["era2"]["kid_year"] = None
        return st

    def season_end(self, st, cap=None):
        old = era2.pasture_cap
        if cap is not None:
            era2.pasture_cap = lambda state: cap
        try:
            era2._season_end(st, 1.0)
        finally:
            era2.pasture_cap = old
        return st

    def test_below_cap_same_as_before(self):
        """K 頭以下なら、上限がないとき (前のコード) と同じに進む (乱数も引かない)"""
        a = self.season_end(self.spring([(None, 120), ("ルオの家", 20)]))
        b = self.season_end(self.spring([(None, 120), ("ルオの家", 20)]), cap=10 ** 9)
        self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True), json.dumps(b, ensure_ascii=False, sort_keys=True))
        self.assertFalse([e for e in a["events"] if "草が足りず" in e["text"]])

    def test_over_cap_fewer_kids(self):
        """K 頭より多いと、多すぎる分の 3 分の 1 がいなくなり、子を産む母ヤギが K/N に減る。同じ state なら同じ結果"""
        free = self.season_end(self.spring([(None, 300), ("ルオの家", 100)]), cap=10 ** 9)
        runs = [self.season_end(self.spring([(None, 300), ("ルオの家", 100)])) for _ in range(2)]
        self.assertEqual(json.dumps(runs[0], ensure_ascii=False, sort_keys=True), json.dumps(runs[1], ensure_ascii=False, sort_keys=True))
        st = runs[0]
        ev = [e for e in st["events"] if "草が足りず" in e["text"]]
        self.assertEqual(len(ev), 2, [e["text"] for e in ev])
        self.assertIn("ヤギ 87 頭がやせていなくなった", ev[0]["text"])  # (400 − 140) / 3
        kids = int(re.search(r"子ヤギが (\d+) 頭生まれた", ev[1]["text"]).group(1))
        kids_free = sum(1 for g in free["era2"]["goats"] if g["born"] == free["day"])
        self.assertEqual(sum(1 for g in st["era2"]["goats"] if g["born"] == st["day"]), kids)
        self.assertLess(kids, kids_free * 0.6)  # 見込み 140/313 = 0.45
        self.assertEqual(len(st["era2"]["goats"]), 400 - 87 + kids)
        self.assertTrue(any(g.get("owner") == "ルオの家" and g["born"] == st["day"] for g in st["era2"]["goats"]))  # 子は母の持ち主


@unittest.skipUnless(STEP, "--step のときだけ (写しで季節を進める)")
class G_StepSmoke(unittest.TestCase):
    """G. step.py: 季節のあとに控えを足し、記録を作り直す。失敗しても季節は止まらない"""

    def run_step(self, code, data, env=None):
        e = dict(os.environ, SOC_DATA=str(data), **(env or {}))
        return subprocess.run([sys.executable, str(code / "step.py"), "season"], env=e, capture_output=True, text=True)

    def copy_code(self):
        c = Path(tempfile.mkdtemp(prefix="rec_code_"))
        for f in SOC.glob("*.py"):
            shutil.copy(f, c / f.name)
        (c / "tools").mkdir()
        for f in (SOC / "tools").glob("*.py"):
            shutil.copy(f, c / "tools" / f.name)
        return c

    def data(self):
        d = scratch()
        os.unlink(d / "answers")
        os.unlink(d / "prompts")
        (d / "answers").mkdir()
        return d

    def test_normal_and_failing_builder_and_off(self):
        code = self.copy_code()
        d1, d2, d3 = self.data(), self.data(), self.data()
        try:
            n0 = len((d1 / "records" / "snapshots.jsonl").read_text(encoding="utf-8").splitlines())
            r = self.run_step(code, d1)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(len((d1 / "records" / "snapshots.jsonl").read_text(encoding="utf-8").splitlines()), n0 + 1)
            meta = json.loads((d1 / "records" / "meta.json").read_text(encoding="utf-8"))
            st = json.loads((d1 / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["state_day"], st["day"])
            self.assertEqual(meta["snapshots"]["live"], 1)
            self.assertEqual(meta["ledger"]["exact_accounts_with_difference"], 0)
            # 記録を作るのに失敗しても、季節は進み、控えは足される
            (code / "tools" / "build_records.py").write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
            r = self.run_step(code, d2)
            self.assertEqual(r.returncode, 0)
            self.assertIn("記録: 記録を作れなかった", r.stdout)
            self.assertEqual(len((d2 / "records" / "snapshots.jsonl").read_text(encoding="utf-8").splitlines()), n0 + 1)
            self.assertEqual(json.loads((d2 / "state.json").read_text(encoding="utf-8"))["day"], st["day"])
            # 同じ世界: 記録があってもなくても、state.json は同じ
            self.assertEqual(sha(d1 / "state.json"), sha(d2 / "state.json"))
            # SOC_RECORDS=0 なら記録を作らない
            shutil.rmtree(d3 / "records")
            r = self.run_step(code, d3, {"SOC_RECORDS": "0"})
            self.assertEqual(r.returncode, 0)
            self.assertFalse((d3 / "records").exists())
            self.assertEqual(sha(d1 / "state.json"), sha(d3 / "state.json"))
        finally:
            for x in (code, d1, d2, d3):
                shutil.rmtree(x, ignore_errors=True)

    def test_everyone_gone(self):
        code = self.copy_code()
        d = self.data()
        try:
            st = json.loads((d / "state.json").read_text(encoding="utf-8"))
            for p in st["people"]:
                p["alive"] = False
            (d / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            n0 = len((d / "records" / "snapshots.jsonl").read_text(encoding="utf-8").splitlines())
            r = self.run_step(code, d)
            self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
            self.assertEqual(len((d / "records" / "snapshots.jsonl").read_text(encoding="utf-8").splitlines()), n0 + 1)
        finally:
            shutil.rmtree(code, ignore_errors=True)
            shutil.rmtree(d, ignore_errors=True)


def tearDownModule():
    if hasattr(Base, "_d"):
        shutil.rmtree(Base._d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
