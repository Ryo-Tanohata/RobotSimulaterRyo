"""古い記録を年ごとのファイルに分ける仕組み (archive.py。2026-10-10) の試し

  python3.13 sim/society/tools/test_archive.py      本物のデータは読むだけ (写しを一時フォルダに作る)。1 分ほど
  SOC_REAL_DATA=フォルダ で、ほかのデータ (本物の写しなど) を読む

本物の state を全部の形に戻し (もうしまってあれば)、写しでしまって、しまう前と同じかを見る:
- 戻すと 1 バイトもちがわない。年のファイルが足りない・多いと止まる。しまう年がなければ何もしない
- 世界の仕組みが読むもの (お題・季節の答えの反映・家族を決める・目安・控え) が、しまう前と同じ
季節を何回か進めて前のコードと比べる試し (A/B) は、docs/society2_phase_plan.md の 7. に結果を書いた
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
sys.path.insert(0, str(SOC))
import archive  # noqa: E402
import era2  # noqa: E402
import knowledge  # noqa: E402
import records  # noqa: E402

REAL = Path(os.environ.get("SOC_REAL_DATA") or (SOC / "data"))


def dump(x):
    return archive._dump(x)


class Archive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = dump(archive.load_state(REAL))  # しまう前の形 (全部)
        cls.d = Path(tempfile.mkdtemp(prefix="arch_test_"))
        small = json.loads(cls.text)
        cls.years = archive.move(small, cls.d, start=True)
        cls.small = dump(small)
        (cls.d / "state.json").write_text(cls.small, encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.d, ignore_errors=True)

    def whole(self):
        return json.loads(self.text)

    def trimmed(self):
        return json.loads(self.small)

    # ---- しまう・戻す ----
    def test_roundtrip(self):
        self.assertTrue(self.years)
        self.assertEqual(dump(archive.load_state(self.d)), self.text)
        st = self.trimmed()
        self.assertEqual(dump(archive.full(st, self.d)), self.text)
        self.assertEqual(dump(st), self.small)  # full は state を変えない
        self.assertLess(len(self.small), len(self.text) // 2)

    def test_layout(self):
        st, w = self.trimmed(), self.whole()
        a = st["archive"]
        self.assertEqual(archive.YEAR, era2.YEAR)  # archive.py は era2 を読まない (ダッシュボードは標準ライブラリだけで動かすため)
        self.assertEqual(a["upto"], st["day"] // archive.YEAR - archive.KEEP_YEARS - 1)
        cut = (a["upto"] + 1) * archive.YEAR
        old = [e for e in st["events"] if e["id"] < a["event"]]
        self.assertTrue(all(e["type"] in archive.KEEP_TYPES and e["day"] < cut for e in old))
        self.assertEqual(old, [e for e in w["events"] if e["id"] < a["event"] and e["type"] in archive.KEEP_TYPES])
        self.assertTrue(all(e["day"] >= cut for e in st["events"] if e["id"] >= a["event"]))
        for k in archive.LISTS:
            self.assertTrue(all(x["day"] >= cut for x in st.get(k, [])), k)
        for law in st["laws"]:
            self.assertTrue(all(v["day"] >= cut for v in law.get("vote_log", [])), law["id"])
        self.assertEqual([law.keys() for law in st["laws"]], [law.keys() for law in w["laws"]])  # 鍵の順も同じ
        for y in self.years:  # 年のファイルは、その年の日だけ
            for k in archive.KINDS:
                for r in archive._read(archive.path(self.d, k, y)):
                    self.assertEqual((r["vote"] if k == "vote_log" else r)["day"] // archive.YEAR, y, (k, y))

    def test_again_nothing(self):
        st = self.trimmed()
        self.assertEqual(archive.move(st, self.d), [])
        self.assertEqual(dump(st), self.small)
        self.assertEqual(archive.move(self.whole(), self.d), [])  # 移行の前の state には、step.py は何もしない

    def test_missing_or_extra(self):
        d2 = Path(tempfile.mkdtemp(prefix="arch_test2_"))
        try:
            shutil.copytree(self.d / archive.DIR, d2 / archive.DIR)
            (d2 / "state.json").write_text(self.small, encoding="utf-8")
            f = archive.path(d2, "vote_log", self.years[0])
            keep = f.read_bytes()
            f.unlink()
            with self.assertRaises(archive.ArchiveError):
                archive.load_state(d2)
            f.write_bytes(keep + keep)  # 2 回書いた
            with self.assertRaises(archive.ArchiveError):
                archive.load_state(d2)
            f.write_bytes(keep)
            archive.path(d2, "events", self.years[-1]).unlink()
            with self.assertRaises(archive.ArchiveError):
                archive.load_state(d2)
        finally:
            shutil.rmtree(d2)

    def test_next_year(self):
        """年が変わると (step.py の季節の終わり)、次の 1 年分だけをしまい、戻すと同じ。前に書きかけたファイルは正しい中身で書きなおす"""
        d2 = Path(tempfile.mkdtemp(prefix="arch_test4_"))
        try:
            shutil.copytree(self.d / archive.DIR, d2 / archive.DIR)
            st, w = self.trimmed(), self.whole()
            st["day"] += archive.YEAR
            w["day"] += archive.YEAR
            y = st["archive"]["upto"] + 1
            stale = archive.path(d2, "harvests", y)
            stale.write_text('{"day":0}\n', encoding="utf-8")  # 前の試みの残り
            days = archive.days_path(d2, y)
            days.write_text('{"labels":"","days":{}}', encoding="utf-8")  # 戻してやり直す前の世界の、アプリの再生の行
            self.assertEqual(archive.move(st, d2), [y])
            self.assertFalse(days.exists())  # しまうときに消す (step.py の export が作り直す)
            self.assertEqual(st["archive"]["upto"], y)
            self.assertEqual(dump(archive.full(st, d2)), dump(w))
            self.assertTrue(all(e["day"] >= (y + 1) * archive.YEAR for e in st["events"] if e["id"] >= st["archive"]["event"]))
            self.assertTrue(archive.path(d2, "events", y).exists())
            self.assertEqual(archive.move(st, d2), [])
        finally:
            shutil.rmtree(d2)

    def test_out_of_order_keeps_state(self):
        """日の順に並んでいない記録があれば、しまわない (state は前のまま)"""
        st = self.whole()
        st["knowledge_log"][3]["day"], st["knowledge_log"][4]["day"] = st["knowledge_log"][4]["day"] + 1, st["knowledge_log"][3]["day"]
        before = dump(st)
        d2 = Path(tempfile.mkdtemp(prefix="arch_test5_"))
        try:
            with self.assertRaises(archive.ArchiveError):
                archive.move(st, d2, start=True)
            self.assertEqual(dump(st), before)
        finally:
            shutil.rmtree(d2)

    def test_write_failure_keeps_state(self):
        """書けなければ state は前のまま (step.py は「しまえなかった」と出して、季節は進んだまま)"""
        st = self.whole()
        bad = Path(tempfile.mkdtemp(prefix="arch_test3_"))
        (bad / archive.DIR).write_text("ファイルなので、この下に書けない", encoding="utf-8")
        try:
            with self.assertRaises(OSError):
                archive.move(st, bad, start=True)
            self.assertEqual(dump(st), self.text)
        finally:
            shutil.rmtree(bad)

    # ---- 世界の仕組みが読むもの ----
    def test_lookups(self):
        st, w = self.trimmed(), self.whole()
        ev, full_ids = archive.Events(st), {e["id"] for e in w["events"]}
        types = {e["id"]: e["type"] for e in w["events"]}
        n = w["next_event"]
        for i in [0, 1, 5, 8, n // 3, n // 2, st["archive"]["event"] - 1, st["archive"]["event"], n - 1, n, n + 5, -1, -3,
                  True, False, 2.0, 2.5, "12", None, float("nan"), float("inf")]:
            self.assertEqual(i in ev, i in full_ids, repr(i))
            if i in full_ids:
                t = ev.type(i)
                self.assertEqual(t == "話す", types[i] == "話す", repr(i))
                self.assertTrue(t == types[i] or (t == archive.MOVED and types[i] not in archive.KEEP_TYPES), repr(i))
        for e in w["events"]:
            if e["type"] == "話す":
                self.assertEqual(ev.who(e["id"]), e["who"])
        for i in (0, st["archive"]["event"] - 1, st["archive"]["event"], n - 1, n):
            got = archive.event_at(st, i)
            self.assertEqual(got, w["events"][i] if i in ev.ev else None, i)
        for first in (st["archive"]["event"], n - 500, n - 1, n, n + 10):
            self.assertEqual(archive.events_from(st, first), w["events"][first:], first)

    def test_prompts(self):
        """お題 (代表の季節のお題・気持ちのお題・年の終わりの集まりのお題) が、しまう前と同じ"""
        for day in (None, (self.whole()["day"] // archive.YEAR + 1) * archive.YEAR - 1):
            st, w = self.trimmed(), self.whole()
            if day is not None:
                st["day"] = w["day"] = day
            first = w["era2"].get("last_first", 0)
            names = era2.answerers(w)
            self.assertEqual(names, era2.answerers(st))
            self.assertTrue(names)
            for n in names:
                p, q = next(x for x in st["people"] if x["name"] == n), next(x for x in w["people"] if x["name"] == n)
                self.assertEqual(era2.season_prompt(st, p, first), era2.season_prompt(w, q, first), n)
            for n in era2.feelers(w):
                p, q = next(x for x in st["people"] if x["name"] == n), next(x for x in w["people"] if x["name"] == n)
                self.assertEqual(era2.feeling_prompt(st, p, first), era2.feeling_prompt(w, q, first), n)
            if day is not None:
                self.assertEqual(era2._year_digest(st), era2._year_digest(w))
                self.assertIn("## 年の名前", era2.season_prompt(w, next(x for x in w["people"] if x["name"] == names[0]), first))

    def test_apply_answers(self):
        """季節の答え (古い出来事をきっかけにした知識・掟の提案・投票) の反映が、しまう前と同じ"""
        st, w = self.trimmed(), self.whole()
        n = w["next_event"]
        talk = [e["id"] for e in w["events"] if e["type"] == "話す" and e["id"] < st["archive"]["event"]]
        other = [e["id"] for e in w["events"] if e["type"] == "採集" and e["id"] < st["archive"]["event"]]
        grow = [e["id"] for e in w["events"] if e["type"] == "育つ" and e["id"] < st["archive"]["event"]]
        laws = [law["id"] for law in w["laws"] if law["status"] in ("提案", "採用")][:3]
        ans = {}
        for i, name in enumerate(era2.answerers(w)):
            ans[name] = json.dumps({
                "say": [{"to": "みんな", "text": f"試しの話 {i}"}],
                "knowledge": [{"op": "add", "text": "古い話と古い出来事", "because": [talk[0], other[3], n - 2], "confidence": 0.7},
                              {"op": "add", "text": "古い話だけ", "because": [talk[i % len(talk)]], "confidence": 0.6},
                              {"op": "add", "text": "古い出来事だけ", "because": [other[i % len(other)], grow[0]], "confidence": 0.6},
                              {"op": "add", "text": "番号のないもの", "because": [n + 100, -1, True, 2.0, "3"], "confidence": 0.5},
                              {"op": "add", "text": "今の話", "because": n, "confidence": 0.5}],
                "proposal": {"text": f"試しの掟 {i}", "because": [talk[1], other[0], n - 1]} if i % 4 == 0 else None,
                "votes": [{"id": x, "agree": (i + j) % 2 == 0, "reason": "試し"} for j, x in enumerate(laws)],
                "job": {"activity": "採集", "place": "camp"}, "feeling": "試し"}, ensure_ascii=False)
        era2.apply_answers(st, ans)
        era2.apply_answers(w, ans)
        self.assertEqual(dump(archive.full(st, self.d)), dump(w))
        labels = {k["label"] for p in w["people"] for k in p["knowledge"] if k["text"] in ("古い話と古い出来事", "古い話だけ", "古い出来事だけ", "番号のないもの")}
        self.assertEqual(labels, {"創発", "伝承"})  # 古い話だけ → 伝承 (話した人も)、ほか → 創発 (True は 1 番の出来事)

    def test_households_and_indicators(self):
        st, w = self.trimmed(), self.whole()
        joined = [p["name"] for p in w["people"] if p.get("origin") == "よそから来た"][:5]
        for s in (st, w):
            for p in s["people"]:
                if p["name"] in joined:
                    p["household"] = None
            era2._sync_households(s)
        self.assertEqual([p.get("household") for p in st["people"]], [p.get("household") for p in w["people"]])
        self.assertEqual(era2.indicators(st), era2.indicators(w))
        self.assertEqual(records.snapshot(st, meeting_first=1, event_first=2), records.snapshot(w, meeting_first=1, event_first=2))

    def test_knowledge_label(self):
        st, w = self.trimmed(), self.whole()
        for because in ([0], [5], [8], [0, 8], [w["next_event"] - 1], [], [True]):
            self.assertEqual(knowledge._label(st, because), knowledge._label(w, because), because)


if __name__ == "__main__":
    unittest.main(verbosity=2)
