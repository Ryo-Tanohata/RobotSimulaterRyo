"""動画 S3P34 (Society 3.0 フェーズ 3・4) のナレーションの数を、記録と合わせる (読むだけ。2026-11-22)

state.json (era2.g7.i4・p4)・しまった出来事 (data/archive/events_YYYY.jsonl)・年報 (reports/yearNNN.html) を読み、
narration_S3P34.json の文に出る数が記録と同じかを確かめる。合わないと止まる (終わりの値 1)。data/ には書かない。

使い方: cd sim/society && python3.13 video/check_S3P34.py [state.json の場所 (既定 data/state.json)]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
YEAR = 120
bad = []


def ok(what, got, want):
    print(("OK  " if got == want else "NG  ") + f"{what}: 記録 {got} / 文 {want}")
    if got != want:
        bad.append(what)


def label(d):
    return f"{d // YEAR}年{d % YEAR + 1}日目"


def events(day):
    y = day // YEAR
    p = os.path.join(ROOT, "data", "archive", f"events_{y:04d}.jsonl")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            evs = [json.loads(line) for line in f if line.strip()]
    else:  # まだしまっていない年は app_data.json から
        with open(os.path.join(ROOT, "data", "app_data.json"), encoding="utf-8") as f:
            evs = json.load(f)["events"]
    return [e for e in evs if e["day"] == day]


def report(y):
    with open(os.path.join(ROOT, "reports", f"year{y}.html"), encoding="utf-8") as f:
        t = f.read()
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "state.json")
    with open(src, encoding="utf-8") as f:
        g = json.load(f)["era2"]["g7"]
    with open(os.path.join(HERE, "narration_S3P34.json"), encoding="utf-8") as f:
        lines = {x["id"]: x for x in json.load(f)}
    txt = "".join(x["text"] for x in lines.values())
    assert "4.0" not in txt and "4.0" not in "".join(x["say"] for x in lines.values()), "「4.0」は出さない"
    i4, p4 = g["i4"], g["p4"]
    r = {int(k): v for k, v in i4["rows"].items()}
    q = {int(k): v for k, v in p4["rows"].items()}
    # 日付
    with open(os.path.join(HERE, "days_S3P34.txt"), encoding="utf-8") as f:
        days = [int(x) for x in f.read().strip().split(",")]
    ok("撮る日", days, sorted({x["day"] for x in lines.values()}))
    for d, want in [(27000, "225年1日目"), (27059, "225年60日目"), (27360, "228年1日目"), (27839, "231年120日目"), (27870, "232年31日目"), (28079, "233年120日目")]:
        ok(f"{d} の日付", label(d), want)
    # n01・n04 フェーズ 3 の始まり、n20 フェーズ 4 の始まり、n30 直し
    ok("n04 フェーズ 3 の始まり", label(i4["day"]), "224年120日目")
    ok("n20 フェーズ 4 の始まり", p4["day"], 27839)
    ok("n30 直しの日", p4["fix1"]["day"], 28079)
    ok("n30 直しの言葉", "小さく直して 2 年見る" in p4["fix1"]["words"], True)
    # n02 はじめの人数
    ok("n02 フェーズ 3 のはじめの人", i4["pop0"], 675)
    # n05 はじめての知らせ
    n0 = i4["notes"]["225"][0]
    ok("n05 はじめての知らせ", (n0["house"], n0["writer"], n0["text"], n0["by"]), ("ハソ4の家", "ヒセ88", "夏の畑は落ちる前に刈りきろう。ヤギはオスから減らそう", "ソワ58"))
    ok("n05 27000 日目に書いた人", [e["who"] for e in events(27000) if e["type"] == "知らせを書く"], ["ヒセ88"])
    # n06 225年の読める大人
    ok("n06 225年 読める大人 / 大人", (r[225]["readers"], r[225]["adults"], round(r[225]["i1_share"] * 100)), (25, 360, 7))
    # n09・n10 手習い
    ev = events(27059)
    ok("n09 字を教えた人 (子 6 人)", sorted(e["who"] for e in ev if e["type"] == "字を教える" and "子 6 人" in e["text"]), sorted(["ソナ75", "トナ77", "ヒセ88"]))
    ok("n09 燃える石を掘った人", [(e["who"], "500 kg 掘って" in e["text"]) for e in ev if e["type"] == "燃える石を掘る"], [("セオ88", True)])
    ok("n10 読めるようになった子", len([e for e in ev if e["type"] == "字を習う" and "読み書きできるようになった" in e["text"]]), 12)
    # n11〜n15 知らせ
    n228 = [n for n in i4["notes"]["228"] if n["day"] == 27359]
    ok("n11 228年夏の知らせの家", len({n["house"] for n in n228}), 4)
    ok("n12 27360 日目に書いた人", sorted(e["who"] for e in events(27360) if e["type"] == "知らせを書く"), sorted(["オネ83", "ワユ88", "ケセ96", "ケセ98"]))
    ok("n13 ムイ12の家の知らせ", [n["text"] for n in n228 if n["house"] == "ムイ12の家"], ["ヤギは草の140頭分をこえている。よそのヤギは受けず、夏は畑を落とさず刈ろう"])
    ok("n14 228年 知らせ 枚・家", (r[228]["notes"], r[228]["note_houses"]), (7, 4))
    ok("n14 227年 使った回", i4["used"]["227"]["n"], 20)
    ok("n15 229年 知らせ 枚・家", (r[229]["notes"], r[229]["note_houses"]), (6, 4))
    ok("n15 知らせ板の目標がそろった日", label(i4["f"]["i2"]), "229年120日目")
    # n16・n17 231年
    ok("n16 231年 読める大人 / 大人", (r[231]["readers"], r[231]["adults"], round(r[231]["i1_share"] * 100)), (99, 380, 26))
    ok("n17 231年 字の仕事 %", round(r[231]["i3_share"] * 100, 1), 1.7)
    # n18 セヤ105 の声
    ok("n18 セヤ105 の声", any(e["type"] == "話す" and e["who"] == "セヤ105" and "字の読み書きも、そろそろ覚えたいな" in e["text"] for e in events(27839)), True)
    # n23・n24 232年31日目
    ev = events(27870)
    ok("n23 燃える石を掘った人", [(e["who"], "500 kg 掘って" in e["text"]) for e in ev if e["type"] == "燃える石を掘る"], [("ホミ74", True)])
    ok("n23 知らせを書いた人", sorted(e["text"].split(" が")[0] for e in ev if e["type"] == "知らせを書く"), sorted(["ハソ4の家の ケセ96", "ラニ58の家の オネ98"]))
    ok("n24 帳をつけた人", len({e["who"] for e in ev if e["type"] == "帳をつける"}), 8)
    ok("n24 子 6 人に教えた人", [e["who"] for e in ev if e["type"] == "字を教える" and "子 6 人" in e["text"]], ["ケセ98"])
    ok("n24 教わる子がいなかった先生", len([e for e in ev if e["type"] == "字を教える" and "教わる子がいなかった" in e["text"]]), 8)
    # n25〜n28 頼み書き 0・233年
    for y in (232, 233):
        ok(f"n25・n26 {y}年 頼みを書いた家・受けた家", (q[y]["wrote"], q[y]["took"], q[y]["req_houses"], q[y]["taker_houses"]), (0, 0, 0, 0))
    ok("n28 読める大人 232・233年 %", (round(q[232]["r_share"] * 100), round(q[233]["r_share"] * 100)), (28, 32))
    ok("n28 233年 食べ物でない仕事 %", round(q[233]["p3_share"] * 100), 32)
    ok("n28 233年 蓄え・ききん", (q[233]["store_end"], q[233]["famine"]), (340, 0))
    ok("n29 233年 人", (r[232]["pop"], q[233]["pop"]), (700, 717))
    ok("n29 ソワ58 が亡くなった (232年の年報)", "ソワ58 (63 歳) — 年をとって 232年120日目" in report(232), True)
    # n27 500 kg = 掘る 1 人日 = まき集め 約 44 人日 (s3 の換算 1 人日 = 11.25 kg)
    ok("n27 500 kg はまき集めの約 44 人日", round(500 / 11.25), 44)
    print("ぜんぶ合った" if not bad else f"合わない: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
