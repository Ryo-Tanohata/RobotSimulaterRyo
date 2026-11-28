"""年報の動画の台本 (1 年 1 本、2〜3 分)。解説の係の文 (reports/explain/year<年>.json) と、係が読んだ数 (/tmp/explain_data_<年>.json) から作る。
   python3.13 script.py <explain_data.json> <reports/explain/yearY.json> <voices.json> <出力フォルダ>
   → <出力>/lines.json (tools/voicevox/synth.py が読む。1 文ごとに話す人の声) と <出力>/script.json (話す人・顔・図・字幕)

並び:
  1. 案内役 (まとめ役) が始める: 年・人の数・ひとことの気分 (3 つの大事なことの顔から)
  2. 案内役が 3 つの大事なことを話す (まとめ役が選んだ 3 つ。顔もまとめ役の選んだもの)。大きな年は、まとめ役の動画の文 (video.lines) を 3 つまで続けて
  3. 分野の係 4 人が、自分の分野の吹き出しを 1〜3 文 (はじめの文に名のり)。吹き出しが 0〜1 の係は、まだ出ていない自分の図の「図の見かた」を 1 文足す
  4. 案内役が閉じる
文の数は、係と事実の確かめの係が確かめた文 (year<年>.json) と、年・人の数だけを使う。新しい数は作らない。
中の呼び名 (d1・t5 など) と ○ × は話さない (plain)。物差しの吹き出しは d1_rows の ○ × からふつうの言葉で作りなおす (phase_text)。
同じ話の図 (人の数の線とタイルなど) は 2 度出さず、2 度めは近い別の図にする (TOPIC・ALT)。
字幕 (text) は係の文のまま。読み上げ (say) は、かっこの中の言いかえを省き、記号を読める形にする。
"""
import json
import re
import sys
from pathlib import Path

D = json.load(open(sys.argv[1], encoding="utf-8"))
X = json.load(open(sys.argv[2], encoding="utf-8"))
V = json.load(open(sys.argv[3], encoding="utf-8"))
OUT = Path(sys.argv[4]); OUT.mkdir(parents=True, exist_ok=True)
Y = X["year"]
P = V["people"]
G = V["guide"]
ORDER = ["pop", "life", "know", "out"]
TEAM_JA = {"pop": "人口の係", "life": "くらしと食べ物の係", "know": "知恵と技術の係", "out": "よその村と町の係"}
# 図の見かたを使うときの、係ごとの図の順 (年報のダッシュボードの図を先に)
TEAM_CHARTS = {"pop": ["t_pop", "c_age", "f_vital", "f_health"], "life": ["c_food", "c_work", "t_store", "t_gdp", "f_food"],
               "know": ["t_lit", "f_edu", "f_env"], "out": ["f_ext", "f_price"]}
MAX_PER_TEAM = 3
# 同じ話の図 (線とタイルなど)。同じ話の図は 2 度出さず、2 度めは ALT の図にする (本人の直し 2026-11-24)
TOPIC = {"k_pop": "pop", "t_pop": "pop", "f_pop": "pop", "k_store": "store", "t_store": "store", "k_lit": "lit", "t_lit": "lit",
         "k_nonfood": "nonfood", "t_nonfood": "nonfood", "k_gdp": "gdp", "t_gdp": "gdp"}
ALT = {"pop": ["c_age", "f_vital"], "f_health": ["x_care", "k_imr"], "gdp": ["f_econ"], "store": ["f_food", "c_food"], "lit": ["f_edu"],
       "nonfood": ["c_work", "f_work"], "c_food": ["f_food"], "c_work": ["f_work"], "f_edu": ["k_lit"], "f_ext": ["f_price"], "k_imr": ["f_health"],
       "c_age": ["f_vital"], "f_vital": ["c_age"], "phase": ["f_vital"]}
