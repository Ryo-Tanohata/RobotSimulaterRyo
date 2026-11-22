"""動画 D1 (村のいちばん最初の日 = 1 日目、画面の日付は 0年2日目) のナレーションを、記録と合わせる (読むだけ。2026-11-22)

しまった出来事 (data/archive/events_0000.jsonl・days_0000.json) と app_data.json (掟・人・場所・グラフの数) を読み、
narration_D1.json の文に出る数と中身が記録と同じかを確かめる。合わないと止まる (終わりの値 1)。data/ には書かない。

使い方: cd sim/society && python3 video/check_D1.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
YEAR = 120
bad = []


def ok(what, got, want):
    print(("OK  " if got == want else "NG  ") + f"{what}: 記録 {got} / 文 {want}")
    if got != want:
        bad.append(what)


def label(d):
    return f"{d // YEAR}年{d % YEAR + 1}日目"


def main():
    with open(os.path.join(HERE, "narration_D1.json"), encoding="utf-8") as f:
        lines = {x["id"]: x for x in json.load(f)}
    txt = "".join(x["text"] for x in lines.values())
    t = {k: v["text"] for k, v in lines.items()}
    assert not re.search(r"claude|opus|sonnet|haiku|gpt", txt + "".join(x.get("say", "") for x in lines.values()), re.I), "モデルの名前は出さない"
    with open(os.path.join(HERE, "days_D1.txt"), encoding="utf-8") as f:
        days = [int(x) for x in f.read().strip().split(",")]
    ok("撮る日", days, [1])
    ok("日付 (n02)", label(1) in t["n02"] and label(0) in t["n02"], True)
    ok("ウィロとイサの掟が決まる日 (n18)", label(7) in t["n18"], True)

    with open(os.path.join(DATA, "archive", "events_0000.jsonl"), encoding="utf-8") as f:
        evs = [json.loads(x) for x in f if x.strip()]
    with open(os.path.join(DATA, "archive", "days_0000.json"), encoding="utf-8") as f:
        rows = json.load(f)["days"]
    with open(os.path.join(DATA, "app_data.json"), encoding="utf-8") as f:
        A = json.load(f)
    ok("0 日目 (最初の夜) の出来事の数", sum(1 for e in evs if e["day"] == 0), 0)
    ev = [e for e in evs if e["day"] == 1]
    ok("1 日目に動いた 5 人", sorted(r["name"] for r in rows["1"]), sorted(["ルオ", "セナ", "タヒ", "ウィロ", "イサ"]))
    here = [p["name"] for p in A["people"] if (p.get("since") or 0) <= 1 and (p.get("born_day") is None or p["born_day"] <= 1)]
    ok("1 日目に村にいた人", here, ["ルオ", "セナ", "タヒ", "ウィロ", "イサ"])
    by = lambda typ: [e for e in ev if e["type"] == typ]
    ok("採集した人と場所 (n07)", sorted((e["who"], "東の林" in e["text"]) for e in by("採集")), [("イサ", True), ("ルオ", True)])
    ok("探索した人と場所 (n08)", sorted((e["who"], "東の林" if "東の林" in e["text"] else "南の川") for e in by("探索")),
       [("ウィロ", "南の川"), ("セナ", "東の林"), ("タヒ", "東の林")])
    ok("探索でわかったこと: ルク 12 頭・木の実が多い (n08)", all("ルクの群れ (12 頭)" in e["text"] and "木の実 が多い" in e["text"] for e in by("探索")), True)
    pl = {p["id"]: p["label"] for p in A["places"]}
    ok("東の林・南の川の遠さ (n07・n08)", ("約 300 m" in pl["東林12"], "約 100 m" in pl["南川12"]), (True, True))
    ok("この日の狩り・火の出来事 (n09・n11)", (len(by("狩り")), len(by("火"))), (0, 0))
    st = next(s for s in A["stats"] if s["day"] == 1)
    ok("この日の火 (stats)", st["fire"], False)
    ok("食べた量 (n10)", f"{st['eaten']:.0f}" in t["n10"], True)
    ok("1 人あたり約 1000 (n10)", round(st["eaten"] / st["alive"], -2), 1000)
    talk = {e["who"]: e["text"] for e in by("話す")}
    ok("ルオの話 (n12)", "「ザガが出るから気をつけよう」" in talk["ルオ"] and "ザガが出るから気をつけよう" in t["n12"], True)
    ok("タヒの話 (n13)", "明日、俺たちで行ってみようぜ" in talk["タヒ"], True)
    ok("イサの話 (n14)", "「東の林で、たくさん集められた」" in talk["イサ"], True)
    ok("セナ・タヒ・ウィロがルクと木の実を知らせた (n13)", all("ルク" in talk[n] and "木の実" in talk[n] for n in ("セナ", "タヒ", "ウィロ")), True)
    share = {}
    for e in by("分ける"):
        share.setdefault(e["who"], []).append(e["data"]["to"])
    ok("分けた人と相手 (n15)", share, {"ルオ": ["セナ", "タヒ", "ウィロ"], "イサ": ["ルオ", "セナ", "タヒ"]})
    L = {l["id"]: l for l in A["laws"]}
    ok("L0 (n06)", (L["L0"]["proposer"], L["L0"]["day"], L["L0"]["text"] in t["n06"]), ("イサ", 0, True))
    who = {e["id"]: e["who"] for e in evs}
    ok("L1 (n17): ウィロが 1 日目に、セナとタヒの話から", (L["L1"]["proposer"], L["L1"]["day"], sorted(who[i] for i in L["L1"]["because"])),
       ("ウィロ", 1, ["セナ", "タヒ"]))
    ok("L0・L1 が決まった日 (n18)", [(L[k]["status"], L[k]["changed"]) for k in ("L0", "L1")], [("採用", 7), ("採用", 7)])
    share_laws = [l for l in A["laws"] if "分け" in l["text"] and l["day"] <= 1]
    ok("1 日目までに分け合う掟はない (n16)", share_laws, [])
    P = {p["name"]: p["personality"] for p in A["people"][:5]}
    ok("性格 (n05)", (P["ルオ"]["協力"] >= 0.9, P["イサ"]["協力"] >= 0.9, P["ルオ"]["大胆"] >= 0.7, P["イサ"]["大胆"] >= 0.7,
                     P["セナ"]["社交"] >= 0.8, P["ウィロ"]["社交"] >= 0.8, P["ウィロ"]["大胆"] <= 0.1, P["タヒ"]["大胆"] >= 0.8), (True,) * 8)
    ok("世界の広さ 2 キロ四方 (n03)", (A["map"]["w"] * A["map"]["cell"], A["map"]["h"] * A["map"]["cell"]), (2000, 2000))
    ok("1 日目は夏 (n03)", 1 % YEAR < 30, True)
    ok("村は 240 年をこえて続いている (n19)", A["day"] // YEAR >= 240, True)
    ok("いま生きている人は 700 人をこえる (n19)", sum(1 for p in A["people"] if p["alive"]) > 700, True)
    print("ぜんぶ合った" if not bad else f"合わない: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
