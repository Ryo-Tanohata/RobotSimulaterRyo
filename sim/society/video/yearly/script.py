"""年報の動画の台本 (1 年 1 本、2〜3 分)。解説の係の文 (reports/explain/year<年>.json) と、係が読んだ数 (/tmp/explain_data_<年>.json) から作る。
   python3.13 script.py <explain_data.json> <reports/explain/yearY.json> <voices.json> <出力フォルダ>
   → <出力>/lines.json (tools/voicevox/synth.py が読む。1 文ごとに話す人の声) と <出力>/script.json (話す人・顔・図・字幕)

並び:
  1. 案内役 (まとめ役) が始める: 年・人の数・ひとことの気分 (3 つの大事なことの顔から)
  2. 案内役が 3 つの大事なことを話す (まとめ役が選んだ 3 つ。顔もまとめ役の選んだもの)。大きな年は、まとめ役の動画の文 (video.lines) を 3 つまで続けて
  3. 分野の係 4 人が、自分の分野の吹き出しを 1〜3 文 (はじめの文に名のり)。吹き出しが 0〜1 の係は、まだ出ていない自分の図の「図の見かた」を 1 文足す
  4. 案内役が閉じる
文の数は、係と事実の確かめの係が確かめた文 (year<年>.json) と、年・人の数だけを使う。新しい数は作らない。
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


def say_of(t):
    """読み上げの形: (かっこ) の言いかえを省く。記号を言葉に"""
    s = re.sub(r"\s*[(（][^()（）]*[)）]", "", t)
    s = s.replace("○", "まる").replace("×", "ばつ").replace("〜", "から").replace("・", "、")
    s = re.sub(r"(?<![A-Za-z])d([1-9])", r"ディー\1", s)
    s = re.sub(r"(\d),(\d{3})", r"\1\2", s)
    s = re.sub(r"\s+", "", s)
    return s


lines = []


def add(who, expr, text, chart, kind, title=None):
    p = P[who]
    n = len(lines) + 1
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
    rows = [(b.get("expr") or "neutral", b["text"], b["chart"]) for b in bs]
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
close = f"{Y}年のまとめは、ここまでです。" + (f"「{worry[0]}」ことは、来年も見ていきますね。" if worry else "来年も、村のようすをお伝えしますね。")
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