# 中の呼び名 (d1・t5 など) は話さない。ふつうの言葉に (本人の直し 2026-11-24)
CODE_JA = {"d1": "寿命", "d2": "15 歳からの寿命", "d3": "人のふえかた", "d4": "生まれる子の数", "d5": "蓄えの守り", "d6": "畑の働き",
           "t1": "町の頼み", "t2": "よそのために働いた家", "t3": "食べ物でない仕事", "t4": "暮らしの守り", "h1": "子の手当て",
           "p1": "果たした頼み", "p2": "よその家のために働いた家", "p3": "食べ物でない仕事", "p4": "暮らしの守り",
           "i1": "読める大人", "i2": "知らせ板", "i3": "字の仕事", "i4": "暮らしの守り"}
CODE = r"(?<![A-Za-z0-9])([a-z])([0-9])(?![0-9A-Za-z])"


def plain(t):
    """字幕と読み上げから、中の呼び名 (d1〜d4・t5 など) と ○ × をなくす。知らない呼び名は消して知らせる"""
    t = re.sub(CODE + r"\s*〜\s*" + CODE, lambda m: f"{CODE_JA.get(m.group(1) + m.group(2), '')}から{CODE_JA.get(m.group(3) + m.group(4), '')}まで", t)

    def one(m):
        k = m.group(1) + m.group(2)
        if k not in CODE_JA:
            print(f"知らない呼び名 {k} を消した: {t}", file=sys.stderr)
        return CODE_JA.get(k, "")
    t = re.sub(CODE, one, t)
    t = t.replace(" ○ ", "よい形").replace("○", "よい形").replace(" × ", "まだ").replace("×", "まだ")
    return re.sub(r"  +", " ", t)


def phase_text(b):
    """物差しの吹き出しは、ふつうの言葉で作りなおす (D1 のとき。数は d1_rows の ○ × だけ)"""
    rows = D.get("d1_rows") or []
    if D.get("phase_panel") != "d1" or not rows:
        return plain(b["text"])
    r = rows[-1]
    ok = [CODE_JA[k] for k in ("d1", "d2", "d3", "d4") if r.get(k + "_ok")]
    ng = [CODE_JA[k] for k in ("d1", "d2", "d3", "d4") if not r.get(k + "_ok")]
    if not ng:
        t = "寿命や生まれる子の数は、江戸時代の村の記録どおりの幅に入っています。"
    else:
        t = (("や".join(ok) + "は、江戸時代の村の記録どおりの幅に入っています。") if ok else "") + "や".join(ng) + "は、記録の幅の外です。"
    if r.get("d5_ok"):
        t += "蓄えの守りの線も超えています。"
    else:
        t += ("蓄えの守りの線だけは、まだ下です。" if not ng else "蓄えの守りの線も、まだ下です。")
    return t


def say_of(t):
    """読み上げの形: (かっこ) の言いかえを省く。記号を言葉に"""
    s = re.sub(r"\s*[(（][^()（）]*[)）]", "", t)
    s = s.replace("○", "まる").replace("×", "ばつ").replace("〜", "から").replace("・", "、")
    s = re.sub(r"(\d),(\d{3})", r"\1\2", s)
    s = re.sub(r"\s+", "", s)
    return s


lines = []
shown = set()  # 出した図の話 (TOPIC)


def pick_chart(chart, text):
    """同じ話の図を 2 度出さない。2 度めは ALT から、まだ出ていない図"""
    if chart.startswith("title"):
        return chart
    top = TOPIC.get(chart, chart)
    if top in shown:
        alts = list(ALT.get(top, []))
        if chart == "f_health" and not any(w in text for w in ("手当て", "薬")):
            alts = ["k_imr", "x_care"]
        for a in alts:
            if TOPIC.get(a, a) not in shown:
                chart = a
                break
        else:
            print(f"図 {chart} は 2 度め (かわりがない): {text}", file=sys.stderr)
    shown.add(TOPIC.get(chart, chart))
    return chart


def add(who, expr, text, chart, kind, title=None):
    p = P[who]
    n = len(lines) + 1
    text = plain(text)
    chart = pick_chart(chart, text)
    lines.append({"id": f"s{n:02d}", "who": who, "name": p["name"], "role": p["role"], "expr": expr, "text": text, "say": say_of(text),
                  "chart": chart, "kind": kind, "title": title})


# 1. 始め
top3 = X.get("top3") or []
ex = [h.get("expr") for h in top3]
good, bad = sum(e in ("smile", "surprise") for e in ex), ex.count("concern")
if bad == 0:
    mood = "うれしい知らせの多い年でした。"
elif good == 0:
    mood = "心配なことの多い年でした。みんなで見ていきましょう。"
elif good >= bad:
    mood = "うれしい知らせが多く、気になることも少しある年でした。"
else:
    mood = "気になることの多い年でしたが、よいこともありました。"
pop = D["this_year"]["pop"]
name = D.get("year_name")
add(G, "smile", f"川辺の村の {Y}年のまとめです。案内役の{P[G]['name']}が、村の係といっしょにお話ししますね。", "title", "open")
add(G, "smile" if bad == 0 else "neutral",
    f"年の終わりの村の人は {pop} 人。" + (f"村の人はこの年を「{name}」と名づけました。" if name else "") + mood, "t_pop", "open")

# 2. 3 つの大事なこと
NUM = ["1 つめ", "2 つめ", "3 つめ"]
for i, h in enumerate(top3[:3]):
    add(G, h.get("expr") or "neutral", f"{NUM[i]}は「{h['title']}」。{h['text']}", h.get("chart") or "title", "top3", title=h["title"])

# 2b. 大きな年 (explain_data.py の big_event) だけ、まとめ役が書いた動画の文 (video.lines) を案内役が読む (前はずんだもんの声の別の動画だった)
vid = X.get("video") or {}
if vid.get("qualifies"):
    for v in (vid.get("lines") or [])[:3]:
        add(G, v.get("expr") or "surprise", v["text"], v.get("chart") or "title", "big")

# 3. 分野の係
used = {h.get("chart") for h in top3}
for team in ORDER:
    who = V["teams"][team]
    bs = [b for b in X.get("bubbles") or [] if b.get("team") == team][:MAX_PER_TEAM]
    rows = [(b.get("expr") or "neutral", phase_text(b) if b["chart"] == "phase" else b["text"], b["chart"]) for b in bs]
    if len(rows) < 2:  # 吹き出しが 0〜1 の係は、まだ出ていない自分の図の「図の見かた」を 1 文足す (図の読みかたの話)
        for cid in TEAM_CHARTS[team]:
            n = (X.get("notes") or {}).get(cid)
            if n and cid not in used and cid not in {c for _, _, c in rows}:
                rows.append(("neutral", n["text"], cid))
                break
    for k, (e, t, c) in enumerate(rows):
        if k == 0:
            t = f"{TEAM_JA[team]}の{P[who]['name']}です。" + t
        add(who, e, t, c, team)
        used.add(c)

# 4. 閉じ
worry = [h["title"] for h in top3 if h.get("expr") == "concern"]
close = f"{Y}年のまとめは、ここまでです。" + (f"「{worry[0]}」のことは、来年も見ていきますね。" if worry else "来年も、村のようすをお伝えしますね。")
add(G, "smile" if not worry else "neutral", close, "title_end", "close")

vo = []
for ln in lines:
    p = P[ln["who"]]
    vo.append({"id": ln["id"], "text": ln["text"], "say": ln["say"], "style": p["style_id"], "vvm": p["vvm"],
               "speed": p.get("speed", 1.0), "pitch": p.get("pitch", 0.0), "intonation": p.get("intonation", 1.0)})
(OUT / "lines.json").write_text(json.dumps(vo, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "script.json").write_text(json.dumps({"year": Y, "lines": lines}, ensure_ascii=False, indent=1), encoding="utf-8")
chars = sum(len(ln["say"]) for ln in lines)
print(f"{Y}年: {len(lines)} 文・読み上げ {chars} 字 (見込み 約 {chars / 7.5 + len(lines) * 1.1:.0f} 秒)")
